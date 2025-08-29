# QuickLiqi Backend Implementation Contracts

## API Endpoints Design

### Settings Management
- `GET /api/settings` - Get buyer criteria settings (singleton)
- `PUT /api/settings` - Update buyer criteria settings
- Auto-create default settings if none exist

### Deals Management
- `GET /api/deals` - Get all deals with optional status filter
- `POST /api/deals` - Create new deal from candidate
- `GET /api/deals/{id}` - Get specific deal details
- `PUT /api/deals/{id}` - Update deal (triggers metric recalculation)
- `DELETE /api/deals/{id}` - Delete deal
- `PATCH /api/deals/{id}/status` - Update deal status (for drag-drop)

### Candidates Management  
- `GET /api/candidates` - Get filtered candidates list
- `POST /api/candidates/csv-import` - Process CSV file and return candidates
- `POST /api/candidates/scan` - SERPAPI scan for new opportunities
- `DELETE /api/candidates/{id}` - Remove candidate after adding to deals

### Data Processing
- `POST /api/calculate-metrics` - Recalculate deal metrics based on settings
- `POST /api/export` - Generate CSV export of deals

## Database Schema Implementation

### MongoDB Collections

**deals** collection:
```javascript
{
  _id: ObjectId,
  created_at: Date,
  status: String, // enum: New, Analyzing, Offer Sent, etc.
  source: String, // redfin_csv, serpapi, manual_add
  
  // Property Info
  address: String,
  city: String,
  state: String,
  zip: String,
  lat: Number,
  lng: Number,
  
  // Pricing & Market Data
  list_price: Number,
  original_price: Number,
  days_on_market: Number,
  
  // Property Details
  property_type: String,
  beds: Number,
  baths: Number,
  sqft: Number,
  lot_size_sqft: Number,
  year_built: Number,
  
  // Listing Info
  link: String,
  photo_url: String,
  listing_agent_name: String,
  listing_agent_phone: String,
  listing_agent_email: String,
  brokerage: String,
  
  // Analysis Fields
  notes: String,
  opportunity_score: Number,
  arv_estimate: Number,
  repair_estimate: Number,
  
  // Investment Analysis
  monthly_rent: Number,
  taxes_insurance_monthly: Number,
  assignment_fee: Number,
  financing_pref: String, // cash, creative, any
  
  // Calculated Metrics (computed on save)
  mao_cash: Number,
  mao_creative: Number,
  noi_monthly: Number,
  debt_service_monthly: Number,
  cash_flow_monthly: Number,
  coc_pct: Number,
  dscr: Number,
  deal_signal: String, // Green, Red
  deal_notes: String,
  offer_suggestion: String
}
```

**settings** collection (singleton):
```javascript
{
  _id: ObjectId,
  min_coc_pct: Number,
  min_dscr: Number,
  min_monthly_cf: Number,
  max_rehab: Number,
  max_down_payment_pct: Number,
  max_interest_rate: Number,
  term_years: Number,
  arv_discount_pct: Number,
  refi_ltv_pct: Number,
  vacancy_pct: Number,
  mgmt_pct: Number,
  maintenance_pct: Number,
  other_expense_pct: Number,
  rent_input_mode: String // manual, csv
}
```

## Frontend Integration Changes

### Remove Mock Data
- Remove all imports from `mock.js` in components
- Replace mock state with API calls using axios

### API Integration Points
1. **Dashboard.jsx**: Replace mock data with API calls
   - Load deals: `GET /api/deals`
   - Load settings: `GET /api/settings`
   - Update deal status: `PATCH /api/deals/{id}/status`

2. **CandidatesTable.jsx**: 
   - Add candidate to deals: `POST /api/deals` (with candidate data)

3. **BuyerCriteriaModal.jsx**:
   - Save settings: `PUT /api/settings`
   - Trigger recalculation: `POST /api/calculate-metrics`

4. **CSVImportModal.jsx**:
   - Process CSV: `POST /api/candidates/csv-import`

5. **DealDrawer.jsx**:
   - Update deal: `PUT /api/deals/{id}`
   - Delete deal: `DELETE /api/deals/{id}`

## SERPAPI Integration

### Environment Variables
- Add `SERPAPI_KEY=pJ3BXrtuu38qdZhDaYvptNr5` to backend/.env
- Enable scan functionality when key is present

### Scan Implementation
- Search queries for Redfin, Zillow, Realtor.com
- Parse results for address, price, DOM, beds, baths, agent info
- Apply same scoring algorithm as CSV import
- Return candidates array for frontend processing

## Financial Calculations Engine

### Calculation Triggers
- New deal creation
- Deal field updates (arv_estimate, repair_estimate, monthly_rent, etc.)
- Settings updates (recalculate all deals)

### Calculation Logic
Implement exact formulas from spec:
1. Operating expenses and NOI calculation
2. Cash MAO (70% rule)  
3. Creative finance MAO (DSCR-based)
4. Scenario selection (cash vs creative)
5. Green/Red signal determination
6. Offer suggestion generation

## Error Handling & Validation
- Validate required fields on deal creation
- Handle SERPAPI rate limits and errors gracefully  
- Validate numeric inputs and ranges
- Provide meaningful error messages

## Testing Approach
- Test all CRUD operations
- Test financial calculations with known inputs
- Test CSV parsing with sample Redfin data
- Test SERPAPI integration (if available)
- Test settings updates and deal recalculation