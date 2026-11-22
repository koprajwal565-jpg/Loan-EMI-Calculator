"""
SmartLoan - SQLite Database Module
Handles persistent storage of calculation history using parameterized queries
and thread-safe SQLite3 connections.
"""

import os
import sqlite3
from datetime import datetime
from config import Config


def get_db_path(custom_path=None):
    """Resolve database file path and ensure target directory exists."""
    if custom_path:
        db_path = custom_path
    else:
        db_path = Config.DATABASE_PATH
        
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        
    return db_path


def get_connection(custom_path=None):
    """
    Establish and return a SQLite database connection with row factory.
    Row factory enables dict-like attribute access on query results.
    """
    path = get_db_path(custom_path)
    conn = sqlite3.connect(path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrency and write performance
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db(custom_path=None):
    """
    Initialize SQLite database tables.
    Runs automatically during application startup.
    """
    conn = get_connection(custom_path)
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    loan_amount REAL NOT NULL,
                    annual_interest_rate REAL NOT NULL,
                    tenure_months INTEGER NOT NULL,
                    tenure_years REAL NOT NULL,
                    loan_type TEXT NOT NULL,
                    monthly_emi REAL NOT NULL,
                    total_interest REAL NOT NULL,
                    total_payment REAL NOT NULL,
                    principal_pct REAL NOT NULL,
                    interest_pct REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_calc_created 
                ON calculations(created_at DESC);
            """)
    finally:
        conn.close()


def insert_calculation(calc_data, custom_path=None):
    """
    Save an EMI calculation to database history using parameterized SQL.
    
    Returns:
        int: The auto-generated ID of the newly inserted record.
    """
    conn = get_connection(custom_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO calculations (
                    loan_amount,
                    annual_interest_rate,
                    tenure_months,
                    tenure_years,
                    loan_type,
                    monthly_emi,
                    total_interest,
                    total_payment,
                    principal_pct,
                    interest_pct,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                calc_data['loan_amount'],
                calc_data['annual_interest_rate'],
                calc_data['tenure_months'],
                calc_data.get('tenure_years', round(calc_data['tenure_months'] / 12.0, 2)),
                calc_data.get('loan_type', 'Personal Loan'),
                calc_data['monthly_emi'],
                calc_data['total_interest'],
                calc_data['total_payment'],
                calc_data.get('principal_pct', 0.0),
                calc_data.get('interest_pct', 0.0),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            return cursor.lastrowid
    finally:
        conn.close()


def get_all_calculations(custom_path=None):
    """
    Retrieve all calculation history records, ordered chronologically newest first.
    
    Returns:
        list of dicts
    """
    conn = get_connection(custom_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, loan_amount, annual_interest_rate, tenure_months, tenure_years,
                   loan_type, monthly_emi, total_interest, total_payment,
                   principal_pct, interest_pct, created_at
            FROM calculations
            ORDER BY id DESC;
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_recent_calculations(limit=5, custom_path=None):
    """
    Retrieve the most recent N calculation records for dashboard display.
    """
    conn = get_connection(custom_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, loan_amount, annual_interest_rate, tenure_months, tenure_years,
                   loan_type, monthly_emi, total_interest, total_payment,
                   principal_pct, interest_pct, created_at
            FROM calculations
            ORDER BY id DESC
            LIMIT ?;
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_calculation_by_id(calc_id, custom_path=None):
    """
    Retrieve a single calculation record by its primary key ID.
    
    Returns:
        dict or None
    """
    conn = get_connection(custom_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, loan_amount, annual_interest_rate, tenure_months, tenure_years,
                   loan_type, monthly_emi, total_interest, total_payment,
                   principal_pct, interest_pct, created_at
            FROM calculations
            WHERE id = ?;
        """, (calc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_calculation(calc_id, custom_path=None):
    """
    Delete a specific calculation record by ID.
    
    Returns:
        bool: True if a record was deleted, False otherwise.
    """
    conn = get_connection(custom_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM calculations WHERE id = ?;", (calc_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()


def clear_all_calculations(custom_path=None):
    """
    Clear all saved calculation records from the history table.
    
    Returns:
        int: Number of records deleted.
    """
    conn = get_connection(custom_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM calculations;")
            deleted_count = cursor.rowcount
            # Reset the autoincrement sequence
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='calculations';")
            return deleted_count
    finally:
        conn.close()


def get_database_stats(custom_path=None):
    """
    Compute aggregate statistics for the dashboard.
    
    Returns:
        dict with total_calculations, total_loan_volume, total_interest_volume, avg_interest_rate
    """
    conn = get_connection(custom_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(loan_amount), 0.0) as total_volume,
                COALESCE(SUM(total_interest), 0.0) as total_interest,
                COALESCE(AVG(annual_interest_rate), 0.0) as avg_rate
            FROM calculations;
        """)
        row = cursor.fetchone()
        return {
            'total_calculations': row['count'],
            'total_loan_volume': round(row['total_volume'], 2),
            'total_interest_volume': round(row['total_interest'], 2),
            'avg_interest_rate': round(row['avg_rate'], 2)
        }
    finally:
        conn.close()
