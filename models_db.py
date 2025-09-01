from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class SettingsModel(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    min_coc_pct: Mapped[float] = mapped_column(Float, default=12.0)
    min_dscr: Mapped[float] = mapped_column(Float, default=1.25)
    min_monthly_cf: Mapped[float] = mapped_column(Float, default=250.0)
    max_rehab: Mapped[float] = mapped_column(Float, default=60000.0)
    max_down_payment_pct: Mapped[float] = mapped_column(Float, default=0.20)
    max_interest_rate: Mapped[float] = mapped_column(Float, default=8.0)
    term_years: Mapped[int] = mapped_column(Integer, default=30)
    arv_discount_pct: Mapped[float] = mapped_column(Float, default=0.70)
    refi_ltv_pct: Mapped[float] = mapped_column(Float, default=0.75)
    vacancy_pct: Mapped[float] = mapped_column(Float, default=5.0)
    mgmt_pct: Mapped[float] = mapped_column(Float, default=8.0)
    maintenance_pct: Mapped[float] = mapped_column(Float, default=5.0)
    other_expense_pct: Mapped[float] = mapped_column(Float, default=17.0)
    rent_input_mode: Mapped[str] = mapped_column(String(10), default="manual")


class DealModel(Base):
    __tablename__ = "deals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), default="New")
    source: Mapped[str] = mapped_column(String(50), default="manual_add")

    address: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    zip: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    list_price: Mapped[float] = mapped_column(Float, nullable=False)
    original_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    days_on_market: Mapped[int] = mapped_column(Integer, nullable=False)

    property_type: Mapped[str] = mapped_column(String(50), default="SFR")
    beds: Mapped[int] = mapped_column(Integer, nullable=False)
    baths: Mapped[float] = mapped_column(Float, nullable=False)
    sqft: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lot_size_sqft: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    year_built: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    listing_agent_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    listing_agent_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    listing_agent_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    brokerage: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    opportunity_score: Mapped[float] = mapped_column(Float, default=0)
    arv_estimate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    repair_estimate: Mapped[float] = mapped_column(Float, default=0)

    monthly_rent: Mapped[float] = mapped_column(Float, default=0)
    taxes_insurance_monthly: Mapped[float] = mapped_column(Float, default=0)
    assignment_fee: Mapped[float] = mapped_column(Float, default=0)
    financing_pref: Mapped[str] = mapped_column(String(10), default="any")

    mao_cash: Mapped[float] = mapped_column(Float, default=0)
    mao_creative: Mapped[float] = mapped_column(Float, default=0)
    noi_monthly: Mapped[float] = mapped_column(Float, default=0)
    debt_service_monthly: Mapped[float] = mapped_column(Float, default=0)
    cash_flow_monthly: Mapped[float] = mapped_column(Float, default=0)
    coc_pct: Mapped[float] = mapped_column(Float, default=0)
    dscr: Mapped[float] = mapped_column(Float, default=0)
    deal_signal: Mapped[str] = mapped_column(String(10), default="Red")
    deal_notes: Mapped[str] = mapped_column(Text, default="")
    offer_suggestion: Mapped[str] = mapped_column(Text, default="")
