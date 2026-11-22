"""
SmartLoan - Loan EMI Calculator & Repayment Planner
Flask Web Application Main Entry Point
College Project for Programming with Python (Semester 3)
"""

import os
import tempfile
# Ensure a writable directory for matplotlib cache
os.environ['MPLCONFIGDIR'] = os.path.join(tempfile.gettempdir(), 'matplotlib')

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_file, Response, abort
)
from config import Config
from calculations import (
    validate_loan_input, calculate_emi, generate_amortization_schedule, compare_loans
)
from database import (
    init_db, insert_calculation, get_all_calculations,
    get_recent_calculations, get_calculation_by_id,
    delete_calculation, clear_all_calculations, get_database_stats
)
from reports import (
    generate_pie_chart, generate_comparison_chart,
    generate_amortization_csv, generate_amortization_pdf
)

app = Flask(__name__)
app.config.from_object(Config)

# Ensure instance and exports directories exist
os.makedirs(app.config['INSTANCE_DIR'], exist_ok=True)
os.makedirs(app.config['EXPORTS_DIR'], exist_ok=True)

# Initialize SQLite database on startup
init_db(app.config['DATABASE_PATH'])


# ============================================================================
# JINJA2 CUSTOM FILTERS
# ============================================================================

@app.template_filter('currency')
def currency_filter(value):
    """Format floating point numbers as Indian currency with ₹ symbol."""
    try:
        val = float(value)
        return f"₹{val:,.2f}"
    except (ValueError, TypeError):
        return f"₹{value}"


@app.template_filter('number_format')
def number_format_filter(value):
    """Format numeric values with commas and 2 decimals."""
    try:
        val = float(value)
        return f"{val:,.2f}"
    except (ValueError, TypeError):
        return str(value)


# ============================================================================
# APPLICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    """
    Home / Dashboard page.
    Displays quick statistics, recent loan calculations, quick calculator widget,
    and platform highlights.
    """
    stats = get_database_stats(app.config['DATABASE_PATH'])
    recent_loans = get_recent_calculations(limit=5, custom_path=app.config['DATABASE_PATH'])
    loan_types = Config.LOAN_TYPES
    return render_template('index.html', stats=stats, recent_loans=recent_loans, loan_types=loan_types)


@app.route('/calculator', methods=['GET'])
def calculator():
    """
    Main Loan EMI Calculator form.
    Pre-populates sample data if requested or loads clean state.
    """
    loan_types = Config.LOAN_TYPES
    # Check for pre-fill parameters (e.g. from recalculate or demo buttons)
    prefill = {
        'loan_amount': request.args.get('amount', '1000000'),
        'annual_interest_rate': request.args.get('rate', '8.5'),
        'tenure_value': request.args.get('tenure', '5'),
        'tenure_unit': request.args.get('unit', 'years'),
        'loan_type': request.args.get('type', 'Home Loan')
    }
    return render_template('calculator.html', loan_types=loan_types, prefill=prefill)


@app.route('/calculate', methods=['POST'])
def calculate():
    """
    Process EMI Calculation form submission.
    Validates inputs, executes Python financial logic, saves to SQLite,
    and redirects to the result dashboard.
    """
    loan_amount = request.form.get('loan_amount')
    annual_interest_rate = request.form.get('annual_interest_rate')
    tenure_value = request.form.get('tenure_value')
    tenure_unit = request.form.get('tenure_unit', 'years')
    loan_type = request.form.get('loan_type', 'Personal Loan')

    is_valid, error_msg, sanitized = validate_loan_input(
        loan_amount=loan_amount,
        annual_interest_rate=annual_interest_rate,
        tenure_value=tenure_value,
        tenure_unit=tenure_unit,
        loan_type=loan_type
    )

    if not is_valid:
        flash(error_msg, 'danger')
        loan_types = Config.LOAN_TYPES
        prefill = {
            'loan_amount': loan_amount or '1000000',
            'annual_interest_rate': annual_interest_rate or '8.5',
            'tenure_value': tenure_value or '5',
            'tenure_unit': tenure_unit,
            'loan_type': loan_type
        }
        return render_template('calculator.html', loan_types=loan_types, prefill=prefill), 400

    # Perform accurate Python financial calculation
    calc_result = calculate_emi(
        loan_amount=sanitized['loan_amount'],
        annual_interest_rate=sanitized['annual_interest_rate'],
        tenure_months=sanitized['tenure_months'],
        loan_type=sanitized['loan_type']
    )

    # Persist calculation in SQLite database
    calc_id = insert_calculation(calc_result, app.config['DATABASE_PATH'])
    flash("EMI calculated successfully and saved to history!", "success")
    return redirect(url_for('results', calc_id=calc_id))


@app.route('/results/<int:calc_id>')
def results(calc_id):
    """
    Visual EMI Result Dashboard.
    Displays 4 summary metric cards, interactive details, and Matplotlib chart.
    """
    record = get_calculation_by_id(calc_id, app.config['DATABASE_PATH'])
    if not record:
        flash(f"Calculation record #{calc_id} was not found.", "warning")
        return redirect(url_for('calculator'))

    # Generate Matplotlib pie chart dynamically
    chart_data_uri = generate_pie_chart(record['loan_amount'], record['total_interest'])

    return render_template(
        'results.html',
        calc=record,
        chart_data_uri=chart_data_uri
    )


@app.route('/amortization/<int:calc_id>')
def amortization(calc_id):
    """
    Complete Month-by-Month Amortization Schedule page.
    Includes pagination, table search, and export shortcuts.
    """
    record = get_calculation_by_id(calc_id, app.config['DATABASE_PATH'])
    if not record:
        flash(f"Calculation record #{calc_id} was not found.", "warning")
        return redirect(url_for('history'))

    # Compute full schedule
    schedule = generate_amortization_schedule(
        loan_amount=record['loan_amount'],
        annual_interest_rate=record['annual_interest_rate'],
        tenure_months=record['tenure_months'],
        monthly_emi=record['monthly_emi']
    )

    # Simple page pagination for large schedules (e.g. 20-30 years = 240-360 rows)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    show_all = request.args.get('all', '0') == '1'

    total_rows = len(schedule)
    if show_all or per_page <= 0:
        displayed_schedule = schedule
        current_page = 1
        total_pages = 1
    else:
        total_pages = (total_rows + per_page - 1) // per_page
        current_page = max(1, min(page, total_pages))
        start_idx = (current_page - 1) * per_page
        end_idx = start_idx + per_page
        displayed_schedule = schedule[start_idx:end_idx]

    return render_template(
        'amortization.html',
        calc=record,
        schedule=displayed_schedule,
        current_page=current_page,
        total_pages=total_pages,
        total_rows=total_rows,
        per_page=per_page,
        show_all=show_all
    )


@app.route('/comparison', methods=['GET', 'POST'])
def comparison():
    """
    Multi-Loan Comparison Tool.
    Compares up to 3 loan options simultaneously with side-by-side metrics,
    financial trade-off advice, and Matplotlib bar charts.
    """
    loan_types = Config.LOAN_TYPES
    
    if request.method == 'GET':
        # Default demo comparison values to help the user test immediately
        default_offers = [
            {'label': 'Offer A (Short Tenure)', 'amount': '2500000', 'rate': '8.5', 'tenure': '10', 'unit': 'years', 'type': 'Home Loan'},
            {'label': 'Offer B (Medium Tenure)', 'amount': '2500000', 'rate': '8.75', 'tenure': '15', 'unit': 'years', 'type': 'Home Loan'},
            {'label': 'Offer C (Long Tenure)', 'amount': '2500000', 'rate': '9.0', 'tenure': '20', 'unit': 'years', 'type': 'Home Loan'}
        ]
        return render_template('comparison.html', loan_types=loan_types, offers=default_offers, comparison_result=None)

    # Process comparison submission
    loans_input = []
    # Collect up to 3 loan offers
    for i in range(1, 4):
        p_val = request.form.get(f'amount_{i}')
        r_val = request.form.get(f'rate_{i}')
        t_val = request.form.get(f'tenure_{i}')
        u_val = request.form.get(f'unit_{i}', 'years')
        lbl_val = request.form.get(f'label_{i}', f'Offer {chr(64+i)}')
        l_type = request.form.get(f'type_{i}', 'Home Loan')
        
        # If at least amount is given, validate
        if p_val and str(p_val).strip():
            is_valid, err, sanitized = validate_loan_input(
                loan_amount=p_val,
                annual_interest_rate=r_val,
                tenure_value=t_val,
                tenure_unit=u_val,
                loan_type=l_type
            )
            if not is_valid:
                flash(f"Error in {lbl_val}: {err}", "danger")
                offers_data = [
                    {'label': request.form.get(f'label_{k}', f'Offer {k}'),
                     'amount': request.form.get(f'amount_{k}', ''),
                     'rate': request.form.get(f'rate_{k}', ''),
                     'tenure': request.form.get(f'tenure_{k}', ''),
                     'unit': request.form.get(f'unit_{k}', 'years'),
                     'type': request.form.get(f'type_{k}', 'Home Loan')}
                    for k in range(1, 4)
                ]
                return render_template('comparison.html', loan_types=loan_types, offers=offers_data, comparison_result=None), 400
            
            loans_input.append({
                'label': lbl_val,
                'loan_amount': sanitized['loan_amount'],
                'annual_interest_rate': sanitized['annual_interest_rate'],
                'tenure_value': float(t_val),
                'tenure_unit': u_val,
                'loan_type': sanitized['loan_type']
            })

    if len(loans_input) < 2:
        flash("Please enter at least two loan offers to compare.", "warning")
        return redirect(url_for('comparison'))

    comparison_result = compare_loans(loans_input)
    chart_data_uri = generate_comparison_chart(comparison_result['loans'])

    # Build sticky form values
    offers_data = []
    for k in range(1, 4):
        offers_data.append({
            'label': request.form.get(f'label_{k}', f'Offer {k}'),
            'amount': request.form.get(f'amount_{k}', ''),
            'rate': request.form.get(f'rate_{k}', ''),
            'tenure': request.form.get(f'tenure_{k}', ''),
            'unit': request.form.get(f'unit_{k}', 'years'),
            'type': request.form.get(f'type_{k}', 'Home Loan')
        })

    return render_template(
        'comparison.html',
        loan_types=loan_types,
        offers=offers_data,
        comparison_result=comparison_result,
        chart_data_uri=chart_data_uri
    )


@app.route('/history')
def history():
    """
    Calculation History page.
    Lists all saved calculations with details, delete, and clear actions.
    """
    all_calcs = get_all_calculations(app.config['DATABASE_PATH'])
    stats = get_database_stats(app.config['DATABASE_PATH'])
    return render_template('history.html', calculations=all_calcs, stats=stats)


@app.route('/history/delete/<int:calc_id>', methods=['POST'])
def history_delete(calc_id):
    """Delete a single calculation record from history."""
    deleted = delete_calculation(calc_id, app.config['DATABASE_PATH'])
    if deleted:
        flash(f"Calculation #{calc_id} has been deleted successfully.", "success")
    else:
        flash(f"Calculation #{calc_id} could not be found.", "warning")
    return redirect(url_for('history'))


@app.route('/history/clear', methods=['POST'])
def history_clear():
    """Clear all saved calculation history."""
    count = clear_all_calculations(app.config['DATABASE_PATH'])
    flash(f"Cleared all {count} calculation records from history.", "info")
    return redirect(url_for('history'))


@app.route('/export/csv/<int:calc_id>')
def export_csv(calc_id):
    """Export the amortization schedule for a calculation as a downloadable CSV file."""
    record = get_calculation_by_id(calc_id, app.config['DATABASE_PATH'])
    if not record:
        abort(404, description="Calculation not found.")

    schedule = generate_amortization_schedule(
        loan_amount=record['loan_amount'],
        annual_interest_rate=record['annual_interest_rate'],
        tenure_months=record['tenure_months'],
        monthly_emi=record['monthly_emi']
    )

    csv_data = generate_amortization_csv(record, schedule)
    filename = f"SmartLoan_Schedule_Loan_{calc_id}_{record['loan_type'].replace(' ', '_')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route('/export/pdf/<int:calc_id>')
def export_pdf(calc_id):
    """Export a comprehensive PDF report with summary, pie chart, and amortization table."""
    record = get_calculation_by_id(calc_id, app.config['DATABASE_PATH'])
    if not record:
        abort(404, description="Calculation not found.")

    schedule = generate_amortization_schedule(
        loan_amount=record['loan_amount'],
        annual_interest_rate=record['annual_interest_rate'],
        tenure_months=record['tenure_months'],
        monthly_emi=record['monthly_emi']
    )

    pdf_bytes = generate_amortization_pdf(record, schedule)
    filename = f"SmartLoan_Report_Loan_{calc_id}.pdf"

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route('/about')
def about():
    """
    About Project page with project objectives, working methodology,
    mathematical foundation, and college submission details.
    """
    return render_template('about.html')


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', error=e), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('404.html', error="Internal Server Error occurred. Please try again."), 500


if __name__ == '__main__':
    # Running in debug mode during local development
    print("=" * 60)
    print(" SmartLoan - Loan EMI Calculator & Repayment Planner")
    print(" Starting Flask local server on http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)
