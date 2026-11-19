"""StreamIQ - Retention and Cohort Analysis.

Calculates exact-day retention rates (Day 1, Day 7, Day 30), generates
cohort retention heatmaps, and enforces strict observation-window logic.
"""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.database import ensure_database_ready, execute_query
from src.retention import (
    calculate_day_n_retention,
    get_anchor_date,
    get_cohort_retention_matrix,
    get_retention_trend_over_time,
)
from src.ui_helpers import (
    apply_custom_css,
    apply_plotly_theme,
    render_hero_header,
    render_kpi_card,
    render_simulated_data_badge,
    render_theme_selector,
    render_top_navbar,
)

st.set_page_config(page_title="Retention & Cohorts — StreamIQ", page_icon="🔄", layout="wide")
apply_custom_css()
ensure_database_ready()

anchor = get_anchor_date()

# Top Brand Bar
render_top_navbar(
    brand_title="StreamIQ | Subscriber Retention & Cohort Analysis",
    date_display=f"Anchor: {anchor}",
)

# Hero Header
render_hero_header(
    badge_text="COHORT RETENTION & CHURN",
    title="Subscriber Retention & Cohort Analysis",
    subtitle="Track viewer return rates across critical lifecycle milestones (Day 1, 7, 30), examine cohort retention matrices, and evaluate habit formation with strict observation windows.",
)

render_simulated_data_badge()

# Filters in Sidebar
render_theme_selector()
st.sidebar.header("Cohort Filters")

df_channels = execute_query("SELECT DISTINCT acquisition_channel FROM users ORDER BY 1")
channels = ["All"] + df_channels["acquisition_channel"].tolist() if not df_channels.empty else ["All"]

df_plans = execute_query("SELECT DISTINCT subscription_plan FROM users ORDER BY 1")
plans = ["All"] + df_plans["subscription_plan"].tolist() if not df_plans.empty else ["All"]

sel_channel = st.sidebar.selectbox("Acquisition Channel", channels)
sel_plan = st.sidebar.selectbox("Subscription Plan", plans)
granularity = st.sidebar.radio("Cohort Matrix Granularity", ["weekly", "monthly"], index=0)

# Compute exact retention KPIs
d1 = calculate_day_n_retention(1, channel=sel_channel, plan=sel_plan, anchor_date=anchor)
d7 = calculate_day_n_retention(7, channel=sel_channel, plan=sel_plan, anchor_date=anchor)
d30 = calculate_day_n_retention(30, channel=sel_channel, plan=sel_plan, anchor_date=anchor)

# KPI Cards (Un-truncated labels, circled ⓘ tooltips)
k1, k2, k3, k4 = st.columns(4)
with k1:
    render_kpi_card(
        label="Day 1 Return Rate",
        value=f"{d1['retention_rate_pct']:.1f}%",
        info_text=f"Percentage of eligible users returning on Day 1 (Evaluated on {d1['eligible_cohort_size']:,} mature users).",
        subtext=f"Cohort: {d1['eligible_cohort_size']:,} users",
    )
with k2:
    render_kpi_card(
        label="Day 7 Return Rate",
        value=f"{d7['retention_rate_pct']:.1f}%",
        info_text=f"Percentage of eligible users returning on Day 7 (Evaluated on {d7['eligible_cohort_size']:,} mature users).",
        subtext=f"Cohort: {d7['eligible_cohort_size']:,} users",
    )
with k3:
    render_kpi_card(
        label="Day 30 Return Rate",
        value=f"{d30['retention_rate_pct']:.1f}%",
        info_text=f"Percentage of eligible users returning on Day 30 (Evaluated on {d30['eligible_cohort_size']:,} mature users).",
        subtext=f"Cohort: {d30['eligible_cohort_size']:,} users",
    )
with k4:
    render_kpi_card(
        label="Latest Event Date",
        value=anchor.strftime("%Y-%m-%d"),
        info_text="Most recent user activity timestamp recorded in the database, used as the cohort maturity anchor date.",
        subtext="Maturity anchor date",
    )

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Observation Window Policy Callout
st.info(
    f"ℹ️ **Observation Window Policy**: Retention rates only include accounts that signed up long enough ago to complete the window "
    f"relative to our latest data on {anchor.strftime('%Y-%m-%d')} (e.g. Day 30 requires signup on or before {d30['cutoff_signup_date']}). "
    f"Recent subscribers are excluded from denominators to prevent artificial churn bias."
)

# Section 1: Retention Heatmap Matrix
st.subheader("1. Signup Cohort Retention Heatmap (%)")

pct_matrix, count_matrix = get_cohort_retention_matrix(
    granularity=granularity,
    periods=6 if granularity == "weekly" else 4,
    channel=sel_channel,
    plan=sel_plan,
)

if not pct_matrix.empty:
    # Exclude 'Cohort Size' from heatmap color scaling
    heatmap_cols = [c for c in pct_matrix.columns if c != "Cohort Size"]
    heatmap_data = pct_matrix[heatmap_cols]

    fig_heat = px.imshow(
        heatmap_data,
        labels=dict(x="Subsequent Period", y="Signup Cohort", color="Retention (%)"),
        x=heatmap_cols,
        y=pct_matrix.index,
        color_continuous_scale=[[0, "#F4F6F9"], [0.2, "#DCE5F0"], [0.5, "#6B7BB8"], [1.0, "#3A4781"]],
        text_auto=".1f",
        aspect="auto",
    )
    apply_plotly_theme(fig_heat)
    fig_heat.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        coloraxis_colorbar=dict(title="Retention %", thickness=14, len=0.75),
    )
    st.plotly_chart(fig_heat, use_container_width=True)
    st.caption("How each signup group retains over time. Darker blue indicates higher retention; blank cells indicate periods that haven't elapsed yet.")

    # Underlying Data Inspection Tabs
    tab_pct, tab_counts = st.tabs(["Retention Percentages (%)", "Active User Headcount"])
    with tab_pct:
        st.dataframe(pct_matrix, use_container_width=True)
    with tab_counts:
        st.dataframe(count_matrix, use_container_width=True)
else:
    st.warning("Insufficient cohort history to generate retention matrix.")

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Section 2: Retention Trend Over Time
st.subheader("2. Weekly Cohort Retention Trends (Day 7 vs Day 1)")
trend_d7 = get_retention_trend_over_time(day_n=7, channel=sel_channel, plan=sel_plan)
trend_d1 = get_retention_trend_over_time(day_n=1, channel=sel_channel, plan=sel_plan)

if not trend_d7.empty:
    fig_t = go.Figure()
    if not trend_d1.empty:
        fig_t.add_trace(
            go.Scatter(
                x=trend_d1["cohort_week"],
                y=trend_d1["retention_rate_pct"],
                mode="lines+markers",
                name="Day 1 Return Rate (%)",
                line=dict(color="#397653", width=2.5, shape="spline", smoothing=1.2),
                marker=dict(size=7, color="#2D5C41"),
            )
        )
    fig_t.add_trace(
        go.Scatter(
            x=trend_d7["cohort_week"],
            y=trend_d7["retention_rate_pct"],
            mode="lines+markers",
            name="Day 7 Return Rate (%)",
            line=dict(color="#3A4781", width=2.5, shape="spline", smoothing=1.2),
            marker=dict(size=7, color="#26334D"),
        )
    )
    apply_plotly_theme(fig_t)
    fig_t.update_layout(
        hovermode="x unified",
        xaxis_title="Signup Week",
        yaxis_title="Return Rate (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_t, use_container_width=True)
    st.caption("Compares immediate next-day return rate against one-week return rate across weekly signup cohorts.")

# Methodology Reference
with st.expander("Retention Methodology"):
    st.markdown(r"""
    - **Exact-Day Retention**: A user must return on the exact calendar day being measured ($t_{event} - t_{signup} = N \text{ days}$). This is the strictest standard for product habituation.
    - **Rolling Retention**: A user counts if they return on that day or any subsequent day ($t_{event} - t_{signup} \ge N \text{ days}$).
    - **Incomplete Observation Handling**: Future or incomplete retention periods appear blank/NaN rather than being incorrectly represented as 0.0%, preventing misleading degradation charts.
    """)
