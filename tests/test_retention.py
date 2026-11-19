"""Unit tests for src/retention.py."""

from __future__ import annotations

import datetime as dt
import numpy as np
import pytest

from src.database import execute_non_query, init_db
from src.retention import (
    calculate_day_n_retention,
    get_cohort_retention_matrix,
    get_retention_overview,
)


@pytest.fixture
def retention_mock_db(tmp_path):
    """Create controlled mock database for retention and cohort tests.

    Anchor Date = 2026-10-24

    Users:
    - U_OLD_1: signed up 2026-09-01 (53 days before anchor -> eligible for D1, D7, D30)
      - Has event on 2026-09-02 (Day 1 exact)
      - Has event on 2026-09-08 (Day 7 exact)
      - Has event on 2026-10-01 (Day 30 exact)
    - U_OLD_2: signed up 2026-09-01 (53 days before anchor -> eligible for D1, D7, D30)
      - Has event on 2026-09-02 (Day 1 exact)
      - No event on Day 7, no event on Day 30 (churned)
    - U_RECENT: signed up 2026-10-20 (4 days before anchor)
      - Eligible for D1 (elapsed >= 1 day)
      - NOT ELIGIBLE for D7 (only 4 days elapsed < 7 days)!
      - NOT ELIGIBLE for D30 (only 4 days elapsed < 30 days)!
      - Has event on 2026-10-21 (Day 1 exact)
    """
    db_file = tmp_path / "retention_test.db"
    init_db(db_file)

    users = [
        ("U_OLD_1", "2026-09-01", "US", "Organic Search", "Standard HD"),
        ("U_OLD_2", "2026-09-01", "UK", "Social Media", "Standard HD"),
        ("U_RECENT", "2026-10-20", "CA", "Referral", "Premium 4K"),
    ]
    for u in users:
        execute_non_query("INSERT INTO users VALUES (?, ?, ?, ?, ?)", u, db_path=db_file)

    events = [
        # U_OLD_1 events
        ("E1", "U_OLD_1", "app_open", "2026-09-02 10:00:00"),  # D1
        ("E2", "U_OLD_1", "app_open", "2026-09-08 10:00:00"),  # D7
        ("E3", "U_OLD_1", "app_open", "2026-10-01 10:00:00"),  # D30

        # U_OLD_2 events
        ("E4", "U_OLD_2", "app_open", "2026-09-02 10:00:00"),  # D1

        # U_RECENT events
        ("E5", "U_RECENT", "app_open", "2026-10-21 10:00:00"), # D1
        # Anchor event
        ("E6", "U_RECENT", "app_open", "2026-10-24 10:00:00"),
    ]
    for e_id, u_id, e_type, ts in events:
        execute_non_query(
            "INSERT INTO events (event_id, user_id, event_type, event_timestamp, session_id) VALUES (?, ?, ?, ?, ?)",
            (e_id, u_id, e_type, ts, f"S_{e_id}"),
            db_path=db_file,
        )

    return db_file


def test_retention_observation_window_exclusion(retention_mock_db):
    """Verify that users whose observation windows have not elapsed are excluded from Day 7 and Day 30."""
    anchor = dt.date(2026, 10, 24)

    # Day 1: All 3 users signed up at least 1 day before anchor (2026-09-01 and 2026-10-20 <= 2026-10-23)
    d1 = calculate_day_n_retention(1, anchor_date=anchor, db_path=retention_mock_db)
    assert d1["eligible_cohort_size"] == 3
    assert d1["retained_count"] == 3
    assert d1["retention_rate_pct"] == 100.0

    # Day 7: Cutoff is 2026-10-17.
    # U_RECENT (2026-10-20) MUST BE EXCLUDED!
    # Only U_OLD_1 and U_OLD_2 are eligible (n=2).
    d7 = calculate_day_n_retention(7, anchor_date=anchor, db_path=retention_mock_db)
    assert d7["eligible_cohort_size"] == 2
    # Only U_OLD_1 returned on Day 7
    assert d7["retained_count"] == 1
    assert d7["retention_rate_pct"] == 50.0

    # Day 30: Cutoff is 2026-09-24.
    # Only U_OLD_1 and U_OLD_2 are eligible (n=2).
    # Only U_OLD_1 returned on Day 30
    d30 = calculate_day_n_retention(30, anchor_date=anchor, db_path=retention_mock_db)
    assert d30["eligible_cohort_size"] == 2
    assert d30["retained_count"] == 1
    assert d30["retention_rate_pct"] == 50.0


def test_zero_eligible_cohort(tmp_path):
    """Verify safe handling when no users meet the observation window."""
    db_file = tmp_path / "recent_only.db"
    init_db(db_file)
    execute_non_query("INSERT INTO users VALUES ('U_NEW', '2026-10-23', 'US', 'Organic Search', 'Standard HD')", db_path=db_file)

    # For Day 30 on anchor 2026-10-24, eligible cohort is 0
    res = calculate_day_n_retention(30, anchor_date=dt.date(2026, 10, 24), db_path=db_file)
    assert res["eligible_cohort_size"] == 0
    assert res["retained_count"] == 0
    assert res["retention_rate_pct"] == 0.0


def test_cohort_matrix_nan_for_incomplete_periods(retention_mock_db):
    """Verify that future/incomplete cohort periods in heatmap matrix contain NaN rather than 0."""
    pct_matrix, count_matrix = get_cohort_retention_matrix(
        granularity="weekly",
        periods=4,
        db_path=retention_mock_db,
    )
    assert not pct_matrix.empty
    # The recent cohort (week 42 / 2026-10-20) has only existed for 4 days
    # So Period 1 (7 days) should be NaN!
    recent_cohort_label = [idx for idx in pct_matrix.index if "42" in idx or "10" in idx]
    if recent_cohort_label:
        cohort = recent_cohort_label[0]
        # Period 1 (7-13 days) cannot have elapsed yet
        col_p1 = [c for c in pct_matrix.columns if "Period 1" in c][0]
        assert np.isnan(pct_matrix.loc[cohort, col_p1])


def test_retention_date_range_filtering(retention_mock_db):
    """Verify that calculate_day_n_retention supports start_date and end_date cohort filtering."""
    anchor = dt.date(2026, 10, 24)

    # Filter cohort to only September 2026: U_OLD_1 and U_OLD_2
    res_sept = calculate_day_n_retention(
        day_n=1,
        start_date="2026-09-01",
        end_date="2026-09-30",
        anchor_date=anchor,
        db_path=retention_mock_db,
    )
    assert res_sept["eligible_cohort_size"] == 2
    assert res_sept["retained_count"] == 2
    assert res_sept["retention_rate_pct"] == 100.0

    # Filter cohort to October only: U_RECENT
    res_oct = calculate_day_n_retention(
        day_n=1,
        start_date="2026-10-01",
        end_date="2026-10-24",
        anchor_date=anchor,
        db_path=retention_mock_db,
    )
    assert res_oct["eligible_cohort_size"] == 1
    assert res_oct["retained_count"] == 1


def test_cohort_matrix_uses_max_date_for_period_completeness(tmp_path):
    """Verify that a cohort is only marked complete for a period if the LATEST user has completed it."""
    db_file = tmp_path / "cohort_max_test.db"
    init_db(db_file)

    # In week 2026-W35: U_A signed up on 2026-09-01 (Tuesday), U_B signed up on 2026-09-06 (Sunday, end of week)
    # Anchor date: 2026-09-15.
    # From U_A (2026-09-01) to anchor (2026-09-15): 14 days elapsed (Period 1 days 7..13 would be complete for U_A alone).
    # BUT from U_B (2026-09-06) to anchor (2026-09-15): only 9 days elapsed. Period 1 (days 7..13) is NOT complete for U_B!
    # Period 1 must be NaN because the cohort's observation window is not complete for all cohort members!
    execute_non_query("INSERT INTO users VALUES ('U_A', '2026-09-01', 'US', 'Organic Search', 'Standard HD')", db_path=db_file)
    execute_non_query("INSERT INTO users VALUES ('U_B', '2026-09-06', 'US', 'Organic Search', 'Standard HD')", db_path=db_file)
    # Event on anchor
    execute_non_query("INSERT INTO events (event_id, user_id, event_type, event_timestamp, session_id) VALUES ('E_ANCHOR', 'U_A', 'app_open', '2026-09-15 12:00:00', 'S0')", db_path=db_file)

    pct_matrix, _ = get_cohort_retention_matrix(
        granularity="weekly",
        periods=2,
        anchor_date=dt.date(2026, 9, 15),
        db_path=db_file,
    )
    assert not pct_matrix.empty
    col_p1 = [c for c in pct_matrix.columns if "Period 1" in c][0]
    # Period 1 must be NaN because U_B hasn't had the full 14 days needed to complete Period 1
    assert np.isnan(pct_matrix.iloc[0][col_p1])

