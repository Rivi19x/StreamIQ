"""StreamIQ - A/B Testing Lab.

Evaluates controlled product experiments with two-proportion z-tests,
sample ratio mismatch (SRM) checks, confidence intervals, and guardrail metrics.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from src.database import ensure_database_ready, execute_query
from src.experimentation import analyze_experiment
from src.ui_helpers import (
    apply_custom_css,
    apply_plotly_theme,
    render_guardrails_table,
    render_hero_header,
    render_kpi_card,
    render_simulated_data_badge,
    render_theme_selector,
    render_top_navbar,
    render_traffic_split_card,
)

st.set_page_config(page_title="A/B Testing Lab — StreamIQ", page_icon="🧪", layout="wide")
apply_custom_css()
ensure_database_ready()

# Top Brand Bar
render_top_navbar(
    brand_title="StreamIQ | A/B Testing & Experimentation Governance",
    date_display="Experiment Governance (2026)",
)

# Hero Header
render_hero_header(
    badge_text="STATISTICAL GOVERNANCE",
    title="A/B Testing & Experimentation Governance",
    subtitle="Evaluate product experiments with two-proportion hypothesis tests, verify sample ratio matching (SRM), inspect 95% confidence intervals, and enforce quality guardrails before rollout.",
)

render_simulated_data_badge()

# Sidebar: Experiment Selector
render_theme_selector()
st.sidebar.header("Experiment Selector")
df_exps = execute_query("SELECT experiment_id, experiment_name, hypothesis FROM experiments ORDER BY experiment_id")
exp_map = dict(zip(df_exps["experiment_name"], df_exps["experiment_id"]))
selected_name = st.sidebar.selectbox("Active Experiments", list(exp_map.keys()))
exp_id = exp_map[selected_name]

# Run Statistical Analysis
res = analyze_experiment(exp_id)

# Experiment Overview Card
meta = res.get("metadata", {})
exp_display_name = meta.get('experiment_name', selected_name)
exp_display_id = meta.get('experiment_id', exp_id)
exp_hypothesis = meta.get('hypothesis', 'N/A')

overview_html = (
    '<div class="analytics-card">'
    '<div class="analytics-card-header">'
    f'<h3 class="analytics-card-title">🧪 {exp_display_name}</h3>'
    f'<span class="hero-badge" style="margin-bottom:0;">TEST ID: {exp_display_id}</span>'
    '</div>'
    f'<div style="font-size:0.95rem; color:var(--text-muted); line-height:1.5;">'
    f'<strong style="color:var(--text-main);">Product Hypothesis:</strong> {exp_hypothesis}'
    '</div>'
    '</div>'
)
if hasattr(st, "html"):
    st.html(overview_html)
else:
    st.markdown(overview_html, unsafe_allow_html=True)

# Automated Decision Banner
rec = res["recommendation"]
if rec == "SHIP":
    badge_html = '<span style="background:#EBF5EE; color:#397653; padding:4px 12px; border-radius:6px; font-weight:700; font-size:0.80rem; border:1px solid #C4E2CF;">🚀 DECISION: SHIP TO PRODUCTION</span>'
    border_color = '#397653'
elif rec == "DO NOT SHIP":
    badge_html = '<span style="background:#FDF2F4; color:#B54747; padding:4px 12px; border-radius:6px; font-weight:700; font-size:0.80rem; border:1px solid #F7D2DB;">⛔ DECISION: DO NOT SHIP</span>'
    border_color = '#B54747'
else:
    badge_html = '<span style="background:#FEF9EE; color:#A66B19; padding:4px 12px; border-radius:6px; font-weight:700; font-size:0.80rem; border:1px solid #F5E5C9;">⚠️ DECISION: CONTINUE TESTING / INVESTIGATE</span>'
    border_color = '#A66B19'

rationale_items = "".join(f"<li>{point}</li>" for point in res['rationale'])
decision_html = (
    f'<div class="analytics-card" style="border-left: 4px solid {border_color};">'
    f'<div style="margin-bottom:12px;">{badge_html}</div>'
    '<div style="font-size:0.95rem; font-weight:700; color:var(--text-main); margin-bottom:8px;">Evaluation Rationale:</div>'
    f'<ul style="margin:0; padding-left:20px; color:var(--text-muted); line-height:1.6; font-size:0.9rem;">{rationale_items}</ul>'
    '</div>'
)
if hasattr(st, "html"):
    st.html(decision_html)
else:
    st.markdown(decision_html, unsafe_allow_html=True)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# Statistical Results Grid (Un-truncated labels, circled ⓘ tooltips)
st.subheader("1. Primary Metric Results")

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi_card(
        label="Control Conversion",
        value=f"{res['conversion_rates']['control_pct']:.2f}%",
        info_text="Conversion rate for the baseline experience (Group A). Baseline against which the experimental treatment variant is evaluated.",
        subtext=f"n = {res['sample_sizes']['control']:,} viewers",
    )
with c2:
    render_kpi_card(
        label="Treatment Conversion",
        value=f"{res['conversion_rates']['treatment_pct']:.2f}%",
        info_text="Conversion rate for the experimental variant (Group B). Introduced feature or flow tested against baseline.",
        subtext=f"n = {res['sample_sizes']['treatment']:,} viewers",
    )
with c3:
    lift_val = res['absolute_difference_pp']
    lift_delta_color = "normal" if lift_val > 0 else ("inverse" if lift_val < 0 else "off")
    render_kpi_card(
        label="Estimated Lift",
        value=f"{lift_val:+.2f} pp",
        info_text="Absolute Lift: Difference in percentage points (Treatment − Control). Relative Lift: Percent change over baseline ((Treatment − Control) / Control).",
        delta=f"Rel: {res['relative_lift_str']}",
        delta_color=lift_delta_color,
        subtext=f"Treatment vs Control",
        card_style="sage" if lift_val > 0 else ("pink" if lift_val < 0 else "white"),
    )
with c4:
    sig_label = "Statistically Significant" if res["stat_significant"] else "Not Significant"
    sig_delta_color = "normal" if res["stat_significant"] else "off"
    render_kpi_card(
        label="Evidence of Effect (P-Value)",
        value=f"{res['p_value']:.4f}",
        info_text="Two-sided z-test p-value. Evidence against the null hypothesis that both conversion rates are identical. A p-value < 0.05 indicates the observed difference is unlikely under the null hypothesis (it does not mean there is a 95% probability the feature worked).",
        delta=sig_label,
        delta_color=sig_delta_color,
        subtext="Threshold: alpha = 0.05",
        card_style="blue" if res["stat_significant"] else "white",
    )

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# Confidence Interval Chart
ci = res["confidence_interval_95"]
diff_pp = res["absolute_difference_pp"]

fig_ci = go.Figure()
# Add reference zero line
fig_ci.add_vline(x=0, line_dash="dash", line_color="#8491A3")
# Add error bar
fig_ci.add_trace(go.Scatter(
    x=[diff_pp],
    y=["Difference (Treatment − Control)"],
    error_x=dict(
        type="data",
        symmetric=False,
        array=[ci[1] - diff_pp],
        arrayminus=[diff_pp - ci[0]],
        color="#3A4781",
        thickness=2.5,
        width=12,
    ),
    mode="markers",
    marker=dict(color="#A92F59", size=12),
    name="Point Estimate (95% CI)",
))
apply_plotly_theme(fig_ci)
fig_ci.update_layout(
    xaxis_title="Conversion Rate Difference (Percentage Points)",
    yaxis_title="",
    height=200,
    margin=dict(l=20, r=20, t=20, b=20),
)
st.plotly_chart(fig_ci, use_container_width=True)
st.caption(f"Estimated difference: **{diff_pp:+.2f} pp** with 95% Confidence Interval: **[{ci[0]:+.2f} pp, {ci[1]:+.2f} pp]**.")

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Secondary & Guardrail Diagnostics Row
st.subheader("2. Traffic Split Verification & Quality Safeguards")
col_srm, col_guard = st.columns(2)

expected_ctrl_share = res.get("expected_control_share", 0.5)
expected_split_str = f"{expected_ctrl_share * 100:.0f}/{(1.0 - expected_ctrl_share) * 100:.0f}"

with col_srm:
    st.markdown("##### Traffic Split Check (Sample Ratio Mismatch)")
    st.caption("Verifies whether user randomization was balanced according to the expected assignment ratio.")
    render_traffic_split_card(
        srm=res["srm_check"],
        sample_sizes=res["sample_sizes"],
        expected_split_str=expected_split_str,
    )

with col_guard:
    st.markdown("##### Guardrail Safeguards")
    st.caption("Quality safeguards ensuring primary metric improvements do not degrade catalog completion or increase streaming errors.")
    guard = res["guardrails"]
    render_guardrails_table(
        comp=guard["completion_rate"],
        err=guard["error_rate"],
    )

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Methodology Reference
with st.expander("Statistical Methodology"):
    st.markdown(r"""
    1. **Hypothesis Testing**: Two-sided two-proportion $z$-test with the null hypothesis that treatment and control conversion rates are equal ($H_0: p_t = p_c$). A $p$-value below $0.05$ provides evidence against the null hypothesis; it does not indicate a 95% probability that the feature worked.
    2. **Confidence Interval**: 95% confidence interval for the difference between two proportions:
       $$CI = (\hat{p}_t - \hat{p}_c) \pm 1.96 \cdot \sqrt{\frac{\hat{p}_c(1-\hat{p}_c)}{n_c} + \frac{\hat{p}_t(1-\hat{p}_t)}{n_t}}$$
    3. **SRM Check**: Pearson's Chi-square goodness-of-fit test with 1 degree of freedom comparing observed allocation counts against theoretical expected allocations.
    4. **Decision Matrix**:
       - **SHIP**: Statistically significant positive lift, healthy SRM, and no guardrail regressions.
       - **DO NOT SHIP**: Statistically significant negative lift or severe guardrail failure.
       - **CONTINUE TESTING**: Inconclusive results or detected sample ratio mismatch.
    """)
