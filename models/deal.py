from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid

# Deal status enum
DealStatus = Literal[
    "New", "Analyzing", "Offer Sent", "Offer Accepted", 
    "Buyer Found", "Under Contract", "Closed", "Dead"
]

# Property type enum  
PropertyType = Literal["SFR", "Condo/Townhome", "Multi-Family"]

# Financing preference enum
FinancingPref = Literal["cash", "creative", "any"]

# Deal signal enum
DealSignal = Literal["Green", "Red"]

class DealBase(BaseModel):
    # Property Info
    address: str
    city: str
    state: str = Field(..., max_length=2)
    zip: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    
    # Pricing & Market Data
    list_price: float
    original_price: Optional[float] = None
    days_on_market: int
    
    # Property Details
    property_type: PropertyType = "SFR"
    beds: int
    baths: float
    sqft: Optional[float] = None
    lot_size_sqft: Optional[float] = None
    year_built: Optional[int] = None
    
    # Listing Info
    link: Optional[str] = None
    photo_url: Optional[str] = None
    listing_agent_name: Optional[str] = None
    listing_agent_phone: Optional[str] = None
    listing_agent_email: Optional[str] = None
    brokerage: Optional[str] = None
    
    # Analysis Fields
    notes: Optional[str] = None
    opportunity_score: Optional[float] = 0
    arv_estimate: Optional[float] = None
    repair_estimate: Optional[float] = 0
    
    # Investment Analysis
    monthly_rent: Optional[float] = 0
    taxes_insurance_monthly: Optional[float] = 0
    assignment_fee: Optional[float] = 0
    financing_pref: FinancingPref = "any"

class DealCreate(DealBase):
    source: str = "manual_add"

class Deal(DealBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: DealStatus = "New"
    source: str = "manual_add"
    
    # Calculated Metrics (computed)
    mao_cash: Optional[float] = 0
    mao_creative: Optional[float] = 0
    noi_monthly: Optional[float] = 0
    debt_service_monthly: Optional[float] = 0
    cash_flow_monthly: Optional[float] = 0
    coc_pct: Optional[float] = 0
    dscr: Optional[float] = 0
    deal_signal: Optional[DealSignal] = "Red"
    deal_notes: Optional[str] = ""
    offer_suggestion: Optional[str] = ""

class DealUpdate(BaseModel):
    # Only allow updating certain fields
    status: Optional[DealStatus] = None
    notes: Optional[str] = None
    arv_estimate: Optional[float] = None
    repair_estimate: Optional[float] = None
    monthly_rent: Optional[float] = None
    taxes_insurance_monthly: Optional[float] = None
    assignment_fee: Optional[float] = None
    financing_pref: Optional[FinancingPref] = None

class DealStatusUpdate(BaseModel):
    status: DealStatus

class Candidate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    address: str
    city: str
    state: str
    list_price: float
    days_on_market: int
    property_type: PropertyType
    beds: int
    baths: float
    sqft: Optional[float] = None
    listing_agent_name: Optional[str] = None
    link: Optional[str] = None
    photo_url: Optional[str] = None
    opportunity_score: float = 0
    deal_signal: DealSignal = "Red"
    offer_suggestion: str = ""