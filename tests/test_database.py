"""Unit tests for src/database.py."""

from __future__ import annotations

import sqlite3
import pytest

from src.database import execute_non_query, execute_query, get_connection, get_table_counts, init_db


@pytest.fixture
def temp_db(tmp_path):
    """Provide a clean temporary SQLite database path."""
    db_file = tmp_path / "test_streamiq.db"
    init_db(db_file)
    return db_file


def test_init_db_creates_all_tables(temp_db):
    """Verify that all core analytical tables are created."""
    counts = get_table_counts(temp_db)
    assert "users" in counts
    assert "content" in counts
    assert "events" in counts
    assert "experiments" in counts
    assert "experiment_assignments" in counts
    assert "experiment_outcomes" in counts

    # Check that initially all tables are empty
    for table, count in counts.items():
        assert count == 0


def test_init_db_is_idempotent(temp_db):
    """Verify that running init_db multiple times does not raise or destroy data."""
    # Insert a dummy user
    execute_non_query(
        "INSERT INTO users (user_id, signup_date, country, acquisition_channel, subscription_plan) "
        "VALUES (?, ?, ?, ?, ?)",
        ("U_TEST_1", "2026-09-01", "United States", "Organic Search", "Standard HD"),
        db_path=temp_db,
    )
    # Re-run init_db
    init_db(temp_db)
    counts = get_table_counts(temp_db)
    assert counts["users"] == 1


def test_foreign_key_enforcement(temp_db):
    """Verify SQLite enforces foreign key constraints."""
    # Inserting an event with non-existent user should fail
    with pytest.raises(sqlite3.IntegrityError):
        execute_non_query(
            "INSERT INTO events (event_id, user_id, event_type, event_timestamp, session_id) "
            "VALUES (?, ?, ?, ?, ?)",
            ("EVT_FAIL", "NON_EXISTENT_USER", "app_open", "2026-09-01 10:00:00", "SES_1"),
            db_path=temp_db,
        )


def test_execute_query_returns_dataframe(temp_db):
    """Verify execute_query returns valid pandas DataFrame."""
    execute_non_query(
        "INSERT INTO users (user_id, signup_date, country, acquisition_channel, subscription_plan) "
        "VALUES (?, ?, ?, ?, ?)",
        ("U_1", "2026-09-01", "Germany", "Referral", "Premium 4K"),
        db_path=temp_db,
    )
    df = execute_query("SELECT user_id, country FROM users WHERE user_id = ?", ("U_1",), db_path=temp_db)
    assert len(df) == 1
    assert df["user_id"].iloc[0] == "U_1"
    assert df["country"].iloc[0] == "Germany"


def test_database_indexes_exist(temp_db):
    """Verify that performance indexes are defined in database schema."""
    df_idx = execute_query("SELECT name FROM sqlite_master WHERE type = 'index'", db_path=temp_db)
    index_names = set(df_idx["name"])
    assert "idx_users_signup" in index_names
    assert "idx_events_user_time" in index_names
    assert "idx_events_type_time" in index_names
    assert "idx_content_genre" in index_names


def test_seed_reproducibility_and_idempotence(tmp_path):
    """Verify that generate_synthetic_data produces identical deterministic results with seed 42."""
    from src.data_generator import generate_synthetic_data

    db1 = tmp_path / "seed_run1.db"
    db2 = tmp_path / "seed_run2.db"

    res1 = generate_synthetic_data(num_users=50, seed=42, db_path=db1, force_recreate=True)
    res2 = generate_synthetic_data(num_users=50, seed=42, db_path=db2, force_recreate=True)

    assert res1["users"] == res2["users"] == 50
    assert res1["events"] == res2["events"]
    assert res1["assignments"] == res2["assignments"]

    # Test idempotence without force_recreate
    res_idempotent = generate_synthetic_data(num_users=50, seed=42, db_path=db1, force_recreate=False)
    assert res_idempotent["status"] == "already_populated"

