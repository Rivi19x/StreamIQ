"""A/B Testing and experimentation analytics module for StreamIQ.

Implements rigorous statistical hypothesis testing:
- Two-proportion z-test with pooled variance
- Absolute difference and relative lift calculations
- 95% Wald confidence intervals with zero-division safety
- Sample Ratio Mismatch (SRM) checks via Pearson Chi-Square test
- Secondary guardrail metric analysis (playback completion and error rates)
- Transparent 3-tier recommendation engine: SHIP, DO NOT SHIP, CONTINUE TESTING / INVESTIGATE
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from src.database import execute_query, get_db_path


def get_all_experiments(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Fetch list of all seeded experiments."""
    sql = "SELECT * FROM experiments ORDER BY start_date DESC"
    df = execute_query(sql, db_path=db_path)
    return df.to_dict(orient="records") if not df.empty else []


def analyze_experiment(
    experiment_id: str,
    alpha: float = 0.05,
    mde_threshold_pp: float = 0.5,
    min_practical_effect_pp: float | None = None,
    expected_control_share: float = 0.5,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Perform complete statistical evaluation for an A/B experiment.

    Calculates:
    - Variant user sizes and conversions
    - Conversion rates, absolute difference, and relative lift
    - Normal approximation validity check (min expected cell count >= 5)
    - Two-sided z-test p-value (or Fisher's exact test fallback)
    - 95% Confidence interval (Wald or Agresti-Caffo for small samples, clamped to [-100%, +100%])
    - Sample ratio mismatch (SRM) check via Pearson Chi-Square test with customizable expected split
    - Guardrail metrics (playback completion and error rates)
    - Statistical vs practical significance evaluation (Minimum Practical Effect Threshold)
      Note: min_practical_effect_pp (or mde_threshold_pp) is a business launch hurdle to justify
      operational rollout complexity, not a pre-experiment statistical power calculation.
    - Telemetry integrity validation (duplicate and unassigned user detection)
    - Decision recommendation with transparent rationale and generalization caveats
    """
    # 1. Fetch experiment metadata
    sql_meta = "SELECT * FROM experiments WHERE experiment_id = ?"
    df_meta = execute_query(sql_meta, (experiment_id,), db_path=db_path)
    if df_meta.empty:
        raise ValueError(f"Experiment '{experiment_id}' not found.")
    meta = df_meta.iloc[0].to_dict()

    # 2. Telemetry and Data Integrity Validation
    # Check for duplicate variant assignments (a user assigned to multiple variants)
    sql_dup = """
        SELECT COUNT(*) AS dup_count FROM (
            SELECT user_id
            FROM experiment_assignments
            WHERE experiment_id = ?
            GROUP BY user_id
            HAVING COUNT(DISTINCT variant) > 1
        )
    """
    df_dup = execute_query(sql_dup, (experiment_id,), db_path=db_path)
    dup_count = int(df_dup.iloc[0]["dup_count"]) if not df_dup.empty else 0

    # Check for unassigned outcomes (outcomes logged without assignment)
    sql_unassigned = """
        SELECT COUNT(*) AS unassigned_count
        FROM experiment_outcomes o
        LEFT JOIN experiment_assignments a
          ON o.experiment_id = a.experiment_id AND o.user_id = a.user_id
        WHERE o.experiment_id = ? AND a.variant IS NULL
    """
    df_unassigned = execute_query(sql_unassigned, (experiment_id,), db_path=db_path)
    unassigned_count = int(df_unassigned.iloc[0]["unassigned_count"]) if not df_unassigned.empty else 0

    # 3. Fetch assignments and outcomes
    sql_data = """
        SELECT
            a.variant,
            COUNT(DISTINCT a.user_id) AS total_users,
            SUM(COALESCE(o.converted, 0)) AS conversions,
            SUM(COALESCE(o.playback_completed, 0)) AS completed_playbacks,
            SUM(COALESCE(o.playback_error, 0)) AS playback_errors
        FROM experiment_assignments a
        LEFT JOIN experiment_outcomes o
          ON a.experiment_id = o.experiment_id AND a.user_id = o.user_id
        WHERE a.experiment_id = ?
        GROUP BY a.variant
    """
    df_data = execute_query(sql_data, (experiment_id,), db_path=db_path)

    # Populate control & treatment stats
    variant_stats: dict[str, dict[str, int]] = {
        "control": {"users": 0, "conversions": 0, "completed": 0, "errors": 0},
        "treatment": {"users": 0, "conversions": 0, "completed": 0, "errors": 0},
    }
    for _, row in df_data.iterrows():
        v = row["variant"]
        if v in variant_stats:
            variant_stats[v] = {
                "users": int(row["total_users"] or 0),
                "conversions": int(row["conversions"] or 0),
                "completed": int(row["completed_playbacks"] or 0),
                "errors": int(row["playback_errors"] or 0),
            }

    ctrl = variant_stats["control"]
    trt = variant_stats["treatment"]

    n_c, x_c = ctrl["users"], ctrl["conversions"]
    n_t, x_t = trt["users"], trt["conversions"]

    # 4. Sample Ratio Mismatch (SRM) check
    total_assigned = n_c + n_t
    if total_assigned > 0:
        expected = [
            total_assigned * expected_control_share,
            total_assigned * (1.0 - expected_control_share),
        ]
        observed = [n_c, n_t]
        srm_stat, srm_p_value = stats.chisquare(f_obs=observed, f_exp=expected)
        srm_detected = bool(srm_p_value < 0.01)  # conservative standard threshold for SRM
    else:
        srm_stat, srm_p_value, srm_detected = 0.0, 1.0, False

    # 5. Conversion Rates & Effect Sizes
    p_c = (x_c / n_c) if n_c > 0 else 0.0
    p_t = (x_t / n_t) if n_t > 0 else 0.0
    diff_abs = p_t - p_c  # absolute difference in proportion
    diff_abs_pp = diff_abs * 100.0  # percentage points

    # Relative Lift
    if p_c > 0:
        rel_lift_pct = (diff_abs / p_c) * 100.0
        rel_lift_str = f"{rel_lift_pct:+.2f}%"
    else:
        rel_lift_pct = None
        rel_lift_str = "N/A (Control rate is 0)"

    # 6. Statistical Hypothesis Testing & Assumption Verification
    # Check normal approximation criteria: n*p >= 5 and n*(1-p) >= 5 for both groups
    normal_assumption_met = bool(
        n_c > 0 and n_t > 0
        and (n_c * p_c) >= 5.0
        and (n_c * (1.0 - p_c)) >= 5.0
        and (n_t * p_t) >= 5.0
        and (n_t * (1.0 - p_t)) >= 5.0
    )

    # Standard Two-Proportion Z-Test
    if n_c > 0 and n_t > 0 and 0 < (x_c + x_t) < (n_c + n_t):
        p_pool = (x_c + x_t) / (n_c + n_t)
        se_pool = math.sqrt(p_pool * (1.0 - p_pool) * ((1.0 / n_c) + (1.0 / n_t)))
        z_stat = diff_abs / se_pool if se_pool > 0 else 0.0
        z_p_value = float(2.0 * stats.norm.sf(abs(z_stat)))
    else:
        z_stat, z_p_value = 0.0, 1.0

    # Fisher's Exact Test (ideal for small samples or violated normal approximations)
    if n_c > 0 and n_t > 0:
        table = [[x_t, n_t - x_t], [x_c, n_c - x_c]]
        _, fisher_p_val = stats.fisher_exact(table)
        fisher_p_value = float(fisher_p_val)
    else:
        fisher_p_value = 1.0

    # Select operational p-value
    if normal_assumption_met:
        p_value = z_p_value
        test_method = "Two-Proportion Z-Test (Pooled)"
    else:
        p_value = fisher_p_value
        test_method = "Fisher's Exact Test (Small Sample / Non-Normal)"

    practical_hurdle_pp = min_practical_effect_pp if min_practical_effect_pp is not None else mde_threshold_pp
    stat_significant = bool(p_value < alpha)
    practically_significant = bool(diff_abs_pp >= practical_hurdle_pp)

    # Confidence Interval Calculation
    z_crit = stats.norm.ppf(1.0 - (alpha / 2.0))
    if normal_assumption_met and n_c > 0 and n_t > 0:
        # Standard Wald interval
        se_diff = math.sqrt((p_c * (1.0 - p_c) / n_c) + (p_t * (1.0 - p_t) / n_t))
        raw_ci_lower = diff_abs - (z_crit * se_diff)
        raw_ci_upper = diff_abs + (z_crit * se_diff)
        ci_method = "Wald"
    elif n_c > 0 and n_t > 0:
        # Agresti-Caffo interval (robust for small samples / extreme proportions)
        n_c_adj, x_c_adj = n_c + 2, x_c + 1
        n_t_adj, x_t_adj = n_t + 2, x_t + 1
        p_c_adj = x_c_adj / n_c_adj
        p_t_adj = x_t_adj / n_t_adj
        diff_adj = p_t_adj - p_c_adj
        se_adj = math.sqrt((p_c_adj * (1.0 - p_c_adj) / n_c_adj) + (p_t_adj * (1.0 - p_t_adj) / n_t_adj))
        raw_ci_lower = diff_adj - (z_crit * se_adj)
        raw_ci_upper = diff_adj + (z_crit * se_adj)
        ci_method = "Agresti-Caffo"
    else:
        raw_ci_lower, raw_ci_upper = 0.0, 0.0
        ci_method = "None"

    # Strictly clamp confidence intervals to valid percentage point bounds [-100%, +100%]
    ci_lower = max(-1.0, min(1.0, raw_ci_lower))
    ci_upper = max(-1.0, min(1.0, raw_ci_upper))

    # 7. Guardrail Metrics
    # Guardrail A: Playback Completion Rate among converted users
    comp_c_rate = (ctrl["completed"] / x_c * 100.0) if x_c > 0 else 0.0
    comp_t_rate = (trt["completed"] / x_t * 100.0) if x_t > 0 else 0.0
    comp_diff = comp_t_rate - comp_c_rate

    # Guardrail B: Playback Error Rate among all assigned users
    err_c_rate = (ctrl["errors"] / n_c * 100.0) if n_c > 0 else 0.0
    err_t_rate = (trt["errors"] / n_t * 100.0) if n_t > 0 else 0.0
    err_diff = err_t_rate - err_c_rate

    guardrails_healthy = bool((err_diff <= 0.5) and (comp_diff >= -3.0))

    # 8. Recommendation Engine with Rigorous Decision Logic
    rationale_points: list[str] = []

    if srm_detected:
        recommendation = "CONTINUE TESTING / INVESTIGATE"
        verdict_color = "warning"
        rationale_points.append(
            f"CRITICAL: Sample Ratio Mismatch (SRM) detected (Chi-square p = {srm_p_value:.4f} < 0.01). "
            "Traffic allocation is biased; results may be invalid. Investigate assignment telemetry."
        )
    elif dup_count > 0 or unassigned_count > 0:
        recommendation = "CONTINUE TESTING / INVESTIGATE"
        verdict_color = "warning"

    if dup_count > 0:
        rationale_points.append(
            f"DATA INTEGRITY ALERT: {dup_count} user(s) were assigned to multiple variants in this experiment. Assignment telemetry must be audited."
        )
    if unassigned_count > 0:
        rationale_points.append(
            f"DATA INTEGRITY ALERT: {unassigned_count} outcome record(s) have no corresponding assignment record."
        )

    if not normal_assumption_met and total_assigned > 0:
        rationale_points.append(
            f"Methodology Note: Minimum cell count criterion (< 5 expected conversions) violated for normal approximation. "
            f"Evaluated using {test_method} (p = {p_value:.4f}) and {ci_method} 95% confidence interval."
        )

    if srm_detected or dup_count > 0 or unassigned_count > 0:
        pass  # Handled above
    elif stat_significant and diff_abs > 0 and guardrails_healthy:
        if practically_significant:
            recommendation = "SHIP"
            verdict_color = "success"
            rationale_points.append(
                f"Statistically significant primary metric improvement detected ({test_method}, p = {p_value:.4f} < {alpha})."
            )
            rationale_points.append(
                f"Absolute lift is {diff_abs_pp:+.2f} pp (95% CI: [{ci_lower * 100:+.2f} pp, {ci_upper * 100:+.2f} pp]), "
                f"representing {rel_lift_str} relative lift (exceeds practical significance threshold of {practical_hurdle_pp:.2f} pp)."
            )
            rationale_points.append(
                f"Guardrails confirmed healthy: Error rate delta is {err_diff:+.2f} pp, and completion rate delta is {comp_diff:+.2f} pp."
            )
            rationale_points.append(
                "Generalization Caveat: Findings reflect the specific test cohort, seasonality, and assignment distribution during the experiment window. "
                "Post-launch metrics must be monitored for novel bias, user fatigue, or catalog cannibalization."
            )
        else:
            recommendation = "CONTINUE TESTING / INVESTIGATE"
            verdict_color = "warning"
            rationale_points.append(
                f"Statistical significance was reached ({test_method}, p = {p_value:.4f} < {alpha}), "
                f"but absolute lift ({diff_abs_pp:+.2f} pp) is below the minimum practical significance threshold ({practical_hurdle_pp:.2f} pp)."
            )
            rationale_points.append(
                "Recommendation: The effect size may be too small to justify rollout complexity and maintenance cost. Re-evaluate ROI."
            )
    elif stat_significant and diff_abs < 0:
        recommendation = "DO NOT SHIP"
        verdict_color = "danger"
        rationale_points.append(
            f"Treatment performed significantly worse than Control ({test_method}, p = {p_value:.4f} < {alpha}, "
            f"lift: {diff_abs_pp:+.2f} pp)."
        )
        rationale_points.append("Deploying this feature would hurt user conversion.")
    elif not guardrails_healthy:
        recommendation = "DO NOT SHIP"
        verdict_color = "danger"
        rationale_points.append(
            f"Guardrail metric breach: Error rate increased by {err_diff:+.2f} pp or playback completion dropped by {comp_diff:+.2f} pp."
        )
    else:
        recommendation = "CONTINUE TESTING / INVESTIGATE"
        verdict_color = "neutral"
        rationale_points.append(
            f"Results are inconclusive: Difference is not statistically significant ({test_method}, p = {p_value:.4f} >= {alpha})."
        )
        rationale_points.append(
            f"The 95% confidence interval spans across zero: [{ci_lower * 100:+.2f} pp, {ci_upper * 100:+.2f} pp]."
        )
        rationale_points.append(
            "Do not ship yet. Continue collecting observations to reach adequate statistical power, or iterate on the hypothesis."
        )

    return {
        "metadata": meta,
        "sample_sizes": {"control": n_c, "treatment": n_t, "total": total_assigned},
        "conversions": {"control": x_c, "treatment": x_t},
        "conversion_rates": {
            "control_pct": round(p_c * 100.0, 2),
            "treatment_pct": round(p_t * 100.0, 2),
        },
        "absolute_difference_pp": round(diff_abs_pp, 2),
        "relative_lift_pct": round(rel_lift_pct, 2) if rel_lift_pct is not None else None,
        "relative_lift_str": rel_lift_str,
        "confidence_interval_95": (round(ci_lower * 100.0, 2), round(ci_upper * 100.0, 2)),
        "ci_method": ci_method,
        "z_statistic": round(z_stat, 3),
        "p_value": round(p_value, 5),
        "fisher_exact_p_value": round(fisher_p_value, 5),
        "normal_assumption_met": normal_assumption_met,
        "stat_significant": stat_significant,
        "practically_significant": practically_significant,
        "min_practical_effect_pp": practical_hurdle_pp,
        "mde_threshold_pp": practical_hurdle_pp,
        "expected_control_share": expected_control_share,
        "duplicate_assignments_count": dup_count,
        "unassigned_outcomes_count": unassigned_count,
        "srm_check": {
            "detected": srm_detected,
            "chi2_stat": round(srm_stat, 3),
            "p_value": round(srm_p_value, 4),
            "expected_control_share": expected_control_share,
        },
        "guardrails": {
            "completion_rate": {
                "control_pct": round(comp_c_rate, 2),
                "treatment_pct": round(comp_t_rate, 2),
                "delta_pp": round(comp_diff, 2),
            },
            "error_rate": {
                "control_pct": round(err_c_rate, 2),
                "treatment_pct": round(err_t_rate, 2),
                "delta_pp": round(err_diff, 2),
            },
            "healthy": guardrails_healthy,
        },
        "recommendation": recommendation,
        "verdict_color": verdict_color,
        "rationale": rationale_points,
    }
