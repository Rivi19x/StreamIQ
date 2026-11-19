"""Funnel conversion analysis module for StreamIQ.

Implements strict chronological user conversion tracking through the 4-stage streaming journey:
1. Registered (User Account Created)
2. Opened App (app_open event >= signup_date)
3. Viewed Content (content_view event >= app_open event)
4. Started Playback (playback_start event >= content_view event)

Guarantees:
- Strict chronological sequence enforcement
- Deduplication (distinct user counting per stage)
- Drop-off calculations and automated bottleneck identification
- Rule-based business hypotheses
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.database import execute_query, get_anchor_date, get_db_path

FUNNEL_STAGES = [
    "1. Registered",
    "2. Opened App",
    "3. Viewed Content",
    "4. Started Playback",
]


def calculate_funnel(
    start_date: str | None = None,
    end_date: str | None = None,
    channel: str | None = None,
    plan: str | None = None,
    conversion_window_days: int | None = None,
    enforce_mature_cohort: bool = True,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Calculate the 4-step chronological streaming onboarding & playback funnel.

    Windows:
    - Registration Window: Filters cohort signup dates [start_date, end_date].
    - Conversion Window: When conversion_window_days is set (e.g. 7, 14, 30 days),
      only subsequent events occurring within N days of the user's signup_date
      qualify. When enforce_mature_cohort=True, users who registered less than
      conversion_window_days before the database anchor date are excluded so all
      analyzed users have had the full window to convert.
    """
    user_clauses: list[str] = []
    user_params: list[Any] = []

    if start_date:
        user_clauses.append("u.signup_date >= ?")
        user_params.append(start_date)
    if end_date:
        user_clauses.append("u.signup_date <= ?")
        user_params.append(end_date)
    if channel and channel != "All":
        user_clauses.append("u.acquisition_channel = ?")
        user_params.append(channel)
    if plan and plan != "All":
        user_clauses.append("u.subscription_plan = ?")
        user_params.append(plan)

    if conversion_window_days is not None and enforce_mature_cohort:
        anchor = get_anchor_date(db_path)
        cutoff_date = (anchor - pd.Timedelta(days=conversion_window_days)).strftime("%Y-%m-%d")
        user_clauses.append("u.signup_date <= ?")
        user_params.append(cutoff_date)

    user_where = ("WHERE " + " AND ".join(user_clauses)) if user_clauses else ""

    # Optional conversion window filters on event timestamps
    window_open_clause = ""
    window_view_clause = ""
    window_start_clause = ""
    query_params = list(user_params)

    if conversion_window_days is not None:
        window_open_clause = "AND e.event_timestamp <= DATETIME(c.signup_date, '+' || ? || ' days')"
        window_view_clause = "AND e.event_timestamp <= DATETIME(o.signup_date, '+' || ? || ' days')"
        window_start_clause = "AND e.event_timestamp <= DATETIME(v.signup_date, '+' || ? || ' days')"
        # Append window parameters for the 3 subqueries
        query_params.extend([conversion_window_days, conversion_window_days, conversion_window_days])

    # SQL query enforcing strict chronological progression:
    # 1. User exists in cohort
    # 2. Earliest app_open >= signup_date (and <= signup_date + window)
    # 3. Earliest content_view >= earliest app_open (and <= signup_date + window)
    # 4. Earliest playback_start >= earliest content_view (and <= signup_date + window)
    sql = f"""
        WITH cohort_users AS (
            SELECT u.user_id, u.signup_date
            FROM users u
            {user_where}
        ),
        user_app_open AS (
            SELECT
                c.user_id,
                c.signup_date,
                MIN(e.event_timestamp) AS first_open_ts
            FROM cohort_users c
            JOIN events e ON c.user_id = e.user_id
            WHERE e.event_type = 'app_open'
              AND e.event_timestamp >= c.signup_date
              {window_open_clause}
            GROUP BY c.user_id, c.signup_date
        ),
        user_content_view AS (
            SELECT
                o.user_id,
                o.signup_date,
                MIN(e.event_timestamp) AS first_view_ts
            FROM user_app_open o
            JOIN events e ON o.user_id = e.user_id
            WHERE e.event_type = 'content_view'
              AND e.event_timestamp >= o.first_open_ts
              {window_view_clause}
            GROUP BY o.user_id, o.signup_date
        ),
        user_playback_start AS (
            SELECT
                v.user_id,
                MIN(e.event_timestamp) AS first_start_ts
            FROM user_content_view v
            JOIN events e ON v.user_id = e.user_id
            WHERE e.event_type = 'playback_start'
              AND e.event_timestamp >= v.first_view_ts
              {window_start_clause}
            GROUP BY v.user_id
        )
        SELECT
            (SELECT COUNT(*) FROM cohort_users) AS stage_1_registered,
            (SELECT COUNT(*) FROM user_app_open) AS stage_2_opened_app,
            (SELECT COUNT(*) FROM user_content_view) AS stage_3_viewed_content,
            (SELECT COUNT(*) FROM user_playback_start) AS stage_4_started_playback
    """
    df = execute_query(sql, query_params, db_path=db_path)

    if df.empty:
        stage_counts = [0, 0, 0, 0]
    else:
        row = df.iloc[0]
        stage_counts = [
            int(row["stage_1_registered"] or 0),
            int(row["stage_2_opened_app"] or 0),
            int(row["stage_3_viewed_content"] or 0),
            int(row["stage_4_started_playback"] or 0),
        ]

    # Build detailed metrics table
    stages_data: list[dict[str, Any]] = []
    base_users = stage_counts[0]

    for idx, (stage_name, count) in enumerate(zip(FUNNEL_STAGES, stage_counts)):
        if idx == 0:
            step_conv = 100.0 if base_users > 0 else 0.0
            overall_conv = 100.0 if base_users > 0 else 0.0
            drop_off_count = 0
            drop_off_pct = 0.0
        else:
            prev_count = stage_counts[idx - 1]
            step_conv = (count / prev_count * 100.0) if prev_count > 0 else 0.0
            overall_conv = (count / base_users * 100.0) if base_users > 0 else 0.0
            drop_off_count = prev_count - count
            drop_off_pct = (drop_off_count / prev_count * 100.0) if prev_count > 0 else 0.0

        stages_data.append({
            "stage_index": idx + 1,
            "stage_name": stage_name,
            "users": count,
            "step_conversion_pct": round(step_conv, 1),
            "overall_conversion_pct": round(overall_conv, 1),
            "users_lost": drop_off_count,
            "drop_off_pct": round(drop_off_pct, 1),
        })

    df_funnel = pd.DataFrame(stages_data)

    # Identify primary drop-off bottleneck (excluding stage 0)
    drop_off_candidates = stages_data[1:]
    if drop_off_candidates and base_users > 0:
        bottleneck = max(drop_off_candidates, key=lambda x: x["users_lost"])
        bottleneck_stage_name = bottleneck["stage_name"]
        prev_stage_name = FUNNEL_STAGES[bottleneck["stage_index"] - 2]
        largest_loss = bottleneck["users_lost"]
        drop_pct = bottleneck["drop_off_pct"]

        # Formulate contextual, rule-based product recommendations
        if "Opened App" in bottleneck_stage_name:
            recommendation = (
                f"Largest user drop-off occurs between {prev_stage_name} and {bottleneck_stage_name} "
                f"(-{largest_loss:,} users, {drop_pct}% loss). "
                "Hypothesis: First-time onboarding friction or delayed registration verification email. "
                "Recommended action: Streamline welcome onboarding and send immediate push/email prompts."
            )
        elif "Viewed Content" in bottleneck_stage_name:
            recommendation = (
                f"Largest user drop-off occurs between {prev_stage_name} and {bottleneck_stage_name} "
                f"(-{largest_loss:,} users, {drop_pct}% loss). "
                "Hypothesis: Home feed discovery paralysis or cold-start recommendations. "
                "Recommended action: Test personalized genre pickers upon first login and curate trending hero reels."
            )
        else:
            recommendation = (
                f"Largest user drop-off occurs between {prev_stage_name} and {bottleneck_stage_name} "
                f"(-{largest_loss:,} users, {drop_pct}% loss). "
                "Hypothesis: Trailer/metadata previews fail to spark viewing intent or video loading friction. "
                "Recommended action: Implement autoplay previews and verify CDN player latency."
            )
    else:
        bottleneck = None
        recommendation = "No bottleneck identified; insufficient user activity in the selected window."

    return {
        "funnel_table": df_funnel,
        "stage_counts": stage_counts,
        "base_users": base_users,
        "final_converted": stage_counts[-1],
        "overall_conversion_pct": round((stage_counts[-1] / base_users * 100.0) if base_users > 0 else 0.0, 2),
        "bottleneck": bottleneck,
        "recommendation": recommendation,
        "conversion_window_days": conversion_window_days,
        "mature_cohort_enforced": bool(enforce_mature_cohort and (conversion_window_days is not None)),
    }


def get_funnel_by_channel(
    start_date: str | None = None,
    end_date: str | None = None,
    plan: str | None = None,
    conversion_window_days: int | None = None,
    db_path: str | Path | None = None,
) -> pd.DataFrame:
    """Calculate multi-stage conversion funnel breakdown by acquisition channel.

    Enforces identical strict chronological progression and optional attribution window.
    """
    user_where_clauses = []
    user_params: list[Any] = []

    if start_date:
        user_where_clauses.append("u.signup_date >= ?")
        user_params.append(start_date)
    if end_date:
        user_where_clauses.append("u.signup_date <= ?")
        user_params.append(end_date)
    if plan and plan != "All":
        user_where_clauses.append("u.subscription_plan = ?")
        user_params.append(plan)

    user_where = ("WHERE " + " AND ".join(user_where_clauses)) if user_where_clauses else ""

    window_open_clause = ""
    window_view_clause = ""
    window_start_clause = ""
    query_params = list(user_params)

    if conversion_window_days is not None:
        window_open_clause = "AND e.event_timestamp <= DATETIME(c.signup_date, '+' || ? || ' days')"
        window_view_clause = "AND e.event_timestamp <= DATETIME(o.signup_date, '+' || ? || ' days')"
        window_start_clause = "AND e.event_timestamp <= DATETIME(v.signup_date, '+' || ? || ' days')"
        query_params.extend([conversion_window_days, conversion_window_days, conversion_window_days])

    sql = f"""
        WITH cohort_users AS (
            SELECT u.user_id, u.signup_date, u.acquisition_channel
            FROM users u
            {user_where}
        ),
        user_app_open AS (
            SELECT
                c.user_id,
                c.signup_date,
                c.acquisition_channel,
                MIN(e.event_timestamp) AS first_open_ts
            FROM cohort_users c
            JOIN events e ON c.user_id = e.user_id
            WHERE e.event_type = 'app_open'
              AND e.event_timestamp >= c.signup_date
              {window_open_clause}
            GROUP BY c.user_id, c.signup_date, c.acquisition_channel
        ),
        user_content_view AS (
            SELECT
                o.user_id,
                o.signup_date,
                o.acquisition_channel,
                MIN(e.event_timestamp) AS first_view_ts
            FROM user_app_open o
            JOIN events e ON o.user_id = e.user_id
            WHERE e.event_type = 'content_view'
              AND e.event_timestamp >= o.first_open_ts
              {window_view_clause}
            GROUP BY o.user_id, o.signup_date, o.acquisition_channel
        ),
        user_playback_start AS (
            SELECT
                v.user_id,
                v.acquisition_channel,
                MIN(e.event_timestamp) AS first_start_ts
            FROM user_content_view v
            JOIN events e ON v.user_id = e.user_id
            WHERE e.event_type = 'playback_start'
              AND e.event_timestamp >= v.first_view_ts
              {window_start_clause}
            GROUP BY v.user_id, v.acquisition_channel
        )
        SELECT
            c.acquisition_channel,
            COUNT(DISTINCT c.user_id) AS registered,
            COUNT(DISTINCT o.user_id) AS app_opened,
            COUNT(DISTINCT v.user_id) AS content_viewed,
            COUNT(DISTINCT p.user_id) AS playback_started
        FROM cohort_users c
        LEFT JOIN user_app_open o ON c.user_id = o.user_id
        LEFT JOIN user_content_view v ON c.user_id = v.user_id
        LEFT JOIN user_playback_start p ON c.user_id = p.user_id
        GROUP BY c.acquisition_channel
        ORDER BY registered DESC
    """
    df = execute_query(sql, query_params, db_path=db_path)
    if df.empty:
        return pd.DataFrame(columns=[
            "acquisition_channel", "registered", "app_opened", "content_viewed",
            "playback_started", "overall_conv_pct", "primary_drop_off_stage"
        ])

    df["registered"] = df["registered"].astype(int)
    df["app_opened"] = df["app_opened"].astype(int)
    df["content_viewed"] = df["content_viewed"].astype(int)
    df["playback_started"] = df["playback_started"].astype(int)

    df["overall_conv_pct"] = (
        (df["playback_started"] / df["registered"] * 100.0)
        .where(df["registered"] > 0, 0.0)
        .round(1)
    )

    # Determine primary drop-off stage for each channel
    def _find_drop_off(row):
        drop_open = row["registered"] - row["app_opened"]
        drop_view = row["app_opened"] - row["content_viewed"]
        drop_play = row["content_viewed"] - row["playback_started"]
        drops = [
            ("2. App Opened", drop_open),
            ("3. Content Viewed", drop_view),
            ("4. Playback Started", drop_play),
        ]
        return max(drops, key=lambda x: x[1])[0]

    df["primary_drop_off_stage"] = df.apply(_find_drop_off, axis=1)
    return df

