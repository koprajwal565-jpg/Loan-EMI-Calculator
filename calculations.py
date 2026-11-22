"""
SmartLoan - Financial Calculations Module
Implements accurate reducing-balance EMI calculations, amortization schedules,
and multi-loan comparisons using Python's Decimal and float modules.
"""

from decimal import Decimal, ROUND_HALF_UP
import math
from config import Config


def round_currency(value):
    """Round a numeric value to two decimal places using standard financial rounding."""
    if isinstance(value, (int, float)):
        dec_val = Decimal(str(value))
    elif isinstance(value, Decimal):
        dec_val = value
    else:
        dec_val = Decimal(str(float(value)))
    return float(dec_val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def validate_loan_input(loan_amount, annual_interest_rate, tenure_value, tenure_unit='years', loan_type='Personal Loan'):
    """
    Validate user inputs for loan calculations.
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None, sanitized_dict: dict or None)
    """
    # 1. Check for empty or None values
    if loan_amount is None or annual_interest_rate is None or tenure_value is None:
        return False, "All fields (Loan Amount, Interest Rate, Tenure) are required.", None
    
    # 2. Parse Loan Amount
    try:
        p = float(loan_amount)
    except (ValueError, TypeError):
        return False, "Loan amount must be a valid numeric value.", None
    
    if math.isnan(p) or math.isinf(p):
        return False, "Loan amount contains an invalid number.", None
    if p < Config.MIN_LOAN_AMOUNT:
        return False, f"Loan amount must be at least ₹{Config.MIN_LOAN_AMOUNT:,.2f}.", None
    if p > Config.MAX_LOAN_AMOUNT:
        return False, f"Loan amount cannot exceed ₹{Config.MAX_LOAN_AMOUNT:,.2f}.", None
    
    # 3. Parse Interest Rate
    try:
        r_annual = float(annual_interest_rate)
    except (ValueError, TypeError):
        return False, "Annual interest rate must be a valid numeric value.", None
    
    if math.isnan(r_annual) or math.isinf(r_annual):
        return False, "Interest rate contains an invalid number.", None
    if r_annual < Config.MIN_INTEREST_RATE:
        return False, "Interest rate cannot be negative.", None
    if r_annual > Config.MAX_INTEREST_RATE:
        return False, f"Interest rate cannot exceed {Config.MAX_INTEREST_RATE}%.", None
    
    # 4. Parse Tenure
    try:
        t_val = float(tenure_value)
    except (ValueError, TypeError):
        return False, "Loan tenure must be a valid numeric value.", None
    
    if math.isnan(t_val) or math.isinf(t_val) or t_val <= 0:
        return False, "Loan tenure must be a positive number greater than zero.", None
    
    unit = str(tenure_unit).strip().lower()
    if unit in ('years', 'year', 'y'):
        tenure_months = int(round(t_val * 12))
        tenure_years = t_val
    elif unit in ('months', 'month', 'm'):
        tenure_months = int(round(t_val))
        tenure_years = round(tenure_months / 12.0, 2)
    else:
        return False, "Tenure unit must be either 'Years' or 'Months'.", None
    
    if tenure_months < Config.MIN_TENURE_MONTHS:
        return False, f"Loan tenure must be at least {Config.MIN_TENURE_MONTHS} month.", None
    if tenure_months > Config.MAX_TENURE_MONTHS:
        return False, f"Loan tenure cannot exceed {Config.MAX_TENURE_MONTHS} months (40 years).", None
    
    # 5. Sanitize Loan Type
    clean_loan_type = str(loan_type).strip() if loan_type else 'Personal Loan'
    if clean_loan_type not in Config.LOAN_TYPES:
        clean_loan_type = 'Other'
    
    sanitized = {
        'loan_amount': round_currency(p),
        'annual_interest_rate': round(r_annual, 4),
        'tenure_months': tenure_months,
        'tenure_years': tenure_years,
        'tenure_unit': unit,
        'loan_type': clean_loan_type
    }
    
    return True, None, sanitized


def calculate_emi(loan_amount, annual_interest_rate, tenure_months, loan_type='Personal Loan'):
    """
    Calculate Monthly EMI and Repayment Summary using reducing-balance method.
    
    Formula:
        EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
        Where:
            P = Principal
            r = Monthly interest rate (annual_interest_rate / 12 / 100)
            n = Total number of monthly instalments
        
        Zero-Interest Case:
            EMI = P / n
    
    Returns:
        dict: Complete calculation summary with rounded currency values and percentages.
    """
    p = float(loan_amount)
    r_annual = float(annual_interest_rate)
    n = int(tenure_months)
    
    if n <= 0:
        raise ValueError("Tenure months must be greater than zero.")
    if p < 0:
        raise ValueError("Loan amount cannot be negative.")
    if r_annual < 0:
        raise ValueError("Interest rate cannot be negative.")
    
    # Monthly interest rate
    monthly_rate = (r_annual / 12.0) / 100.0
    
    if monthly_rate == 0.0:
        raw_emi = p / n
    else:
        factor = (1.0 + monthly_rate) ** n
        raw_emi = p * monthly_rate * factor / (factor - 1.0)
    
    monthly_emi = round_currency(raw_emi)
    
    # Generate schedule to obtain precise totals with month-by-month rounding adjustments
    schedule = generate_amortization_schedule(p, r_annual, n, monthly_emi)
    
    total_interest = round_currency(sum(item['interest_paid'] for item in schedule))
    total_payment = round_currency(sum(item['emi'] for item in schedule))
    principal = round_currency(p)
    
    # Percentage breakdown
    if total_payment > 0:
        principal_pct = round((principal / total_payment) * 100.0, 2)
        interest_pct = round(100.0 - principal_pct, 2)
    else:
        principal_pct = 100.0
        interest_pct = 0.0
    
    tenure_years = round(n / 12.0, 2)
    
    return {
        'loan_amount': principal,
        'annual_interest_rate': r_annual,
        'monthly_interest_rate': round(monthly_rate * 100, 4),
        'tenure_months': n,
        'tenure_years': tenure_years,
        'loan_type': loan_type,
        'monthly_emi': monthly_emi,
        'total_principal': principal,
        'total_interest': total_interest,
        'total_payment': total_payment,
        'principal_pct': principal_pct,
        'interest_pct': interest_pct,
        'amortization_schedule': schedule
    }


def generate_amortization_schedule(loan_amount, annual_interest_rate, tenure_months, monthly_emi=None):
    """
    Generate month-by-month loan repayment schedule.
    
    Columns:
        - Month Number (1..n)
        - Opening Balance
        - Monthly EMI
        - Principal Paid
        - Interest Paid
        - Closing Balance
        
    Handles final month rounding adjustments so that closing balance reaches 0.00.
    """
    p = float(loan_amount)
    r_annual = float(annual_interest_rate)
    n = int(tenure_months)
    monthly_rate = (r_annual / 12.0) / 100.0
    
    if monthly_emi is None:
        if monthly_rate == 0.0:
            raw_emi = p / n
        else:
            factor = (1.0 + monthly_rate) ** n
            raw_emi = p * monthly_rate * factor / (factor - 1.0)
        base_emi = round_currency(raw_emi)
    else:
        base_emi = round_currency(monthly_emi)
    
    schedule = []
    opening_balance = round_currency(p)
    
    for month in range(1, n + 1):
        if monthly_rate == 0.0:
            interest_paid = 0.0
        else:
            interest_paid = round_currency(opening_balance * monthly_rate)
        
        # Handle final month or situations where remaining balance is less than base EMI
        if month == n:
            # Final month exact adjustment
            principal_paid = opening_balance
            month_emi = round_currency(principal_paid + interest_paid)
            closing_balance = 0.0
        else:
            principal_paid = round_currency(base_emi - interest_paid)
            
            # If principal paid exceeds remaining balance (edge cases on high payments)
            if principal_paid > opening_balance:
                principal_paid = opening_balance
                month_emi = round_currency(principal_paid + interest_paid)
                closing_balance = 0.0
            else:
                closing_balance = round_currency(opening_balance - principal_paid)
                month_emi = base_emi
        
        schedule.append({
            'month': month,
            'opening_balance': opening_balance,
            'emi': month_emi,
            'principal_paid': principal_paid,
            'interest_paid': interest_paid,
            'closing_balance': closing_balance
        })
        
        opening_balance = closing_balance
        if opening_balance <= 0.0 and month < n:
            # Loan repaid earlier due to rounding adjustments
            # Fill remaining months with zeros or truncate
            break
            
    return schedule


def compare_loans(loans_data):
    """
    Compare up to 3 loan offers.
    
    Parameters:
        loans_data: list of dicts, each containing:
            - 'loan_amount'
            - 'annual_interest_rate'
            - 'tenure_value'
            - 'tenure_unit'
            - 'loan_label' (e.g., 'Offer A', 'Offer B', 'Offer C')
            
    Returns:
        dict containing:
            - 'loans': list of calculated summaries for each offer
            - 'lowest_payment_index': index of offer with lowest total repayment
            - 'lowest_emi_index': index of offer with lowest monthly EMI
            - 'analysis_notes': list of practical insights comparing total cost vs monthly cash flow
    """
    results = []
    
    for idx, loan_item in enumerate(loans_data):
        label = loan_item.get('label') or f"Loan Option {idx + 1}"
        p = float(loan_item['loan_amount'])
        r = float(loan_item['annual_interest_rate'])
        t_val = float(loan_item['tenure_value'])
        unit = loan_item.get('tenure_unit', 'years').strip().lower()
        
        if unit in ('years', 'year', 'y'):
            months = int(round(t_val * 12))
            years = t_val
        else:
            months = int(round(t_val))
            years = round(months / 12.0, 2)
            
        summary = calculate_emi(p, r, months, loan_type=loan_item.get('loan_type', 'Comparison'))
        summary['label'] = label
        summary['option_number'] = idx + 1
        results.append(summary)
        
    if not results:
        return {'loans': [], 'analysis_notes': []}
        
    # Find lowest total payment
    lowest_payment_idx = min(range(len(results)), key=lambda i: results[i]['total_payment'])
    # Find lowest monthly EMI
    lowest_emi_idx = min(range(len(results)), key=lambda i: results[i]['monthly_emi'])
    
    analysis_notes = []
    best_cost_loan = results[lowest_payment_idx]
    best_emi_loan = results[lowest_emi_idx]
    
    if lowest_payment_idx == lowest_emi_idx:
        analysis_notes.append(
            f"{best_cost_loan['label']} is clearly the superior option: it provides both the lowest monthly EMI "
            f"(₹{best_cost_loan['monthly_emi']:,.2f}) and the lowest overall repayment "
            f"(₹{best_cost_loan['total_payment']:,.2f}), saving you maximum money."
        )
    else:
        diff_payment = abs(best_emi_loan['total_payment'] - best_cost_loan['total_payment'])
        diff_emi = abs(best_cost_loan['monthly_emi'] - best_emi_loan['monthly_emi'])
        
        analysis_notes.append(
            f"Financial Trade-Off Analysis: {best_emi_loan['label']} gives the smallest monthly burden "
            f"(₹{best_emi_loan['monthly_emi']:,.2f}/month vs ₹{best_cost_loan['monthly_emi']:,.2f}/month), "
            f"saving ₹{diff_emi:,.2f} each month."
        )
        analysis_notes.append(
            f"However, {best_cost_loan['label']} has the lowest overall cost. Choosing {best_cost_loan['label']} saves you "
            f"₹{diff_payment:,.2f} in total interest over the life of the loan. Lower monthly payments often disguise higher overall interest due to extended tenure."
        )
        
    return {
        'loans': results,
        'lowest_payment_index': lowest_payment_idx,
        'lowest_emi_index': lowest_emi_idx,
        'analysis_notes': analysis_notes
    }
