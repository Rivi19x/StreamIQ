"""Executive reporting module for StreamIQ.

Generates downloadable executive Markdown briefings and CSV data exports
for leadership, product management, and stakeholder reviews.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import pandas as pd

from src.analytics import get_executive_kpis, get_genre_popularity, get_segment_summary
from src.experimentation import analyze_experiment, get_all_experiments
from src.funnel import calculate_funnel
from src.recommendations import generate_business_recommendations
from src.retention import get_retention_overview


def generate_executive_markdown_report(
    selected_recommendation_indices: list[int] | None = None,
    db_path: str | Path | None = None,
) -> str:
    """Generate a comprehensive executive briefing in Markdown format."""
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Fetch data
    kpis = get_executive_kpis(db_path=db_path)
    ret = get_retention_overview(db_path=db_path)
    funnel = calculate_funnel(db_path=db_path)
    genres = get_genre_popularity(db_path=db_path)
    segments = get_segment_summary(db_path=db_path)
    recs = generate_business_recommendations(db_path=db_path)

    # Filter recommendations if specified
    if selected_recommendation_indices is not None and recs:
        recs = [recs[i] for i in selected_recommendation_indices if 0 <= i < len(recs)]

    # Fetch A/B Experiments summary
    exp_summary_blocks = []
    for exp in get_all_experiments(db_path=db_path):
        try:
            res = analyze_experiment(exp["experiment_id"], db_path=db_path)
            exp_summary_blocks.append(
                f"- **{exp['experiment_name']} ({exp['experiment_id']})**\n"
                f"  - Primary Metric: `{exp['primary_metric']}` | Status: `{exp['status']}`\n"
                f"  - Control: {res['conversion_rates']['control_pct']}% (n={res['sample_sizes']['control']:,}) | "
                f"Treatment: {res['conversion_rates']['treatment_pct']}% (n={res['sample_sizes']['treatment']:,})\n"
                f"  - Absolute Lift: **{res['absolute_difference_pp']:+.2f} pp** ({res['relative_lift_str']})\n"
                f"  - 95% Confidence Interval: `[{res['confidence_interval_95'][0]:+.2f} pp, {res['confidence_interval_95'][1]:+.2f} pp]` | p-value: `{res['p_value']:.4f}`\n"
                f"  - **Decision Verdict**: `{res['recommendation']}`\n"
            )
        except Exception as e:
            exp_summary_blocks.append(
                f"- **{exp['experiment_name']} ({exp['experiment_id']})**: Evaluation error ({str(e)})\n"
            )

    exp_text = "\n".join(exp_summary_blocks) if exp_summary_blocks else "No experiments currently evaluated."

    # Top genres summary
    top_genres_text = ""
    if not genres.empty:
        top_3 = genres.head(3)
        genre_lines = [
            f"1. **{row['genre']}**: {int(row['playback_starts']):,} starts ({row['completion_rate_pct']}% completion rate)"
            for _, row in top_3.iterrows()
        ]
        top_genres_text = "\n".join(genre_lines)

    # User segments summary
    segments_text = ""
    if not segments.empty:
        seg_lines = [
            f"- **{row['user_segment']}**: {int(row['user_count']):,} users ({row['user_share_pct']}%) | Avg {row['avg_sessions']} sessions"
            for _, row in segments.iterrows()
        ]
        segments_text = "\n".join(seg_lines)

    # Build recommendations markdown
    recs_text = ""
    for idx, r in enumerate(recs, start=1):
        recs_text += f"""
### Recommendation {idx}: {r['title']}
* **Category**: {r['category']}
* **Finding**: {r['finding']}
* **Supporting Evidence**: {r['supporting_evidence']}
* **Business Significance**: {r['business_significance']}
* **Possible Explanations to Investigate**: {r['possible_explanations']}
* **Recommended Next Step**: {r['recommended_next_step']}
* **Success Metric**: `{r['success_metric']}`
* **Guardrail Metric**: `{r['guardrail_metric']}`
* **Limitations**: {r['limitations']}
"""

    report = f"""# StreamIQ Executive Product Analytics Briefing

**Generated On**: {now_str}  
**Data Environment**: Synthetic Simulation Engine (Reproducible Seed)  
**Notice**: *All user, session, and experiment activities are simulated for portfolio and demonstration purposes. No real user data or external streaming platform data is utilized.*

---

## 1. Executive Summary & Core Platform KPIs

| Metric | Current Value | Definition & Notes |
| :--- | :--- | :--- |
| **Total Registered Users** | **{kpis['total_registered_users']:,}** | Cumulative user registrations in platform database |
| **Active Users** | **{kpis['active_users']:,}** | Distinct users with qualifying events in current scope |
| **Sessions per Active User** | **{kpis['sessions_per_active_user']:.2f}** | Total distinct sessions divided by active users |
| **Playback Completion Rate** | **{kpis['playback_completion_rate']:.1f}%** | Completed streams divided by eligible playback starts |
| **Day 1 Retention** | **{ret['d1']['retention_rate_pct']:.1f}%** | Re-engagement exactly 1 calendar day post-registration (n={ret['d1']['eligible_cohort_size']:,}) |
| **Day 7 Retention** | **{ret['d7']['retention_rate_pct']:.1f}%** | Re-engagement exactly 7 calendar days post-registration (n={ret['d7']['eligible_cohort_size']:,}) |
| **Day 30 Retention** | **{ret['d30']['retention_rate_pct']:.1f}%** | Re-engagement exactly 30 calendar days post-registration (n={ret['d30']['eligible_cohort_size']:,}) |

---

## 2. Onboarding & Playback Funnel Health

* **Registration to Playback Conversion**: **{funnel.get('overall_conversion_pct', 0.0):.1f}%**
* **Primary Bottleneck**: {funnel.get('bottleneck', {}).get('stage_name', 'None')}
* **Bottleneck Loss**: {funnel.get('bottleneck', {}).get('users_lost', 0):,} users ({funnel.get('bottleneck', {}).get('drop_off_pct', 0.0):.1f}% stage drop-off)
* **Funnel Diagnostics**: {funnel.get('recommendation', 'Healthy conversion sequence.')}

---

## 3. Content & Audience Dynamics

### Top 3 Content Genres by Playback Volume
{top_genres_text}

### Audience Segment Distribution
{segments_text}

---

## 4. Controlled A/B Experimentation Outcomes

{exp_text}

---

## 5. Strategic Product & Business Recommendations

{recs_text}

---

## 6. Analytical Methodology & Limitations
- **Cohort Observation Windows**: Retention metrics strictly exclude cohorts whose observation periods have not yet fully elapsed, ensuring no artificial churn bias.
- **Statistical Testing**: A/B comparisons utilize two-proportion z-tests with pooled variance and Wald 95% confidence intervals; Sample Ratio Mismatch (SRM) checks enforce 50/50 traffic validity.
- **Simulation Transparency**: All behaviors reflect synthetic behavioral models designed to emulate streaming consumption dynamics.
"""
    return report.strip()


def export_recommendations_csv(db_path: str | Path | None = None) -> pd.DataFrame:
    """Generate a clean pandas DataFrame of all current business recommendations."""
    recs = generate_business_recommendations(db_path=db_path)
    return pd.DataFrame(recs)
