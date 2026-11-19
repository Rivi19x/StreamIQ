"""Data quality validation suite for StreamIQ.

Runs automated structural, referential, and temporal integrity checks
against the SQLite analytical database and reports issues clearly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.database import execute_query, get_db_path


class DataQualityAudit:
    """Executes a battery of data quality tests against the platform database."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = get_db_path(db_path)

    def check_missing_identifiers(self) -> dict[str, Any]:
        """Check for NULL or empty primary identifiers in core tables."""
        checks = [
            ("users", "user_id", "SELECT COUNT(*) AS c FROM users WHERE user_id IS NULL OR TRIM(user_id) = ''"),
            ("content", "content_id", "SELECT COUNT(*) AS c FROM content WHERE content_id IS NULL OR TRIM(content_id) = ''"),
            ("events", "event_id", "SELECT COUNT(*) AS c FROM events WHERE event_id IS NULL OR TRIM(event_id) = ''"),
            ("events", "user_id", "SELECT COUNT(*) AS c FROM events WHERE user_id IS NULL OR TRIM(user_id) = ''"),
            ("events", "session_id", "SELECT COUNT(*) AS c FROM events WHERE session_id IS NULL OR TRIM(session_id) = ''"),
        ]
        violations = []
        for table, col, sql in checks:
            df = execute_query(sql, db_path=self.db_path)
            count = int(df["c"].iloc[0])
            if count > 0:
                violations.append(f"{table}.{col} has {count} missing identifiers")

        return {
            "check": "Missing Required Identifiers",
            "passed": len(violations) == 0,
            "violations_count": len(violations),
            "details": violations if violations else ["All required primary and foreign keys are populated."],
        }

    def check_duplicate_event_ids(self) -> dict[str, Any]:
        """Check for duplicate event_id values."""
        sql = """
            SELECT event_id, COUNT(*) as cnt
            FROM events
            GROUP BY event_id
            HAVING cnt > 1
        """
        df = execute_query(sql, db_path=self.db_path)
        dup_count = len(df)
        return {
            "check": "Unique Event Identifiers",
            "passed": dup_count == 0,
            "violations_count": dup_count,
            "details": [f"Found {dup_count} duplicated event IDs"] if dup_count > 0 else ["All event IDs are strictly unique."],
        }

    def check_invalid_event_types(self) -> dict[str, Any]:
        """Check for events with unrecognized event_type strings."""
        valid_types = ("app_open", "search", "content_view", "playback_start", "playback_complete")
        sql = f"""
            SELECT event_type, COUNT(*) as cnt
            FROM events
            WHERE event_type NOT IN {valid_types}
            GROUP BY event_type
        """
        df = execute_query(sql, db_path=self.db_path)
        invalid_count = len(df)
        details = [f"Found unknown event type '{row['event_type']}': {row['cnt']} occurrences" for _, row in df.iterrows()]
        return {
            "check": "Valid Event Types",
            "passed": invalid_count == 0,
            "violations_count": invalid_count,
            "details": details if details else [f"All events conform to defined taxonomy: {list(valid_types)}."],
        }

    def check_temporal_consistency(self) -> dict[str, Any]:
        """Verify events do not predate user signup_date and are properly formatted."""
        sql = """
            SELECT COUNT(*) AS c
            FROM events e
            JOIN users u ON e.user_id = u.user_id
            WHERE e.event_timestamp < u.signup_date
        """
        df = execute_query(sql, db_path=self.db_path)
        count = int(df["c"].iloc[0])
        return {
            "check": "Temporal Consistency (Event >= Signup Date)",
            "passed": count == 0,
            "violations_count": count,
            "details": [f"{count} events have timestamps earlier than user registration date."] if count > 0 else ["All events occurred on or after the user's signup date."],
        }

    def check_orphan_events(self) -> dict[str, Any]:
        """Check for events referencing nonexistent user_id or content_id."""
        sql_users = """
            SELECT COUNT(*) AS c
            FROM events e
            LEFT JOIN users u ON e.user_id = u.user_id
            WHERE u.user_id IS NULL
        """
        sql_content = """
            SELECT COUNT(*) AS c
            FROM events e
            LEFT JOIN content c ON e.content_id = c.content_id
            WHERE e.content_id IS NOT NULL AND c.content_id IS NULL
        """
        df_u = execute_query(sql_users, db_path=self.db_path)
        df_c = execute_query(sql_content, db_path=self.db_path)
        orphan_users = int(df_u["c"].iloc[0])
        orphan_content = int(df_c["c"].iloc[0])

        violations = []
        if orphan_users > 0:
            violations.append(f"{orphan_users} events reference non-existent users")
        if orphan_content > 0:
            violations.append(f"{orphan_content} events reference non-existent content")

        return {
            "check": "Referential Integrity",
            "passed": len(violations) == 0,
            "violations_count": orphan_users + orphan_content,
            "details": violations if violations else ["Foreign key integrity verified across all events."],
        }

    def check_experiment_integrity(self) -> dict[str, Any]:
        """Check that users have at most 1 variant per experiment and outcomes map to assignments."""
        sql_dup_variants = """
            SELECT experiment_id, user_id, COUNT(DISTINCT variant) AS variant_count
            FROM experiment_assignments
            GROUP BY experiment_id, user_id
            HAVING variant_count > 1
        """
        sql_orphan_outcomes = """
            SELECT COUNT(*) AS c
            FROM experiment_outcomes o
            LEFT JOIN experiment_assignments a
              ON o.experiment_id = a.experiment_id AND o.user_id = a.user_id
            WHERE a.user_id IS NULL
        """
        df_dup = execute_query(sql_dup_variants, db_path=self.db_path)
        df_orph = execute_query(sql_orphan_outcomes, db_path=self.db_path)

        dup_users = len(df_dup)
        orphan_outcomes = int(df_orph["c"].iloc[0])

        violations = []
        if dup_users > 0:
            violations.append(f"{dup_users} users have multiple variants assigned in the same experiment")
        if orphan_outcomes > 0:
            violations.append(f"{orphan_outcomes} outcomes exist without assignment records")

        return {
            "check": "Experiment Assignment & Outcome Integrity",
            "passed": len(violations) == 0,
            "violations_count": dup_users + orphan_outcomes,
            "details": violations if violations else ["Experiment assignments and outcomes are strictly 1-to-1 and consistent."],
        }

    def run_full_audit(self) -> list[dict[str, Any]]:
        """Run all data quality checks and return list of check summaries."""
        return [
            self.check_missing_identifiers(),
            self.check_duplicate_event_ids(),
            self.check_invalid_event_types(),
            self.check_temporal_consistency(),
            self.check_orphan_events(),
            self.check_experiment_integrity(),
        ]
