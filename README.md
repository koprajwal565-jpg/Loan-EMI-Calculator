# SmartLoan – Loan EMI Calculator and Repayment Planner

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask 3.1](https://img.shields.io/badge/Framework-Flask%203.1-black.svg)](https://flask.palletsprojects.com/)
[![SQLite 3](https://img.shields.io/badge/Database-SQLite%203-003B57.svg)](https://www.sqlite.org/)
[![Matplotlib 3.11](https://img.shields.io/badge/Charts-Matplotlib%203.11-11557C.svg)](https://matplotlib.org/)
[![ReportLab 5.1](https://img.shields.io/badge/PDF-ReportLab%205.1-E11D48.svg)](https://www.reportlab.com/)
[![Tests Passing](https://img.shields.io/badge/Tests-26%2F26%20Passing-success.svg)](TESTING_REPORT.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Semester 3 Engineering College Project &bull; Programming with Python**  
> A complete, fully functional Python full-stack web application designed for financial planning, accurate reducing-balance EMI calculations, month-by-month loan amortization, multi-offer loan comparisons, SQLite persistence, and automated PDF/CSV reporting.

---

## 📋 Table of Contents
1. [Project Overview](#-project-overview)
2. [Project Objectives](#-project-objectives)
3. [Key Features](#-key-features)
4. [Technology Stack](#-technology-stack)
5. [The EMI Mathematical Formula](#-the-emi-mathematical-formula)
6. [Folder Structure](#-folder-structure)
7. [Installation & Setup](#-installation--setup)
8. [Running the Application](#-running-the-application)
9. [Running Automated Tests](#-running-automated-tests)
10. [Sample EMI Calculation](#-sample-emi-calculation)
11. [Database Architecture](#-database-architecture)
12. [PDF & CSV Export Pipeline](#-pdf--csv-export-pipeline)
13. [Future Enhancements](#-future-enhancements)
14. [Author & Academic Details](#-author--academic-details)
15. [License](#-license)

---

## 🌟 Project Overview
When applying for credit products (such as Home Loans, Car Loans, Education Loans, or Personal Loans), retail borrowers are often given a single monthly instalment figure that obscures how much compound interest they will pay over the entire term. Furthermore, evaluating competing loan offers with different tenures and interest rates can be confusing.

**SmartLoan** is built primarily in **Python** to solve these problems. It calculates precise Equated Monthly Instalments (EMI), generates month-by-month repayment schedules, offers side-by-side comparison of up to 3 loan offers, stores records in an SQLite database, and exports publication-ready PDF and CSV reports.

---

## 🎯 Project Objectives
- **Mathematical Integrity:** Eliminate floating-point roundoff errors in financial computation using Python's `Decimal` standards and round currency to two decimal places.
- **Zero-Balance Guarantee:** Ensure the final loan closing balance amortizes strictly to ₹0.00 through automated final-month balancing.
- **Support for Promotional Financing:** Handle zero-interest financing gracefully ($EMI = \frac{P}{n}$) without division-by-zero exceptions.
- **Granular Amortization Visibility:** Produce month-by-month tables detailing opening balance, EMI, principal paid, interest paid, and closing balance.
- **Comparative Decision Support:** Compare up to 3 competing loan proposals simultaneously with side-by-side matrices, graphical Matplotlib visualizations, and educational advice.
- **Persistent Data Storage:** Safely record calculation history in SQLite using parameterized SQL queries.
- **Beginner-Friendly Code Architecture:** Maintain clean, modular Python code suitable for academic viva presentation.

---

## 🚀 Key Features

- **Accurate Reducing-Balance Math (Python Decimal):** Evaluates standard compounding equations with 2-decimal financial rounding.
- **Zero-Interest Financing Support ($r = 0$):** Handles 0% promotional or manufacturer financing schemes smoothly without division-by-zero crashes.
- **Detailed Month-by-Month Amortization:** Complete schedule with Month, Opening Balance, EMI, Principal Paid, Interest Paid, and Closing Balance. Includes an automated final-month balancing adjustment ensuring the closing balance reaches strictly **₹0.00**.
- **Interactive Multi-Loan Comparator:** Compare up to 3 competing loan offers side-by-side with grouped Matplotlib bar charts and educational advice explaining the trade-off between lower monthly cash flow and higher compounding lifetime interest.
- **Persistent SQLite Database:** Automatically initializes `instance/smartloan.db` on startup and uses parameterized SQL queries to safely save, retrieve, view, and delete calculations.
- **Publication-Ready PDF Reports (ReportLab):** Generates multi-page PDF documents featuring executive summary tables, embedded Matplotlib donut charts, and formatted amortization tables with "Page X of Y" pagination.
- **CSV Spreadsheet Export:** Native Python `csv` export for instant spreadsheet auditing in Microsoft Excel or Google Sheets.
- **Modern Fintech UI/UX:** Styled in dark navy blue (`#0F172A`), vibrant accent blue (`#2563EB`), emerald green (`#059669`), and white cards with subtle shadows. Includes a responsive sidebar on desktop and collapsible navigation on mobile.

---

## 🛠 Technology Stack

- **Backend:** Python 3 (Python 3.10+)
- **Web Framework:** Flask 3.1
- **Database:** SQLite 3 (Built-in standard library)
- **Charts & Visualizations:** Matplotlib 3.11 (Headless `Agg` backend)
- **PDF Generation:** ReportLab 5.1
- **Spreadsheet Generation:** Python `csv` module (Built-in)
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5, Bootstrap Icons
- **Testing Framework:** Pytest 9.2

---

## 📐 The EMI Mathematical Formula

### 1. Standard Reducing-Balance Loan
In a standard reducing-balance loan, interest is calculated on the remaining principal balance rather than the original borrowing:

$$\text{EMI} = \frac{P \times r \times (1 + r)^n}{(1 + r)^n - 1}$$

Where:
- **$P$ (Principal):** The total money borrowed (e.g., ₹10,00,000).
- **$R$ (Annual Interest Rate):** The percentage rate per year quoted by the lender (e.g., 8.5%).
- **$r$ (Monthly Interest Rate):** Calculated as:
  $$r = \frac{R}{12 \times 100}$$
- **$n$ (Total Number of Monthly Instalments):** If tenure is in years ($Y$), $n = Y \times 12$.

### 2. Zero-Interest Promo Loan ($r = 0$)
When the annual interest rate is 0.0%:
$$\text{EMI} = \frac{P}{n}$$
$$\text{Total Interest} = 0.00$$
$$\text{Total Repayment} = P$$

### 3. Month-by-Month Amortization Logic
For each month $m \in \{1, 2, \dots, n\}$:
- $\text{Interest Paid}_m = \text{Opening Balance}_m \times r$
- $\text{Principal Paid}_m = \text{EMI} - \text{Interest Paid}_m$
- $\text{Closing Balance}_m = \text{Opening Balance}_m - \text{Principal Paid}_m$
- **Final Month ($m = n$):** $\text{Principal Paid}_n = \text{Opening Balance}_n$, $\text{Closing Balance}_n = 0.00$.

---

## 📁 Folder Structure

```
Loan-EMI-Calculator/
│
├── app.py                     # Main Flask web application, routes & filters
├── config.py                  # Application settings, limits & currency configuration
├── calculations.py            # Financial math (EMI formula, amortization, comparison)
├── database.py                # SQLite database operations & parameterized queries
├── reports.py                 # Matplotlib charts (PNG/Base64) & ReportLab PDF / CSV
├── requirements.txt           # Python library dependencies
├── README.md                  # Comprehensive setup and usage instructions
├── TESTING_REPORT.md          # 26/26 automated unit test report
├── LICENSE                    # MIT Open Source License
├── .gitignore                 # Git ignore file for Python, SQLite & exports
│
├── instance/                  # Automatically created SQLite database folder
│   └── smartloan.db           # Persistent SQLite database file
│
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Master layout with responsive sidebar & topbar
│   ├── index.html             # Home / Dashboard with KPI cards & quick estimator
│   ├── calculator.html        # Main EMI calculator input form with presets
│   ├── results.html           # Result dashboard with 4 metric cards & pie chart
│   ├── amortization.html      # Month-by-month table with search & pagination
│   ├── comparison.html        # 3-way loan comparator with bar chart
│   ├── history.html           # SQLite history table with search & delete actions
│   ├── about.html             # Academic project documentation & viva notes
│   └── 404.html               # Custom 404 error page
│
├── static/                    # Frontend static assets
│   ├── css/
│   │   └── style.css          # Custom fintech styling (navy blue theme, cards)
│   ├── js/
│   │   └── main.js            # Table search, chips, mobile sidebar toggle
│   └── images/                # Static visual assets
│
├── exports/                   # Downloadable PDF reports and CSV files
│
├── tests/                     # Automated test suite (100% pass rate)
│   ├── test_calculations.py   # Math formulas, zero-rate, boundaries, schedule
│   ├── test_database.py       # SQLite CRUD, stats, deletion, and wipe tests
│   └── test_routes.py         # Flask routes, form validation, PDF/CSV downloads
│
└── docs/                      # College project documentation
    ├── problem_statement.md   # Problem statement and core objectives
    ├── algorithm.md           # Step-by-step algorithms
    ├── flowchart.md           # Mermaid system & calculation flowcharts
    ├── sample_input_output.md # Verified test cases & sample outputs
    └── project_report.md      # Full academic project report for college submission
```

---

## 💻 Installation & Setup

Clone the repository and prepare the virtual environment:

```powershell
# 1. Clone the repository
git clone https://github.com/koprajwal565-jpg/Loan-EMI-Calculator.git

# 2. Change into the project directory
cd Loan-EMI-Calculator

# 3. Create a Python Virtual Environment
python -m venv venv

# 4. Activate the Virtual Environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows Command Prompt:
venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

# 5. Install Required Dependencies
pip install -r requirements.txt
```

---

## ▶️ Running the Application

Start the Flask server:
```powershell
python app.py
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🧪 Running Automated Tests

Run the full automated test suite using `pytest`:
```powershell
python -m pytest -v
```

All 26 unit and integration tests pass in ~6 seconds with 100% success rate. See [TESTING_REPORT.md](TESTING_REPORT.md) for full test execution logs.

---

## 📊 Sample EMI Calculation

### Example: Standard Retail Home Loan
- **Principal ($P$):** ₹25,00,000 (₹25 Lakhs)
- **Annual Interest Rate ($R$):** 8.50% p.a.
- **Tenure:** 15 Years (180 Months)
- **Loan Category:** Home Loan

### Output:
- **Monthly EMI:** **₹24,618.73**
- **Total Principal:** ₹25,00,000.00 (56.42%)
- **Total Interest:** **₹19,31,371.40** (43.58%)
- **Total Repayment:** **₹44,31,371.40**
- **Closing Balance after Month 180:** **₹0.00**

---

## 🗄 Database Architecture

SmartLoan utilizes an ACID-compliant local SQLite database (`instance/smartloan.db`). The table is initialized automatically on startup:

```sql
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
```
All queries use parameterized placeholders (`?`) to prevent SQL injection vulnerabilities.

---

## 📑 PDF & CSV Export Pipeline

- **PDF Generation (`reports.py`):** Uses ReportLab's flowable framework (`SimpleDocTemplate`, `Table`, `Image`) with a custom two-pass `NumberedCanvas` to draw dynamic "Page X of Y" numbering, styled financial tables, and embedded Matplotlib donut charts.
- **CSV Streaming (`reports.py`):** Uses Python's built-in `csv` module with `io.StringIO` to generate RFC 4180 compliant CSV schedules for spreadsheet auditing.

---

## 🔮 Future Enhancements

- **Interactive Prepayment Simulator:** Visualizing how one-off annual bonus prepayments shorten loan tenure.
- **Floating Interest Rate Modeler:** Stress-testing monthly repayments against central bank repo rate revisions.
- **User Authentication:** Multi-user accounts with personal saved loan portfolios.

---

## 👤 Author & Academic Details

- **Student / Author:** Prajwal K O
- **GitHub:** [@koprajwal565-jpg](https://github.com/koprajwal565-jpg)
- **Course:** Programming with Python &bull; Semester 3
- **Degree:** Bachelor of Engineering / Technology (Computer Science & Engineering)

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
