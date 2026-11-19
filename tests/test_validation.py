"""Unit tests for src/validation.py."""

from __future__ import annotations

import pytest

from src.database import execute_non_query, init_db
from src.validation import DataQualityAudit


@pytest.fixture
def clean_audit_db(tmp_path):
    """Clean database with valid relational structure."""
    db_file = tmp_path / "clean_audit.db"
    init_db(db_file)
    execute_non_query("INSERT INTO users VALUES ('U1', '2026-09-01', 'US', 'Organic Search', 'Standard HD')", db_path=db_file)
    execute_non_query("INSERT INTO content VALUES ('C1', 'Movie', 'Action', 2024, 100)", db_path=db_file)
    execute_non_query("INSERT INTO events VALUES ('E1', 'U1', 'C1', 'app_open', '2026-09-01 12:00:00', 'S1')", db_path=db_file)
    execute_non_query("INSERT INTO experiments VALUES ('EXP1', 'Test', 'Hyp', '2026-09-01', '2026-09-30', 'metric', 'active')", db_path=db_file)
    execute_non_query("INSERT INTO experiment_assignments VALUES ('EXP1', 'U1', 'control')", db_path=db_file)
    execute_non_query("INSERT INTO experiment_outcomes VALUES ('EXP1', 'U1', 1, 1, 0)", db_path=db_file)
    return db_file


def test_clean_database_passes_all_audits(clean_audit_db):
    """Verify that a clean database passes all checks with 0 violations."""
    audit = DataQualityAudit(clean_audit_db)
    results = audit.run_full_audit()
    assert len(results) == 6
    for r in results:
        assert r["passed"] is True
        assert r["violations_count"] == 0


def test_audit_detects_invalid_event_type(clean_audit_db):
    """Verify detection of invalid event taxonomy."""
    # Insert an event with unauthorized type
    execute_non_query("INSERT INTO events VALUES ('E_BAD', 'U1', 'C1', 'fake_swipe_left', '2026-09-01 12:05:00', 'S1')", db_path=clean_audit_db)
    audit = DataQualityAudit(clean_audit_db)
    res = audit.check_invalid_event_types()
    assert res["passed"] is False
    assert res["violations_count"] == 1
    assert "fake_swipe_left" in res["details"][0]


def test_audit_detects_temporal_inconsistency(clean_audit_db):
    """Verify detection of event timestamp preceding user signup date."""
    # User U1 signed up on 2026-09-01. Event at 2026-08-15 is an anomaly.
    execute_non_query("INSERT INTO events VALUES ('E_EARLY', 'U1', 'C1', 'app_open', '2026-08-15 12:00:00', 'S1')", db_path=clean_audit_db)
    audit = DataQualityAudit(clean_audit_db)
    res = audit.check_temporal_consistency()
    assert res["passed"] is False
    assert res["violations_count"] == 1
