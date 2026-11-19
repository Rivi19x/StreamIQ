"""Core product analytics module for StreamIQ.

Implements calculation of core platform metrics:
- Active Users (DAU, WAU, MAU, filtered active user count)
- Engagement metrics (sessions per active user, event distributions)
- Content and Genre popularity rankings
- Playback completion rates
- Rule-based user segmentation
- Cohort and channel breakdowns
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import pandas as pd

from src.database import execute_query, get_anchor_date, get_db_path


def build_filter_clauses(
    start_date: str | None = None,
    end_date: str | None = None,
    genre: str | None = None,
    channel: str | None = None,
    plan: str | None = None,
) -> tuple[str, list[Any]]:
    """Build parameterized WHERE clauses for events joined with users and content."""
    clauses: list[str] = []
    params: list[Any] = []

    if start_date:
        clauses.append("DATE(e.event_timestamp) >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("DATE(e.event_timestamp) <= ?")
        params.append(end_date)
    if genre and genre != "All":
        clauses.append("c.genre = ?")
        params.append(genre)
    if channel and channel != "All":
        clauses.append("u.acquisition_channel = ?")
        params.append(channel)
    if plan and plan != "All":
        clauses.append("u.subscription_plan = ?")
        params.append(plan)

    where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where_sql, params


def get_executive_kpis(
    start_date: str | None = None,
    end_date: str | None = None,
    genre: str | None = None,
    channel: str | None = None,
    plan: str | None = None,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Calculate the 5 primary executive command center KPIs based on filters.

    Returns:
    - total_registered_users: Total user count matching user attributes
    - active_users: Distinct users with at least 1 event in selected period/filters
    - sessions_per_active_user: Total sessions / active users
    - playback_completion_rate: Completed playbacks / Playback starts (in %)
    - day7_retention_rate: Day 7 retention rate for mature cohorts
    """
    where_sql, params = build_filter_clauses(start_date, end_date, genre, channel, plan)

    # 1. Total Registered Users matching user criteria (channel, plan, and signup_date <= end_date)
    user_clauses = []
    user_params = []
    if end_date:
        user_clauses.append("signup_date <= ?")
        user_params.append(end_date)
    if channel and channel != "All":
        user_clauses.append("acquisition_channel = ?")
        user_params.append(channel)
    if plan and plan != "All":
        user_clauses.append("subscription_plan = ?")
        user_params.append(plan)
    user_where = ("WHERE " + " AND ".join(user_clauses)) if user_clauses else ""

    sql_users = f"SELECT COUNT(*) AS total_users FROM users {user_where}"
    df_users = execute_query(sql_users, user_params, db_path=db_path)
    total_users = int(df_users["total_users"].iloc[0]) if not df_users.empty else 0

    # 2. Events, Sessions, and Active Users
    sql_events = f"""
        SELECT
            COUNT(DISTINCT e.user_id) AS active_users,
            COUNT(DISTINCT e.session_id) AS total_sessions,
            COUNT(*) AS total_events,
            SUM(CASE WHEN e.event_type = 'playback_start' THEN 1 ELSE 0 END) AS playback_starts,
            SUM(CASE WHEN e.event_type = 'playback_complete' THEN 1 ELSE 0 END) AS playback_completes
        FROM events e
        JOIN users u ON e.user_id = u.user_id
        LEFT JOIN content c ON e.content_id = c.content_id
        {where_sql}
    """
    df_evt = execute_query(sql_events, params, db_path=db_path)

    active_users = int(df_evt["active_users"].iloc[0]) if not df_evt.empty and df_evt["active_users"].iloc[0] is not None else 0
    total_sessions = int(df_evt["total_sessions"].iloc[0]) if not df_evt.empty and df_evt["total_sessions"].iloc[0] is not None else 0
    playback_starts = int(df_evt["playback_starts"].iloc[0]) if not df_evt.empty and df_evt["playback_starts"].iloc[0] is not None else 0
    playback_completes = int(df_evt["playback_completes"].iloc[0]) if not df_evt.empty and df_evt["playback_completes"].iloc[0] is not None else 0

    sessions_per_active = (total_sessions / active_users) if active_users > 0 else 0.0
    completion_rate = (playback_completes / playback_starts * 100.0) if playback_starts > 0 else 0.0

    return {
        "total_registered_users": total_users,
        "active_users": active_users,
        "total_sessions": total_sessions,
        "sessions_per_active_user": round(sessions_per_active, 2),
        "playback_starts": playback_starts,
        "playback_completes": playback_completes,
        "playback_completion_rate": round(completion_rate, 2),
    }


def get_active_users_trend(
    start_date: str | None = None,
    end_date: str | None = None,
    genre: str | None = None,
    channel: str | None = None,
    plan: str | None = None,
    db_path: str | Path | None = None,
) -> pd.DataFrame:
    """Return daily active users (DAU) and session counts over time."""
    where_sql, params = build_filter_clauses(start_date, end_date, genre, channel, plan)
    sql = f"""
        SELECT
            DATE(e.event_timestamp) AS date,
            COUNT(DISTINCT e.user_id) AS active_users,
            COUNT(DISTINCT e.session_id) AS sessions,
            COUNT(*) AS total_events
        FROM events e
        JOIN users u ON e.user_id = u.user_id
        LEFT JOIN content c ON e.content_id = c.content_id
        {where_sql}
        GROUP BY DATE(e.event_timestamp)
        ORDER BY date ASC
    """
    return execute_query(sql, params, db_path=db_path)


def get_genre_popularity(
    start_date: str | None = None,
    end_date: str | None = None,
    channel: str | None = None,
    plan: str | None = None,
    db_path: str | Path | None = None,
) -> pd.DataFrame:
    """Rank genres by views, playback starts, and completion rates."""
    clauses = ["c.genre IS NOT NULL"]
    params: list[Any] = []
    if start_date:
        clauses.append("DATE(e.event_timestamp) >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("DATE(e.event_timestamp) <= ?")
        params.append(end_date)
    if channel and channel != "All":
        clauses.append("u.acquisition_channel = ?")
        params.append(channel)
    if plan and plan != "All":
        clauses.append("u.subscription_plan = ?")
        params.append(plan)

    where_sql = "WHERE " + " AND ".join(clauses)
    sql = f"""
        SELECT
            c.genre,
            COUNT(DISTINCT e.user_id) AS unique_viewers,
            SUM(CASE WHEN e.event_type = 'content_view' THEN 1 ELSE 0 END) AS content_views,
            SUM(CASE WHEN e.event_type = 'playback_start' THEN 1 ELSE 0 END) AS playback_starts,
            SUM(CASE WHEN e.event_type = 'playback_complete' THEN 1 ELSE 0 END) AS playback_completes,
            ROUND(
                100.0 * SUM(CASE WHEN e.event_type = 'playback_complete' THEN 1 ELSE 0 END) /
                NULLIF(SUM(CASE WHEN e.event_type = 'playback_start' THEN 1 ELSE 0 END), 0),
                2
            ) AS completion_rate_pct
        FROM events e
        JOIN content c ON e.content_id = c.content_id
        JOIN users u ON e.user_id = u.user_id
        {where_sql}
        GROUP BY c.genre
        ORDER BY playback_starts DESC
    """
    return execute_query(sql, params, db_path=db_path)


def get_content_rankings(
    limit: int = 15,
    genre: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db_path: str | Path | None = None,
) -> pd.DataFrame:
    """Rank individual titles by playback activity and completion rate."""
    clauses = ["c.content_id IS NOT NULL"]
    params: list[Any] = []
    if genre and genre != "All":
        clauses.append("c.genre = ?")
        params.append(genre)
    if start_date:
        clauses.append("DATE(e.event_timestamp) >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("DATE(e.event_timestamp) <= ?")
        params.append(end_date)

    where_sql = "WHERE " + " AND ".join(clauses)
    sql = f"""
        SELECT
            c.content_id,
            c.title,
            c.genre,
            c.release_year,
            c.duration_minutes,
            COUNT(DISTINCT e.user_id) AS unique_viewers,
            SUM(CASE WHEN e.event_type = 'content_view' THEN 1 ELSE 0 END) AS views,
            SUM(CASE WHEN e.event_type = 'playback_start' THEN 1 ELSE 0 END) AS starts,
            SUM(CASE WHEN e.event_type = 'playback_complete' THEN 1 ELSE 0 END) AS completes,
            ROUND(
                100.0 * SUM(CASE WHEN e.event_type = 'playback_complete' THEN 1 ELSE 0 END) /
                NULLIF(SUM(CASE WHEN e.event_type = 'playback_start' THEN 1 ELSE 0 END), 0),
                1
            ) AS completion_rate_pct
        FROM content c
        JOIN events e ON c.content_id = e.content_id
        {where_sql}
        GROUP BY c.content_id, c.title, c.genre, c.release_year, c.duration_minutes
        ORDER BY starts DESC
        LIMIT {limit}
    """
    return execute_query(sql, params, db_path=db_path)


def get_user_segmentation(
    as_of_date: str | None = None,
    channel: str | None = None,
    plan: str | None = None,
    db_path: str | Path | None = None,
) -> pd.DataFrame:
    """Classify all registered users into 4 transparent, documented rule-based segments:

    1. 'New Users': Registered within 7 days of as_of_date (not churned; still onboarding).
    2. 'Highly Active': >= 15 total sessions.
    3. 'Moderately Active': 5 to 14 total sessions.
    4. 'Low Activity': 1 to 4 total sessions (registered > 7 days ago).
    """
    if as_of_date is None:
        as_of_date = get_anchor_date(db_path).isoformat()

    params: list[Any] = [as_of_date]
    user_filter_clauses = []
    if channel and channel != "All":
        user_filter_clauses.append("u.acquisition_channel = ?")
        params.append(channel)
    if plan and plan != "All":
        user_filter_clauses.append("u.subscription_plan = ?")
        params.append(plan)

    user_where = ("WHERE " + " AND ".join(user_filter_clauses)) if user_filter_clauses else ""

    sql = f"""
        WITH user_activity AS (
            SELECT
                u.user_id,
                u.signup_date,
                u.country,
                u.acquisition_channel,
                u.subscription_plan,
                CAST(JULIANDAY(?) - JULIANDAY(u.signup_date) AS INTEGER) AS account_age_days,
                COUNT(DISTINCT e.session_id) AS total_sessions,
                COUNT(e.event_id) AS total_events,
                SUM(CASE WHEN e.event_type = 'playback_start' THEN 1 ELSE 0 END) AS total_playbacks
            FROM users u
            LEFT JOIN events e ON u.user_id = e.user_id
            {user_where}
            GROUP BY u.user_id
        )
        SELECT
            user_id,
            signup_date,
            country,
            acquisition_channel,
            subscription_plan,
            account_age_days,
            total_sessions,
            total_events,
            total_playbacks,
            CASE
                WHEN account_age_days <= 7 THEN 'New Users'
                WHEN total_sessions >= 15 THEN 'Highly Active'
                WHEN total_sessions >= 5 THEN 'Moderately Active'
                ELSE 'Low Activity'
            END AS user_segment
        FROM user_activity
    """
    return execute_query(sql, params, db_path=db_path)


def get_segment_summary(
    as_of_date: str | None = None,
    channel: str | None = None,
    plan: str | None = None,
    db_path: str | Path | None = None,
) -> pd.DataFrame:
    """Aggregate summary statistics per user segment."""
    df_seg = get_user_segmentation(as_of_date=as_of_date, channel=channel, plan=plan, db_path=db_path)
    if df_seg.empty:
        return pd.DataFrame()

    summary = (
        df_seg.groupby("user_segment")
        .agg(
            user_count=("user_id", "count"),
            avg_sessions=("total_sessions", "mean"),
            avg_events=("total_events", "mean"),
            avg_playbacks=("total_playbacks", "mean"),
        )
        .reset_index()
    )
    total_users = summary["user_count"].sum()
    summary["user_share_pct"] = (summary["user_count"] / total_users * 100.0).round(1)
    summary["avg_sessions"] = summary["avg_sessions"].round(1)
    summary["avg_events"] = summary["avg_events"].round(1)
    summary["avg_playbacks"] = summary["avg_playbacks"].round(1)

    # Sort in logical business order
    order_map = {"Highly Active": 1, "Moderately Active": 2, "Low Activity": 3, "New Users": 4}
    summary["sort_order"] = summary["user_segment"].map(order_map)
    summary = summary.sort_values("sort_order").drop(columns=["sort_order"])
    return summary


def get_channel_performance(
    start_date: str | None = None,
    end_date: str | None = None,
    plan: str | None = None,
    db_path: str | Path | None = None,
) -> pd.DataFrame:
    """Compare acquisition channels by user volume, engagement, and playbacks."""
    clauses = []
    params: list[Any] = []
    if plan and plan != "All":
        clauses.append("u.subscription_plan = ?")
        params.append(plan)
    if start_date:
        clauses.append("DATE(e.event_timestamp) >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("DATE(e.event_timestamp) <= ?")
        params.append(end_date)

    where_clause = ("WHERE " + " AND ".join(clauses)) if clauses else ""

    sql = f"""
        SELECT
            u.acquisition_channel,
            COUNT(DISTINCT u.user_id) AS total_users,
            COUNT(DISTINCT e.user_id) AS active_users,
            COUNT(DISTINCT e.session_id) AS total_sessions,
            ROUND(CAST(COUNT(DISTINCT e.session_id) AS FLOAT) / NULLIF(COUNT(DISTINCT e.user_id), 0), 2) AS sessions_per_user,
            SUM(CASE WHEN e.event_type = 'playback_start' THEN 1 ELSE 0 END) AS playback_starts,
            SUM(CASE WHEN e.event_type = 'playback_complete' THEN 1 ELSE 0 END) AS playback_completes,
            ROUND(
                100.0 * SUM(CASE WHEN e.event_type = 'playback_complete' THEN 1 ELSE 0 END) /
                NULLIF(SUM(CASE WHEN e.event_type = 'playback_start' THEN 1 ELSE 0 END), 0),
                1
            ) AS completion_rate_pct
        FROM users u
        LEFT JOIN events e ON u.user_id = e.user_id
        {where_clause}
        GROUP BY u.acquisition_channel
        ORDER BY total_users DESC
    """
    return execute_query(sql, params, db_path=db_path)


def get_plan_performance(
    start_date: str | None = None,
    end_date: str | None = None,
    channel: str | None = None,
    db_path: str | Path | None = None,
) -> pd.DataFrame:
    """Compare subscription plans by user volume and playback activity."""
    clauses = []
    params: list[Any] = []
    if channel and channel != "All":
        clauses.append("u.acquisition_channel = ?")
        params.append(channel)
    if start_date:
        clauses.append("DATE(e.event_timestamp) >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("DATE(e.event_timestamp) <= ?")
        params.append(end_date)

    where_clause = ("WHERE " + " AND ".join(clauses)) if clauses else ""

    sql = f"""
        SELECT
            u.subscription_plan,
            COUNT(DISTINCT u.user_id) AS total_users,
            COUNT(DISTINCT e.user_id) AS active_users,
            COUNT(DISTINCT e.session_id) AS total_sessions,
            ROUND(CAST(COUNT(DISTINCT e.session_id) AS FLOAT) / NULLIF(COUNT(DISTINCT e.user_id), 0), 2) AS sessions_per_user,
            SUM(CASE WHEN e.event_type = 'playback_start' THEN 1 ELSE 0 END) AS playback_starts,
            SUM(CASE WHEN e.event_type = 'playback_complete' THEN 1 ELSE 0 END) AS playback_completes,
            ROUND(
                100.0 * SUM(CASE WHEN e.event_type = 'playback_complete' THEN 1 ELSE 0 END) /
                NULLIF(SUM(CASE WHEN e.event_type = 'playback_start' THEN 1 ELSE 0 END), 0),
                1
            ) AS completion_rate_pct
        FROM users u
        LEFT JOIN events e ON u.user_id = e.user_id
        {where_clause}
        GROUP BY u.subscription_plan
        ORDER BY total_users DESC
    """
    return execute_query(sql, params, db_path=db_path)
