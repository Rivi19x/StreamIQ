"""Synthetic data generator for StreamIQ.

Generates a realistic, reproducible synthetic dataset for a streaming platform:
- 2,000 users with acquisition channels, countries, and subscription tiers
- 100 content items across 8 genres
- Realistic sequential event sessions (app_open -> search/content_view -> playback_start -> playback_complete)
- A/B experiments with user-level randomized assignments and consistent outcomes

DISCLOSURE: All data produced by this module is purely synthetic / simulated for demonstration
and portfolio purposes. It does not originate from Netflix or any real streaming enterprise.
"""

from __future__ import annotations

import datetime as dt
import random
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.database import get_connection, init_db

RANDOM_SEED = 42

COUNTRIES = ["United States", "United Kingdom", "Canada", "Germany", "India", "France", "Brazil", "Australia"]
COUNTRY_WEIGHTS = [0.35, 0.15, 0.10, 0.10, 0.15, 0.05, 0.05, 0.05]

ACQUISITION_CHANNELS = ["Organic Search", "Social Media", "Paid Search", "Referral", "Email Campaign"]
CHANNEL_WEIGHTS = [0.30, 0.25, 0.20, 0.15, 0.10]

SUBSCRIPTION_PLANS = ["Free Ad-Supported", "Standard HD", "Premium 4K"]
PLAN_WEIGHTS = [0.45, 0.35, 0.20]

GENRES = ["Action", "Comedy", "Drama", "Sci-Fi", "Thriller", "Documentary", "Romance", "Animation"]
GENRE_WEIGHTS = [0.22, 0.18, 0.18, 0.14, 0.10, 0.08, 0.05, 0.05]

CONTENT_TITLES = [
    ("Cosmic Drift", "Sci-Fi", 2024, 118),
    ("The Midnight Courier", "Thriller", 2023, 102),
    ("Echoes of Tomorrow", "Sci-Fi", 2025, 126),
    ("Silicon Dreams", "Documentary", 2022, 88),
    ("Laugh Out Loud NYC", "Comedy", 2023, 94),
    ("Crown of Shadows", "Drama", 2024, 142),
    ("Neon Nights", "Action", 2024, 110),
    ("Parisian Serenade", "Romance", 2021, 98),
    ("Dragonfly Protocol", "Action", 2025, 122),
    ("The Quiet Valley", "Drama", 2020, 105),
    ("Quantum Paradox", "Sci-Fi", 2024, 134),
    ("Almost Famous", "Comedy", 2022, 101),
    ("Ocean Secrets", "Documentary", 2023, 76),
    ("Cyberpunk Uprising", "Sci-Fi", 2025, 115),
    ("The Iron Fortress", "Action", 2023, 130),
    ("Sunset in Amalfi", "Romance", 2024, 92),
    ("Whimsical Forest", "Animation", 2023, 85),
    ("The Silent Witness", "Thriller", 2022, 109),
    ("Urban Rhythm", "Drama", 2021, 116),
    ("Space Odyssey: Alpha", "Sci-Fi", 2024, 140),
]


def _generate_synthetic_content_list(count: int = 100) -> list[dict[str, Any]]:
    """Generate 100 synthetic content catalogue items."""
    rng = random.Random(RANDOM_SEED)
    items: list[dict[str, Any]] = []

    adjectives = [
        "Hidden", "Last", "Golden", "Silent", "Dark", "Infinite", "Electric", "Brave",
        "Crimson", "Wild", "Lost", "Final", "Forgotten", "Savage", "Frozen", "Wandering"
    ]
    nouns = [
        "Horizon", "Journey", "Chronicles", "Legacy", "Station", "Voyage", "Empire", "Cipher",
        "Mystery", "Frontier", "Alliance", "Reckoning", "Echo", "Sanctuary", "Flight", "Destiny"
    ]

    for i in range(1, count + 1):
        content_id = f"CNT{i:04d}"
        if i <= len(CONTENT_TITLES):
            title, genre, release_year, duration = CONTENT_TITLES[i - 1]
        else:
            title = f"{rng.choice(adjectives)} {rng.choice(nouns)}"
            genre = rng.choices(GENRES, weights=GENRE_WEIGHTS, k=1)[0]
            release_year = rng.randint(2018, 2026)
            duration = rng.randint(22, 145)

        items.append({
            "content_id": content_id,
            "title": title,
            "genre": genre,
            "release_year": release_year,
            "duration_minutes": duration,
        })
    return items


def generate_synthetic_data(
    num_users: int = 2000,
    seed: int = RANDOM_SEED,
    db_path: str | Path | None = None,
    force_recreate: bool = False,
) -> dict[str, int]:
    """Populate SQLite database with reproducible synthetic data.

    If database already has records and force_recreate is False, skips generation.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Check if already populated
    cursor.execute("SELECT COUNT(*) FROM users")
    existing_users = cursor.fetchone()[0]
    if existing_users > 0 and not force_recreate:
        cursor.execute("SELECT COUNT(*) FROM events")
        existing_events = cursor.fetchone()[0]
        conn.close()
        return {
            "users": existing_users,
            "events": existing_events,
            "status": "already_populated",
        }

    if force_recreate:
        cursor.execute("DELETE FROM experiment_outcomes")
        cursor.execute("DELETE FROM experiment_assignments")
        cursor.execute("DELETE FROM experiments")
        cursor.execute("DELETE FROM events")
        cursor.execute("DELETE FROM content")
        cursor.execute("DELETE FROM users")
        conn.commit()

    # Fixed seed for deterministic data generation
    random.seed(seed)
    np.random.seed(seed)
    rng = random.Random(seed)

    # 1. Generate Content Catalogue (100 items)
    content_list = _generate_synthetic_content_list(100)
    cursor.executemany(
        """
        INSERT INTO content (content_id, title, genre, release_year, duration_minutes)
        VALUES (:content_id, :title, :genre, :release_year, :duration_minutes)
        """,
        content_list,
    )
    content_ids = [c["content_id"] for c in content_list]

    # 2. Generate Users (2,000 users over a 105-day signup window)
    # Window: 2026-07-01 to 2026-10-14, anchor date = 2026-10-24
    anchor_date = dt.date(2026, 10, 24)
    start_signup_date = dt.date(2026, 7, 1)
    signup_days_span = (anchor_date - start_signup_date).days  # 115 days

    users: list[dict[str, Any]] = []
    user_activity_profiles: dict[str, str] = {}  # highly_active, moderate, low, dormant

    for i in range(1, num_users + 1):
        user_id = f"USR{i:05d}"
        days_offset = rng.randint(0, signup_days_span - 7)  # allow at least 7 days before anchor
        signup_dt = start_signup_date + dt.timedelta(days=days_offset)
        country = rng.choices(COUNTRIES, weights=COUNTRY_WEIGHTS, k=1)[0]
        channel = rng.choices(ACQUISITION_CHANNELS, weights=CHANNEL_WEIGHTS, k=1)[0]
        plan = rng.choices(SUBSCRIPTION_PLANS, weights=PLAN_WEIGHTS, k=1)[0]

        # Activity profile affects session frequency and retention
        profile_choice = rng.choices(
            ["highly_active", "moderate", "low", "churned_early"],
            weights=[0.20, 0.40, 0.25, 0.15],
            k=1,
        )[0]
        user_activity_profiles[user_id] = profile_choice

        users.append({
            "user_id": user_id,
            "signup_date": signup_dt.isoformat(),
            "country": country,
            "acquisition_channel": channel,
            "subscription_plan": plan,
        })

    cursor.executemany(
        """
        INSERT INTO users (user_id, signup_date, country, acquisition_channel, subscription_plan)
        VALUES (:user_id, :signup_date, :country, :acquisition_channel, :subscription_plan)
        """,
        users,
    )

    # 3. Generate Events & Realistic Sessions
    # Each session follows strict chronological sequence:
    # app_open -> (optional search) -> content_view -> (optional playback_start) -> (optional playback_complete)
    events: list[dict[str, Any]] = []

    # Map content items by genre for realistic user genre affinity
    content_by_genre: dict[str, list[str]] = {}
    for c in content_list:
        content_by_genre.setdefault(c["genre"], []).append(c["content_id"])

    event_counter = 1

    for u in users:
        u_id = u["user_id"]
        u_signup = dt.date.fromisoformat(u["signup_date"])
        u_profile = user_activity_profiles[u_id]
        fav_genre = rng.choices(GENRES, weights=GENRE_WEIGHTS, k=1)[0]

        # Number of active days based on profile
        days_since_signup = (anchor_date - u_signup).days

        if u_profile == "churned_early":
            active_days_offsets = [0]
            if rng.random() < 0.25 and days_since_signup >= 1:
                active_days_offsets.append(1)  # tiny D1 retention
        elif u_profile == "low":
            # 1 to 4 sessions, concentrated near signup
            num_days = min(rng.randint(2, 4), max(1, days_since_signup))
            active_days_offsets = sorted(list({0} | set(rng.sample(range(0, min(14, max(1, days_since_signup))), num_days))))
        elif u_profile == "moderate":
            # Multiple sessions across up to 30 days
            num_days = min(rng.randint(5, 12), max(1, days_since_signup))
            potential_pool = range(0, max(1, days_since_signup))
            active_days_offsets = sorted(list({0, 1, 7} if days_since_signup >= 7 and rng.random() < 0.6 else {0} | set(rng.sample(potential_pool, min(num_days, len(potential_pool))))))
        else:  # highly_active
            # Retained across D1, D7, D30 and frequent usage
            num_days = min(rng.randint(15, 35), max(1, days_since_signup))
            potential_pool = list(range(0, max(1, days_since_signup)))
            active_days_offsets = set(rng.sample(potential_pool, min(num_days, len(potential_pool))))
            active_days_offsets.add(0)
            if days_since_signup >= 1 and rng.random() < 0.85:
                active_days_offsets.add(1)
            if days_since_signup >= 7 and rng.random() < 0.75:
                active_days_offsets.add(7)
            if days_since_signup >= 30 and rng.random() < 0.60:
                active_days_offsets.add(30)
            active_days_offsets = sorted(list(active_days_offsets))

        # Generate sessions for active days
        for day_offset in active_days_offsets:
            if day_offset > days_since_signup:
                continue

            session_date = u_signup + dt.timedelta(days=day_offset)
            # Sessions per day (1 or 2)
            sessions_count = 1 if u_profile != "highly_active" else (1 if rng.random() < 0.6 else 2)

            for sess_idx in range(sessions_count):
                session_id = f"SES_{u_id}_{day_offset}_{sess_idx}"
                # Start time between 08:00 and 23:00
                sess_hour = rng.randint(8, 22)
                sess_minute = rng.randint(0, 50)
                sess_second = rng.randint(0, 50)
                current_timestamp = dt.datetime(
                    session_date.year, session_date.month, session_date.day,
                    sess_hour, sess_minute, sess_second
                )

                # Step 1: app_open
                events.append({
                    "event_id": f"EVT{event_counter:08d}",
                    "user_id": u_id,
                    "content_id": None,
                    "event_type": "app_open",
                    "event_timestamp": current_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "session_id": session_id,
                })
                event_counter += 1

                # Step 2: search (optional, 45% chance)
                if rng.random() < 0.45:
                    current_timestamp += dt.timedelta(seconds=rng.randint(10, 45))
                    events.append({
                        "event_id": f"EVT{event_counter:08d}",
                        "user_id": u_id,
                        "content_id": None,
                        "event_type": "search",
                        "event_timestamp": current_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "session_id": session_id,
                    })
                    event_counter += 1

                # Step 3: content_view (75% probability after open)
                if rng.random() < 0.75:
                    current_timestamp += dt.timedelta(seconds=rng.randint(15, 60))
                    # Pick content matching user's favorite genre 60% of time, else random
                    if rng.random() < 0.60 and content_by_genre.get(fav_genre):
                        picked_content = rng.choice(content_by_genre[fav_genre])
                    else:
                        picked_content = rng.choice(content_ids)

                    events.append({
                        "event_id": f"EVT{event_counter:08d}",
                        "user_id": u_id,
                        "content_id": picked_content,
                        "event_type": "content_view",
                        "event_timestamp": current_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "session_id": session_id,
                    })
                    event_counter += 1

                    # Step 4: playback_start (60% probability after view)
                    if rng.random() < 0.60:
                        current_timestamp += dt.timedelta(seconds=rng.randint(5, 30))
                        events.append({
                            "event_id": f"EVT{event_counter:08d}",
                            "user_id": u_id,
                            "content_id": picked_content,
                            "event_type": "playback_start",
                            "event_timestamp": current_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            "session_id": session_id,
                        })
                        event_counter += 1

                        # Step 5: playback_complete (70% probability after playback_start)
                        if rng.random() < 0.70:
                            current_timestamp += dt.timedelta(minutes=rng.randint(20, 110))
                            events.append({
                                "event_id": f"EVT{event_counter:08d}",
                                "user_id": u_id,
                                "content_id": picked_content,
                                "event_type": "playback_complete",
                                "event_timestamp": current_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                "session_id": session_id,
                            })
                            event_counter += 1

    # Bulk insert events in batches of 5000
    batch_size = 5000
    for i in range(0, len(events), batch_size):
        cursor.executemany(
            """
            INSERT INTO events (event_id, user_id, content_id, event_type, event_timestamp, session_id)
            VALUES (:event_id, :user_id, :content_id, :event_type, :event_timestamp, :session_id)
            """,
            events[i : i + batch_size],
        )

    # 4. Generate Experiments & Outcomes
    experiments = [
        {
            "experiment_id": "EXP_001_HERO_CAROUSEL",
            "experiment_name": "Homepage Hero Carousel Autoplay Preview",
            "hypothesis": "Video previews in the hero carousel will increase content_view to playback_start conversion rate by >=10% relative without increasing playback error rates.",
            "start_date": "2026-08-01",
            "end_date": "2026-09-15",
            "primary_metric": "playback_start_rate",
            "status": "completed",
        },
        {
            "experiment_id": "EXP_002_SEARCH_ALGO_V2",
            "experiment_name": "Context-Aware Semantic Search Ranking",
            "hypothesis": "Personalized neural search ranking will improve search-to-playback conversion rate by >=8% relative.",
            "start_date": "2026-09-01",
            "end_date": "2026-10-15",
            "primary_metric": "search_conversion_rate",
            "status": "completed",
        },
    ]

    cursor.executemany(
        """
        INSERT INTO experiments (experiment_id, experiment_name, hypothesis, start_date, end_date, primary_metric, status)
        VALUES (:experiment_id, :experiment_name, :hypothesis, :start_date, :end_date, :primary_metric, :status)
        """,
        experiments,
    )

    # Experiment Assignments & Outcomes
    # EXP 1: 1,400 eligible users assigned (700 control, 700 treatment)
    # Control conversion rate: ~35.0%, Treatment conversion rate: ~41.5% (significant positive lift ~18.5% relative)
    # Playback completed: Control ~80%, Treatment ~81% (healthy guardrail)
    # Playback errors: Control ~3.0%, Treatment ~3.1% (neutral guardrail)
    exp1_users = [u["user_id"] for u in users[:1400]]
    exp1_assignments: list[dict[str, Any]] = []
    exp1_outcomes: list[dict[str, Any]] = []

    for idx, u_id in enumerate(exp1_users):
        variant = "control" if idx % 2 == 0 else "treatment"
        exp1_assignments.append({
            "experiment_id": "EXP_001_HERO_CAROUSEL",
            "user_id": u_id,
            "variant": variant,
        })

        if variant == "control":
            converted = 1 if rng.random() < 0.35 else 0
            completed = 1 if converted and rng.random() < 0.80 else 0
            error = 1 if rng.random() < 0.030 else 0
        else:
            converted = 1 if rng.random() < 0.415 else 0
            completed = 1 if converted and rng.random() < 0.81 else 0
            error = 1 if rng.random() < 0.031 else 0

        exp1_outcomes.append({
            "experiment_id": "EXP_001_HERO_CAROUSEL",
            "user_id": u_id,
            "converted": converted,
            "playback_completed": completed,
            "playback_error": error,
        })

    # EXP 2: 1,200 eligible users assigned (600 control, 600 treatment)
    # Control conversion rate: ~28.0%, Treatment conversion rate: ~28.5% (inconclusive / neutral, p > 0.05)
    # Playback errors: Control ~2.5%, Treatment ~2.7%
    exp2_users = [u["user_id"] for u in users[600:1800]]
    exp2_assignments: list[dict[str, Any]] = []
    exp2_outcomes: list[dict[str, Any]] = []

    for idx, u_id in enumerate(exp2_users):
        variant = "control" if idx % 2 == 0 else "treatment"
        exp2_assignments.append({
            "experiment_id": "EXP_002_SEARCH_ALGO_V2",
            "user_id": u_id,
            "variant": variant,
        })

        if variant == "control":
            converted = 1 if rng.random() < 0.280 else 0
            completed = 1 if converted and rng.random() < 0.78 else 0
            error = 1 if rng.random() < 0.025 else 0
        else:
            converted = 1 if rng.random() < 0.285 else 0
            completed = 1 if converted and rng.random() < 0.77 else 0
            error = 1 if rng.random() < 0.027 else 0

        exp2_outcomes.append({
            "experiment_id": "EXP_002_SEARCH_ALGO_V2",
            "user_id": u_id,
            "converted": converted,
            "playback_completed": completed,
            "playback_error": error,
        })

    cursor.executemany(
        """
        INSERT INTO experiment_assignments (experiment_id, user_id, variant)
        VALUES (:experiment_id, :user_id, :variant)
        """,
        exp1_assignments + exp2_assignments,
    )

    cursor.executemany(
        """
        INSERT INTO experiment_outcomes (experiment_id, user_id, converted, playback_completed, playback_error)
        VALUES (:experiment_id, :user_id, :converted, :playback_completed, :playback_error)
        """,
        exp1_outcomes + exp2_outcomes,
    )

    conn.commit()
    conn.close()

    return {
        "users": len(users),
        "content": len(content_list),
        "events": len(events),
        "experiments": len(experiments),
        "assignments": len(exp1_assignments) + len(exp2_assignments),
        "status": "generated_successfully",
    }


if __name__ == "__main__":
    print("Initializing StreamIQ database and generating synthetic dataset...")
    result = generate_synthetic_data(num_users=2000, force_recreate=True)
    print(f"Data generation complete: {result}")
