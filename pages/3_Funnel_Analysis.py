"""StreamIQ - Funnel Analysis.

Visualizes the 4-step user journey from registration to playback start,
identifies conversion bottlenecks, and isolates drop-off points.
"""

from __future__ import annotations

import datetime as dt
import plotly.graph_objects as go
import streamlit as st

from src.database import ensure_database_ready, execute_query
from src.funnel import calculate_funnel, get_funnel_by_channel
from src.ui_helpers import (
    apply_custom_css,
    apply_plotly_theme,
    render_hero_header,
    render_kpi_card,
    render_simulated_data_badge,
    render_theme_selector,
    render_top_navbar,
)

st.set_page_config(page_title="Funnel Analysis — StreamIQ", page_icon="🔻", layout="wide")
apply_custom_css()
ensure_database_ready()

# Filters in Sidebar
render_theme_selector()
st.sidebar.header("Funnel Filters")

df_channels = execute_query("SELECT DISTINCT acquisition_channel FROM users ORDER BY 1")
channels = ["All"] + df_channels["acquisition_channel"].tolist() if not df_channels.empty else ["All"]

df_plans = execute_query("SELECT DISTINCT subscription_plan FROM users ORDER BY 1")
plans = ["All"] + df_plans["subscription_plan"].tolist() if not df_plans.empty else ["All"]

df_dates = execute_query("SELECT MIN(DATE(signup_date)) as min_d, MAX(DATE(signup_date)) as max_d FROM users")
min_date = dt.date(2026, 7, 1)
max_date = dt.date(2026, 10, 24)
if not df_dates.empty and df_dates["min_d"].iloc[0]:
    try:
        min_date = dt.date.fromisoformat(df_dates["min_d"].iloc[0])
        max_date = dt.date.fromisoformat(df_dates["max_d"].iloc[0])
    except Exception:
        pass

date_range = st.sidebar.date_input("Registration Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
sel_channel = st.sidebar.selectbox("Acquisition Channel", channels)
sel_plan = st.sidebar.selectbox("Subscription Plan", plans)

window_options = {
    "No Limit (Entire History)": None,
    "7 Days (Fast Conversion Window)": 7,
    "14 Days (Standard Window)": 14,
    "30 Days (Extended Window)": 30,
}
sel_window_label = st.sidebar.selectbox("Conversion Window", list(window_options.keys()), index=0)
sel_window_days = window_options[sel_window_label]

start_date_str = date_range[0].isoformat() if len(date_range) > 0 else None
end_date_str = date_range[1].isoformat() if len(date_range) > 1 else None

# Top Brand Bar
render_top_navbar(
    brand_title="StreamIQ | Conversion Funnel & Drop-off Diagnostics",
    date_display=f"{start_date_str or min_date.isoformat()} → {end_date_str or max_date.isoformat()}",
)

# Hero Header
render_hero_header(
    badge_text="CONVERSION & RETENTION FUNNELS",
    title="Conversion Funnel & Drop-off Diagnostics",
    subtitle="Track viewers chronologically from account creation through video playback, diagnose stage-by-stage drop-off friction, and compare conversion performance across acquisition channels.",
)

render_simulated_data_badge()

# Calculate Funnel
funnel_result = calculate_funnel(
    start_date=start_date_str,
    end_date=end_date_str,
    channel=sel_channel,
    plan=sel_plan,
    conversion_window_days=sel_window_days,
)

df_funnel = funnel_result["funnel_table"]
bottleneck = funnel_result["bottleneck"]

# KPI Headline Cards (Un-truncated labels, circled ⓘ tooltips)
k1, k2, k3, k4 = st.columns(4)
with k1:
    render_kpi_card(
        label="Starting Accounts",
        value=f"{funnel_result['base_users']:,}",
        info_text="Total users who registered within the selected cohort window and filter criteria.",
        subtext="Stage 1 baseline",
    )
with k2:
    render_kpi_card(
        label="Reached Playback",
        value=f"{funnel_result['final_converted']:,}",
        info_text="Users who successfully started streaming a video in proper chronological order.",
        subtext="Stage 4 converted",
    )
with k3:
    render_kpi_card(
        label="End-to-End Conversion",
        value=f"{funnel_result['overall_conversion_pct']:.1f}%",
        info_text="Percentage of starting accounts who made it all the way from registration to video playback.",
        subtext="Full funnel yield",
    )
with k4:
    if bottleneck:
        # Extract clean step name without numeric prefix e.g. "Started Playback"
        clean_step = bottleneck["stage_name"].split(". ", 1)[-1]
        render_kpi_card(
            label="Biggest Drop-off Step",
            value=clean_step,
            info_text=f"The largest audience loss occurs at '{clean_step}': {bottleneck['users_lost']:,} viewers abandoned the funnel ({bottleneck['drop_off_pct']:.1f}% drop-off).",
            delta=f"-{bottleneck['users_lost']:,} lost",
            delta_color="inverse",
            subtext=f"Drop-off rate: {bottleneck['drop_off_pct']:.1f}%",
            card_style="pink",
        )
    else:
        render_kpi_card(
            label="Biggest Drop-off Step",
            value="None",
            info_text="No bottleneck detected in the current funnel cohort.",
            subtext="Smooth progression",
            card_style="sage",
        )

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Section 1: Journey Progression & Conversion Breakdown
st.subheader("1. User Journey Progression & Step Breakdown")
col_chart, col_table = st.columns([3, 2])

with col_chart:
    st.markdown("##### Visual Funnel Progression")
    fig_funnel = go.Figure(
        go.Funnel(
            y=df_funnel["stage_name"],
            x=df_funnel["users"],
            textinfo="value+percent initial+percent previous",
            marker=dict(
                color=["#3A4781", "#4F5F9F", "#6B7BB8", "#8B9BD1"],
                line=dict(width=1, color="#26334D"),
            ),
            connector=dict(line=dict(color="#DCE3EC", width=1.5)),
        )
    )
    apply_plotly_theme(fig_funnel)
    fig_funnel.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_funnel, use_container_width=True)
    st.caption("Visual funnel showing user headcount and relative retention across successive stages.")

with col_table:
    st.markdown("##### Step-by-Step Conversion Breakdown")
    display_funnel = df_funnel[["stage_name", "users", "step_conversion_pct", "overall_conversion_pct", "users_lost", "drop_off_pct"]].rename(
        columns={
            "stage_name": "Journey Step",
            "users": "Users Reaching Step",
            "step_conversion_pct": "Step Conversion (%)",
            "overall_conversion_pct": "Overall Conversion (%)",
            "users_lost": "Users Lost",
            "drop_off_pct": "Drop-off Rate (%)",
        }
    )
    st.dataframe(
        display_funnel,
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "**Metric Definitions**: "
        "**Step Conversion**: % of viewers reaching this step from the previous stage. • "
        "**Overall Conversion**: % of starting accounts reaching this step from Stage 1. • "
        "**Users Lost**: Net accounts dropping out at this transition. • "
        "**Drop-off Rate**: % audience loss relative to the preceding step."
    )

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Section 2: Acquisition Channel Funnel Comparison
st.subheader("2. Conversion by Acquisition Channel")
df_channel_funnel = get_funnel_by_channel(
    start_date=start_date_str,
    end_date=end_date_str,
    plan=sel_plan,
    conversion_window_days=sel_window_days,
)
if not df_channel_funnel.empty:
    display_ch_funnel = df_channel_funnel.rename(
        columns={
            "acquisition_channel": "Acquisition Channel",
            "registered": "1. Registered",
            "app_opened": "2. Opened App",
            "content_viewed": "3. Viewed Content",
            "playback_started": "4. Started Playback",
            "overall_conv_pct": "Overall Conversion (%)",
            "primary_drop_off_stage": "Primary Bottleneck Stage",
        }
    )
    st.dataframe(display_ch_funnel, use_container_width=True, hide_index=True)
    st.caption("Channel-level funnel performance showing cohort progression and primary drop-off stage per acquisition source.")

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Diagnostic Recommendations Callout
st.subheader("3. Actionable Bottleneck Insights")
if funnel_result["recommendation"]:
    st.info(f"💡 **Key Finding**: {funnel_result['recommendation']}")
else:
    st.info("Insufficient funnel activity to identify an actionable bottleneck.")

with st.expander("Funnel Methodology"):
    st.markdown("""
    - **Registration Window**: Qualifying users are selected using their account creation dates.
    - **Conversion Observation Window**: Subsequent events must occur within the selected number of calendar days after registration.
    - **Chronological Sequencing**: Users must complete events in the correct order: Registration → App Open → Content View → Playback Start.
    - **Deduplication**: Each user is counted only once at each funnel stage.
    - **Incomplete Observation Handling**: Cohorts without sufficient observation history are excluded from applicable denominators.
    - **Hypotheses vs. Causes**: Diagnostic insights identify mathematical bottlenecks, while actual root causes require further investigation and validation.
    """)
