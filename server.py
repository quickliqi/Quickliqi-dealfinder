from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session, init_db, engine
from models_db import DealModel, SettingsModel
import os
import logging
import json
import csv
import io
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

# Import models
from deal import Deal, DealCreate, DealUpdate, DealStatusUpdate, Candidate
from settings import Settings, SettingsUpdate

# Import services
from services.calculations import FinancialCalculator
from services.serpapi_scanner import SerpApiScanner

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = FastAPI(title="QuickLiqi API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize services
calculator = FinancialCalculator()
scanner = SerpApiScanner()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def model_to_dict(model) -> Dict[str, Any]:
    data = dict(model.__dict__)
    data.pop("_sa_instance_state", None)
    return data

# Dependency to get settings
async def get_settings(session: AsyncSession = Depends(get_session)) -> Settings:
    """Get current buyer criteria settings, create default if none exist."""
    result = await session.execute(select(SettingsModel))
    settings_row = result.scalars().first()
    if not settings_row:
        default_settings = Settings()
        session.add(SettingsModel(**default_settings.dict()))
        await session.commit()
        return default_settings
    return Settings(**model_to_dict(settings_row))

# Helper function to recalculate deal metrics
async def recalculate_deal_metrics(deal_data: Dict[str, Any], settings: Settings) -> Dict[str, Any]:
    """Recalculate and update deal metrics based on current settings."""
    calculated_metrics = calculator.calculate_deal_metrics(deal_data, settings)
    deal_data.update(calculated_metrics)
    return deal_data

# Settings endpoints
@api_router.get("/settings", response_model=Settings)
async def get_buyer_criteria(session: AsyncSession = Depends(get_session)):
    """Get current buyer criteria settings."""
    return await get_settings(session)

@api_router.put("/settings", response_model=Settings)
async def update_buyer_criteria(settings_update: SettingsUpdate, session: AsyncSession = Depends(get_session)):
    """Update buyer criteria settings and recalculate all deal metrics."""
    current_settings = await get_settings(session)

    update_data = settings_update.dict(exclude_unset=True)
    updated_settings = Settings(**{**current_settings.dict(), **update_data})

    result = await session.execute(select(SettingsModel))
    settings_row = result.scalars().first()
    if settings_row:
        for key, value in updated_settings.dict().items():
            setattr(settings_row, key, value)
    else:
        session.add(SettingsModel(**updated_settings.dict()))

    deals_result = await session.execute(select(DealModel))
    for deal_row in deals_result.scalars():
        deal_dict = model_to_dict(deal_row)
        updated_deal = await recalculate_deal_metrics(deal_dict, updated_settings)
        for key, value in updated_deal.items():
            if hasattr(deal_row, key):
                setattr(deal_row, key, value)

    await session.commit()
    logger.info("Settings updated and all deals recalculated")
    return updated_settings

# Deals endpoints
@api_router.get("/deals", response_model=List[Deal])
async def get_deals(status: Optional[str] = None, session: AsyncSession = Depends(get_session)):
    """Get all deals, optionally filtered by status."""
    stmt = select(DealModel)
    if status:
        stmt = stmt.where(DealModel.status == status)
    stmt = stmt.order_by(DealModel.created_at.desc())
    result = await session.execute(stmt)
    return [Deal(**model_to_dict(d)) for d in result.scalars().all()]

@api_router.post("/deals", response_model=Deal)
async def create_deal(deal_create: DealCreate, session: AsyncSession = Depends(get_session)):
    """Create a new deal from candidate or manual entry."""
    settings = await get_settings(session)

    deal_data = deal_create.dict()
    deal_data["created_at"] = datetime.utcnow()
    deal_data["status"] = "New"

    if not deal_data.get("arv_estimate"):
        deal_data["arv_estimate"] = deal_data["list_price"] * 1.3

    deal_data["opportunity_score"] = calculator.calculate_opportunity_score(deal_data)
    deal_data = await recalculate_deal_metrics(deal_data, settings)

    deal = Deal(**deal_data)
    session.add(DealModel(**deal.dict()))
    await session.commit()

    logger.info(f"Created new deal: {deal.address}")
    return deal

@api_router.get("/deals/{deal_id}", response_model=Deal)
async def get_deal(deal_id: str, session: AsyncSession = Depends(get_session)):
    """Get specific deal by ID."""
    result = await session.execute(select(DealModel).where(DealModel.id == deal_id))
    deal_row = result.scalars().first()
    if not deal_row:
        raise HTTPException(status_code=404, detail="Deal not found")

    return Deal(**model_to_dict(deal_row))

@api_router.put("/deals/{deal_id}", response_model=Deal)
async def update_deal(deal_id: str, deal_update: DealUpdate, session: AsyncSession = Depends(get_session)):
    """Update deal and recalculate metrics."""
    result = await session.execute(select(DealModel).where(DealModel.id == deal_id))
    deal_row = result.scalars().first()
    if not deal_row:
        raise HTTPException(status_code=404, detail="Deal not found")

    update_data = deal_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(deal_row, key, value)

    financial_fields = {
        'arv_estimate', 'repair_estimate', 'monthly_rent',
        'taxes_insurance_monthly', 'assignment_fee', 'financing_pref'
    }
    if any(field in update_data for field in financial_fields):
        settings = await get_settings(session)
        deal_dict = model_to_dict(deal_row)
        deal_dict = await recalculate_deal_metrics(deal_dict, settings)
        for key, value in deal_dict.items():
            if hasattr(deal_row, key):
                setattr(deal_row, key, value)

    await session.commit()
    logger.info(f"Updated deal: {deal_id}")
    return Deal(**model_to_dict(deal_row))

@api_router.patch("/deals/{deal_id}/status", response_model=Deal)
async def update_deal_status(deal_id: str, status_update: DealStatusUpdate, session: AsyncSession = Depends(get_session)):
    """Update deal status (for pipeline drag-and-drop)."""
    result = await session.execute(select(DealModel).where(DealModel.id == deal_id))
    deal_row = result.scalars().first()
    if not deal_row:
        raise HTTPException(status_code=404, detail="Deal not found")

    deal_row.status = status_update.status
    await session.commit()

    logger.info(f"Updated deal status: {deal_id} -> {status_update.status}")
    return Deal(**model_to_dict(deal_row))

@api_router.delete("/deals/{deal_id}")
async def delete_deal(deal_id: str, session: AsyncSession = Depends(get_session)):
    """Delete a deal."""
    result = await session.execute(select(DealModel).where(DealModel.id == deal_id))
    deal_row = result.scalars().first()
    if not deal_row:
        raise HTTPException(status_code=404, detail="Deal not found")
    await session.delete(deal_row)
    await session.commit()

    logger.info(f"Deleted deal: {deal_id}")
    return {"message": "Deal deleted successfully"}

# CSV Import endpoint
@api_router.post("/candidates/csv-import", response_model=List[Candidate])
async def import_csv(
    file: UploadFile = File(...),
    mapping: str = Form(...),
    filters: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    """Process uploaded CSV file and return candidate properties."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Parse form data
        field_mapping = json.loads(mapping)
        filter_params = json.loads(filters)
        
        # Read and parse CSV
        content = await file.read()
        csv_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        candidates = []
        settings = await get_settings(session)
        
        for row in csv_reader:
            try:
                # Map CSV fields to candidate data
                candidate_data = {}
                for field, header in field_mapping.items():
                    if header and header in row:
                        value = row[header].strip().replace('"', '') if row[header] else ''
                        
                        # Convert numeric fields
                        if field in ['list_price', 'days_on_market', 'beds', 'baths', 'sqft', 'year_built']:
                            try:
                                if field in ['beds', 'days_on_market', 'year_built']:
                                    candidate_data[field] = int(float(value.replace(',', ''))) if value else 0
                                elif field in ['baths']:
                                    candidate_data[field] = float(value) if value else 0
                                else:
                                    candidate_data[field] = float(value.replace(',', '').replace('$', '')) if value else 0
                            except (ValueError, AttributeError):
                                candidate_data[field] = 0
                        else:
                            candidate_data[field] = value
                
                # Apply basic filters
                list_price = candidate_data.get('list_price', 0)
                dom = candidate_data.get('days_on_market', 0)
                beds = candidate_data.get('beds', 0)
                
                if (dom < filter_params.get('dom_min', 100) or
                    list_price > filter_params.get('price_max', 1000000) or
                    beds < filter_params.get('beds_min', 1) or
                    not candidate_data.get('address')):
                    continue
                
                # Calculate opportunity score
                candidate_data['opportunity_score'] = calculator.calculate_opportunity_score(candidate_data)
                
                # Determine deal signal (simplified)
                deal_signal = "Green" if candidate_data['opportunity_score'] >= 60 else "Red"
                candidate_data['deal_signal'] = deal_signal
                
                # Generate offer suggestion
                if deal_signal == "Green":
                    arv_est = list_price * 1.3
                    mao = arv_est * 0.7 - 20000 - 5000  # Assume $20k repairs, $5k fee
                    candidate_data['offer_suggestion'] = f"Cash offer ≈ ${int(mao):,} (ARV×70% − repairs − fee)."
                else:
                    candidate_data['offer_suggestion'] = "Requires analysis - below criteria thresholds."
                
                # Generate photo URL
                candidate_data['photo_url'] = f"https://images.unsplash.com/photo-{1560000000000 + hash(candidate_data['address']) % 100000000}?w=400&h=300&fit=crop"
                
                # Create candidate
                candidate = Candidate(**candidate_data)
                candidates.append(candidate)
                
            except Exception as e:
                logger.warning(f"Error processing CSV row: {e}")
                continue
        
        # Sort by opportunity score
        candidates.sort(key=lambda x: x.opportunity_score, reverse=True)
        
        logger.info(f"Processed CSV import: {len(candidates)} candidates")
        return candidates[:50]  # Return top 50
        
    except Exception as e:
        logger.error(f"CSV import error: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")

# SERPAPI Scan endpoint
@api_router.post("/candidates/scan", response_model=List[Candidate])
async def scan_market_opportunities(
    city: str = Form(...),
    state: str = Form(...),
    filters: str = Form("{}")
):
    """Scan market for new opportunities using SERPAPI."""
    if not scanner.is_enabled():
        raise HTTPException(status_code=400, detail="SERPAPI_KEY not configured")
    
    try:
        filter_params = json.loads(filters) if filters else {}
        
        candidates = scanner.scan_market(city, state, filter_params)
        
        logger.info(f"SERPAPI scan completed: {len(candidates)} candidates found")
        return candidates
        
    except Exception as e:
        logger.error(f"Market scan error: {e}")
        raise HTTPException(status_code=400, detail=f"Error scanning market: {str(e)}")

# Export endpoint
@api_router.get("/export")
async def export_deals(session: AsyncSession = Depends(get_session)):
    """Export all deals to CSV format."""
    result = await session.execute(select(DealModel).order_by(DealModel.created_at.desc()))
    deals = [Deal(**model_to_dict(d)) for d in result.scalars().all()]
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    headers = [
        'Address', 'City', 'State', 'Price', 'DOM', 'Status', 'Signal', 'Score',
        'Beds', 'Baths', 'SqFt', 'Type', 'Agent', 'ARV', 'Repairs', 'Rent',
        'Cash Flow', 'CoC %', 'DSCR', 'Notes'
    ]
    writer.writerow(headers)
    
    # Data rows
    for deal in deals:
        writer.writerow([
            deal.address,
            deal.city,
            deal.state,
            deal.list_price,
            deal.days_on_market,
            deal.status,
            deal.deal_signal,
            deal.opportunity_score,
            deal.beds,
            deal.baths,
            deal.sqft,
            deal.property_type,
            deal.listing_agent_name,
            deal.arv_estimate,
            deal.repair_estimate,
            deal.monthly_rent,
            deal.cash_flow_monthly,
            deal.coc_pct,
            deal.dscr,
            deal.notes
        ])
    
    output.seek(0)
    
    # Create streaming response
    def iter_csv():
        yield output.getvalue()
    
    return StreamingResponse(
        iter(iter_csv()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=quickliqi_deals_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

# Recalculate metrics endpoint
@api_router.post("/calculate-metrics")
async def recalculate_all_metrics(session: AsyncSession = Depends(get_session)):
    """Recalculate financial metrics for all deals based on current settings."""
    settings = await get_settings(session)
    updated_count = 0

    result = await session.execute(select(DealModel))
    for deal_row in result.scalars():
        try:
            deal_dict = model_to_dict(deal_row)
            updated_deal = await recalculate_deal_metrics(deal_dict, settings)
            for key, value in updated_deal.items():
                if hasattr(deal_row, key):
                    setattr(deal_row, key, value)
            updated_count += 1
        except Exception as e:
            logger.error(f"Error recalculating deal {deal_row.id}: {e}")

    await session.commit()
    logger.info(f"Recalculated metrics for {updated_count} deals")
    return {"message": f"Recalculated metrics for {updated_count} deals"}

# Health check endpoint
@api_router.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)):
    """Health check endpoint."""
    try:
        await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "serpapi_enabled": scanner.is_enabled(),
        "database": db_status,
    }

# Legacy root endpoint
@api_router.get("/")
async def root():
    return {"message": "QuickLiqi API is running"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    await init_db()


@app.on_event("shutdown")
async def shutdown_db_client():
    await engine.dispose()
