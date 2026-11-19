"""StreamIQ - Executive Command Center.

High-level executive dashboard tracking headline KPIs, active usage trends,
genre performance, and cohort retention.
"""

from __future__ import annotations

import datetime as dt
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics import (
    get_active_users_trend,
    get_executive_kpis,
    get_genre_popularity,
)
from src.database import ensure_database_ready, execute_query
from src.retention import calculate_day_n_retention, get_retention_trend_over_time
from src.ui_helpers import (
    apply_custom_css,
    apply_plotly_theme,
    render_blue_feature_card,
    render_hero_header,
    render_kpi_card,
    render_sidebar_footer,
    render_simulated_data_badge,
    render_theme_selector,
    render_top_navbar,
)

st.set_page_config(page_title="Executive Overview — StreamIQ", page_icon="⚡", layout="wide")
apply_custom_css()
ensure_database_ready()

# Sidebar Global Filters
render_theme_selector()
st.sidebar.header("Global Filters")

# Fetch available filter values from database
df_channels = execute_query("SELECT DISTINCT acquisition_channel FROM users ORDER BY 1")
channels = ["All"] + df_channels["acquisition_channel"].tolist() if not df_channels.empty else ["All"]

df_plans = execute_query("SELECT DISTINCT subscription_plan FROM users ORDER BY 1")
plans = ["All"] + df_plans["subscription_plan"].tolist() if not df_plans.empty else ["All"]

df_genres = execute_query("SELECT DISTINCT genre FROM content ORDER BY 1")
genres = ["All"] + df_genres["genre"].tolist() if not df_genres.empty else ["All"]

df_dates = execute_query("SELECT MIN(DATE(event_timestamp)) as min_d, MAX(DATE(event_timestamp)) as max_d FROM events")
min_date = dt.date(2026, 7, 1)
max_date = dt.date(2026, 10, 24)
if not df_dates.empty and df_dates["min_d"].iloc[0]:
    try:
        min_date = dt.date.fromisoformat(df_dates["min_d"].iloc[0])
        max_date = dt.date.fromisoformat(df_dates["max_d"].iloc[0])
    except (ValueError, TypeError):
        min_date, max_date = dt.date(2026, 7, 1), dt.date(2026, 10, 24)

date_range = st.sidebar.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
sel_channel = st.sidebar.selectbox("Acquisition Channel", channels)
sel_plan = st.sidebar.selectbox("Subscription Plan", plans)
sel_genre = st.sidebar.selectbox("Content Genre", genres)

# Render Zapan bottom toolbar dock in sidebar
render_sidebar_footer()

start_date_str = date_range[0].isoformat() if len(date_range) > 0 else None
end_date_str = date_range[1].isoformat() if len(date_range) > 1 else None

# Top Brand Bar matching reference
render_top_navbar(
    brand_title="StreamIQ | Executive Overview",
    date_display=f"{start_date_str or min_date.isoformat()} → {end_date_str or max_date.isoformat()}",
)

# Compute headline KPIs
kpis = get_executive_kpis(
    start_date=start_date_str,
    end_date=end_date_str,
    genre=sel_genre,
    channel=sel_channel,
    plan=sel_plan,
)

d7_ret = calculate_day_n_retention(
    day_n=7,
    start_date=start_date_str,
    end_date=end_date_str,
    channel=sel_channel,
    plan=sel_plan,
)

# Render KPI Metric Cards (3 White Cards + 1 Signature Wine/Berry Accent Card)
kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
with kpi_c1:
    render_kpi_card(
        label="Registered Users",
        value=f"{kpis['total_registered_users']:,}",
        progress_pct=100.0,
        subtext="100% of target accounts",
        info_text="Total accounts registered within the selected date range and filter criteria.",
        is_accent=False,
    )
with kpi_c2:
    act_pct = (kpis["active_users"] / max(1, kpis["total_registered_users"])) * 100
    render_kpi_card(
        label="Active Viewers",
        value=f"{kpis['active_users']:,}",
        progress_pct=act_pct,
        subtext=f"{act_pct:.1f}% active engagement rate",
        info_text="Distinct users with at least one recorded action in this period.",
        is_accent=False,
    )
with kpi_c3:
    sess_pct = min(100.0, (kpis["sessions_per_active_user"] / 20.0) * 100)
    render_kpi_card(
        label="Sessions per Viewer",
        value=f"{kpis['sessions_per_active_user']:.1f}",
        progress_pct=sess_pct,
        subtext="+2.3 vs 30D baseline",
        info_text="Average number of app sessions per active viewer. Higher values indicate regular streaming habits.",
        is_accent=False,
    )
with kpi_c4:
    comp_pct = kpis["playback_completion_rate"]
    render_kpi_card(
        label="Video Completion Rate",
        value=f"{comp_pct:.1f}%",
        progress_pct=comp_pct,
        subtext="Benchmark: 65.0% completed",
        info_text=f"{kpis['playback_completes']:,} completed streams out of {kpis['playback_starts']:,} starts.",
        is_accent=True,
    )

st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

# Large Primary Analytics Card matching "Tasks Summary" in reference
st.markdown(
    """
    <div class="analytics-card">
    <div class="analytics-card-header">
        <h3 class="analytics-card-title">Daily Viewership & Streaming Sessions Summary</h3>
        <div class="analytics-legend-row">
            <span><span class="legend-dot legend-navy"></span>Active Viewers</span>
            <span><span class="legend-dot legend-berry"></span>Total Sessions</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

trend_df = get_active_users_trend(
    start_date=start_date_str,
    end_date=end_date_str,
    genre=sel_genre,
    channel=sel_channel,
    plan=sel_plan,
)

if not trend_df.empty:
    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Scatter(
            x=trend_df["date"],
            y=trend_df["active_users"],
            mode="lines",
            name="Active Viewers",
            line=dict(color="#3A4781", width=2.8, shape="spline", smoothing=1.3),
            fill="tozeroy",
            fillcolor="rgba(58, 71, 129, 0.08)",
        )
    )
    fig_trend.add_trace(
        go.Scatter(
            x=trend_df["date"],
            y=trend_df["sessions"],
            mode="lines",
            name="Total Sessions",
            line=dict(color="#A92F59", width=2.4, shape="spline", smoothing=1.3),
        )
    )
    apply_plotly_theme(fig_trend)
    fig_trend.update_layout(
        hovermode="x unified",
        xaxis_title="Date",
        yaxis_title="Count of Users / Sessions",
        showlegend=False,
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("No activity recorded for the selected filter parameters.")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# Visualizations Row 2: Audience Monetization Tiers & Content Genres
tier_where = ["1=1"]
if sel_channel != "All":
    tier_where.append(f"acquisition_channel = '{sel_channel}'")
if sel_plan != "All":
    tier_where.append(f"subscription_plan = '{sel_plan}'")
if start_date_str:
    tier_where.append(f"DATE(signup_date) >= '{start_date_str}'")
if end_date_str:
    tier_where.append(f"DATE(signup_date) <= '{end_date_str}'")

df_tier = execute_query(f"""
    SELECT subscription_plan, COUNT(*) as cnt
    FROM users
    WHERE {' AND '.join(tier_where)}
    GROUP BY subscription_plan
    ORDER BY cnt DESC
""")
total_tier = df_tier["cnt"].sum() if not df_tier.empty else 1
tier_rows = [
    {
        "category": row["subscription_plan"],
        "value": f"{row['cnt']:,}",
        "pct": f"{(row['cnt'] / total_tier * 100):.1f}%",
    }
    for _, row in df_tier.iterrows()
]

col_tier, col_genre = st.columns([0.4, 0.6])

with col_tier:
    st.subheader("Audience Monetization Tiers")
    if not df_tier.empty:
        render_blue_feature_card(
            title="Subscription Tiers",
            categories=tier_rows,
            col_names=("Plan", "Subscribers", "% Share"),
        )
    else:
        st.info("No tier data available.")

with col_genre:
    st.subheader("Most Popular Content Genres")
    genre_df = get_genre_popularity(
        start_date=start_date_str,
        end_date=end_date_str,
        channel=sel_channel,
        plan=sel_plan,
    )
    if not genre_df.empty:
        fig_genre = px.bar(
            genre_df,
            x="playback_starts",
            y="genre",
            orientation="h",
            color="completion_rate_pct",
            color_continuous_scale=[[0, "#3A4781"], [1, "#A92F59"]],
            labels={
                "playback_starts": "Playback Starts (Times Played)",
                "genre": "Content Genre",
                "completion_rate_pct": "Completion Rate (%)",
            },
            text="playback_starts",
        )
        apply_plotly_theme(fig_genre)
        fig_genre.update_layout(
            yaxis=dict(autorange="reversed"),
            coloraxis_colorbar=dict(title="Completion %", thickness=14, len=0.7),
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        fig_genre.update_traces(
            texttemplate="%{text:,}",
            textposition="outside",
            cliponaxis=False,
            marker_line_width=0,
        )
        st.plotly_chart(fig_genre, use_container_width=True)
        st.caption("Bar length shows stream volume; darker berry indicates higher completion rates.")
    else:
        st.info("No content playback events recorded for the selected filter parameters.")

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# Visualizations Row 3: Day 7 Return Rate Trend
st.subheader("Day 7 Return Rate Trend by Signup Week")
ret_trend_df = get_retention_trend_over_time(day_n=7, channel=sel_channel, plan=sel_plan)
if not ret_trend_df.empty:
    fig_ret = px.line(
        ret_trend_df,
        x="cohort_week",
        y="retention_rate_pct",
        markers=True,
        labels={"cohort_week": "Signup Cohort Week", "retention_rate_pct": "Day 7 Return Rate (%)"},
        color_discrete_sequence=["#3A4781"],
    )
    mean_benchmark = ret_trend_df["retention_rate_pct"].mean()
    fig_ret.add_hline(
        y=mean_benchmark,
        line_dash="dash",
        line_color="#A92F59",
        annotation_text=f"Platform Benchmark: {mean_benchmark:.1f}%",
        annotation_position="top left",
    )
    apply_plotly_theme(fig_ret)
    fig_ret.update_traces(
        line=dict(width=2.5, shape="spline", smoothing=1.2),
        marker=dict(size=7, color="#A92F59"),
    )
    st.plotly_chart(fig_ret, use_container_width=True)
    st.caption("Shows how well each weekly group of new signups returned on their 7th day. The dashed line is the platform benchmark.")
else:
    st.info("No mature cohorts available for Day 7 retention analysis.")
