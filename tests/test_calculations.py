"""
SmartLoan - Calculations & Business Logic Automated Test Suite
Tests reducing-balance formulas, zero-interest edge cases, input boundary validation,
amortization schedule accuracy, and final-month rounding reconciliations.
"""

import pytest
from decimal import Decimal
from calculations import (
    validate_loan_input, calculate_emi, generate_amortization_schedule,
    compare_loans, round_currency
)
from config import Config


class TestEmiCalculations:
    """Test suite for financial math functions."""

    def test_normal_emi_calculation(self):
        """1. Test normal EMI calculation with realistic standard home loan values."""
        # Loan: 10 Lakhs, 8.5% p.a., 5 years (60 months)
        principal = 1000000.0
        rate = 8.5
        tenure_months = 60

        result = calculate_emi(principal, rate, tenure_months, loan_type='Home Loan')

        assert result['loan_amount'] == 1000000.0
        assert result['annual_interest_rate'] == 8.5
        assert result['tenure_months'] == 60
        # Expected EMI for 10L at 8.5% for 60 months is ~20,516.53
        assert 20500.0 <= result['monthly_emi'] <= 20550.0
        assert result['total_interest'] > 0
        assert result['total_payment'] == round_currency(result['total_principal'] + result['total_interest'])
        assert result['principal_pct'] + result['interest_pct'] == pytest.approx(100.0, abs=0.1)

    def test_zero_interest_loan(self):
        """2. Test zero-interest promotional loan (r = 0, EMI = P / n)."""
        principal = 120000.0
        rate = 0.0
        tenure_months = 12

        result = calculate_emi(principal, rate, tenure_months, loan_type='Car Loan')

        # With 0% interest, EMI should be exactly 120,000 / 12 = 10,000.00
        assert result['monthly_emi'] == 10000.00
        assert result['total_interest'] == 0.00
        assert result['total_payment'] == 120000.00
        assert result['principal_pct'] == 100.00
        assert result['interest_pct'] == 0.00

    def test_very_small_loan_amount(self):
        """3. Test minimum valid loan amount."""
        principal = Config.MIN_LOAN_AMOUNT  # ₹1,000
        rate = 12.0
        tenure_months = 6

        result = calculate_emi(principal, rate, tenure_months, loan_type='Personal Loan')

        assert result['monthly_emi'] > 0
        assert result['total_payment'] >= principal
        assert len(result['amortization_schedule']) == 6
        assert result['amortization_schedule'][-1]['closing_balance'] == 0.00

    def test_large_loan_amount(self):
        """4. Test high-value loan amount (₹5 Crores)."""
        principal = 50000000.0  # ₹5 Crores
        rate = 9.0
        tenure_months = 240     # 20 years

        result = calculate_emi(principal, rate, tenure_months, loan_type='Home Loan')

        assert result['monthly_emi'] > 0
        assert result['total_interest'] > 0
        # For long tenure, interest typically exceeds principal
        assert result['total_interest'] > principal
        assert result['amortization_schedule'][-1]['closing_balance'] == 0.00

    def test_invalid_loan_amount(self):
        """5. Test invalid loan amount inputs (negative, below minimum, excessive, non-numeric)."""
        # Negative
        valid, err, _ = validate_loan_input(-50000, 8.5, 5, 'years')
        assert not valid
        assert "at least" in err.lower() or "negative" in err.lower()

        # Below minimum
        valid, err, _ = validate_loan_input(500, 8.5, 5, 'years')
        assert not valid
        assert "at least" in err.lower()

        # Excessive
        valid, err, _ = validate_loan_input(9999999999, 8.5, 5, 'years')
        assert not valid
        assert "cannot exceed" in err.lower()

        # Non-numeric string
        valid, err, _ = validate_loan_input("one_million", 8.5, 5, 'years')
        assert not valid
        assert "valid numeric" in err.lower()

    def test_negative_interest_rate(self):
        """6. Test negative interest rate validation."""
        valid, err, _ = validate_loan_input(500000, -2.5, 5, 'years')
        assert not valid
        assert "negative" in err.lower()

    def test_invalid_loan_tenure(self):
        """7. Test invalid loan tenure (zero, negative, excessive, text)."""
        # Zero tenure
        valid, err, _ = validate_loan_input(500000, 8.5, 0, 'years')
        assert not valid
        assert "positive" in err.lower() or "greater than zero" in err.lower()

        # Negative tenure
        valid, err, _ = validate_loan_input(500000, 8.5, -3, 'months')
        assert not valid

        # Excessive (> 480 months / 40 years)
        valid, err, _ = validate_loan_input(500000, 8.5, 50, 'years')
        assert not valid
        assert "cannot exceed" in err.lower()

    def test_amortization_schedule_accuracy(self):
        """8. Test mathematical accuracy across all months in the schedule."""
        principal = 600000.0
        rate = 10.0
        tenure_months = 24
        monthly_rate = (rate / 12.0) / 100.0

        schedule = generate_amortization_schedule(principal, rate, tenure_months)

        assert len(schedule) == 24
        for row in schedule:
            # Check interest = opening * monthly_rate (within rounding)
            expected_interest = round_currency(row['opening_balance'] * monthly_rate)
            assert abs(row['interest_paid'] - expected_interest) <= 0.05
            # Check EMI = principal_paid + interest_paid
            assert round_currency(row['principal_paid'] + row['interest_paid']) == row['emi']

    def test_final_outstanding_balance_is_zero(self):
        """9. Test that final month closing balance strictly reconciles to ₹0.00."""
        # Test across various tenure and rate combinations
        test_cases = [
            (250000.0, 7.25, 36),
            (1500000.0, 9.15, 84),
            (333333.33, 11.0, 15),
            (100000.0, 0.0, 10),    # Zero-interest
        ]

        for p, r, n in test_cases:
            schedule = generate_amortization_schedule(p, r, n)
            last_row = schedule[-1]
            assert last_row['closing_balance'] == 0.00, f"Failed for P={p}, r={r}, n={n}"
            total_principal_paid = sum(row['principal_paid'] for row in schedule)
            assert abs(total_principal_paid - p) <= 0.05, f"Principal sum mismatch for P={p}"

    def test_loan_comparison_logic(self):
        """Test multi-loan comparison identifies best cost and best EMI correctly."""
        loans = [
            {'label': 'Short Loan', 'loan_amount': 1000000, 'annual_interest_rate': 8.5, 'tenure_value': 5, 'tenure_unit': 'years'},
            {'label': 'Long Loan', 'loan_amount': 1000000, 'annual_interest_rate': 8.5, 'tenure_value': 15, 'tenure_unit': 'years'},
        ]

        comp = compare_loans(loans)
        assert len(comp['loans']) == 2
        # Short loan has higher EMI but much lower total repayment
        assert comp['lowest_payment_index'] == 0  # Short loan is cheaper overall
        assert comp['lowest_emi_index'] == 1      # Long loan has smaller monthly EMI
        assert len(comp['analysis_notes']) >= 1
