# StreamIQ — Product Analytics & Experimentation Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.36+-FF4B4B.svg)](https://streamlit.io/)
[![Pytest](https://img.shields.io/badge/pytest-passing-brightgreen.svg)](https://pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **IMPORTANT SIMULATED DATA DISCLOSURE**:  
> All user accounts, viewing sessions, streaming events, and A/B experiment outcomes presented in StreamIQ are **100% synthetically generated** using a deterministic, reproducible mathematical simulation engine. This project is created as a professional portfolio demonstration for Product Analyst, Data Analyst, Business Analyst, and Product Management roles. It is **not affiliated with, endorsed by, or derived from Netflix or any real streaming enterprise**.

---

## 1. Project Overview & Business Problem

Modern digital video streaming platforms face intense subscriber acquisition costs, content catalog licensing overhead, and subscriber churn. Product and Growth teams require granular, real-time analytics to answer critical business questions:

1. **Where do users abandon the customer journey?** Identifying whether drop-off happens during onboarding, content discovery, or player initialization.
2. **How sticky is the product over time?** Measuring exact Day 1, Day 7, and Day 30 retention across weekly signup cohorts while strictly excluding incomplete observation windows to avoid artificial churn reporting.
3. **What content drives engagement?** Evaluating genre completion rates, watch-time velocity, and subscriber segment affinity.
4. **Do product features actually drive conversion?** Evaluating feature rollouts using statistical A/B testing with two-proportion z-tests, 95% Wald confidence intervals, Sample Ratio Mismatch (SRM) checks, and guardrail metric safeguards.
5. **How can analytics become executive action?** Generating evidence-based business recommendations and downloadable executive briefings.

StreamIQ is an end-to-end, locally runnable product analytics and experimentation platform built to solve these challenges.

---

## 2. Core Features & Capabilities

StreamIQ comprises 6 dedicated analytical modules accessible via a unified Streamlit multipage application:

| # | Module | Core Functionality |
| :-: | :--- | :--- |
| **1** | **Executive Command Center** | Headline KPI cards (Total Users, Active Users, Sessions/User, D7 Retention, Completion Rate), interactive DAU/sessions trends, genre popularity, and weekly cohort retention trends with global multi-dimensional filtering. |
| **2** | **User Behaviour Analytics** | Content catalog performance rankings, genre share analysis, 4-tier rule-based audience lifecycle segmentation, session distributions, and acquisition channel efficiency comparisons. |
| **3** | **Funnel Conversion Analysis** | Strict chronological 4-stage streaming journey (`Registered` → `Opened App` → `Viewed Content` → `Started Playback`), deduplication, drop-off quantification, and automated bottleneck detection with product hypotheses. |
| **4** | **Retention & Cohort Analysis** | Exact calendar-day Day 1, Day 7, and Day 30 retention. Enforces observation window completeness (excluding incomplete windows). Interactive weekly and monthly cohort heatmap matrix with underlying count inspections. |
| **5** | **A/B Testing Lab** | Two-proportion z-tests with pooled variance, relative lift, 95% Wald confidence intervals, Pearson Chi-Square Sample Ratio Mismatch (SRM) checks, guardrail tracking, and a 3-tier recommendation engine (**SHIP**, **DO NOT SHIP**, **CONTINUE TESTING**). |
| **6** | **Business Recommendations** | Automated synthesis of computed findings into prioritized product initiatives (Finding, Evidence, Business Significance, Explanations, Next Steps, Success/Guardrail KPIs). One-click export of Executive Briefings (`.md`) and data (`.csv`). |

---

## 3. Technology Stack

* **Language**: Python 3.10+ (tested on Python 3.12)
* **Frontend**: Streamlit 1.36+ (custom clean SaaS styling)
* **Data Manipulation**: Pandas 2.2+, NumPy 1.26+
* **Analytical Database**: SQLite 3 with typed schema, primary keys, foreign key constraints, and performance indexes
* **Interactive Visualizations**: Plotly 5.22+ (`plotly_white` theme)
* **Statistical Computing**: SciPy 1.14+ (Normal distribution CDF, Chi-square goodness-of-fit)
* **Automated Testing**: Pytest 8.0+ (22 comprehensive unit tests covering calculations, zero denominators, sequence ordering, and validation)

---

## 4. Platform Architecture & Data Pipeline

```
StreamIQ/
├── app.py                             # Main landing hub & platform overview
├── requirements.txt                   # Dependency manifest
├── README.md                          # Comprehensive project documentation
├── .gitignore                         # Version control exclusions
│
├── pages/                             # Multipage Streamlit Application
│   ├── 1_Executive_Command_Center.py  # Headline KPIs & macro trends
│   ├── 2_User_Behaviour_Analytics.py  # Catalog rankings & audience segmentation
│   ├── 3_Funnel_Analysis.py           # Chronological funnel & drop-off diagnostics
│   ├── 4_Retention_Cohort_Analysis.py # Exact-day retention & cohort heatmaps
│   ├── 5_AB_Testing_Lab.py            # Statistical A/B testing & decision engine
│   └── 6_Business_Recommendations.py  # Strategic action items & report export
│
├── src/                               # Analytical & Business Logic Layer
│   ├── __init__.py                    # Package initialization
│   ├── database.py                    # SQLite schema, connection factory & query helpers
│   ├── data_generator.py              # Reproducible synthetic data generator (seed 42)
│   ├── analytics.py                   # DAU/WAU, engagement, rankings & segmentation
│   ├── funnel.py                      # Chronological funnel tracking & bottleneck logic
│   ├── retention.py                   # Calendar-day retention & cohort matrices
│   ├── experimentation.py             # Two-proportion z-tests, SRM & decision engine
│   ├── recommendations.py             # Rule-based business recommendation generator
│   ├── reporting.py                   # Markdown briefing & CSV export generation
│   ├── ui_helpers.py                  # Shared SaaS styling & design system
│   └── validation.py                  # 6-point automated data quality audit suite
│
├── tests/                             # Automated Pytest Suite
│   ├── __init__.py
│   ├── test_database.py               # Schema, foreign keys, query helpers
│   ├── test_analytics.py              # KPI math, zero denominators, rankings
│   ├── test_funnel.py                 # Strict sequence ordering, deduplication
│   ├── test_retention.py              # Incomplete window exclusions, cohort matrix
│   ├── test_experimentation.py        # Statistical tests, SRM, lift, zero division
│   └── test_validation.py             # Data quality checks & anomaly detection
│
├── data/
│   ├── .gitkeep
│   └── streamiq.db                    # Persistent SQLite local database (generated)
│
└── docs/
    ├── metric_definitions.md          # Formal mathematical formulas & edge cases
    └── architecture.md                # System architecture & Mermaid ER diagrams
```

---

## 5. Database Schema & Data Generation

The database (`data/streamiq.db`) is structured into 6 relational tables:

1. `users`: `user_id` (PK), `signup_date`, `country`, `acquisition_channel`, `subscription_plan`.
2. `content`: `content_id` (PK), `title`, `genre`, `release_year`, `duration_minutes`.
3. `events`: `event_id` (PK), `user_id` (FK), `content_id` (FK, nullable), `event_type`, `event_timestamp`, `session_id`.
4. `experiments`: `experiment_id` (PK), `experiment_name`, `hypothesis`, `start_date`, `end_date`, `primary_metric`, `status`.
5. `experiment_assignments`: `(experiment_id, user_id)` (PK), `variant` (`control` or `treatment`).
6. `experiment_outcomes`: `(experiment_id, user_id)` (PK), `converted`, `playback_completed`, `playback_error`.

### Reproducible Synthetic Generator
* Controlled by fixed random seeds (`random.seed(42)`, `np.random.seed(42)`).
* Generates **2,000 users** across 5 channels and 3 tiers.
* Generates **100 content items** across 8 genres.
* Generates **61,000+ realistic session events** with strict sequential timestamps (`app_open` $\le$ `search`/`content_view` $\le$ `playback_start` $\le$ `playback_complete`).
* Seeds 2 realistic A/B experiments:
  - `EXP_001_HERO_CAROUSEL`: Statistically significant win (+18.5% relative lift, healthy guardrails) $\rightarrow$ **SHIP**.
  - `EXP_002_SEARCH_ALGO_V2`: Inconclusive outcome ($p \ge 0.05$, CI spans zero) $\rightarrow$ **CONTINUE TESTING**.

---

## 6. Installation & Setup Guide (Windows PowerShell)

Follow these step-by-step instructions to set up and run StreamIQ locally on Windows:

### Step 1: Open Windows PowerShell and Navigate to Workspace
```powershell
cd StreamIQ
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell displays an execution policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` once).*

### Step 3: Upgrade Pip and Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Initialize Database and Generate Synthetic Data
```powershell
python -m src.data_generator
```
*Expected output: `Data generation complete: {'users': 2000, 'content': 100, 'events': 61064, ...}`*

### Step 5: Execute Automated Unit Test Suite
```powershell
python -m pytest -v
```
*Expected output: `============================= 37 passed in X.XXs =============================`*

### Step 6: Launch StreamIQ Web Application
```powershell
python -m streamlit run app.py
```
*Your browser will automatically open:*  
👉 **Local URL**: `http://localhost:8501`

---

## 7. Automated Testing Suite

StreamIQ enforces high reliability with 22 automated tests covering core analytical edge cases:

* **Calculation Tests on Mock Data**: Evaluates known input-output pairs rather than circular assertions on generated data.
* **Funnel Sequence Violations**: Validates that events executed out of order (e.g. playback start before viewing content) do not qualify for funnel conversion.
* **Retention Incomplete Window Exclusions**: Verifies that users registered within the last 6 days are excluded from Day 7 retention denominators.
* **Zero Denominator Handling**: Guarantees zero-division safety when control conversion rate is 0% (relative lift reports `N/A`) or when user sessions are zero.
* **Statistical Rigor**: Tests two-proportion z-tests, 95% Wald confidence intervals, and Chi-square Sample Ratio Mismatch (SRM) alerts.
* **Data Quality Audits**: Validates referential integrity, event taxonomy, duplicate ID rejection, and timestamp anomalies.

Run tests anytime with:
```powershell
python -m pytest -v
```

---

## 8. Analytical Metric Formulas & Definitions

Detailed mathematical formulas, observation window criteria, and statistical models are fully documented in:
📖 **[`docs/metric_definitions.md`](docs/metric_definitions.md)**

Detailed system architecture diagrams, entity relationship models, and data pipelines are available in:
📖 **[`docs/architecture.md`](docs/architecture.md)**

---

## 9. Troubleshooting & Common Questions

1. **`streamlit : The term 'streamlit' is not recognized`**  
   *Resolution*: Run via Python module: `python -m streamlit run app.py`.

2. **`ModuleNotFoundError: No module named 'src'`**  
   *Resolution*: Ensure you run commands from the project root (`StreamIQ/`), or run with `python -m src.data_generator` and `python -m pytest`.

3. **Port 8501 already in use**  
   *Resolution*: Launch on a custom port:  
   `python -m streamlit run app.py --server.port 8502`

---

## 10. Publishing to GitHub & Future Deployment

### Publishing to GitHub
1. Initialize Git repository:
   ```powershell
   git init
   git add .
   git commit -m "feat: Initial commit of StreamIQ Product Analytics Platform"
   ```
2. Create a new repository on GitHub (e.g. `StreamIQ-Product-Analytics`).
3. Push code:
   ```powershell
   git remote add origin https://github.com/<your-username>/StreamIQ-Product-Analytics.git
   git branch -M main
   git push -u origin main
   ```

### Free Cloud Deployment via Streamlit Community Cloud
1. Push repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io/).
3. Connect your repository, set the Main file path to `app.py`, and deploy! The app will automatically generate the database on first load.

---

## 11. Portfolio Presentation Highlights

When demonstrating StreamIQ in interviews:
- **Product Management**: Showcase the **Business Recommendations** module and explain how analytical bottlenecks convert into concrete hypotheses, success metrics, and guardrails.
- **Product Analytics / Business Analysis**: Showcase **Funnel Analysis** and **Retention & Cohort Analysis**, highlighting the strict chronological ordering and observation window exclusion rules.
- **Data Analytics / Science**: Showcase the **A/B Testing Lab**, explaining the two-proportion z-test, SRM diagnostics, Wald confidence intervals, and the critical distinction between statistical significance and business impact.

---

*StreamIQ • Engineered with analytical precision for modern digital product teams.*
