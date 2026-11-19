"""Database management module for StreamIQ.

Provides connection handling, schema initialization, and query execution
using SQLite for persistent local analytical storage.
"""

from __future__ import annotations

import datetime as dt
import os
import sqlite3
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

# Default database path: <project_root>/data/streamiq.db
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "streamiq.db"


def get_db_path(db_path: str | Path | None = None) -> Path:
    """Resolve database path, defaulting to DEFAULT_DB_PATH."""
    if db_path is None:
        return DEFAULT_DB_PATH
    return Path(db_path)


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Get a SQLite database connection with row factory and foreign keys enabled."""
    target_path = get_db_path(db_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path | None = None) -> None:
    """Initialize database tables and indexes if they do not exist."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            signup_date TEXT NOT NULL,
            country TEXT NOT NULL,
            acquisition_channel TEXT NOT NULL,
            subscription_plan TEXT NOT NULL
        );
    """)

    # 2. Content Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content (
            content_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            genre TEXT NOT NULL,
            release_year INTEGER NOT NULL,
            duration_minutes INTEGER NOT NULL
        );
    """)

    # 3. Events Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            content_id TEXT,
            event_type TEXT NOT NULL,
            event_timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (content_id) REFERENCES content(content_id) ON DELETE SET NULL
        );
    """)

    # 4. Experiments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            experiment_id TEXT PRIMARY KEY,
            experiment_name TEXT NOT NULL,
            hypothesis TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            primary_metric TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('active', 'completed', 'scheduled'))
        );
    """)

    # 5. Experiment Assignments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiment_assignments (
            experiment_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            variant TEXT NOT NULL CHECK(variant IN ('control', 'treatment')),
            PRIMARY KEY (experiment_id, user_id),
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
    """)

    # 6. Experiment Outcomes Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiment_outcomes (
            experiment_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            converted INTEGER NOT NULL CHECK(converted IN (0, 1)),
            playback_completed INTEGER NOT NULL CHECK(playback_completed IN (0, 1)),
            playback_error INTEGER NOT NULL CHECK(playback_error IN (0, 1)),
            PRIMARY KEY (experiment_id, user_id),
            FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
    """)

    # Indexes for high-performance analytical queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_signup ON users(signup_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_channel ON users(acquisition_channel);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_plan ON users(subscription_plan);")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_genre ON content(genre);")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_user_time ON events(user_id, event_timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type_time ON events(event_type, event_timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_content ON events(content_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_assign_user ON experiment_assignments(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_outcomes_user ON experiment_outcomes(user_id);")

    conn.commit()
    conn.close()


_DEFAULT_DB_READY = False


def ensure_database_ready(
    db_path: str | Path | None = None,
    force_check: bool = False,
) -> None:
    """Ensure SQLite database schema is initialized and seeded with synthetic data if empty.

    Guarantees zero-config cloud deployments on Streamlit Community Cloud where
    the local SQLite database is not committed to git or is freshly cloned.
    """
    global _DEFAULT_DB_READY
    target_path = get_db_path(db_path)
    is_default = (db_path is None) or (str(target_path.resolve()) == str(DEFAULT_DB_PATH.resolve()))

    if is_default and _DEFAULT_DB_READY and not force_check:
        return

    target_path.parent.mkdir(parents=True, exist_ok=True)
    init_db(target_path)

    # Check if users table is populated
    counts = get_table_counts(target_path)
    if counts.get("users", 0) == 0:
        if is_default:
            from src.data_generator import generate_synthetic_data

            generate_synthetic_data(num_users=2000, seed=42, db_path=target_path)

    if is_default:
        _DEFAULT_DB_READY = True


def execute_query(
    sql: str,
    params: Iterable[Any] | dict[str, Any] = (),
    db_path: str | Path | None = None,
) -> pd.DataFrame:
    """Execute a SELECT query and return results as a Pandas DataFrame."""
    if db_path is None:
        ensure_database_ready(DEFAULT_DB_PATH)

    conn = get_connection(db_path)
    try:
        df = pd.read_sql_query(sql, conn, params=params)
        return df
    finally:
        conn.close()


def execute_non_query(
    sql: str,
    params: Iterable[Any] | dict[str, Any] = (),
    db_path: str | Path | None = None,
) -> int:
    """Execute an INSERT, UPDATE, or DELETE query and return the number of affected rows."""
    if db_path is None:
        ensure_database_ready(DEFAULT_DB_PATH)

    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def get_table_counts(db_path: str | Path | None = None) -> dict[str, int]:
    """Return dictionary of row counts for all core tables."""
    tables = [
        "users",
        "content",
        "events",
        "experiments",
        "experiment_assignments",
        "experiment_outcomes",
    ]
    counts: dict[str, int] = {}
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        for t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            counts[t] = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        # Table might not exist yet
        pass
    finally:
        conn.close()
    return counts


def get_anchor_date(db_path: str | Path | None = None) -> dt.date:
    """Return the latest date present in events, or default to 2026-10-24."""
    try:
        df = execute_query("SELECT MAX(DATE(event_timestamp)) AS max_date FROM events", db_path=db_path)
        if not df.empty and df["max_date"].iloc[0] is not None:
            return dt.date.fromisoformat(df["max_date"].iloc[0])
    except Exception:
        pass
    return dt.date(2026, 10, 24)

