import math
from typing import Dict, Any
from models.deal import Deal
from models.settings import Settings

class FinancialCalculator:
    """
    Financial calculation engine for real estate deal analysis.
    Implements the exact logic specified in the requirements.
    """
    
    @staticmethod
    def calculate_deal_metrics(deal_data: Dict[str, Any], settings: Settings) -> Dict[str, Any]:
        """
        Calculate all financial metrics for a deal based on current settings.
        Returns updated deal data with computed fields.
        """
        # Extract deal properties
        list_price = float(deal_data.get('list_price', 0))
        arv_estimate = float(deal_data.get('arv_estimate', 0)) or list_price * 1.3
        repair_estimate = float(deal_data.get('repair_estimate', 0))
        monthly_rent = float(deal_data.get('monthly_rent', 0))
        taxes_insurance_monthly = float(deal_data.get('taxes_insurance_monthly', 0))
        assignment_fee = float(deal_data.get('assignment_fee', 0))
        financing_pref = deal_data.get('financing_pref', 'any')
        sqft = float(deal_data.get('sqft', 0))
        
        # A) Operating Expenses and NOI
        gross = monthly_rent
        pct_exp = settings.vacancy_pct + settings.mgmt_pct + settings.maintenance_pct + settings.other_expense_pct
        opex_guess = gross * (pct_exp / 100)
        
        if taxes_insurance_monthly > 0:
            opex = taxes_insurance_monthly + gross * ((settings.vacancy_pct + settings.mgmt_pct + settings.maintenance_pct) / 100)
        else:
            opex = opex_guess
        
        noi_monthly = max(gross - opex, 0)
        
        # B) Cash MAO (70% rule)
        mao_cash = max(arv_estimate * settings.arv_discount_pct - repair_estimate - assignment_fee, 0)
        total_cash_in = list_price + repair_estimate + assignment_fee
        coc_cash = ((noi_monthly * 12) / total_cash_in * 100) if total_cash_in > 0 else 0
        
        # C) Creative Finance MAO (seller-finance approximation)
        max_annual_debt = (noi_monthly * 12) / settings.min_dscr if noi_monthly > 0 else 0
        max_payment_monthly = max_annual_debt / 12
        
        # Convert payment to max loan amount
        r = (settings.max_interest_rate / 100) / 12
        n = settings.term_years * 12
        
        if r > 0:
            l_max = max_payment_monthly * (1 - (1 + r) ** (-n)) / r
        else:
            l_max = max_payment_monthly * n
        
        # Price ceiling given down-payment cap
        price_max_from_dscr = l_max / (1 - settings.max_down_payment_pct) if settings.max_down_payment_pct < 1 else l_max
        price_max = min(price_max_from_dscr, arv_estimate)
        
        down_payment_cash = price_max * settings.max_down_payment_pct
        total_cash_in_creative = down_payment_cash + repair_estimate + assignment_fee
        debt_service_monthly = max_payment_monthly
        cash_flow_monthly_creative = noi_monthly - debt_service_monthly
        coc_creative = ((cash_flow_monthly_creative * 12) / total_cash_in_creative * 100) if total_cash_in_creative > 0 else 0
        mao_creative = max(price_max - repair_estimate - assignment_fee, 0)
        
        # D) Scenario selection and final metrics
        if financing_pref == "cash":
            scenario = "cash"
        elif financing_pref == "creative":
            scenario = "creative"
        else:  # any
            scenario = "cash" if coc_cash >= coc_creative else "creative"
        
        if scenario == "cash":
            dscr = 999  # No debt service for cash
            cash_flow_monthly = noi_monthly
            coc_pct = coc_cash
            final_debt_service = 0
        else:
            dscr = (noi_monthly * 12) / (debt_service_monthly * 12) if debt_service_monthly > 0 else 0
            cash_flow_monthly = cash_flow_monthly_creative
            coc_pct = coc_creative
            final_debt_service = debt_service_monthly
        
        # E) Green/Red decision and offer suggestion
        thresholds_met = (
            monthly_rent > 0 and
            repair_estimate <= settings.max_rehab and
            cash_flow_monthly >= settings.min_monthly_cf and
            coc_pct >= settings.min_coc_pct and
            dscr >= settings.min_dscr
        )
        
        deal_signal = "Green" if thresholds_met else "Red"
        
        # Generate deal notes
        if deal_signal == "Green":
            deal_notes = "Meets buyer criteria."
        else:
            failures = []
            if monthly_rent <= 0:
                failures.append("No rent data")
            if repair_estimate > settings.max_rehab:
                failures.append("Rehab high")
            if cash_flow_monthly < settings.min_monthly_cf:
                failures.append("CF low")
            if coc_pct < settings.min_coc_pct:
                failures.append(f"CoC {coc_pct:.1f}% < {settings.min_coc_pct}%")
            if dscr < settings.min_dscr and scenario != "cash":
                failures.append(f"DSCR {dscr:.2f} < {settings.min_dscr}")
            
            deal_notes = "; ".join(failures[:3]) + "." if failures else "Below criteria."
        
        # Generate offer suggestion
        if scenario == "cash":
            offer_suggestion = f"Cash offer ≈ ${round(mao_cash):,} (ARV×{int(settings.arv_discount_pct * 100)}% − repairs − fee)."
        else:
            offer_suggestion = (
                f"Seller-finance price ≤ ${round(mao_creative):,}, "
                f"≤ {round(settings.max_down_payment_pct * 100)}% down, "
                f"rate ≤ {settings.max_interest_rate}%, "
                f"est. P&I ${round(debt_service_monthly):,}, "
                f"CF ${round(cash_flow_monthly):,}/mo."
            )
        
        # Return all calculated values
        return {
            'mao_cash': round(mao_cash),
            'mao_creative': round(mao_creative),
            'noi_monthly': round(noi_monthly),
            'debt_service_monthly': round(final_debt_service),
            'cash_flow_monthly': round(cash_flow_monthly),
            'coc_pct': round(coc_pct, 1),
            'dscr': round(dscr, 2),
            'deal_signal': deal_signal,
            'deal_notes': deal_notes,
            'offer_suggestion': offer_suggestion
        }
    
    @staticmethod
    def calculate_opportunity_score(deal_data: Dict[str, Any], reference_data: list = None) -> float:
        """
        Calculate opportunity score (0-100) based on DOM, price/sqft, property type, and size.
        """
        dom = int(deal_data.get('days_on_market', 0))
        list_price = float(deal_data.get('list_price', 0))
        sqft = float(deal_data.get('sqft', 0))
        property_type = deal_data.get('property_type', 'SFR')
        
        # DOM component (0-40 points)
        dom_score = min((dom / 200) * 40, 40)
        
        # Price per sqft component (0-40 points) 
        price_per_sqft = list_price / sqft if sqft > 0 else 0
        # Assume lower price/sqft is better (inverse scoring)
        # Using $200/sqft as reference point
        price_score = max(0, 40 - (price_per_sqft / 200) * 40)
        
        # Property type bonus (0-10 points)
        type_bonus = {
            'SFR': 10,
            'Multi-Family': 5,
            'Condo/Townhome': 0
        }.get(property_type, 0)
        
        # Size bonus (0-10 points)
        size_bonus = 10 if 900 <= sqft <= 1800 else 0
        
        # Calculate final score
        total_score = dom_score + price_score + type_bonus + size_bonus
        return max(0, min(100, round(total_score)))