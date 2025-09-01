"""create deals and settings tables

Revision ID: 0001
Revises: 
Create Date: 2024-09-01
"""

from alembic import op
import sqlalchemy as sa


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "settings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("min_coc_pct", sa.Float, nullable=False, default=12.0),
        sa.Column("min_dscr", sa.Float, nullable=False, default=1.25),
        sa.Column("min_monthly_cf", sa.Float, nullable=False, default=250.0),
        sa.Column("max_rehab", sa.Float, nullable=False, default=60000.0),
        sa.Column("max_down_payment_pct", sa.Float, nullable=False, default=0.20),
        sa.Column("max_interest_rate", sa.Float, nullable=False, default=8.0),
        sa.Column("term_years", sa.Integer, nullable=False, default=30),
        sa.Column("arv_discount_pct", sa.Float, nullable=False, default=0.70),
        sa.Column("refi_ltv_pct", sa.Float, nullable=False, default=0.75),
        sa.Column("vacancy_pct", sa.Float, nullable=False, default=5.0),
        sa.Column("mgmt_pct", sa.Float, nullable=False, default=8.0),
        sa.Column("maintenance_pct", sa.Float, nullable=False, default=5.0),
        sa.Column("other_expense_pct", sa.Float, nullable=False, default=17.0),
        sa.Column("rent_input_mode", sa.String(10), nullable=False, default="manual"),
    )

    op.create_table(
        "deals",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="New"),
        sa.Column("source", sa.String(50), nullable=False, default="manual_add"),
        sa.Column("address", sa.String, nullable=False),
        sa.Column("city", sa.String, nullable=False),
        sa.Column("state", sa.String(2), nullable=False),
        sa.Column("zip", sa.String, nullable=True),
        sa.Column("lat", sa.Float, nullable=True),
        sa.Column("lng", sa.Float, nullable=True),
        sa.Column("list_price", sa.Float, nullable=False),
        sa.Column("original_price", sa.Float, nullable=True),
        sa.Column("days_on_market", sa.Integer, nullable=False),
        sa.Column("property_type", sa.String(50), nullable=False, default="SFR"),
        sa.Column("beds", sa.Integer, nullable=False),
        sa.Column("baths", sa.Float, nullable=False),
        sa.Column("sqft", sa.Float, nullable=True),
        sa.Column("lot_size_sqft", sa.Float, nullable=True),
        sa.Column("year_built", sa.Integer, nullable=True),
        sa.Column("link", sa.Text, nullable=True),
        sa.Column("photo_url", sa.Text, nullable=True),
        sa.Column("listing_agent_name", sa.String, nullable=True),
        sa.Column("listing_agent_phone", sa.String, nullable=True),
        sa.Column("listing_agent_email", sa.String, nullable=True),
        sa.Column("brokerage", sa.String, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("opportunity_score", sa.Float, nullable=False, default=0),
        sa.Column("arv_estimate", sa.Float, nullable=True),
        sa.Column("repair_estimate", sa.Float, nullable=False, default=0),
        sa.Column("monthly_rent", sa.Float, nullable=False, default=0),
        sa.Column("taxes_insurance_monthly", sa.Float, nullable=False, default=0),
        sa.Column("assignment_fee", sa.Float, nullable=False, default=0),
        sa.Column("financing_pref", sa.String(10), nullable=False, default="any"),
        sa.Column("mao_cash", sa.Float, nullable=False, default=0),
        sa.Column("mao_creative", sa.Float, nullable=False, default=0),
        sa.Column("noi_monthly", sa.Float, nullable=False, default=0),
        sa.Column("debt_service_monthly", sa.Float, nullable=False, default=0),
        sa.Column("cash_flow_monthly", sa.Float, nullable=False, default=0),
        sa.Column("coc_pct", sa.Float, nullable=False, default=0),
        sa.Column("dscr", sa.Float, nullable=False, default=0),
        sa.Column("deal_signal", sa.String(10), nullable=False, default="Red"),
        sa.Column("deal_notes", sa.Text, nullable=False, default=""),
        sa.Column("offer_suggestion", sa.Text, nullable=False, default=""),
    )


def downgrade() -> None:
    op.drop_table("deals")
    op.drop_table("settings")

