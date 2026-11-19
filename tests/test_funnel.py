"""Unit tests for src/funnel.py."""

from __future__ import annotations

import pytest

from src.database import execute_non_query, init_db
from src.funnel import FUNNEL_STAGES, calculate_funnel


@pytest.fixture
def funnel_test_db(tmp_path):
    """Create a strictly controlled dataset to test chronological sequence and deduplication.

    Users:
    - User 1 (Normal full journey): Registered -> Open -> View -> Play
    - User 2 (Partial journey): Registered -> Open -> View (no playback)
    - User 3 (Open only, multiple opens): Registered -> Open (5 times) (no view, no play)
    - User 4 (Out of order violation): Registered -> Playback without earlier content view!
    - User 5 (Registered only): No events
    """
    db_file = tmp_path / "funnel_test.db"
    init_db(db_file)

    users = [
        ("U1", "2026-09-01", "US", "Organic Search", "Standard HD"),
        ("U2", "2026-09-01", "US", "Organic Search", "Standard HD"),
        ("U3", "2026-09-01", "US", "Organic Search", "Standard HD"),
        ("U4", "2026-09-01", "US", "Organic Search", "Standard HD"),
        ("U5", "2026-09-01", "US", "Organic Search", "Standard HD"),
    ]
    for u in users:
        execute_non_query("INSERT INTO users VALUES (?, ?, ?, ?, ?)", u, db_path=db_file)

    execute_non_query("INSERT INTO content VALUES ('C1', 'Test Movie', 'Action', 2024, 100)", db_path=db_file)

    # User 1: Perfect chronological order
    execute_non_query("INSERT INTO events VALUES ('E1', 'U1', NULL, 'app_open', '2026-09-01 10:00:00', 'S1')", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E2', 'U1', 'C1', 'content_view', '2026-09-01 10:02:00', 'S1')", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E3', 'U1', 'C1', 'playback_start', '2026-09-01 10:05:00', 'S1')", db_path=db_file)

    # User 2: Drops off before playback
    execute_non_query("INSERT INTO events VALUES ('E4', 'U2', NULL, 'app_open', '2026-09-01 11:00:00', 'S2')", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E5', 'U2', 'C1', 'content_view', '2026-09-01 11:03:00', 'S2')", db_path=db_file)

    # User 3: Opens app 3 times, deduplication check
    execute_non_query("INSERT INTO events VALUES ('E6', 'U3', NULL, 'app_open', '2026-09-01 12:00:00', 'S3a')", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E7', 'U3', NULL, 'app_open', '2026-09-01 13:00:00', 'S3b')", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E8', 'U3', NULL, 'app_open', '2026-09-01 14:00:00', 'S3c')", db_path=db_file)

    # User 4: Has playback_start at 15:00, but content_view occurred at 16:00 (chronological violation)
    execute_non_query("INSERT INTO events VALUES ('E9', 'U4', NULL, 'app_open', '2026-09-01 14:30:00', 'S4')", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E10', 'U4', 'C1', 'playback_start', '2026-09-01 15:00:00', 'S4')", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E11', 'U4', 'C1', 'content_view', '2026-09-01 16:00:00', 'S4')", db_path=db_file)

    return db_file


def test_chronological_funnel_counts(funnel_test_db):
    """Verify exact counts at each funnel stage and strict sequence adherence."""
    result = calculate_funnel(db_path=funnel_test_db)
    counts = result["stage_counts"]

    # Stage 1: Registered = 5 users (U1, U2, U3, U4, U5)
    assert counts[0] == 5

    # Stage 2: Opened App = 4 users (U1, U2, U3, U4)
    assert counts[1] == 4

    # Stage 3: Viewed Content = 2 users (U1, U2). Note: U4 viewed after playback, but U4 did view after app_open so U4 qualifies for content view
    # Let's verify U4: app_open 14:30, content_view 16:00 >= 14:30, so U4 qualifies for Viewed Content!
    # U1, U2, U4 qualify for Stage 3 = 3 users
    assert counts[2] == 3

    # Stage 4: Started Playback = ONLY U1 qualifies!
    # U4 had playback_start at 15:00 which is BEFORE content_view at 16:00! So U4 fails Stage 4!
    assert counts[3] == 1


def test_funnel_conversion_percentages(funnel_test_db):
    """Verify step and overall conversion calculations."""
    result = calculate_funnel(db_path=funnel_test_db)
    df = result["funnel_table"]

    # Overall conversion: 1 / 5 = 20.0%
    assert result["overall_conversion_pct"] == 20.0

    # Step conversion for Opened App: 4 / 5 = 80.0%
    assert df.loc[df["stage_name"] == "2. Opened App", "step_conversion_pct"].iloc[0] == 80.0

    # Step conversion for Started Playback: 1 / 3 = 33.3%
    assert df.loc[df["stage_name"] == "4. Started Playback", "step_conversion_pct"].iloc[0] == 33.3


def test_funnel_bottleneck_detection(funnel_test_db):
    """Verify that the bottleneck identification accurately picks the largest drop-off."""
    result = calculate_funnel(db_path=funnel_test_db)
    bottleneck = result["bottleneck"]
    assert bottleneck is not None
    # Users lost:
    # 1 -> 2: 5 - 4 = 1 lost
    # 2 -> 3: 4 - 3 = 1 lost
    # 3 -> 4: 3 - 1 = 2 lost (Largest loss is 2 users at Started Playback)
    assert bottleneck["stage_name"] == "4. Started Playback"
    assert bottleneck["users_lost"] == 2
    assert "Started Playback" in result["recommendation"]


def test_funnel_conversion_window_cutoff(tmp_path):
    """Verify that events occurring after conversion_window_days are strictly excluded from the funnel."""
    db_file = tmp_path / "funnel_window.db"
    init_db(db_file)

    # U_FAST converts within 2 days
    # U_SLOW converts 20 days later
    execute_non_query("INSERT INTO users VALUES ('U_FAST', '2026-09-01', 'US', 'Organic Search', 'Standard HD')", db_path=db_file)
    execute_non_query("INSERT INTO users VALUES ('U_SLOW', '2026-09-01', 'US', 'Organic Search', 'Standard HD')", db_path=db_file)
    execute_non_query("INSERT INTO content VALUES ('C1', 'Movie', 'Action', 2024, 100)", db_path=db_file)

    # U_FAST: Open day 1, View day 1, Play day 2
    execute_non_query("INSERT INTO events VALUES ('E1', 'U_FAST', NULL, 'app_open', '2026-09-01 10:00:00', 'S1')", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E2', 'U_FAST', 'C1', 'content_view', '2026-09-01 10:05:00', 'S1')", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E3', 'U_FAST', 'C1', 'playback_start', '2026-09-02 10:00:00', 'S1')", db_path=db_file)

    # U_SLOW: Open day 1, but View and Play day 21 (20 days later)
    execute_non_query("INSERT INTO events VALUES ('E4', 'U_SLOW', NULL, 'app_open', '2026-09-01 10:00:00', 'S2')", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E5', 'U_SLOW', 'C1', 'content_view', '2026-09-21 10:00:00', 'S2')", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E6', 'U_SLOW', 'C1', 'playback_start', '2026-09-21 10:10:00', 'S2')", db_path=db_file)

    # Anchor event to ensure anchor date is late September
    execute_non_query("INSERT INTO events VALUES ('E7', 'U_SLOW', NULL, 'app_open', '2026-09-30 10:00:00', 'S3')", db_path=db_file)

    # 1. Unbounded window: Both users complete the funnel
    res_unbounded = calculate_funnel(conversion_window_days=None, db_path=db_file)
    assert res_unbounded["stage_counts"] == [2, 2, 2, 2]

    # 2. 7-Day window: Only U_FAST completes within 7 days; U_SLOW drops off after Opened App
    res_7d = calculate_funnel(conversion_window_days=7, db_path=db_file)
    # Stage 1: 2, Stage 2: 2, Stage 3: 1 (U_FAST only), Stage 4: 1 (U_FAST only)
    assert res_7d["stage_counts"] == [2, 2, 1, 1]
    assert res_7d["overall_conversion_pct"] == 50.0


def test_get_funnel_by_channel(funnel_test_db):
    """Verify that get_funnel_by_channel groups by channel and computes exact conversion."""
    from src.funnel import get_funnel_by_channel

    df = get_funnel_by_channel(db_path=funnel_test_db)
    assert not df.empty
    assert "acquisition_channel" in df.columns
    assert "overall_conv_pct" in df.columns
    assert "primary_drop_off_stage" in df.columns

    # In funnel_test_db, all 5 users are 'Organic Search'
    row = df.iloc[0]
    assert row["acquisition_channel"] == "Organic Search"
    assert row["registered"] == 5
    assert row["app_opened"] == 4
    assert row["content_viewed"] == 3
    assert row["playback_started"] == 1
    assert row["overall_conv_pct"] == 20.0
    assert row["primary_drop_off_stage"] == "4. Playback Started"


