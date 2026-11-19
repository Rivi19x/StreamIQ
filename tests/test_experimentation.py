"""Unit tests for src/experimentation.py."""

from __future__ import annotations

import pytest

from src.database import get_connection, init_db
from src.experimentation import analyze_experiment


@pytest.fixture
def exp_test_db(tmp_path):
    """Seed experiments with known parameters using fast bulk transactions."""
    db_file = tmp_path / "exp_test.db"
    init_db(db_file)

    conn = get_connection(db_file)
    cursor = conn.cursor()

    # Insert Experiment records
    cursor.execute(
        """
        INSERT INTO experiments VALUES
        ('EXP_WIN', 'Win Test', 'Hypothesis win', '2026-08-01', '2026-08-31', 'conversion', 'completed'),
        ('EXP_TIE', 'Inconclusive Test', 'Hypothesis tie', '2026-08-01', '2026-08-31', 'conversion', 'completed'),
        ('EXP_SRM', 'SRM Test', 'Hypothesis SRM', '2026-08-01', '2026-08-31', 'conversion', 'completed')
        """
    )

    users_to_insert = []
    assignments_to_insert = []
    outcomes_to_insert = []

    # 1. EXP_WIN: Control 100/1000 (10%), Treatment 160/1000 (16%) -> z ~= 4.0, p < 0.001
    for i in range(1000):
        u_c = f"U_WIN_C_{i}"
        users_to_insert.append((u_c, "2026-07-01", "US", "Organic Search", "Standard HD"))
        assignments_to_insert.append(("EXP_WIN", u_c, "control"))
        conv = 1 if i < 100 else 0
        outcomes_to_insert.append(("EXP_WIN", u_c, conv, conv, 0))

        u_t = f"U_WIN_T_{i}"
        users_to_insert.append((u_t, "2026-07-01", "US", "Organic Search", "Standard HD"))
        assignments_to_insert.append(("EXP_WIN", u_t, "treatment"))
        conv = 1 if i < 160 else 0
        outcomes_to_insert.append(("EXP_WIN", u_t, conv, conv, 0))

    # 2. EXP_TIE: Control 100/1000 (10%), Treatment 102/1000 (10.2%) -> p > 0.8
    for i in range(1000):
        u_c = f"U_TIE_C_{i}"
        users_to_insert.append((u_c, "2026-07-01", "US", "Organic Search", "Standard HD"))
        assignments_to_insert.append(("EXP_TIE", u_c, "control"))
        conv = 1 if i < 100 else 0
        outcomes_to_insert.append(("EXP_TIE", u_c, conv, conv, 0))

        u_t = f"U_TIE_T_{i}"
        users_to_insert.append((u_t, "2026-07-01", "US", "Organic Search", "Standard HD"))
        assignments_to_insert.append(("EXP_TIE", u_t, "treatment"))
        conv = 1 if i < 102 else 0
        outcomes_to_insert.append(("EXP_TIE", u_t, conv, conv, 0))

    # 3. EXP_SRM: 100 Control vs 900 Treatment (severe traffic bias)
    for i in range(100):
        u_c = f"U_SRM_C_{i}"
        users_to_insert.append((u_c, "2026-07-01", "US", "Organic Search", "Standard HD"))
        assignments_to_insert.append(("EXP_SRM", u_c, "control"))
        outcomes_to_insert.append(("EXP_SRM", u_c, 1, 1, 0))

    for i in range(900):
        u_t = f"U_SRM_T_{i}"
        users_to_insert.append((u_t, "2026-07-01", "US", "Organic Search", "Standard HD"))
        assignments_to_insert.append(("EXP_SRM", u_t, "treatment"))
        outcomes_to_insert.append(("EXP_SRM", u_t, 1, 1, 0))

    # Single bulk insert with single commit
    cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?)", users_to_insert)
    cursor.executemany("INSERT INTO experiment_assignments VALUES (?, ?, ?)", assignments_to_insert)
    cursor.executemany("INSERT INTO experiment_outcomes VALUES (?, ?, ?, ?, ?)", outcomes_to_insert)
    conn.commit()
    conn.close()

    return db_file


def test_experiment_win_recommendation(exp_test_db):
    """Verify that a statistically significant lift with healthy guardrails yields SHIP."""
    res = analyze_experiment("EXP_WIN", db_path=exp_test_db)
    assert res["recommendation"] == "SHIP"
    assert res["stat_significant"] is True
    assert res["conversion_rates"]["control_pct"] == 10.0
    assert res["conversion_rates"]["treatment_pct"] == 16.0
    assert res["absolute_difference_pp"] == 6.0
    assert res["relative_lift_pct"] == 60.0  # (16 - 10) / 10 = +60%
    assert res["p_value"] < 0.001
    assert res["srm_check"]["detected"] is False


def test_experiment_inconclusive_recommendation(exp_test_db):
    """Verify that an insignificant result yields CONTINUE TESTING."""
    res = analyze_experiment("EXP_TIE", db_path=exp_test_db)
    assert res["recommendation"] == "CONTINUE TESTING / INVESTIGATE"
    assert res["stat_significant"] is False
    assert res["p_value"] > 0.05
    # Confidence interval crosses 0
    ci = res["confidence_interval_95"]
    assert ci[0] < 0.0 < ci[1]


def test_sample_ratio_mismatch_detection(exp_test_db):
    """Verify that an unbalanced traffic allocation triggers SRM warning."""
    res = analyze_experiment("EXP_SRM", db_path=exp_test_db)
    assert res["srm_check"]["detected"] is True
    assert res["srm_check"]["p_value"] < 0.001
    assert res["recommendation"] == "CONTINUE TESTING / INVESTIGATE"
    assert "Sample Ratio Mismatch" in res["rationale"][0]


def test_zero_conversions_lift_handling(tmp_path):
    """Verify that 0 control conversion rate handles relative lift gracefully (N/A)."""
    db_file = tmp_path / "zero_conv.db"
    init_db(db_file)
    conn = get_connection(db_file)
    c = conn.cursor()
    c.execute("INSERT INTO experiments VALUES ('EXP_ZERO', 'Z', 'H', '2026-08-01', '2026-08-31', 'c', 'active')")
    c.execute("INSERT INTO users VALUES ('U1', '2026-08-01', 'US', 'Organic Search', 'Standard HD')")
    c.execute("INSERT INTO users VALUES ('U2', '2026-08-01', 'US', 'Organic Search', 'Standard HD')")
    c.execute("INSERT INTO experiment_assignments VALUES ('EXP_ZERO', 'U1', 'control'), ('EXP_ZERO', 'U2', 'treatment')")
    c.execute("INSERT INTO experiment_outcomes VALUES ('EXP_ZERO', 'U1', 0, 0, 0), ('EXP_ZERO', 'U2', 1, 1, 0)")
    conn.commit()
    conn.close()

    res = analyze_experiment("EXP_ZERO", db_path=db_file)
    assert res["conversion_rates"]["control_pct"] == 0.0
    assert res["conversion_rates"]["treatment_pct"] == 100.0
    assert res["relative_lift_pct"] is None
    assert "N/A" in res["relative_lift_str"]


def test_small_sample_and_non_normal_handling(tmp_path):
    """Verify that small samples trigger Fisher's Exact Test and Agresti-Caffo CI clamping."""
    db_file = tmp_path / "small_sample.db"
    init_db(db_file)
    conn = get_connection(db_file)
    c = conn.cursor()
    c.execute("INSERT INTO experiments VALUES ('EXP_SMALL', 'Small N', 'H', '2026-08-01', '2026-08-31', 'c', 'active')")
    # 5 users control (1 converted), 5 users treatment (4 converted)
    for i in range(5):
        u_c = f"UC_{i}"
        c.execute("INSERT INTO users VALUES (?, '2026-08-01', 'US', 'Organic Search', 'Standard HD')", (u_c,))
        c.execute("INSERT INTO experiment_assignments VALUES ('EXP_SMALL', ?, 'control')", (u_c,))
        c.execute("INSERT INTO experiment_outcomes VALUES ('EXP_SMALL', ?, ?, ?, 0)", (u_c, 1 if i == 0 else 0, 1 if i == 0 else 0))

        u_t = f"UT_{i}"
        c.execute("INSERT INTO users VALUES (?, '2026-08-01', 'US', 'Organic Search', 'Standard HD')", (u_t,))
        c.execute("INSERT INTO experiment_assignments VALUES ('EXP_SMALL', ?, 'treatment')", (u_t,))
        c.execute("INSERT INTO experiment_outcomes VALUES ('EXP_SMALL', ?, ?, ?, 0)", (u_t, 1 if i < 4 else 0, 1 if i < 4 else 0))

    conn.commit()
    conn.close()

    res = analyze_experiment("EXP_SMALL", db_path=db_file)
    assert res["normal_assumption_met"] is False
    assert res["ci_method"] == "Agresti-Caffo"
    # CI bounds must never exceed +/- 100%
    ci = res["confidence_interval_95"]
    assert -100.0 <= ci[0] <= 100.0
    assert -100.0 <= ci[1] <= 100.0
    assert res["fisher_exact_p_value"] > 0.0


def test_duplicate_assignments_detection(tmp_path):
    """Verify that users assigned to multiple variants trigger a telemetry alert and block SHIP."""
    db_file = tmp_path / "dup_assign.db"
    conn = get_connection(db_file)
    c = conn.cursor()
    # Create tables without compound primary key to simulate faulty upstream data
    c.execute("CREATE TABLE experiments (experiment_id TEXT, experiment_name TEXT, hypothesis TEXT, start_date TEXT, end_date TEXT, primary_metric TEXT, status TEXT)")
    c.execute("CREATE TABLE users (user_id TEXT, signup_date TEXT, country TEXT, acquisition_channel TEXT, subscription_plan TEXT)")
    c.execute("CREATE TABLE experiment_assignments (experiment_id TEXT, user_id TEXT, variant TEXT)")
    c.execute("CREATE TABLE experiment_outcomes (experiment_id TEXT, user_id TEXT, converted INT, playback_completed INT, playback_error INT)")

    c.execute("INSERT INTO experiments VALUES ('EXP_DUP', 'Dup Test', 'H', '2026-08-01', '2026-08-31', 'c', 'active')")
    c.execute("INSERT INTO users VALUES ('U1', '2026-08-01', 'US', 'Organic Search', 'Standard HD')")
    # U1 is assigned to BOTH control and treatment!
    c.execute("INSERT INTO experiment_assignments VALUES ('EXP_DUP', 'U1', 'control')")
    c.execute("INSERT INTO experiment_assignments VALUES ('EXP_DUP', 'U1', 'treatment')")
    c.execute("INSERT INTO experiment_outcomes VALUES ('EXP_DUP', 'U1', 1, 1, 0)")
    conn.commit()
    conn.close()

    res = analyze_experiment("EXP_DUP", db_path=db_file)
    assert res["duplicate_assignments_count"] == 1
    assert res["recommendation"] == "CONTINUE TESTING / INVESTIGATE"
    assert any("DATA INTEGRITY ALERT" in r for r in res["rationale"])


def test_practical_significance_mde_threshold(exp_test_db):
    """Verify that a statistically significant lift below MDE / practical threshold is flagged as practically insignificant."""
    # In EXP_WIN, lift is +6.0 pp (statistically significant, p < 0.001)
    # If the product team sets the minimum practical effect threshold to 10.0 pp:
    res = analyze_experiment("EXP_WIN", min_practical_effect_pp=10.0, db_path=exp_test_db)
    assert res["stat_significant"] is True
    assert res["practically_significant"] is False
    assert res["min_practical_effect_pp"] == 10.0
    assert res["recommendation"] == "CONTINUE TESTING / INVESTIGATE"
    assert any("minimum practical significance threshold" in r for r in res["rationale"])


def test_mde_threshold_blocks_ship_when_lift_is_below_threshold(exp_test_db):
    """Verify that an MDE threshold higher than the observed lift prevents premature SHIP."""
    # In EXP_WIN, lift is +6.0 pp (statistically significant, p < 0.001)
    # If the product team set MDE threshold to 8.0 pp:
    res = analyze_experiment("EXP_WIN", mde_threshold_pp=8.0, db_path=exp_test_db)
    assert res["stat_significant"] is True
    assert res["practically_significant"] is False
    assert res["recommendation"] == "CONTINUE TESTING / INVESTIGATE"
    assert any("minimum practical significance threshold" in r for r in res["rationale"])


def test_ship_decision_includes_generalization_caveat(exp_test_db):
    """Verify that when an experiment yields SHIP, a generalization caveat is documented."""
    res = analyze_experiment("EXP_WIN", mde_threshold_pp=0.5, db_path=exp_test_db)
    assert res["recommendation"] == "SHIP"
    assert any("Generalization Caveat" in r for r in res["rationale"])


def test_srm_custom_expected_allocation_ratio(exp_test_db):
    """Verify that SRM test respects custom expected allocation ratio (e.g., 10/90 canary split)."""
    # EXP_SRM has 100 Control and 900 Treatment (10% Control, 90% Treatment)
    # Default 50/50 expectation triggers SRM warning
    res_default = analyze_experiment("EXP_SRM", expected_control_share=0.5, db_path=exp_test_db)
    assert res_default["srm_check"]["detected"] is True
    assert res_default["srm_check"]["p_value"] < 0.001

    # Custom 10/90 expectation matches observed traffic exactly -> No SRM
    res_custom = analyze_experiment("EXP_SRM", expected_control_share=0.10, db_path=exp_test_db)
    assert res_custom["srm_check"]["detected"] is False
    assert res_custom["srm_check"]["p_value"] > 0.99
    assert res_custom["srm_check"]["expected_control_share"] == 0.10


