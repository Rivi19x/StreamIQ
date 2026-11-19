"""Retention and cohort analysis module for StreamIQ.

Implements rigorous product retention calculations:
- Day 1, Day 7, and Day 30 exact-day retention
- Exclusion of incomplete observation windows to prevent artificial churn bias
- Documented distinction between exact-day and rolling retention
- Weekly and monthly signup cohort matrices for heatmap visualization
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.database import execute_query, get_db_path


def get_anchor_date(db_path: str | Path | None = None) -> dt.date:
    """Return the latest date present in events, or default to 2026-10-24."""
    sql = "SELECT MAX(DATE(event_timestamp)) AS max_date FROM events"
    df = execute_query(sql, db_path=db_path)
    if not df.empty and df["max_date"].iloc[0] is not None:
        try:
            return dt.date.fromisoformat(df["max_date"].iloc[0])
        except ValueError:
            pass
    return dt.date(2026, 10, 24)


def calculate_day_n_retention(
    day_n: int,
    start_date: str | None = None,
    end_date: str | None = None,
    channel: str | None = None,
    plan: str | None = None,
    anchor_date: dt.date | None = None,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Calculate exact-day retention for Day N (e.g., N=1, 7, 30).

    IMPORTANT: Only users whose signup date is at least N days before the anchor date
    are eligible. Users whose observation windows have not yet elapsed are excluded
    from the denominator, avoiding artificial churn reporting.
    """
    if anchor_date is None:
        anchor_date = get_anchor_date(db_path)

    cutoff_date = (anchor_date - dt.timedelta(days=day_n)).isoformat()

    clauses: list[str] = []
    params: list[Any] = []

    if start_date:
        clauses.append("u.signup_date >= ?")
        params.append(start_date)

    effective_end = min(end_date, cutoff_date) if end_date else cutoff_date
    clauses.append("u.signup_date <= ?")
    params.append(effective_end)

    if channel and channel != "All":
        clauses.append("u.acquisition_channel = ?")
        params.append(channel)
    if plan and plan != "All":
        clauses.append("u.subscription_plan = ?")
        params.append(plan)

    where_sql = "WHERE " + " AND ".join(clauses)

    sql = f"""
        WITH eligible_users AS (
            SELECT u.user_id, u.signup_date
            FROM users u
            {where_sql}
        ),
        retained_users AS (
            SELECT DISTINCT eu.user_id
            FROM eligible_users eu
            JOIN events e ON eu.user_id = e.user_id
            WHERE DATE(e.event_timestamp) = DATE(eu.signup_date, '+{day_n} days')
        )
        SELECT
            (SELECT COUNT(*) FROM eligible_users) AS eligible_cohort_size,
            (SELECT COUNT(*) FROM retained_users) AS retained_count
    """
    df = execute_query(sql, params, db_path=db_path)
    if df.empty:
        eligible = 0
        retained = 0
    else:
        eligible = int(df["eligible_cohort_size"].iloc[0] or 0)
        retained = int(df["retained_count"].iloc[0] or 0)

    rate_pct = (retained / eligible * 100.0) if eligible > 0 else 0.0

    return {
        "day_n": day_n,
        "eligible_cohort_size": eligible,
        "retained_count": retained,
        "retention_rate_pct": round(rate_pct, 2),
        "anchor_date": anchor_date.isoformat(),
        "cutoff_signup_date": cutoff_date,
        "is_sufficient": eligible >= 10,
    }


def get_retention_overview(
    channel: str | None = None,
    plan: str | None = None,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Calculate D1, D7, and D30 retention metrics."""
    anchor = get_anchor_date(db_path)
    d1 = calculate_day_n_retention(1, channel=channel, plan=plan, anchor_date=anchor, db_path=db_path)
    d7 = calculate_day_n_retention(7, channel=channel, plan=plan, anchor_date=anchor, db_path=db_path)
    d30 = calculate_day_n_retention(30, channel=channel, plan=plan, anchor_date=anchor, db_path=db_path)

    return {
        "d1": d1,
        "d7": d7,
        "d30": d30,
        "anchor_date": anchor.isoformat(),
    }


def get_retention_trend_over_time(
    day_n: int = 7,
    channel: str | None = None,
    plan: str | None = None,
    db_path: str | Path | None = None,
) -> pd.DataFrame:
    """Calculate rolling Day N retention by weekly signup cohorts."""
    anchor = get_anchor_date(db_path)
    cutoff_date = (anchor - dt.timedelta(days=day_n)).isoformat()

    clauses = ["u.signup_date <= ?"]
    params: list[Any] = [cutoff_date]

    if channel and channel != "All":
        clauses.append("u.acquisition_channel = ?")
        params.append(channel)
    if plan and plan != "All":
        clauses.append("u.subscription_plan = ?")
        params.append(plan)

    where_sql = "WHERE " + " AND ".join(clauses)

    sql = f"""
        WITH cohort_users AS (
            SELECT
                u.user_id,
                u.signup_date,
                STRFTIME('%Y-W%W', u.signup_date) AS cohort_week
            FROM users u
            {where_sql}
        ),
        retained AS (
            SELECT DISTINCT
                cu.user_id,
                cu.cohort_week
            FROM cohort_users cu
            JOIN events e ON cu.user_id = e.user_id
            WHERE DATE(e.event_timestamp) = DATE(cu.signup_date, '+{day_n} days')
        )
        SELECT
            c.cohort_week,
            COUNT(DISTINCT c.user_id) AS cohort_size,
            COUNT(DISTINCT r.user_id) AS retained_users,
            ROUND(100.0 * COUNT(DISTINCT r.user_id) / COUNT(DISTINCT c.user_id), 2) AS retention_rate_pct
        FROM cohort_users c
        LEFT JOIN retained r ON c.user_id = r.user_id
        GROUP BY c.cohort_week
        ORDER BY c.cohort_week ASC
    """
    return execute_query(sql, params, db_path=db_path)


def get_cohort_retention_matrix(
    granularity: str = "weekly",
    periods: int = 6,
    channel: str | None = None,
    plan: str | None = None,
    anchor_date: dt.date | None = None,
    db_path: str | Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build a cohort retention matrix.

    granularity: 'weekly' (periods 0..5 weeks) or 'monthly' (periods 0..3 months)
    Returns:
    - (pct_matrix, count_matrix)
    Incomplete periods (cohorts whose period has not elapsed yet relative to anchor date)
    are filled with NaN rather than 0.
    """
    if anchor_date is None:
        anchor = get_anchor_date(db_path)
    else:
        anchor = anchor_date

    clauses: list[str] = []
    params: list[Any] = []
    if channel and channel != "All":
        clauses.append("u.acquisition_channel = ?")
        params.append(channel)
    if plan and plan != "All":
        clauses.append("u.subscription_plan = ?")
        params.append(plan)

    where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""

    date_format = "%Y-W%W" if granularity == "weekly" else "%Y-%m"
    period_days = 7 if granularity == "weekly" else 30

    sql = f"""
        SELECT
            u.user_id,
            u.signup_date,
            STRFTIME('{date_format}', u.signup_date) AS cohort_label,
            e.event_timestamp
        FROM users u
        LEFT JOIN events e ON u.user_id = e.user_id
        {where_sql}
    """
    df = execute_query(sql, params, db_path=db_path)
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    df["signup_date"] = pd.to_datetime(df["signup_date"]).dt.date

    # Users and their cohort sizes
    user_cohorts = df[["user_id", "signup_date", "cohort_label"]].drop_duplicates()
    cohort_sizes = user_cohorts.groupby("cohort_label")["user_id"].nunique()

    # Calculate period for each event
    valid_events = df.dropna(subset=["event_timestamp"]).copy()
    valid_events["event_date"] = pd.to_datetime(valid_events["event_timestamp"]).dt.date
    valid_events["days_diff"] = (valid_events["event_date"] - valid_events["signup_date"]).apply(lambda x: x.days)
    valid_events = valid_events[valid_events["days_diff"] >= 0]
    valid_events["period_num"] = valid_events["days_diff"] // period_days

    # Filter to requested number of periods
    valid_events = valid_events[valid_events["period_num"] < periods]

    # Aggregate active users per cohort and period
    if not valid_events.empty:
        active_in_period = (
            valid_events.groupby(["cohort_label", "period_num"])["user_id"]
            .nunique()
            .unstack(fill_value=0)
        )
    else:
        active_in_period = pd.DataFrame(0.0, index=cohort_sizes.index, columns=range(periods))

    # Reindex to ensure all cohorts and requested periods exist
    active_in_period = active_in_period.reindex(index=cohort_sizes.index, columns=range(periods), fill_value=0.0)

    # Mask incomplete periods
    # For each cohort, find max signup date in that cohort to verify the observation window has fully elapsed
    cohort_max_signups = user_cohorts.groupby("cohort_label")["signup_date"].max()

    count_matrix = active_in_period.copy().astype(float)
    pct_matrix = active_in_period.copy().astype(float)

    for cohort, size in cohort_sizes.items():
        max_date = cohort_max_signups[cohort]
        days_elapsed_min = (anchor - max_date).days
        for p in range(periods):
            # Period p covers days [p * period_days, (p + 1) * period_days - 1].
            # For period p to be fully observed, all users in the cohort must have lived through period p's end.
            if p > 0 and days_elapsed_min < ((p + 1) * period_days - 1):
                count_matrix.loc[cohort, p] = np.nan
                pct_matrix.loc[cohort, p] = np.nan
            elif p == 0 and days_elapsed_min < 0:
                count_matrix.loc[cohort, p] = np.nan
                pct_matrix.loc[cohort, p] = np.nan
            else:
                pct_matrix.loc[cohort, p] = round(count_matrix.loc[cohort, p] / size * 100.0, 1)

    # Insert cohort size column
    pct_matrix.insert(0, "Cohort Size", cohort_sizes)
    count_matrix.insert(0, "Cohort Size", cohort_sizes)

    # Format period column names
    col_map = {p: f"Period {p} ({'W' if granularity == 'weekly' else 'M'}{p})" for p in range(periods)}
    pct_matrix = pct_matrix.rename(columns=col_map)
    count_matrix = count_matrix.rename(columns=col_map)

    return pct_matrix, count_matrix
