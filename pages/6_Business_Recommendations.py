"""StreamIQ - Business Recommendations and Executive Report Generator.

Converts calculated analytics into prioritized, actionable business initiatives
and generates downloadable executive briefings (Markdown) and underlying data (CSV).
"""

from __future__ import annotations

import streamlit as st

from src.database import ensure_database_ready
from src.recommendations import generate_business_recommendations
from src.reporting import export_recommendations_csv, generate_executive_markdown_report
from src.ui_helpers import (
    apply_custom_css,
    render_hero_header,
    render_simulated_data_badge,
    render_theme_selector,
    render_top_navbar,
)

st.set_page_config(page_title="Business Recommendations — StreamIQ", page_icon="📋", layout="wide")
apply_custom_css()
ensure_database_ready()
render_theme_selector()

# Top Brand Bar
render_top_navbar(
    brand_title="StreamIQ | Business Recommendations & Executive Briefing",
    date_display="Strategic Initiatives (2026)",
)

# Hero Header
render_hero_header(
    badge_text="STRATEGIC ROADMAPS",
    title="Business Recommendations & Executive Briefing",
    subtitle="Translate empirical behavioral findings into prioritized product roadmaps, define measurable guardrails, and generate executive briefing documents.",
)

render_simulated_data_badge()

# Generate calculated recommendations
recs = generate_business_recommendations()

if not recs:
    st.warning("Insufficient platform data to generate evidence-backed recommendations.")
    st.stop()

# Interactive Selection for Executive Report
st.subheader("1. Strategic Analytical Findings & Action Items")
st.markdown("Review the evidence-backed recommendations below and select which items to include in your Executive Briefing:")

selected_indices: list[int] = []

for idx, r in enumerate(recs):
    with st.container(border=True):
        include = st.checkbox(
            f"**[{r['category']}] {r['title']}**",
            value=True,
            key=f"rec_select_{idx}",
        )
        if include:
            selected_indices.append(idx)

        st.markdown(f"**Observed Finding**: {r['finding']}")
        st.markdown(f"**Supporting Evidence**: {r['supporting_evidence']}")
        st.markdown(f"**Business Significance**: {r['business_significance']}")
        st.markdown(f"**Possible Explanation (Hypothesis)**: {r['possible_explanations']}")
        st.markdown(f"**Recommended Next Step (Action)**: {r['recommended_next_step']}")

        c_succ, c_guard, c_limit = st.columns(3)
        with c_succ:
            st.info(f"🎯 **Success Metric**:\n\n{r['success_metric']}")
        with c_guard:
            st.warning(f"🛡️ **Guardrail Metric**:\n\n{r['guardrail_metric']}")
        with c_limit:
            st.caption(f"⚠️ **Limitations**:\n\n{r['limitations']}")

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# Section 2: Executive Report Generator & Export Center
st.subheader("2. Executive Report Export Center")
st.markdown("Generate a tailored briefing document containing your selected findings, headline KPIs, and methodological disclosures.")

# Generate markdown report
markdown_report = generate_executive_markdown_report(selected_recommendation_indices=selected_indices)
df_recs_csv = export_recommendations_csv()

tab_preview, tab_raw_md, tab_raw_csv = st.tabs(["Briefing Preview", "Markdown Source", "Tabular CSV Data"])

with tab_preview:
    st.markdown(markdown_report)

with tab_raw_md:
    st.code(markdown_report, language="markdown")

with tab_raw_csv:
    st.dataframe(df_recs_csv, use_container_width=True)

# Download Action Buttons
st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
st.markdown("##### Download Artifacts")
col_d1, col_d2 = st.columns(2)

with col_d1:
    st.download_button(
        label="📥 Download Executive Briefing (.md)",
        data=markdown_report,
        file_name="StreamIQ_Executive_Briefing.md",
        mime="text/markdown",
        use_container_width=True,
    )

with col_d2:
    csv_bytes = df_recs_csv.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Underlying Recommendations (.csv)",
        data=csv_bytes,
        file_name="StreamIQ_Business_Recommendations.csv",
        mime="text/csv",
        use_container_width=True,
    )
