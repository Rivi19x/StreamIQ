"""StreamIQ - Product Analytics & Experimentation Platform.

Main entry point and application navigation hub.
"""

from __future__ import annotations

import streamlit as st

from src.database import ensure_database_ready, get_table_counts, init_db
from src.data_generator import generate_synthetic_data
from src.ui_helpers import (
    apply_custom_css,
    render_hero_header,
    render_kpi_card,
    render_module_card,
    render_simulated_data_badge,
    render_theme_selector,
    render_top_navbar,
)
from src.validation import DataQualityAudit

# Streamlit Page Configuration
st.set_page_config(
    page_title="StreamIQ — Product Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_css()

# Sidebar Info
st.sidebar.title("StreamIQ 📊")
st.sidebar.caption("Product Analytics & Experimentation Engine")
render_theme_selector()
st.sidebar.markdown("---")

# Verify database exists & is populated
ensure_database_ready()
counts = get_table_counts()

# Top Brand Bar matching reference
render_top_navbar(
    brand_title="StreamIQ | Platform Overview & Architecture",
    date_display="Simulated Dataset (2026)",
)

# Top Hero Header
render_hero_header(
    badge_text="PRODUCT ANALYTICS PLATFORM",
    title="Platform Overview & Analytics Architecture",
    subtitle="Evaluate subscriber behavior, analyze multi-stage conversion funnels, track retention cohorts, and govern A/B testing experiments with statistical rigor.",
)

render_simulated_data_badge()

# Beginner-friendly platform introduction
with st.expander("📖 First time here? Quick guide to StreamIQ in 60 seconds"):
    st.markdown("""
    Welcome to **StreamIQ**! This application simulates what a modern product analytics stack (like Amplitude, Mixpanel, or internal streaming intelligence platforms) does:

    * **Executive Command Center**: A bird's-eye view of high-level business health (active users, session frequency, retention).
    * **User Behaviour Analytics**: Who is watching what? Identifies top-performing shows, user activity tiers, and subscription plan trends.
    * **Funnel Analysis**: Where do viewers give up? Tracks users step-by-step from registration to hitting 'Play', highlighting friction points.
    * **Retention & Cohort Analysis**: Do viewers come back? Measures Day 1, 7, and 30 return rates to evaluate subscriber stickiness.
    * **A/B Testing Lab**: Does a new feature actually work? Tests hypotheses with statistical rigor to decide whether to **Ship** or **Halt**.
    * **Business Recommendations**: What should leadership do next? Summarizes concrete, evidence-backed action items with measurable goals.
    """)

# Platform Health & Database Summary Cards
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    render_kpi_card(
        label="Registered Accounts",
        value=f"{counts.get('users', 0):,}",
        info_text="Total registered user accounts stored in the platform database.",
        subtext="All-time user base",
        card_style="blue",
    )
with col2:
    render_kpi_card(
        label="Catalog Titles",
        value=f"{counts.get('content', 0):,}",
        info_text="Total active movies and series titles available in the streaming catalog.",
        subtext="Movies & series",
        card_style="sage",
    )
with col3:
    render_kpi_card(
        label="Tracked Actions",
        value=f"{counts.get('events', 0):,}",
        info_text="Total user interaction events recorded (app opens, content views, playbacks).",
        subtext="Behavioral event stream",
        card_style="lavender",
    )
with col4:
    render_kpi_card(
        label="A/B Tests Run",
        value=f"{counts.get('experiments', 0):,}",
        info_text="Controlled experiments evaluated across control and variant user cohorts.",
        subtext="Evaluated experiments",
        card_style="pink",
    )
with col5:
    render_kpi_card(
        label="Experiment Viewers",
        value=f"{counts.get('experiment_assignments', 0):,}",
        info_text="Total unique viewers assigned to active or completed experimental cohorts.",
        subtext="Allocated test viewers",
        card_style="yellow",
    )

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Application Modules Grid
st.subheader("Explore Analytics Modules")
st.markdown("Select an analytical domain below to inspect live product telemetry, diagnostic models, and experimentation results:")

m_col1, m_col2 = st.columns(2)

with m_col1:
    render_module_card(
        icon="⚡",
        title="Executive Command Center",
        subtitle="High-level platform health & growth tracking",
        description="Executive-ready performance dashboard tracking platform scale, streaming volume, and audience return rates:",
        bullets=[
            "<strong>Key Headline KPIs</strong>: Active viewers, video completion rates, sessions per viewer, and 7-day return rates.",
            "<strong>Multidimensional Filters</strong>: Slice by date range, content genre, acquisition channel, or subscription plan.",
            "<strong>Telemetry Trends</strong>: Day-by-day active viewers and streaming demand curves.",
        ],
    )
    st.page_link("pages/1_Executive_Command_Center.py", label="Open Executive Command Center →", icon="⚡")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    render_module_card(
        icon="👥",
        title="User Behaviour Analytics",
        subtitle="Engagement, content affinity & user tiers",
        description="Deep behavioral breakdown of audience streaming patterns, catalog affinity, and tier distributions:",
        bullets=[
            "<strong>Top Content Leaderboard</strong>: Rankings of most-streamed titles with duration and completion rates.",
            "<strong>Audience Segmentation</strong>: Group viewers into Highly Active, Moderately Active, Low Activity, and New Explorers.",
            "<strong>Acquisition Channel Comparison</strong>: Organic search vs social vs referral streaming intensity.",
        ],
    )
    st.page_link("pages/2_User_Behaviour_Analytics.py", label="Open User Behaviour Analytics →", icon="👥")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    render_module_card(
        icon="🔻",
        title="Funnel Analysis",
        subtitle="Multi-step user journey & drop-off diagnosis",
        description="Chronological conversion analysis pinpointing where users abandon the path to video playback:",
        bullets=[
            "<strong>The 4-Step Sequence</strong>: Account Created → App Opened → Show Viewed → Playback Started.",
            "<strong>Bottleneck Identification</strong>: Mathematical detection of the step with highest abandoned users.",
            "<strong>Observation Window Filters</strong>: Fair conversion attribution windows (7, 14, 30 days, or full period).",
        ],
    )
    st.page_link("pages/3_Funnel_Analysis.py", label="Open Funnel Analysis →", icon="🔻")

with m_col2:
    render_module_card(
        icon="🔄",
        title="Retention & Cohort Analysis",
        subtitle="Cohort decay curves & habituation matrices",
        description="Subscriber habituation and churn tracking evaluated with rigorous observation window rules:",
        bullets=[
            "<strong>Exact-Day Return Rates</strong>: Day 1, Day 7, and Day 30 user return percentages.",
            "<strong>Observation Window Policy</strong>: Mature cohort denominator cutoff prevents artificial churn distortion.",
            "<strong>Cohort Heatmap Matrix</strong>: Weekly/monthly signup groups tracked across subsequent retention cycles.",
        ],
    )
    st.page_link("pages/4_Retention_Cohort_Analysis.py", label="Open Retention & Cohort Analysis →", icon="🔄")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    render_module_card(
        icon="🧪",
        title="A/B Testing Lab",
        subtitle="Scientific experimentation & rollout governance",
        description="Statistically grounded experimentation framework protecting platform user experience:",
        bullets=[
            "<strong>Automated Ship / No-Ship Decisions</strong>: Two-proportion z-tests, p-values, and 95% confidence intervals.",
            "<strong>Traffic Split Verification (SRM)</strong>: Chi-square goodness-of-fit test detecting sample ratio mismatches.",
            "<strong>Quality Guardrails</strong>: Verifies video playback errors and app crashes remain within safe limits.",
        ],
    )
    st.page_link("pages/5_AB_Testing_Lab.py", label="Open A/B Testing Lab →", icon="🧪")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    render_module_card(
        icon="📋",
        title="Business Recommendations",
        subtitle="Evidence-backed roadmaps & executive briefing export",
        description="Synthesizes raw behavioral metrics into prioritized, high-leverage product initiatives:",
        bullets=[
            "<strong>8-Part Product Management Framework</strong>: Findings, evidence, significance, hypotheses, and actions.",
            "<strong>Target Metrics</strong>: Explicit primary success KPIs and counter-balancing guardrail metrics.",
            "<strong>Executive Export Center</strong>: One-click download of ready-to-share Markdown briefings and CSV data.",
        ],
    )
    st.page_link("pages/6_Business_Recommendations.py", label="Open Business Recommendations →", icon="📋")

st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)

# Data Quality & Integrity Section
audit_header_html = (
    '<div class="analytics-card">'
    '<div class="analytics-card-header">'
    '<h3 class="analytics-card-title">🛡️ Data Quality &amp; Integrity Validation Suite</h3>'
    '<span class="hero-badge" style="margin-bottom: 0;">AUTOMATED AUDIT</span>'
    '</div>'
    '<p style="font-size: 0.875rem; color: var(--text-muted); margin-bottom: 16px;">'
    'StreamIQ enforces strict referential integrity, foreign key constraints, temporal sequencing, and schema consistency. '
    'Click below to execute the live database audit suite:'
    '</p>'
    '</div>'
)
if hasattr(st, "html"):
    st.html(audit_header_html)
else:
    st.markdown(audit_header_html, unsafe_allow_html=True)

if st.button("Run Full Data Quality Audit", type="primary"):
    audit = DataQualityAudit()
    results = audit.run_full_audit()
    all_passed = all(r["passed"] for r in results)

    if all_passed:
        st.success("✅ All 6 data quality and referential integrity checks passed with 0 violations!")
    else:
        st.error("⚠️ Some data quality checks reported violations.")

    for r in results:
        status_icon = "✅" if r["passed"] else "❌"
        with st.expander(f"{status_icon} {r['check']} (Violations: {r['violations_count']})"):
            for detail in r["details"]:
                st.markdown(f"- {detail}")

st.markdown("---")
st.caption("StreamIQ Product Analytics • Built with Python, Streamlit, Pandas, SQLite, Plotly & SciPy.")
