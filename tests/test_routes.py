"""
SmartLoan - Flask Routes & Exports Automated Test Suite
Tests all endpoints, HTTP methods, form validations, PDF/CSV downloads, and error handling.
"""

import os
import tempfile
os.environ['MPLCONFIGDIR'] = os.path.join(tempfile.gettempdir(), 'matplotlib')
import pytest
from app import app
from database import init_db, insert_calculation
from reports import (
    generate_pie_chart, generate_comparison_chart,
    generate_amortization_csv, generate_amortization_pdf
)
from calculations import generate_amortization_schedule


@pytest.fixture
def client():
    """Create Flask test client configured with isolated temporary database."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    app.config['TESTING'] = True
    app.config['DATABASE_PATH'] = db_path
    init_db(db_path)
    
    with app.test_client() as test_client:
        yield test_client
        
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


class TestReportsAndExports:
    """Tests for PDF, CSV, and Matplotlib chart generators."""

    def test_csv_generation(self):
        """13. Test CSV export formatting and content."""
        calc_data = {
            'loan_amount': 500000.0,
            'annual_interest_rate': 8.5,
            'tenure_months': 12,
            'tenure_years': 1.0,
            'loan_type': 'Car Loan',
            'monthly_emi': 43610.0,
            'total_interest': 23320.0,
            'total_payment': 523320.0
        }
        schedule = generate_amortization_schedule(500000.0, 8.5, 12, 43610.0)
        csv_text = generate_amortization_csv(calc_data, schedule)

        assert "SmartLoan - Loan EMI & Amortization Repayment Schedule" in csv_text
        assert "Opening Balance (Rs)" in csv_text
        assert "Closing Balance (Rs)" in csv_text
        # Check rows exist
        lines = [line for line in csv_text.splitlines() if line.strip()]
        assert len(lines) >= 14  # Header metadata + table header + 12 months

    def test_pdf_generation(self):
        """12. Test PDF report generation and binary validity."""
        calc_data = {
            'loan_amount': 1000000.0,
            'annual_interest_rate': 8.5,
            'tenure_months': 24,
            'tenure_years': 2.0,
            'loan_type': 'Home Loan',
            'monthly_emi': 45456.0,
            'total_interest': 90944.0,
            'total_payment': 1090944.0,
            'principal_pct': 91.7,
            'interest_pct': 8.3
        }
        schedule = generate_amortization_schedule(1000000.0, 8.5, 24, 45456.0)
        pdf_bytes = generate_amortization_pdf(calc_data, schedule)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000  # Substantial PDF payload
        assert pdf_bytes.startswith(b'%PDF')  # Valid PDF binary signature

    def test_chart_generation(self):
        """Test Matplotlib base64 chart generation."""
        pie_b64 = generate_pie_chart(1000000, 250000)
        assert pie_b64.startswith("data:image/png;base64,")

        comp_loans = [
            {'label': 'Offer A', 'loan_amount': 500000, 'monthly_emi': 15000, 'total_interest': 50000},
            {'label': 'Offer B', 'loan_amount': 500000, 'monthly_emi': 12000, 'total_interest': 80000}
        ]
        comp_b64 = generate_comparison_chart(comp_loans)
        assert comp_b64.startswith("data:image/png;base64,")


class TestFlaskRoutes:
    """14. Test suite for all Flask web application routes."""

    def test_dashboard_route(self, client):
        """Test GET / renders dashboard successfully."""
        response = client.get('/')
        assert response.status_code == 200
        assert b"SmartLoan" in response.data
        assert b"Financial Dashboard" in response.data

    def test_calculator_get_route(self, client):
        """Test GET /calculator renders input form."""
        response = client.get('/calculator')
        assert response.status_code == 200
        assert b"Loan Parameters" in response.data
        assert b"Calculate EMI" in response.data

    def test_calculate_post_valid(self, client):
        """Test POST /calculate with valid data redirects to results."""
        payload = {
            'loan_amount': '1500000',
            'annual_interest_rate': '8.75',
            'tenure_value': '5',
            'tenure_unit': 'years',
            'loan_type': 'Home Loan'
        }
        response = client.post('/calculate', data=payload, follow_redirects=False)
        assert response.status_code == 302
        assert '/results/' in response.headers['Location']

    def test_calculate_post_invalid(self, client):
        """Test POST /calculate with negative amount fails with 400."""
        payload = {
            'loan_amount': '-50000',
            'annual_interest_rate': '8.75',
            'tenure_value': '5',
            'tenure_unit': 'years',
            'loan_type': 'Home Loan'
        }
        response = client.post('/calculate', data=payload, follow_redirects=True)
        assert response.status_code == 400
        assert b"at least" in response.data or b"negative" in response.data

    def test_results_and_amortization_routes(self, client):
        """Test GET /results/<id> and GET /amortization/<id>."""
        # First insert a test calculation
        dummy = {
            'loan_amount': 800000.0, 'annual_interest_rate': 9.0,
            'tenure_months': 36, 'tenure_years': 3.0,
            'loan_type': 'Personal Loan', 'monthly_emi': 25435.0,
            'total_interest': 115660.0, 'total_payment': 915660.0,
            'principal_pct': 87.4, 'interest_pct': 12.6
        }
        calc_id = insert_calculation(dummy, app.config['DATABASE_PATH'])

        # Result page
        res = client.get(f'/results/{calc_id}')
        assert res.status_code == 200
        assert b"Calculation Results Dashboard" in res.data
        assert b"Monthly EMI" in res.data

        # Amortization page
        res_amort = client.get(f'/amortization/{calc_id}')
        assert res_amort.status_code == 200
        assert b"Amortization Repayment Schedule" in res_amort.data
        assert b"Opening Balance" in res_amort.data

    def test_downloads_csv_and_pdf(self, client):
        """Test CSV and PDF download endpoints."""
        dummy = {
            'loan_amount': 500000.0, 'annual_interest_rate': 8.5,
            'tenure_months': 12, 'tenure_years': 1.0,
            'loan_type': 'Car Loan', 'monthly_emi': 43610.0,
            'total_interest': 23320.0, 'total_payment': 523320.0,
            'principal_pct': 95.5, 'interest_pct': 4.5
        }
        calc_id = insert_calculation(dummy, app.config['DATABASE_PATH'])

        # CSV Download
        res_csv = client.get(f'/export/csv/{calc_id}')
        assert res_csv.status_code == 200
        assert res_csv.mimetype == 'text/csv'
        assert b"SmartLoan" in res_csv.data

        # PDF Download
        res_pdf = client.get(f'/export/pdf/{calc_id}')
        assert res_pdf.status_code == 200
        assert res_pdf.mimetype == 'application/pdf'
        assert res_pdf.data.startswith(b'%PDF')

    def test_comparison_routes(self, client):
        """Test GET and POST /comparison."""
        res_get = client.get('/comparison')
        assert res_get.status_code == 200
        assert b"Multi-Offer Loan Comparison" in res_get.data

        payload = {
            'label_1': 'Bank Alpha', 'amount_1': '2000000', 'rate_1': '8.5', 'tenure_1': '10', 'unit_1': 'years', 'type_1': 'Home Loan',
            'label_2': 'Bank Beta', 'amount_2': '2000000', 'rate_2': '9.0', 'tenure_2': '15', 'unit_2': 'years', 'type_2': 'Home Loan',
        }
        res_post = client.post('/comparison', data=payload)
        assert res_post.status_code == 200
        assert b"Side-by-Side Metric Matrix" in res_post.data
        assert b"Bank Alpha" in res_post.data

    def test_history_and_deletion_routes(self, client):
        """Test GET /history, POST /history/delete/<id>, and POST /history/clear."""
        dummy = {
            'loan_amount': 300000.0, 'annual_interest_rate': 10.0,
            'tenure_months': 12, 'tenure_years': 1.0,
            'loan_type': 'Personal Loan', 'monthly_emi': 26374.0,
            'total_interest': 16488.0, 'total_payment': 316488.0,
            'principal_pct': 94.8, 'interest_pct': 5.2
        }
        calc_id = insert_calculation(dummy, app.config['DATABASE_PATH'])

        # View history
        res_hist = client.get('/history')
        assert res_hist.status_code == 200
        assert f"#{calc_id}".encode() in res_hist.data

        # Delete single record
        res_del = client.post(f'/history/delete/{calc_id}', follow_redirects=True)
        assert res_del.status_code == 200
        assert b"deleted successfully" in res_del.data

        # Clear all
        insert_calculation(dummy, app.config['DATABASE_PATH'])
        res_clear = client.post('/history/clear', follow_redirects=True)
        assert res_clear.status_code == 200
        assert b"Cleared all" in res_clear.data

    def test_about_and_404(self, client):
        """Test About page and custom 404 handler."""
        res_about = client.get('/about')
        assert res_about.status_code == 200
        assert b"About SmartLoan" in res_about.data

        res_404 = client.get('/this-page-does-not-exist')
        assert res_404.status_code == 404
        assert b"Resource Not Found" in res_404.data
