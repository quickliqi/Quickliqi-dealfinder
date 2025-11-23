from pydantic import BaseModel, Field
from typing import Literal, Optional

# Rent input mode enum
RentInputMode = Literal["manual", "csv"]

class Settings(BaseModel):
    # Financial Thresholds
    min_coc_pct: float = 12.0
    min_dscr: float = 1.25
    min_monthly_cf: float = 250.0
    max_rehab: float = 60000.0
    
    # Financing Parameters
    max_down_payment_pct: float = 0.20
    max_interest_rate: float = 8.0
    term_years: int = 30
    arv_discount_pct: float = 0.70
    refi_ltv_pct: float = 0.75
    
    # Operating Expense Assumptions (percentages)
    vacancy_pct: float = 5.0
    mgmt_pct: float = 8.0
    maintenance_pct: float = 5.0
    other_expense_pct: float = 17.0
    
    # Additional Settings
    rent_input_mode: RentInputMode = "manual"

class SettingsUpdate(BaseModel):
    min_coc_pct: Optional[float] = None
    min_dscr: Optional[float] = None
    min_monthly_cf: Optional[float] = None
    max_rehab: Optional[float] = None
    max_down_payment_pct: Optional[float] = None
    max_interest_rate: Optional[float] = None
    term_years: Optional[int] = None
    arv_discount_pct: Optional[float] = None
    refi_ltv_pct: Optional[float] = None
    vacancy_pct: Optional[float] = None
    mgmt_pct: Optional[float] = None
    maintenance_pct: Optional[float] = None
    other_expense_pct: Optional[float] = None
    rent_input_mode: Optional[RentInputMode] = None