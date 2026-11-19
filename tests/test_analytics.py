"""Unit tests for src/analytics.py."""

from __future__ import annotations

import pytest
import pandas as pd

from src.analytics import (
    build_filter_clauses,
    get_content_rankings,
    get_executive_kpis,
    get_genre_popularity,
    get_segment_summary,
    get_user_segmentation,
)
from src.database import execute_non_query, init_db


@pytest.fixture
def mock_analytics_db(tmp_path):
    """Seed a small, deterministic database for exact analytical calculations."""
    db_file = tmp_path / "mock_analytics.db"
    init_db(db_file)

    # 3 Users:
    # U1: signed up 2026-09-01 (old), 10 sessions (Moderately Active)
    # U2: signed up 2026-09-01 (old), 16 sessions (Highly Active)
    # U3: signed up 2026-10-22 (new <= 7 days from 2026-10-24), 2 sessions (New Users)
    users_data = [
        ("U1", "2026-09-01", "United States", "Organic Search", "Standard HD"),
        ("U2", "2026-09-01", "United Kingdom", "Social Media", "Premium 4K"),
        ("U3", "2026-10-22", "Canada", "Organic Search", "Free Ad-Supported"),
    ]
    for u in users_data:
        execute_non_query(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
            u,
            db_path=db_file,
        )

    # 2 Content items
    execute_non_query("INSERT INTO content VALUES ('C1', 'Action Hero', 'Action', 2024, 120)", db_path=db_file)
    execute_non_query("INSERT INTO content VALUES ('C2', 'Comedy Night', 'Comedy', 2023, 90)", db_path=db_file)

    # Events:
    # Session 1 for U1: app_open, content_view (C1), playback_start (C1), playback_complete (C1)
    execute_non_query("INSERT INTO events VALUES ('E1', 'U1', NULL, 'app_open', '2026-09-01 10:00:00', 'S1')", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E2', 'U1', 'C1', 'content_view', '2026-09-01 10:01:00', 'S1')", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E3', 'U1', 'C1', 'playback_start', '2026-09-01 10:02:00', 'S1')", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E4', 'U1', 'C1', 'playback_complete', '2026-09-01 11:30:00', 'S1')", db_path=db_file)

    # Session 2 for U1: app_open, content_view (C1), playback_start (C1) [no complete]
    execute_non_query("INSERT INTO events VALUES ('E5', 'U1', NULL, 'app_open', '2026-09-02 10:00:00', 'S2')", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E6', 'U1', 'C1', 'content_view', '2026-09-02 10:01:00', 'S2')", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E7', 'U1', 'C1', 'playback_start', '2026-09-02 10:02:00', 'S2')", db_path=db_file)

    return db_file


def test_executive_kpis_exact_values(mock_analytics_db):
    """Verify KPI calculations on known mock data."""
    kpis = get_executive_kpis(db_path=mock_analytics_db)
    assert kpis["total_registered_users"] == 3
    assert kpis["active_users"] == 1  # Only U1 has events
    assert kpis["total_sessions"] == 2
    assert kpis["sessions_per_active_user"] == 2.0
    assert kpis["playback_starts"] == 2
    assert kpis["playback_completes"] == 1
    # 1 complete / 2 starts = 50.0%
    assert kpis["playback_completion_rate"] == 50.0


def test_zero_denominator_kpis(tmp_path):
    """Verify graceful handling when database has users but zero events."""
    db_file = tmp_path / "empty_events.db"
    init_db(db_file)
    execute_non_query("INSERT INTO users VALUES ('U0', '2026-09-01', 'US', 'Organic Search', 'Standard HD')", db_path=db_file)

    kpis = get_executive_kpis(db_path=db_file)
    assert kpis["total_registered_users"] == 1
    assert kpis["active_users"] == 0
    assert kpis["sessions_per_active_user"] == 0.0
    assert kpis["playback_completion_rate"] == 0.0


def test_filter_clauses():
    """Verify parameterized filter clause generation."""
    sql, params = build_filter_clauses(
        start_date="2026-09-01",
        end_date="2026-09-30",
        genre="Action",
        channel="Organic Search",
        plan="Standard HD",
    )
    assert "DATE(e.event_timestamp) >= ?" in sql
    assert "DATE(e.event_timestamp) <= ?" in sql
    assert "c.genre = ?" in sql
    assert "u.acquisition_channel = ?" in sql
    assert "u.subscription_plan = ?" in sql
    assert len(params) == 5


def test_genre_popularity_ranking(mock_analytics_db):
    """Verify genre ranking math."""
    df = get_genre_popularity(db_path=mock_analytics_db)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["genre"] == "Action"
    assert row["playback_starts"] == 2
    assert row["playback_completes"] == 1
    assert row["completion_rate_pct"] == 50.0


def test_user_segmentation_rules(mock_analytics_db):
    """Verify rule-based user segmentation logic."""
    df_seg = get_user_segmentation(as_of_date="2026-10-24", db_path=mock_analytics_db)
    seg_map = dict(zip(df_seg["user_id"], df_seg["user_segment"]))

    # U3 signed up on 2026-10-22 (account age 2 days <= 7 days) -> 'New Users'
    assert seg_map["U3"] == "New Users"

    # U1 has 2 sessions, registered > 7 days ago -> 'Low Activity'
    assert seg_map["U1"] == "Low Activity"

    # U2 has 0 sessions, registered > 7 days ago -> 'Low Activity'
    assert seg_map["U2"] == "Low Activity"


def test_user_segmentation_filters(mock_analytics_db):
    """Verify that user segmentation and summary respect channel and plan filters."""
    # Filter by Organic Search: should include U1 and U3, exclude U2
    df_organic = get_user_segmentation(channel="Organic Search", as_of_date="2026-10-24", db_path=mock_analytics_db)
    assert set(df_organic["user_id"]) == {"U1", "U3"}

    summary_organic = get_segment_summary(channel="Organic Search", as_of_date="2026-10-24", db_path=mock_analytics_db)
    assert int(summary_organic["user_count"].sum()) == 2

    # Filter by Premium 4K plan: should only include U2
    df_premium = get_user_segmentation(plan="Premium 4K", as_of_date="2026-10-24", db_path=mock_analytics_db)
    assert set(df_premium["user_id"]) == {"U2"}


def test_channel_and_plan_performance_filters(mock_analytics_db):
    """Verify channel and plan performance breakdown filtering."""
    from src.analytics import get_channel_performance, get_plan_performance

    # Channel performance filtered by Standard HD plan
    df_chan = get_channel_performance(plan="Standard HD", db_path=mock_analytics_db)
    assert len(df_chan) == 1
    assert df_chan.iloc[0]["acquisition_channel"] == "Organic Search"
    assert df_chan.iloc[0]["total_users"] == 1
    assert df_chan.iloc[0]["total_sessions"] == 2

    # Plan performance filtered by Organic Search channel
    df_plan = get_plan_performance(channel="Organic Search", db_path=mock_analytics_db)
    assert set(df_plan["subscription_plan"]) == {"Standard HD", "Free Ad-Supported"}
    assert "playback_completes" in df_plan.columns


def test_executive_kpis_date_range_registration_cutoff(mock_analytics_db):
    """Verify that historical end_date filters out registrations that occurred after end_date."""
    # End date in September 2026: U3 registered in October 2026 must be excluded
    kpis_sept = get_executive_kpis(end_date="2026-09-30", db_path=mock_analytics_db)
    assert kpis_sept["total_registered_users"] == 2  # Only U1 and U2
    assert kpis_sept["active_users"] == 1  # U1

