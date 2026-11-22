"""
SmartLoan - SQLite Database Automated Test Suite
Tests schema initialization, insertion, retrieval, individual deletion,
and complete history wiping using isolated test databases.
"""

import os
import tempfile
import pytest
from database import (
    init_db, insert_calculation, get_all_calculations,
    get_recent_calculations, get_calculation_by_id,
    delete_calculation, clear_all_calculations, get_database_stats
)


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for test isolation."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    init_db(path)
    yield path
    # Cleanup after test completes
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


class TestDatabaseOperations:
    """Test suite for SQLite operations."""

    def test_database_initialization(self, temp_db):
        """Test database table creation and schema readiness."""
        records = get_all_calculations(temp_db)
        assert records == []
        stats = get_database_stats(temp_db)
        assert stats['total_calculations'] == 0
        assert stats['total_loan_volume'] == 0.0

    def test_insert_and_retrieve_calculation(self, temp_db):
        """10. Test inserting a calculation and retrieving it by ID and list."""
        dummy_calc = {
            'loan_amount': 750000.0,
            'annual_interest_rate': 9.25,
            'tenure_months': 36,
            'tenure_years': 3.0,
            'loan_type': 'Car Loan',
            'monthly_emi': 23945.12,
            'total_interest': 112024.32,
            'total_payment': 862024.32,
            'principal_pct': 87.0,
            'interest_pct': 13.0
        }

        # Insert record
        calc_id = insert_calculation(dummy_calc, temp_db)
        assert calc_id is not None
        assert calc_id > 0

        # Retrieve by ID
        fetched = get_calculation_by_id(calc_id, temp_db)
        assert fetched is not None
        assert fetched['id'] == calc_id
        assert fetched['loan_amount'] == 750000.0
        assert fetched['loan_type'] == 'Car Loan'
        assert fetched['monthly_emi'] == 23945.12

        # Retrieve all
        all_rows = get_all_calculations(temp_db)
        assert len(all_rows) == 1
        assert all_rows[0]['id'] == calc_id

        # Check stats
        stats = get_database_stats(temp_db)
        assert stats['total_calculations'] == 1
        assert stats['total_loan_volume'] == 750000.0

    def test_delete_individual_calculation(self, temp_db):
        """11. Test deleting an individual record from database."""
        dummy_1 = {
            'loan_amount': 500000.0, 'annual_interest_rate': 8.5,
            'tenure_months': 24, 'tenure_years': 2.0,
            'loan_type': 'Personal Loan', 'monthly_emi': 22730.0,
            'total_interest': 45520.0, 'total_payment': 545520.0,
            'principal_pct': 91.6, 'interest_pct': 8.4
        }
        dummy_2 = {
            'loan_amount': 2000000.0, 'annual_interest_rate': 8.5,
            'tenure_months': 120, 'tenure_years': 10.0,
            'loan_type': 'Home Loan', 'monthly_emi': 24796.0,
            'total_interest': 975520.0, 'total_payment': 2975520.0,
            'principal_pct': 67.2, 'interest_pct': 32.8
        }

        id1 = insert_calculation(dummy_1, temp_db)
        id2 = insert_calculation(dummy_2, temp_db)

        assert len(get_all_calculations(temp_db)) == 2

        # Delete id1
        success = delete_calculation(id1, temp_db)
        assert success is True

        # Verify id1 is gone but id2 remains
        assert get_calculation_by_id(id1, temp_db) is None
        assert get_calculation_by_id(id2, temp_db) is not None
        assert len(get_all_calculations(temp_db)) == 1

        # Deleting non-existent returns False
        assert delete_calculation(9999, temp_db) is False

    def test_clear_all_calculations(self, temp_db):
        """Test clearing entire calculation history."""
        dummy = {
            'loan_amount': 100000.0, 'annual_interest_rate': 10.0,
            'tenure_months': 12, 'tenure_years': 1.0,
            'loan_type': 'Other', 'monthly_emi': 8791.0,
            'total_interest': 5492.0, 'total_payment': 105492.0,
            'principal_pct': 94.8, 'interest_pct': 5.2
        }

        insert_calculation(dummy, temp_db)
        insert_calculation(dummy, temp_db)
        assert len(get_all_calculations(temp_db)) == 2

        cleared_count = clear_all_calculations(temp_db)
        assert cleared_count == 2
        assert len(get_all_calculations(temp_db)) == 0
        stats = get_database_stats(temp_db)
        assert stats['total_calculations'] == 0
