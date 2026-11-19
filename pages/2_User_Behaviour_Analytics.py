"""StreamIQ - User Behaviour Analytics.

In-depth behavioral analysis of catalog consumption, user segmentation,
channel performance, and activity distributions.
"""

from __future__ import annotations

import datetime as dt
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics import (
    get_channel_performance,
    get_content_rankings,
    get_executive_kpis,
    get_genre_popularity,
    get_plan_performance,
    get_segment_summary,
    get_user_segmentation,
)
from src.database import ensure_database_ready, execute_query
from src.ui_helpers import (
    apply_custom_css,
    apply_plotly_theme,
    render_hero_header,
    render_kpi_card,
    render_simulated_data_badge,
    render_theme_selector,
    render_top_navbar,
)

st.set_page_config(page_title="User Behaviour Analytics — StreamIQ", page_icon="👥", layout="wide")
apply_custom_css()
ensure_database_ready()

# Filters in Sidebar
render_theme_selector()
st.sidebar.header("Behavior Filters")

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
    except Exception:
        pass

date_range = st.sidebar.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
sel_channel = st.sidebar.selectbox("Acquisition Channel", channels)
sel_plan = st.sidebar.selectbox("Subscription Plan", plans)
sel_genre = st.sidebar.selectbox("Content Genre", genres)

start_date_str = date_range[0].isoformat() if len(date_range) > 0 else None
end_date_str = date_range[1].isoformat() if len(date_range) > 1 else None

# Top Brand Bar
render_top_navbar(
    brand_title="StreamIQ | Viewer Engagement & Content Catalog Performance",
    date_display=f"{start_date_str or min_date.isoformat()} → {end_date_str or max_date.isoformat()}",
)

# Hero Header
render_hero_header(
    badge_text="ENGAGEMENT & AUDIENCE TIERS",
    title="Viewer Engagement & Content Catalog Performance",
    subtitle="Evaluate catalog consumption trends, identify audience lifecycle segments, and analyze viewer engagement across marketing channels and subscription tiers.",
)

render_simulated_data_badge()

# Beginner-friendly guide expander
with st.expander("📖 Guide: How we segment viewers and measure behavior (Click to expand)"):
    st.markdown("""
    * **Top Streamed Content**: Shows which movies and series are capturing the most viewing starts and which keep viewers engaged all the way to the end.
    * **Audience Lifecycle Segments**:
      - **New Users**: Registered within the last 7 days. Still discovering the catalog and getting oriented; protected from being marked as inactive.
      - **Highly Active**: Logged **15 or more lifetime sessions**. These are your power viewers and brand champions.
      - **Moderately Active**: Logged **5 to 14 lifetime sessions**. Regular, habitual viewers.
      - **Low Activity**: Logged **1 to 4 lifetime sessions** (and joined over 7 days ago). These users are at immediate risk of churning and need re-engagement.
    * **Why this matters**: Product teams use this segmentation to tailor experiences—e.g., showing simpler onboarding to new users, sending re-engagement emails to low-activity viewers, and recommending niche content to power users.
    """)

# Activity Metrics Row
kpis = get_executive_kpis(
    start_date=start_date_str,
    end_date=end_date_str,
    genre=sel_genre,
    channel=sel_channel,
    plan=sel_plan,
)

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    render_kpi_card(
        label="Total Sessions",
        value=f"{kpis['total_sessions']:,}",
        info_text="Total individual app opening and browsing sessions logged in the selected window.",
        subtext="Platform visits",
        card_style="blue",
    )
with m2:
    render_kpi_card(
        label="Playback Starts",
        value=f"{kpis['playback_starts']:,}",
        info_text="Total count of streaming sessions initiated by viewers across all titles.",
        subtext="Initiated streams",
        card_style="sage",
    )
with m3:
    render_kpi_card(
        label="Completed Streams",
        value=f"{kpis['playback_completes']:,}",
        info_text="Total streaming sessions watched through to completion (100% video runtime).",
        subtext="Full completions",
        card_style="lavender",
    )
with m4:
    render_kpi_card(
        label="Completion Rate",
        value=f"{kpis['playback_completion_rate']:.1f}%",
        info_text="Completed Streams ÷ Playback Starts. Indicates audience satisfaction with chosen titles.",
        subtext="Catalog satisfaction",
        card_style="pink",
    )
with m5:
    render_kpi_card(
        label="Sessions / Viewer",
        value=f"{kpis['sessions_per_active_user']:.2f}",
        info_text="Average viewing sessions per active user. Higher density indicates regular habituation.",
        subtext="Session frequency",
        card_style="yellow",
    )

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Section 1: Content Popularity & Genre Affinity
st.subheader("1. Content Catalog Performance & Popularity")
col_cat1, col_cat2 = st.columns([3, 2])

with col_cat1:
    st.markdown("##### Most Watched Titles")
    content_df = get_content_rankings(
        limit=10,
        genre=sel_genre,
        start_date=start_date_str,
        end_date=end_date_str,
    )
    if not content_df.empty:
        display_content = content_df[["title", "genre", "release_year", "duration_minutes", "unique_viewers", "starts", "completion_rate_pct"]].rename(
            columns={
                "title": "Title",
                "genre": "Genre",
                "release_year": "Year",
                "duration_minutes": "Duration (min)",
                "unique_viewers": "Unique Viewers",
                "starts": "Stream Starts",
                "completion_rate_pct": "Completion Rate (%)",
            }
        )
        st.dataframe(display_content, use_container_width=True, hide_index=True)
        st.caption("Top 10 titles sorted by stream volume. High completion rates indicate strong audience satisfaction.")
    else:
        st.info("No content activity for selected filters.")

with col_cat2:
    st.markdown("##### Playback Volume by Genre")
    genre_df = get_genre_popularity(
        start_date=start_date_str,
        end_date=end_date_str,
        channel=sel_channel,
        plan=sel_plan,
    )
    if not genre_df.empty:
        fig_pie = px.pie(
            genre_df,
            values="playback_starts",
            names="genre",
            hole=0.55,
            color_discrete_sequence=["#3A4781", "#A92F59", "#397653", "#A66B19", "#6B4E9B", "#64748B"],
        )
        apply_plotly_theme(fig_pie)
        fig_pie.update_traces(
            textposition="inside",
            textinfo="percent+label",
            marker=dict(line=dict(color="#FFFFFF", width=2)),
        )
        fig_pie.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)
        st.caption("Distribution of total stream starts across catalog genres.")

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Section 2: User Segmentation & Activity Distribution
st.subheader("2. Audience Lifecycle Segments")

seg_summary = get_segment_summary(channel=sel_channel, plan=sel_plan, as_of_date=end_date_str)
df_user_seg = get_user_segmentation(channel=sel_channel, plan=sel_plan, as_of_date=end_date_str)

seg_c1, seg_c2 = st.columns([1, 1])

with seg_c1:
    if not seg_summary.empty:
        fig_seg = px.bar(
            seg_summary,
            x="user_segment",
            y="user_count",
            color="user_segment",
            text="user_share_pct",
            labels={"user_segment": "Audience Segment", "user_count": "Number of Users", "user_share_pct": "Audience Share (%)"},
            color_discrete_map={
                "Highly Active": "#397653",
                "Moderately Active": "#3A4781",
                "Low Activity": "#A66B19",
                "New Users": "#6B4E9B",
            },
        )
        apply_plotly_theme(fig_seg)
        fig_seg.update_traces(
            texttemplate="%{text}%",
            textposition="outside",
            marker_line_width=0,
        )
        fig_seg.update_layout(showlegend=False)
        st.plotly_chart(fig_seg, use_container_width=True)
        st.caption("Proportion of platform users categorized into each behavioral lifecycle tier.")

with seg_c2:
    if not seg_summary.empty:
        display_seg = seg_summary[["user_segment", "user_count", "user_share_pct", "avg_sessions", "avg_playbacks"]].rename(
            columns={
                "user_segment": "Segment",
                "user_count": "Users",
                "user_share_pct": "Audience Share (%)",
                "avg_sessions": "Avg Sessions / User",
                "avg_playbacks": "Avg Plays / User",
            }
        )
        st.dataframe(display_seg, use_container_width=True, hide_index=True)
        st.caption("Viewer distribution, session intensity, and playback frequency across audience segments.")

# Distribution of Sessions
st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
st.markdown("##### User Activity Distribution (Sessions per Account)")
if not df_user_seg.empty:
    fig_hist = px.histogram(
        df_user_seg,
        x="total_sessions",
        nbins=25,
        color_discrete_sequence=["#3A4781"],
        labels={"total_sessions": "Lifetime Sessions", "count": "Number of Users"},
    )
    apply_plotly_theme(fig_hist)
    fig_hist.update_traces(marker_line_width=1, marker_line_color="#FFFFFF")
    st.plotly_chart(fig_hist, use_container_width=True)
    st.caption("Histogram showing the right-skewed session distribution typical of digital subscription services.")

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Section 3: Channel & Subscription Plan Comparisons
st.subheader("3. Acquisition Channel & Subscription Tier Comparisons")

ch_col, pl_col = st.columns(2)

with ch_col:
    st.markdown("##### Average Sessions per Viewer by Marketing Channel")
    ch_df = get_channel_performance(start_date=start_date_str, end_date=end_date_str, plan=sel_plan)
    if not ch_df.empty:
        fig_ch = px.bar(
            ch_df,
            x="acquisition_channel",
            y="sessions_per_user",
            color="completion_rate_pct",
            color_continuous_scale=[[0, "#EAF0F6"], [1, "#3A4781"]],
            labels={
                "acquisition_channel": "Acquisition Channel",
                "sessions_per_user": "Average Sessions / Viewer",
                "completion_rate_pct": "Completion Rate (%)",
            },
        )
        apply_plotly_theme(fig_ch)
        fig_ch.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig_ch, use_container_width=True)
        st.caption("Channels with higher sessions per user indicate higher-intent, habit-forming viewers.")

with pl_col:
    st.markdown("##### Stream Starts by Subscription Plan")
    pl_df = get_plan_performance(start_date=start_date_str, end_date=end_date_str, channel=sel_channel)
    if not pl_df.empty:
        fig_pl = px.bar(
            pl_df,
            x="subscription_plan",
            y="playback_starts",
            color="completion_rate_pct",
            color_continuous_scale=[[0, "#F5E8ED"], [1, "#A92F59"]],
            labels={
                "subscription_plan": "Subscription Plan",
                "playback_starts": "Playback Starts (Times Played)",
                "completion_rate_pct": "Completion Rate (%)",
            },
        )
        apply_plotly_theme(fig_pl)
        st.plotly_chart(fig_pl, use_container_width=True)
        st.caption("Compares total stream volume and completion rates across monetization tiers.")

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Section 4: Analytical Synthesis
st.subheader("4. Key Takeaways & Product Hypotheses")
st.markdown("""
* **Takeaway 1: Power Viewers Drive Most Consumption**
  - *Observation*: Highly Active users (15+ sessions) generate the vast majority of completed streams.
  - *Why this happens (Hypothesis)*: Once a viewer adds shows to their personal watchlist and builds a viewing habit, they return consistently.
  - *Keep in mind*: Correlation is not causation—users who love streaming may naturally log more sessions.

* **Takeaway 2: Organic & Referral Channels Bring Higher-Intent Audiences**
  - *Observation*: Viewers joining via Referrals and Organic Search log more sessions per user than those from Paid Social ads.
  - *Why this happens (Hypothesis)*: Word-of-mouth users join knowing specifically what show they want to watch, whereas paid ad clicks are often curious casual browsers.

* **Takeaway 3: Ad-Supported Viewers Show Slightly Lower Completion Rates**
  - *Observation*: Free Ad-Supported users finish slightly fewer shows than Premium 4K subscribers.
  - *Why this happens (Hypothesis)*: Commercial interruptions or differing device formats (e.g., viewing on mobile during commutes vs living room TVs).
""")
