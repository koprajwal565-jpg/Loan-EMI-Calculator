# SmartLoan: Algorithmic Specifications

This document outlines the step-by-step algorithms implemented in Python across the SmartLoan platform.

---

## 1. Input Validation and Normalization Algorithm

```
Algorithm: ValidateAndNormalizeLoanInput
Input:
    loan_amount (str/float)
    annual_interest_rate (str/float)
    tenure_value (str/float)
    tenure_unit (str) -> "years" or "months"
    loan_type (str)
Output:
    (is_valid: Boolean, error_message: String, sanitized_dict: Dictionary)

Step 1: Check if any required field (loan_amount, annual_interest_rate, tenure_value) is null or empty.
        If yes, Return (False, "All fields are required", None).

Step 2: Parse loan_amount as float.
        If casting fails, is NaN, or is Infinite, Return (False, "Invalid numeric value", None).
        If loan_amount < 1,000, Return (False, "Minimum loan amount is ₹1,000", None).
        If loan_amount > 100,000,000, Return (False, "Maximum loan amount is ₹10 Crores", None).

Step 3: Parse annual_interest_rate as float.
        If casting fails, is NaN, or is Infinite, Return (False, "Invalid numeric value", None).
        If annual_interest_rate < 0.0, Return (False, "Interest rate cannot be negative", None).
        If annual_interest_rate > 100.0, Return (False, "Interest rate cannot exceed 100%", None).

Step 4: Parse tenure_value as float.
        If casting fails, is NaN, or tenure_value <= 0, Return (False, "Tenure must be positive", None).
        If tenure_unit is "years", tenure_months = round(tenure_value * 12).
        Else if tenure_unit is "months", tenure_months = round(tenure_value).
        Else Return (False, "Invalid tenure unit", None).
        If tenure_months < 1, Return (False, "Minimum tenure is 1 month", None).
        If tenure_months > 480, Return (False, "Maximum tenure is 480 months (40 years)", None).

Step 5: Normalize loan_type against supported categories ['Home Loan', 'Personal Loan', 'Car Loan', 'Education Loan', 'Other'].
        Default to 'Other' if unrecognized.

Step 6: Return (True, None, {loan_amount, annual_interest_rate, tenure_months, tenure_years, loan_type}).
```

---

## 2. Equated Monthly Instalment (EMI) Calculation Algorithm

```
Algorithm: ComputeReducingBalanceEMI
Input:
    P: Principal Loan Amount (float)
    R: Annual Interest Rate in % (float)
    N: Total Tenure in Months (int)
Output:
    Monthly EMI, Total Interest, Total Payment, Principal %, Interest %

Step 1: Calculate monthly interest rate:
        r = (R / 12) / 100

Step 2: Check for zero-interest promotional condition:
        If r == 0.0:
            raw_emi = P / N
            Total_Interest = 0.00
            Total_Payment = P
        Else:
            factor = (1 + r)^N
            raw_emi = P * r * factor / (factor - 1)

Step 3: Round raw_emi to 2 decimal places using Decimal ROUND_HALF_UP:
        monthly_emi = round_currency(raw_emi)

Step 4: Execute AmortizationSchedule(P, R, N, monthly_emi) to obtain exact month-by-month values.

Step 5: Aggregate totals from schedule:
        Total_Interest = sum(month.interest_paid for month in schedule)
        Total_Payment = sum(month.emi for month in schedule)

Step 6: Calculate percentage ratios:
        Principal_% = (P / Total_Payment) * 100
        Interest_% = (Total_Interest / Total_Payment) * 100

Step 7: Return calculated dictionary.
```

---

## 3. Month-by-Month Amortization Schedule Algorithm

```
Algorithm: GenerateAmortizationSchedule
Input:
    P: Principal Loan Amount
    R: Annual Interest Rate (%)
    N: Total Number of Months
    base_emi: Standard Monthly EMI
Output:
    schedule: List of Dicts [{month, opening_balance, emi, principal_paid, interest_paid, closing_balance}]

Step 1: Initialize r = (R / 12) / 100.
        Initialize opening_balance = P.
        Initialize schedule = empty list.

Step 2: For month = 1 to N do:
        If r == 0:
            interest_paid = 0.00
        Else:
            interest_paid = round_currency(opening_balance * r)

        // Step 2a: Final Month Exact Adjustment
        If month == N:
            principal_paid = opening_balance
            month_emi = round_currency(principal_paid + interest_paid)
            closing_balance = 0.00
        Else:
            principal_paid = round_currency(base_emi - interest_paid)
            // Safety guard: if principal_paid exceeds remaining opening_balance
            If principal_paid > opening_balance:
                principal_paid = opening_balance
                month_emi = round_currency(principal_paid + interest_paid)
                closing_balance = 0.00
            Else:
                closing_balance = round_currency(opening_balance - principal_paid)
                month_emi = base_emi

        Append record {month, opening_balance, month_emi, principal_paid, interest_paid, closing_balance} to schedule.
        Set opening_balance = closing_balance.

        If opening_balance <= 0.00 and month < N:
            Break loop (loan repaid early).

Step 3: Return schedule.
```

---

## 4. Multi-Loan Offer Comparison Algorithm

```
Algorithm: CompareLoanOffers
Input:
    loans_data: List of up to 3 loan offers
Output:
    comparison_summary: Results, lowest_cost_index, lowest_emi_index, analytical_notes

Step 1: For each offer in loans_data:
        Calculate EMI and repayment metrics using ComputeReducingBalanceEMI.
        Store resulting summary in results list.

Step 2: Identify index with minimum Total_Payment:
        lowest_payment_index = index of min(results[i].total_payment)

Step 3: Identify index with minimum Monthly_EMI:
        lowest_emi_index = index of min(results[i].monthly_emi)

Step 4: Generate educational analytical advice:
        If lowest_payment_index == lowest_emi_index:
            Advise that the offer provides undisputed superiority in both monthly burden and total cost.
        Else:
            Calculate difference in monthly cash flow: diff_emi = abs(emi_a - emi_b).
            Calculate difference in lifetime interest: diff_interest = abs(total_a - total_b).
            Advise that while the lower EMI offer frees up monthly cash flow, the lower total payment offer yields superior lifetime financial savings by avoiding compound interest over extended tenures.

Step 5: Return comparison_summary.
```
