import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Application configuration settings."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smartloan-college-secret-key-2026-python-sem3')
    
    # Instance folder and SQLite Database Path
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    DATABASE_PATH = os.path.join(INSTANCE_DIR, 'smartloan.db')
    
    # Export directory for CSV and PDF reports
    EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')
    
    # Loan Input Boundaries for Safe Financial Calculations
    MIN_LOAN_AMOUNT = 1000.0          # Minimum ₹1,000
    MAX_LOAN_AMOUNT = 100000000.0     # Maximum ₹10 Crores (100 Million)
    MIN_INTEREST_RATE = 0.0          # 0% promotional / zero-interest loans
    MAX_INTEREST_RATE = 100.0        # 100% annual rate cap
    MIN_TENURE_MONTHS = 1            # At least 1 month
    MAX_TENURE_MONTHS = 480          # Up to 40 years (480 months)
    
    # Supported Loan Categories
    LOAN_TYPES = [
        'Home Loan',
        'Personal Loan',
        'Car Loan',
        'Education Loan',
        'Other'
    ]
    
    # Currency symbol
    CURRENCY_SYMBOL = '₹'
