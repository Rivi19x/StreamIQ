"""UI styling and shared component helpers for StreamIQ Streamlit application.

Implements the warm pastel clay/cream dashboard design system:
- Soft warm ivory/cream background with pitch-dark floating sidebar.
- 5 signature pastel metric cards (Yellow, Pink, Green, Blue, Violet).
- Professional breadcrumb and status header bar.
- Standardized container radius (12px) and button/input radius (8px).
- Theme-aware Plotly data visualization styling.
- Complete Light and Dark theme support.
"""

from __future__ import annotations

import html
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio

# Set base Plotly template
pio.templates.default = "plotly_white"

# Backward compatibility color constants
THEME_COLOR_PRIMARY = "#18181B"
THEME_COLOR_SECONDARY = "#0284C7"
THEME_COLOR_ACCENT = "#65A30D"
THEME_COLOR_WARNING = "#EAB308"
THEME_COLOR_VIOLET = "#8B5CF6"
THEME_COLOR_DANGER = "#EC4899"
THEME_COLOR_SURFACE = "#FAF7F0"
THEME_COLOR_CARD = "#FFFFFF"
THEME_COLOR_TEXT_MAIN = "#18181B"
THEME_COLOR_TEXT_MUTED = "#71717A"

GLASS_PALETTE = {
    "blue": "#B7D5F7",
    "yellow": "#FDE89C",
    "pink": "#FCD5E5",
    "green": "#C7D99E",
    "violet": "#E2D4F0",
    "amber": "#FDE89C",
    "rose": "#FCD5E5",
    "slate": "#71717A",
}


def render_theme_selector() -> str:
    """Render a sleek theme switcher in the sidebar and return 'light' or 'dark'."""
    current = st.session_state.get("app_theme_radio") or st.session_state.get("app_theme", "Light Theme")
    st.session_state["app_theme"] = current

    st.sidebar.markdown(
        """
        <div style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.06em; margin-bottom:4px;">
            🌓 Display Theme
        </div>
        """,
        unsafe_allow_html=True,
    )
    current_idx = 0 if current == "Light Theme" else 1
    selected_theme = st.sidebar.radio(
        "Display Theme",
        options=["Light Theme", "Dark Theme"],
        index=current_idx,
        horizontal=True,
        key="app_theme_radio",
        label_visibility="collapsed",
    )
    if selected_theme != st.session_state.get("app_theme"):
        st.session_state["app_theme"] = selected_theme
        st.rerun()

    return "dark" if selected_theme == "Dark Theme" else "light"


def apply_custom_css() -> None:
    """Inject polished, Zapan-reference SaaS CSS supporting both Light and Dark themes."""
    active_theme = st.session_state.get("app_theme_radio") or st.session_state.get("app_theme", "Light Theme")
    is_dark = (active_theme == "Dark Theme")

    if is_dark:
        theme_vars = """
    --canvas-bg: #0B0F19;
    --card-bg: #182234;
    --card-border: #2A3852;
    --card-shadow: 0 2px 8px rgba(0, 0, 0, 0.45);
    --text-main: #F8FAFC;
    --text-muted: #94A3B8;
    --text-subtext: #64748B;
    --top-nav-bg: #111827;
    --top-nav-border: #1F2937;
    --top-nav-pill-bg: #1E293B;
    --top-nav-pill-border: #334155;
    --top-nav-pill-text: #F8FAFC;

    /* Dark Theme Burgundy Sidebar (#3C0A1C) with Pure White High-Contrast Typography */
    --sidebar-bg: #3C0A1C;
    --sidebar-border: #5A122B;
    --sidebar-title: #FFFFFF;
    --sidebar-label: #FFFFFF;
    --sidebar-text: #FFFFFF;
    --sidebar-link: #FFFFFF;
    --sidebar-link-hover: #5A122B;
    --sidebar-link-active-bg: #6E1535;
    --sidebar-link-active-text: #FFFFFF;
    --sidebar-link-active-border: #9F1239;
    --sidebar-input-bg: #2A0513;
    --sidebar-input-border: #7C1B41;
    --sidebar-input-text: #FFFFFF;
    --sidebar-user-bg: #2A0513;
    --sidebar-user-border: #7C1B41;
    --sidebar-avatar-bg: #4A0D25;
    --sidebar-btn-bg: #2A0513;
    --sidebar-btn-border: #7C1B41;
    --sidebar-btn-text: #FFFFFF;
    --sidebar-btn-hover-bg: #5A122B;
    --sidebar-btn-hover-text: #FFFFFF;
    --sidebar-view-more-text: #FFFFFF;
    --sidebar-view-more-bg: #4A0D25;
    --sidebar-view-more-border: #7C1B41;
    --sidebar-view-more-hover-text: #FFFFFF;
    --sidebar-view-more-hover-bg: #6E1535;
    --sidebar-view-more-hover-border: #9F1239;

    --expander-bg: #182234;
    --expander-border: #2A3852;
    --badge-neutral-bg: #1E293B;
    --badge-neutral-text: #CBD5E1;
    --tooltip-bg: #0B0F19;
    --tooltip-border: #334155;
    --banner-bg: #182234;
    --divider-color: #2A3852;

    --berry-primary: #E11D48;
    --navy-secondary: #60A5FA;
    --kpi-accent-bg: linear-gradient(135deg, #881337 0%, #4C0519 100%);
    --kpi-accent-border: #9F1239;
    --kpi-accent-text: #FFFFFF;
    --kpi-accent-sub: #FECDD3;

    --status-healthy-bg: #0D2818;
    --status-healthy-text: #4ADE80;
    --status-healthy-border: #166534;
    --status-warn-bg: #2C1A04;
    --status-warn-text: #FBBF24;
    --status-warn-border: #92400E;
    --status-error-bg: #370C15;
    --status-error-text: #F87171;
    --status-error-border: #991B1B;
    --table-th-bg: #1E293B;
        """
    else:
        theme_vars = """
    --canvas-bg: #F4F6F9;
    --card-bg: #FFFFFF;
    --card-border: #DCE3EC;
    --card-shadow: 0 2px 8px rgba(38, 51, 77, 0.04);
    --text-main: #26334D;
    --text-muted: #64748B;
    --text-subtext: #8491A3;
    --top-nav-bg: #FFFFFF;
    --top-nav-border: #DCE3EC;
    --top-nav-pill-bg: #F4F6F9;
    --top-nav-pill-border: #DCE3EC;
    --top-nav-pill-text: #26334D;

    /* Light Theme Light Grey-Blue Sidebar (#EAF0F6) with Deep Navy Typography */
    --sidebar-bg: #EAF0F6;
    --sidebar-border: #DCE3EC;
    --sidebar-title: #26334D;
    --sidebar-label: #64748B;
    --sidebar-text: #26334D;
    --sidebar-link: #26334D;
    --sidebar-link-hover: #DFE7F0;
    --sidebar-link-active-bg: #DCE5F0;
    --sidebar-link-active-text: #26334D;
    --sidebar-link-active-border: #3A4781;
    --sidebar-input-bg: #FFFFFF;
    --sidebar-input-border: #DCE3EC;
    --sidebar-input-text: #26334D;
    --sidebar-user-bg: #FFFFFF;
    --sidebar-user-border: #DCE3EC;
    --sidebar-avatar-bg: #DCE5F0;
    --sidebar-btn-bg: #FFFFFF;
    --sidebar-btn-border: #DCE3EC;
    --sidebar-btn-text: #26334D;
    --sidebar-btn-hover-bg: #DCE5F0;
    --sidebar-btn-hover-text: #A92F59;
    --sidebar-view-more-text: #26334D;
    --sidebar-view-more-bg: #FFFFFF;
    --sidebar-view-more-border: #DCE3EC;
    --sidebar-view-more-hover-text: #A92F59;
    --sidebar-view-more-hover-bg: #DCE5F0;
    --sidebar-view-more-hover-border: #3A4781;

    --expander-bg: #FFFFFF;
    --expander-border: #DCE3EC;
    --badge-neutral-bg: #F4F6F9;
    --badge-neutral-text: #64748B;
    --tooltip-bg: #26334D;
    --tooltip-border: #3A4781;
    --banner-bg: #FFFFFF;
    --divider-color: #DCE3EC;

    --berry-primary: #A92F59;
    --navy-secondary: #3A4781;
    --color-success: #397653;
    --color-warning: #A66B19;
    --color-error: #B54747;

    --kpi-accent-bg: linear-gradient(135deg, #A92F59 0%, #7E1F40 100%);
    --kpi-accent-border: #8F2348;
    --kpi-accent-text: #FFFFFF;
    --kpi-accent-sub: #FCE7F0;

    --kpi-pink-bg: #FDF2F5;
    --kpi-pink-border: #F7D3DE;
    --kpi-pink-accent: #A92F59;

    --kpi-green-bg: #F1F7F3;
    --kpi-green-border: #D4E7D9;
    --kpi-green-accent: #397653;

    --kpi-blue-bg: #F0F5FA;
    --kpi-blue-border: #D2E3F2;
    --kpi-blue-accent: #3A4781;

    --kpi-violet-bg: #F6F3FA;
    --kpi-violet-border: #E3D9F2;
    --kpi-violet-accent: #6B4E9B;

    --kpi-yellow-bg: #FDFBF2;
    --kpi-yellow-border: #F6EAC9;
    --kpi-yellow-accent: #A66B19;

    --status-healthy-bg: #EBF5EE;
    --status-healthy-text: #1E663B;
    --status-healthy-border: #C4E2CF;
    --status-warn-bg: #FEF9EE;
    --status-warn-text: #A66B19;
    --status-warn-border: #F5E5C9;
    --status-error-bg: #FDF2F4;
    --status-error-text: #B54747;
    --status-error-border: #F7D2DB;
    --table-th-bg: #EAF0F6;
        """

    st.markdown(
        f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');

:root {{
{theme_vars}
}}

html, body, [class*="css"] {{
    font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text-main);
}}

/* Base Canvas */
.stApp {{
    background: var(--canvas-bg) !important;
    color: var(--text-main) !important;
    min-height: 100vh;
}}

.stApp,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
.stApp [data-testid="stMarkdownContainer"] h1,
.stApp [data-testid="stMarkdownContainer"] h2,
.stApp [data-testid="stMarkdownContainer"] h3,
.stApp [data-testid="stMarkdownContainer"] h4,
.stApp [data-testid="stHeadingWithActionElements"] h1,
.stApp [data-testid="stHeadingWithActionElements"] h2,
.stApp [data-testid="stHeadingWithActionElements"] h3,
.stApp [data-testid="stHeadingWithActionElements"] h4 {{
    color: var(--text-main) !important;
}}

.stApp p,
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li,
.stApp [data-testid="stMarkdownContainer"] span {{
    color: var(--text-muted) !important;
}}

.stApp strong,
.stApp b,
.stApp [data-testid="stMarkdownContainer"] strong,
.stApp [data-testid="stMarkdownContainer"] b {{
    color: var(--text-main) !important;
}}

.stApp .stCaption, .stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p {{
    color: var(--text-subtext) !important;
}}

/* Expander Header & Text in Dark / Light */
div[data-testid="stExpander"] details summary p,
div[data-testid="stExpander"] details summary span,
div[data-testid="stExpander"] details summary div,
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] details summary svg {{
    color: var(--text-main) !important;
    fill: var(--text-main) !important;
}}

/* STREAMLIT HEADER & PADDING - NO CLIPPING */
header[data-testid="stHeader"] {{
    background: transparent !important;
    height: 3.25rem !important;
    z-index: 99 !important;
}}

.block-container {{
    padding-top: 3.75rem !important;
    padding-bottom: 3.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1440px !important;
}}

/* Hide automatic heading anchor chain-link icons */
[data-testid="stHeaderActionElements"],
a.anchor-link {{
    display: none !important;
}}

/* SIDEBAR STYLING - LIGHT RED IN LIGHT THEME / BURGUNDY IN DARK THEME */
[data-testid="stSidebar"] {{
    background-color: var(--sidebar-bg) !important;
    border-right: 1px solid var(--sidebar-border) !important;
}}

/* Ensure all sidebar typography has maximum intentional contrast */
[data-testid="stSidebar"],
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] span {{
    color: var(--sidebar-text) !important;
}}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {{
    color: var(--sidebar-title) !important;
    font-weight: 700 !important;
}}

[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
    color: var(--sidebar-label) !important;
}}

[data-testid="stSidebar"] [data-testid="stSelectbox"] label,
[data-testid="stSidebar"] [data-testid="stDateInput"] label,
[data-testid="stSidebar"] [data-testid="stRadio"] label {{
    color: var(--sidebar-label) !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
}}

/* Radio button options high-contrast text */
[data-testid="stSidebar"] [data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stRadio"] label p,
[data-testid="stSidebar"] [data-testid="stRadio"] label span,
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label div p {{
    color: var(--sidebar-label) !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
}}

/* Sidebar inputs & selectboxes */
[data-testid="stSidebar"] div[data-baseweb="select"] > div,
[data-testid="stSidebar"] div[data-baseweb="input"] > div,
[data-testid="stSidebar"] div[data-baseweb="base-input"] {{
    background-color: var(--sidebar-input-bg) !important;
    border: 1px solid var(--sidebar-input-border) !important;
    border-radius: 8px !important;
}}

[data-testid="stSidebar"] div[data-baseweb="select"] div,
[data-testid="stSidebar"] div[data-baseweb="select"] span,
[data-testid="stSidebar"] div[data-baseweb="select"] svg,
[data-testid="stSidebar"] input {{
    background-color: transparent !important;
    color: var(--sidebar-input-text) !important;
    fill: var(--sidebar-input-text) !important;
}}

[data-testid="stSidebar"] svg {{
    fill: var(--sidebar-input-text) !important;
    color: var(--sidebar-input-text) !important;
}}

/* SIDEBAR VIEW MORE & BUTTON VISIBILITY */
[data-testid="stSidebar"] div.stButton > button,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button {{
    background-color: var(--sidebar-btn-bg) !important;
    color: var(--sidebar-btn-text) !important;
    border: 1px solid var(--sidebar-btn-border) !important;
    border-radius: 8px !important;
    padding: 8px 14px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
}}

[data-testid="stSidebar"] div.stButton > button:hover,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button:hover {{
    background-color: var(--sidebar-btn-hover-bg) !important;
    color: var(--sidebar-btn-hover-text) !important;
    border-color: var(--sidebar-btn-hover-text) !important;
    box-shadow: 0 2px 6px rgba(188, 20, 81, 0.15) !important;
}}

[data-testid="stSidebarNav"] {{
    padding-top: 1rem;
}}

[data-testid="stSidebarNav"] li {{
    height: auto !important;
    margin-bottom: 4px !important;
}}

[data-testid="stSidebarNav"] a {{
    display: flex !important;
    align-items: center !important;
    text-decoration: none !important;
    font-weight: 600 !important;
    color: var(--sidebar-link) !important;
    border-radius: 8px !important;
    padding: 7px 14px !important;
    min-height: 38px !important;
    box-sizing: border-box !important;
    transition: all 0.15s ease !important;
}}

[data-testid="stSidebarNav"] a span,
[data-testid="stSidebarNav"] span {{
    color: var(--sidebar-link) !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
}}

[data-testid="stSidebarNav"] a:hover {{
    background-color: var(--sidebar-link-hover) !important;
}}

[data-testid="stSidebarNav"] a:hover span {{
    color: var(--sidebar-link) !important;
}}

[data-testid="stSidebarNav"] a[aria-current="page"] {{
    background-color: var(--sidebar-link-active-bg) !important;
    border: 1.5px solid var(--sidebar-link-active-border) !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1) !important;
    font-weight: 700 !important;
}}

[data-testid="stSidebarNav"] a[aria-current="page"] span {{
    color: var(--sidebar-link-active-text) !important;
    font-weight: 700 !important;
}}

/* STREAMLIT SIDEBAR NAV "VIEW MORE" BUTTON VISIBILITY */
button[data-testid="stSidebarNavViewButton"],
[data-testid="stSidebarNav"] button,
div[data-testid="stSidebarNavSeparator"] + div button,
button.eczjsme1,
button[class*="stSidebarNavViewButton"] {{
    color: var(--sidebar-view-more-text) !important;
    background-color: var(--sidebar-view-more-bg) !important;
    border: 1px solid var(--sidebar-view-more-border) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 6px 14px !important;
    cursor: pointer !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin-top: 6px !important;
    transition: all 0.15s ease !important;
}}

button[data-testid="stSidebarNavViewButton"] *,
[data-testid="stSidebarNav"] button *,
div[data-testid="stSidebarNavSeparator"] + div button *,
button.eczjsme1 *,
button[class*="stSidebarNavViewButton"] * {{
    color: var(--sidebar-view-more-text) !important;
    fill: var(--sidebar-view-more-text) !important;
    font-weight: 600 !important;
}}

button[data-testid="stSidebarNavViewButton"]:hover,
[data-testid="stSidebarNav"] button:hover,
div[data-testid="stSidebarNavSeparator"] + div button:hover,
button.eczjsme1:hover,
button[class*="stSidebarNavViewButton"]:hover {{
    color: var(--sidebar-view-more-hover-text) !important;
    background-color: var(--sidebar-view-more-hover-bg) !important;
    border-color: var(--sidebar-view-more-hover-border) !important;
}}

button[data-testid="stSidebarNavViewButton"]:hover *,
[data-testid="stSidebarNav"] button:hover *,
div[data-testid="stSidebarNavSeparator"] + div button:hover *,
button.eczjsme1:hover *,
button[class*="stSidebarNavViewButton"]:hover * {{
    color: var(--sidebar-view-more-hover-text) !important;
    fill: var(--sidebar-view-more-hover-text) !important;
}}

/* Sidebar User Profile Card (Replacement for non-functional utility icons) */
.sidebar-user-card {{
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    padding: 10px 12px !important;
    margin-top: 24px !important;
    background: var(--sidebar-user-bg) !important;
    border: 1px solid var(--sidebar-user-border) !important;
    border-radius: 10px !important;
    box-sizing: border-box !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
}}

.sidebar-user-avatar {{
    width: 32px !important;
    height: 32px !important;
    border-radius: 50% !important;
    background: var(--sidebar-avatar-bg) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 1rem !important;
    flex-shrink: 0 !important;
}}

.sidebar-user-details {{
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
}}

.sidebar-user-name {{
    font-size: 0.84rem !important;
    font-weight: 700 !important;
    color: var(--sidebar-title) !important;
    line-height: 1.2 !important;
}}

.sidebar-user-role {{
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    color: var(--sidebar-label) !important;
    display: flex !important;
    align-items: center !important;
    gap: 5px !important;
    margin-top: 2px !important;
    opacity: 0.85 !important;
}}

.sidebar-user-dot {{
    width: 6px !important;
    height: 6px !important;
    border-radius: 50% !important;
    background-color: #10B981 !important;
    display: inline-block !important;
}}

/* Streamlit Column Flex Stretch & Overflow Visible for Unclipped Tooltips */
div[data-testid="stHorizontalBlock"] {{
    align-items: stretch !important;
    display: flex !important;
    flex-direction: row !important;
    gap: 14px !important;
    overflow: visible !important;
}}

div[data-testid="column"] {{
    display: flex !important;
    flex-direction: column !important;
    min-width: 0 !important;
    overflow: visible !important;
}}

div[data-testid="column"] > div {{
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 auto !important;
    height: 100% !important;
    min-width: 0 !important;
    overflow: visible !important;
}}

div[data-testid="column"] [data-testid="stHtml"],
div[data-testid="column"] [data-testid="stMarkdownContainer"] {{
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 auto !important;
    height: 100% !important;
    min-width: 0 !important;
    overflow: visible !important;
}}

/* ZAPAN WHITE TOP NAVBAR */
.top-navbar {{
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    flex-wrap: nowrap !important;
    gap: 12px !important;
    background: var(--top-nav-bg) !important;
    border: 1px solid var(--top-nav-border) !important;
    border-radius: 12px !important;
    padding: 10px 18px !important;
    margin-bottom: 20px !important;
    box-shadow: var(--card-shadow) !important;
    min-height: 52px !important;
    box-sizing: border-box !important;
}}

.nav-left-box {{
    display: flex !important;
    align-items: center !important;
    gap: 14px !important;
    flex: 0 1 auto !important;
    min-width: 0 !important;
}}

.nav-brand-group {{
    display: flex !important;
    align-items: center !important;
    gap: 9px !important;
    white-space: nowrap !important;
}}

.nav-brand-lead {{
    font-size: 1.15rem !important;
    font-weight: 800 !important;
    color: var(--text-main) !important;
    letter-spacing: -0.02em !important;
}}

.nav-toggle-badge {{
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}}

.nav-toggle-btn {{
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 26px !important;
    height: 26px !important;
    background: var(--top-nav-pill-bg) !important;
    border: 1px solid var(--top-nav-pill-border) !important;
    border-radius: 6px !important;
    font-size: 0.95rem !important;
    color: var(--text-muted) !important;
    font-weight: 700 !important;
}}

.nav-page-title {{
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: var(--text-main) !important;
    letter-spacing: -0.01em !important;
}}

.nav-right-box {{
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    flex-shrink: 0 !important;
}}

.nav-status-badge {{
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    background: var(--top-nav-pill-bg) !important;
    border: 1px solid var(--top-nav-pill-border) !important;
    border-radius: 8px !important;
    padding: 5px 11px !important;
    font-size: 0.76rem !important;
    font-weight: 500 !important;
    color: var(--text-muted) !important;
}}

.nav-status-dot {{
    width: 6px !important;
    height: 6px !important;
    border-radius: 50% !important;
    background-color: #10B981 !important;
    display: inline-block !important;
}}

.nav-date-pill {{
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    background: var(--top-nav-pill-bg) !important;
    border: 1px solid var(--top-nav-pill-border) !important;
    border-radius: 8px !important;
    padding: 5px 12px !important;
    font-size: 0.76rem !important;
    font-weight: 600 !important;
    color: var(--top-nav-pill-text) !important;
}}

/* HERO HEADER */
.hero-banner {{
    padding: 2px 0 14px 0 !important;
    margin-bottom: 12px !important;
}}

.hero-badge {{
    display: inline-block !important;
    background-color: var(--top-nav-pill-bg) !important;
    color: var(--berry-primary) !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    padding: 3px 10px !important;
    border-radius: 6px !important;
    margin-bottom: 6px !important;
    border: 1px solid var(--card-border) !important;
}}

.hero-title {{
    font-size: 1.95rem !important;
    font-weight: 700 !important;
    color: var(--text-main) !important;
    line-height: 1.25 !important;
    margin: 2px 0 4px 0 !important;
    letter-spacing: -0.025em !important;
}}

.hero-subtitle {{
    font-size: 0.92rem !important;
    color: var(--text-muted) !important;
    margin: 0 !important;
    line-height: 1.55 !important;
    max-width: 920px !important;
}}

/* ZAPAN REPRODUCED KPI CARDS (3 WHITE + 1 ACCENT) */
.kpi-card {{
    border-radius: 12px !important;
    padding: 14px 14px !important;
    min-height: 124px !important;
    height: 100% !important;
    box-sizing: border-box !important;
    position: relative !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    overflow: visible !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}}

.kpi-card:hover {{
    transform: translateY(-1px) !important;
    z-index: 40 !important;
}}

/* White KPI Cards (Cards 1, 2, 3) */
.kpi-card-white {{
    background: var(--card-bg) !important;
    border: 1px solid var(--card-border) !important;
    box-shadow: var(--card-shadow) !important;
    color: var(--text-main) !important;
}}

.kpi-card-white:hover {{
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08) !important;
}}

.kpi-card-white .kpi-icon-circle {{
    width: 34px !important;
    height: 34px !important;
    border-radius: 50% !important;
    background-color: var(--berry-primary) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
}}

.kpi-card-white .kpi-icon-circle svg {{
    color: #FFFFFF !important;
    stroke: #FFFFFF !important;
}}

.kpi-card-white .kpi-val {{
    font-size: 1.65rem !important;
    font-weight: 800 !important;
    color: var(--text-main) !important;
    line-height: 1.15 !important;
    letter-spacing: -0.02em !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}

.kpi-card-white .kpi-val.kpi-val-sm {{
    font-size: 1.35rem !important;
}}

.kpi-card-white .kpi-val.kpi-val-xs {{
    font-size: 1.15rem !important;
}}

.kpi-card-white .kpi-lbl {{
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    margin-top: 2px !important;
    line-height: 1.3 !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
}}

.kpi-card-white .kpi-progress-track {{
    background-color: var(--divider-color) !important;
    height: 4px !important;
    border-radius: 2px !important;
    overflow: hidden !important;
    margin: 10px 0 8px 0 !important;
    width: 100% !important;
}}

.kpi-card-white .kpi-progress-fill {{
    background-color: var(--berry-primary) !important;
    height: 100% !important;
    border-radius: 2px !important;
}}

.kpi-card-white .kpi-caption-text {{
    font-size: 0.78rem !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
}}

/* Signature Wine/Berry Accent KPI Card (Card 4) */
.kpi-card-accent {{
    background: var(--kpi-accent-bg) !important;
    border: 1px solid var(--kpi-accent-border) !important;
    box-shadow: 0 4px 14px rgba(124, 27, 65, 0.25) !important;
    color: #FFFFFF !important;
}}

.kpi-card-accent:hover {{
    box-shadow: 0 6px 18px rgba(124, 27, 65, 0.35) !important;
}}

.kpi-card-accent .kpi-icon-circle {{
    width: 34px !important;
    height: 34px !important;
    border-radius: 50% !important;
    background-color: #FFFFFF !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
}}

.kpi-card-accent .kpi-icon-circle svg {{
    color: var(--berry-primary) !important;
    stroke: var(--berry-primary) !important;
}}

.kpi-card-accent .kpi-val {{
    font-size: 1.65rem !important;
    font-weight: 800 !important;
    color: #FFFFFF !important;
    line-height: 1.15 !important;
    letter-spacing: -0.02em !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}

.kpi-card-accent .kpi-val.kpi-val-sm {{
    font-size: 1.35rem !important;
}}

.kpi-card-accent .kpi-val.kpi-val-xs {{
    font-size: 1.15rem !important;
}}

.kpi-card-accent .kpi-lbl {{
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--kpi-accent-sub) !important;
    margin-top: 2px !important;
    line-height: 1.3 !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
}}

.kpi-card-accent .kpi-progress-track {{
    background-color: rgba(255, 255, 255, 0.25) !important;
    height: 4px !important;
    border-radius: 2px !important;
    overflow: hidden !important;
    margin: 10px 0 8px 0 !important;
    width: 100% !important;
}}

.kpi-card-accent .kpi-progress-fill {{
    background-color: #FFFFFF !important;
    height: 100% !important;
    border-radius: 2px !important;
}}

.kpi-card-accent .kpi-caption-text {{
    font-size: 0.78rem !important;
    color: var(--kpi-accent-sub) !important;
    font-weight: 500 !important;
}}

/* Soft Pastel Pink KPI Card */
.kpi-card-pink {{
    background: var(--kpi-pink-bg) !important;
    border: 1px solid var(--kpi-pink-border) !important;
    box-shadow: var(--card-shadow) !important;
    color: var(--text-main) !important;
}}

.kpi-card-pink:hover {{
    box-shadow: 0 4px 14px rgba(169, 47, 89, 0.12) !important;
}}

.kpi-card-pink .kpi-icon-circle {{
    width: 34px !important;
    height: 34px !important;
    border-radius: 50% !important;
    background-color: #FCE4EC !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
}}

.kpi-card-pink .kpi-val {{
    font-size: 1.65rem !important;
    font-weight: 800 !important;
    color: var(--text-main) !important;
    line-height: 1.15 !important;
    letter-spacing: -0.02em !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}

.kpi-card-pink .kpi-val.kpi-val-sm {{
    font-size: 1.35rem !important;
}}

.kpi-card-pink .kpi-val.kpi-val-xs {{
    font-size: 1.15rem !important;
}}

.kpi-card-pink .kpi-lbl {{
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    margin-top: 2px !important;
    line-height: 1.3 !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
}}

.kpi-card-pink .kpi-progress-track {{
    background-color: var(--kpi-pink-border) !important;
    height: 4px !important;
    border-radius: 2px !important;
    overflow: hidden !important;
    margin: 10px 0 8px 0 !important;
    width: 100% !important;
}}

.kpi-card-pink .kpi-progress-fill {{
    background-color: var(--berry-primary) !important;
    height: 100% !important;
    border-radius: 2px !important;
}}

.kpi-card-pink .kpi-caption-text {{
    font-size: 0.78rem !important;
    color: var(--text-subtext) !important;
    font-weight: 500 !important;
}}

/* Pale Sage KPI Card */
.kpi-card-sage,
.kpi-card-green {{
    background: var(--kpi-green-bg) !important;
    border: 1px solid var(--kpi-green-border) !important;
    box-shadow: var(--card-shadow) !important;
    color: var(--text-main) !important;
}}

.kpi-card-sage:hover,
.kpi-card-green:hover {{
    box-shadow: 0 4px 14px rgba(57, 118, 83, 0.12) !important;
}}

.kpi-card-sage .kpi-icon-circle,
.kpi-card-green .kpi-icon-circle {{
    width: 34px !important;
    height: 34px !important;
    border-radius: 50% !important;
    background-color: #E2EFE5 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
}}

.kpi-card-sage .kpi-val,
.kpi-card-green .kpi-val {{
    font-size: 1.65rem !important;
    font-weight: 800 !important;
    color: var(--text-main) !important;
    line-height: 1.15 !important;
    letter-spacing: -0.02em !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}

.kpi-card-sage .kpi-val.kpi-val-sm,
.kpi-card-green .kpi-val.kpi-val-sm {{
    font-size: 1.35rem !important;
}}

.kpi-card-sage .kpi-val.kpi-val-xs,
.kpi-card-green .kpi-val.kpi-val-xs {{
    font-size: 1.15rem !important;
}}

.kpi-card-sage .kpi-lbl,
.kpi-card-green .kpi-lbl {{
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    margin-top: 2px !important;
    line-height: 1.3 !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
}}

.kpi-card-sage .kpi-progress-track,
.kpi-card-green .kpi-progress-track {{
    background-color: var(--kpi-green-border) !important;
    height: 4px !important;
    border-radius: 2px !important;
    overflow: hidden !important;
    margin: 10px 0 8px 0 !important;
    width: 100% !important;
}}

.kpi-card-sage .kpi-progress-fill,
.kpi-card-green .kpi-progress-fill {{
    background-color: var(--color-success) !important;
    height: 100% !important;
    border-radius: 2px !important;
}}

.kpi-card-sage .kpi-caption-text,
.kpi-card-green .kpi-caption-text {{
    font-size: 0.78rem !important;
    color: var(--text-subtext) !important;
    font-weight: 500 !important;
}}

/* Muted Light Blue KPI Card */
.kpi-card-blue {{
    background: var(--kpi-blue-bg) !important;
    border: 1px solid var(--kpi-blue-border) !important;
    box-shadow: var(--card-shadow) !important;
    color: var(--text-main) !important;
}}

.kpi-card-blue:hover {{
    box-shadow: 0 4px 14px rgba(58, 71, 129, 0.12) !important;
}}

.kpi-card-blue .kpi-icon-circle {{
    width: 34px !important;
    height: 34px !important;
    border-radius: 50% !important;
    background-color: #E2ECF7 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
}}

.kpi-card-blue .kpi-val {{
    font-size: 1.65rem !important;
    font-weight: 800 !important;
    color: var(--text-main) !important;
    line-height: 1.15 !important;
    letter-spacing: -0.02em !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}

.kpi-card-blue .kpi-val.kpi-val-sm {{
    font-size: 1.35rem !important;
}}

.kpi-card-blue .kpi-val.kpi-val-xs {{
    font-size: 1.15rem !important;
}}

.kpi-card-blue .kpi-lbl {{
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    margin-top: 2px !important;
    line-height: 1.3 !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
}}

.kpi-card-blue .kpi-progress-track {{
    background-color: var(--kpi-blue-border) !important;
    height: 4px !important;
    border-radius: 2px !important;
    overflow: hidden !important;
    margin: 10px 0 8px 0 !important;
    width: 100% !important;
}}

.kpi-card-blue .kpi-progress-fill {{
    background-color: var(--navy-secondary) !important;
    height: 100% !important;
    border-radius: 2px !important;
}}

.kpi-card-blue .kpi-caption-text {{
    font-size: 0.78rem !important;
    color: var(--text-subtext) !important;
    font-weight: 500 !important;
}}

/* Soft Lavender KPI Card */
.kpi-card-lavender,
.kpi-card-violet {{
    background: var(--kpi-violet-bg) !important;
    border: 1px solid var(--kpi-violet-border) !important;
    box-shadow: var(--card-shadow) !important;
    color: var(--text-main) !important;
}}

.kpi-card-lavender:hover,
.kpi-card-violet:hover {{
    box-shadow: 0 4px 14px rgba(107, 78, 155, 0.12) !important;
}}

.kpi-card-lavender .kpi-icon-circle,
.kpi-card-violet .kpi-icon-circle {{
    width: 34px !important;
    height: 34px !important;
    border-radius: 50% !important;
    background-color: #EDE7F6 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
}}

.kpi-card-lavender .kpi-val,
.kpi-card-violet .kpi-val {{
    font-size: 1.65rem !important;
    font-weight: 800 !important;
    color: var(--text-main) !important;
    line-height: 1.15 !important;
    letter-spacing: -0.02em !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}

.kpi-card-lavender .kpi-val.kpi-val-sm {{
    font-size: 1.35rem !important;
}}

.kpi-card-lavender .kpi-val.kpi-val-xs {{
    font-size: 1.15rem !important;
}}

.kpi-card-lavender .kpi-lbl,
.kpi-card-violet .kpi-lbl {{
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    margin-top: 2px !important;
    line-height: 1.3 !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
}}

.kpi-card-lavender .kpi-progress-track,
.kpi-card-violet .kpi-progress-track {{
    background-color: var(--kpi-violet-border) !important;
    height: 4px !important;
    border-radius: 2px !important;
    overflow: hidden !important;
    margin: 10px 0 8px 0 !important;
    width: 100% !important;
}}

.kpi-card-lavender .kpi-progress-fill,
.kpi-card-violet .kpi-progress-fill {{
    background-color: #6B4E9B !important;
    height: 100% !important;
    border-radius: 2px !important;
}}

.kpi-card-lavender .kpi-caption-text,
.kpi-card-violet .kpi-caption-text {{
    font-size: 0.78rem !important;
    color: var(--text-subtext) !important;
    font-weight: 500 !important;
}}

/* Very Light Warm Yellow KPI Card */
.kpi-card-yellow,
.kpi-card-amber {{
    background: var(--kpi-yellow-bg) !important;
    border: 1px solid var(--kpi-yellow-border) !important;
    box-shadow: var(--card-shadow) !important;
    color: var(--text-main) !important;
}}

.kpi-card-yellow:hover,
.kpi-card-amber:hover {{
    box-shadow: 0 4px 14px rgba(166, 107, 25, 0.12) !important;
}}

.kpi-card-yellow .kpi-icon-circle,
.kpi-card-amber .kpi-icon-circle {{
    width: 34px !important;
    height: 34px !important;
    border-radius: 50% !important;
    background-color: #FEF3D6 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
}}

.kpi-card-yellow .kpi-val,
.kpi-card-amber .kpi-val {{
    font-size: 1.65rem !important;
    font-weight: 800 !important;
    color: var(--text-main) !important;
    line-height: 1.15 !important;
    letter-spacing: -0.02em !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}

.kpi-card-yellow .kpi-val.kpi-val-sm {{
    font-size: 1.35rem !important;
}}

.kpi-card-yellow .kpi-val.kpi-val-xs {{
    font-size: 1.15rem !important;
}}

.kpi-card-yellow .kpi-lbl,
.kpi-card-amber .kpi-lbl {{
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    margin-top: 2px !important;
    line-height: 1.3 !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
}}

.kpi-card-yellow .kpi-progress-track,
.kpi-card-amber .kpi-progress-track {{
    background-color: var(--kpi-yellow-border) !important;
    height: 4px !important;
    border-radius: 2px !important;
    overflow: hidden !important;
    margin: 10px 0 8px 0 !important;
    width: 100% !important;
}}

.kpi-card-yellow .kpi-progress-fill,
.kpi-card-amber .kpi-progress-fill {{
    background-color: var(--color-warning) !important;
    height: 100% !important;
    border-radius: 2px !important;
}}

.kpi-card-yellow .kpi-caption-text,
.kpi-card-amber .kpi-caption-text {{
    font-size: 0.78rem !important;
    color: var(--text-subtext) !important;
    font-weight: 500 !important;
}}

.kpi-card-header-row {{
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    min-width: 0 !important;
}}

.kpi-card-metric-block {{
    display: flex !important;
    flex-direction: column !important;
    min-width: 0 !important;
    overflow: hidden !important;
    flex: 1 1 auto !important;
}}

.kpi-card-bottom-row {{
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
}}

/* Circled Information Icon (ⓘ) & Tooltip */
.kpi-info-wrapper {{
    position: relative !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    outline: none !important;
    padding: 2px !important;
    border-radius: 50% !important;
    opacity: 0.8 !important;
    transition: opacity 0.15s ease !important;
    z-index: 20 !important;
}}

.kpi-info-wrapper:hover,
.kpi-info-wrapper:focus {{
    opacity: 1 !important;
    z-index: 999999 !important;
}}

.kpi-info-icon {{
    color: inherit !important;
    display: block !important;
}}

.kpi-tooltip-bubble {{
    position: absolute !important;
    bottom: calc(100% + 10px) !important;
    right: -4px !important;
    width: max-content !important;
    max-width: 205px !important;
    min-width: 150px !important;
    box-sizing: border-box !important;
    background: #0F172A !important;
    border: 1px solid #334155 !important;
    color: #F8FAFC !important;
    font-size: 0.74rem !important;
    font-weight: 500 !important;
    line-height: 1.45 !important;
    text-transform: none !important;
    letter-spacing: normal !important;
    padding: 9px 12px !important;
    border-radius: 8px !important;
    box-shadow: 0 12px 28px -4px rgba(0, 0, 0, 0.5) !important;
    visibility: hidden !important;
    opacity: 0 !important;
    transform: translateY(4px) !important;
    transition: opacity 0.2s ease, transform 0.2s ease, visibility 0.2s !important;
    pointer-events: none !important;
    z-index: 999999 !important;
    text-align: left !important;
    white-space: normal !important;
    word-break: normal !important;
    overflow-wrap: break-word !important;
}}

.kpi-tooltip-bubble::after {{
    content: "" !important;
    position: absolute !important;
    top: 100% !important;
    right: 8px !important;
    border-width: 6px !important;
    border-style: solid !important;
    border-color: #0F172A transparent transparent transparent !important;
}}

.kpi-info-wrapper:hover .kpi-tooltip-bubble,
.kpi-info-wrapper:focus .kpi-tooltip-bubble {{
    visibility: visible !important;
    opacity: 1 !important;
    transform: translateY(0) !important;
}}

/* ZAPAN WHITE ANALYTICS CONTAINER CARD */
.analytics-card {{
    background: var(--card-bg) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 12px !important;
    padding: 20px 22px !important;
    margin-bottom: 20px !important;
    box-shadow: var(--card-shadow) !important;
}}

.analytics-card-header {{
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    margin-bottom: 12px !important;
    padding-bottom: 10px !important;
    border-bottom: 1px solid var(--divider-color) !important;
}}

.analytics-card-title {{
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    color: var(--text-main) !important;
    margin: 0 !important;
    letter-spacing: -0.015em !important;
}}

.analytics-legend-row {{
    display: flex !important;
    align-items: center !important;
    gap: 16px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
}}

.legend-dot {{
    display: inline-block !important;
    width: 9px !important;
    height: 9px !important;
    border-radius: 50% !important;
    margin-right: 5px !important;
}}

.legend-navy {{
    background-color: var(--navy-secondary) !important;
}}

.legend-berry {{
    background-color: var(--berry-primary) !important;
}}

/* TABLE CONTROLS & FOOTER */
.table-footer-controls {{
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    margin-top: 14px !important;
    padding-top: 12px !important;
    border-top: 1px solid var(--divider-color) !important;
    font-size: 0.80rem !important;
    color: var(--text-muted) !important;
}}

.table-pill-select {{
    display: inline-block !important;
    background: var(--card-bg) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 6px !important;
    padding: 2px 8px !important;
    font-weight: 600 !important;
    color: var(--text-main) !important;
    margin: 0 4px !important;
}}

.platform-footer-note {{
    font-size: 0.74rem !important;
    color: var(--text-subtext) !important;
    margin-top: 6px !important;
}}

/* COHORT & CATEGORY BREAKDOWN CARD */
.glass-feature-card {{
    background: var(--card-bg) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 12px !important;
    padding: 20px 22px !important;
    color: var(--text-main) !important;
    box-shadow: var(--card-shadow) !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    box-sizing: border-box !important;
}}

.glass-feature-header {{
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    margin-bottom: 8px !important;
}}

.glass-feature-title {{
    color: var(--text-main) !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
}}

.glass-feature-table {{
    width: 100% !important;
    border-collapse: collapse !important;
    margin-top: 10px !important;
    font-size: 0.82rem !important;
}}

.glass-feature-table th {{
    color: var(--text-subtext) !important;
    font-weight: 600 !important;
    text-align: left !important;
    padding: 8px 8px !important;
    border-bottom: 1px solid var(--divider-color) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}}

.glass-feature-table td {{
    color: var(--text-main) !important;
    padding: 9px 8px !important;
    border-bottom: 1px solid var(--divider-color) !important;
}}

/* THEMED ACCESSIBLE DATA TABLES (For SRM Check, Guardrails, and Diagnostics) */
.custom-themed-table {{
    width: 100% !important;
    border-collapse: separate !important;
    border-spacing: 0 !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    font-size: 0.86rem !important;
    margin-top: 12px !important;
    margin-bottom: 8px !important;
}}

.custom-themed-table thead tr {{
    background-color: var(--table-th-bg) !important;
}}

.custom-themed-table th {{
    color: var(--text-main) !important;
    font-weight: 700 !important;
    text-align: left !important;
    padding: 10px 14px !important;
    border-bottom: 1px solid var(--card-border) !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
}}

.custom-themed-table tbody tr {{
    background-color: var(--card-bg) !important;
    transition: background-color 0.15s ease !important;
}}

.custom-themed-table tbody tr:not(:last-child) td {{
    border-bottom: 1px solid var(--card-border) !important;
}}

.custom-themed-table td {{
    color: var(--text-main) !important;
    padding: 11px 14px !important;
    font-weight: 500 !important;
    vertical-align: middle !important;
}}

.custom-themed-table td.val-bold {{
    font-weight: 700 !important;
}}

/* STATUS PILLS & BADGES */
.status-pill {{
    display: inline-flex !important;
    align-items: center !important;
    gap: 5px !important;
    padding: 3px 10px !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    font-size: 0.76rem !important;
    letter-spacing: 0.02em !important;
    white-space: nowrap !important;
}}

.status-pill-healthy {{
    background-color: var(--status-healthy-bg) !important;
    color: var(--status-healthy-text) !important;
    border: 1px solid var(--status-healthy-border) !important;
}}

.status-pill-warning {{
    background-color: var(--status-warn-bg) !important;
    color: var(--status-warn-text) !important;
    border: 1px solid var(--status-warn-border) !important;
}}

.status-pill-error {{
    background-color: var(--status-error-bg) !important;
    color: var(--status-error-text) !important;
    border: 1px solid var(--status-error-border) !important;
}}

/* SRM STATUS BOX */
.srm-status-card {{
    background-color: var(--status-healthy-bg) !important;
    border: 1px solid var(--status-healthy-border) !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    margin-bottom: 12px !important;
}}

.srm-status-card.error {{
    background-color: var(--status-error-bg) !important;
    border-color: var(--status-error-border) !important;
}}

.srm-status-title {{
    color: var(--status-healthy-text) !important;
    font-size: 0.88rem !important;
    font-weight: 700 !important;
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    margin-bottom: 4px !important;
}}

.srm-status-card.error .srm-status-title {{
    color: var(--status-error-text) !important;
}}

.srm-status-desc {{
    color: var(--text-main) !important;
    font-size: 0.82rem !important;
    margin-bottom: 8px !important;
}}

.srm-stats-row {{
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 12px !important;
    font-size: 0.78rem !important;
    color: var(--text-muted) !important;
}}

.srm-stats-item {{
    background-color: rgba(0, 0, 0, 0.04) !important;
    padding: 2px 8px !important;
    border-radius: 4px !important;
    border: 1px solid rgba(0, 0, 0, 0.08) !important;
}}

/* RECOMMENDATION FULL-WIDTH CARD */
.rec-full-card {{
    background: var(--card-bg) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 12px !important;
    padding: 20px 24px !important;
    margin-bottom: 20px !important;
    box-shadow: var(--card-shadow) !important;
    box-sizing: border-box !important;
    width: 100% !important;
}}

.rec-header-row {{
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    margin-bottom: 14px !important;
    padding-bottom: 12px !important;
    border-bottom: 1px solid var(--divider-color) !important;
}}

.rec-title-text {{
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    color: var(--text-main) !important;
    line-height: 1.3 !important;
}}

.rec-badge {{
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    padding: 3px 9px !important;
    border-radius: 6px !important;
    background: var(--top-nav-pill-bg) !important;
    color: var(--berry-primary) !important;
    border: 1px solid var(--card-border) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
    white-space: nowrap !important;
}}

.rec-content-section {{
    margin-bottom: 12px !important;
    font-size: 0.88rem !important;
    line-height: 1.6 !important;
    color: var(--text-muted) !important;
}}

.rec-content-section strong {{
    color: var(--text-main) !important;
}}

/* NOTICE BANNER */
.notice-banner {{
    background-color: var(--banner-bg) !important;
    border: 1px solid var(--card-border) !important;
    border-left: 4px solid var(--berry-primary) !important;
    padding: 12px 18px !important;
    border-radius: 8px !important;
    color: var(--text-muted) !important;
    font-size: 0.84rem !important;
    line-height: 1.5 !important;
    margin-bottom: 18px !important;
    box-shadow: var(--card-shadow) !important;
}}

/* BUTTONS */
div.stButton > button,
div[data-testid="stDownloadButton"] > button {{
    background-color: var(--card-bg) !important;
    color: var(--text-main) !important;
    border-radius: 8px !important;
    border: 1px solid var(--card-border) !important;
    padding: 8px 18px !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
}}

div.stButton > button:hover,
div[data-testid="stDownloadButton"] > button:hover {{
    background-color: #FFF5F7 !important;
    color: var(--berry-primary) !important;
    border-color: var(--berry-primary) !important;
    box-shadow: 0 2px 6px rgba(188, 20, 81, 0.15) !important;
    transform: translateY(-1px) !important;
}}

/* STREAMLIT TABS */
div[data-baseweb="tab-list"] {{
    gap: 6px !important;
    border-bottom: 1px solid var(--divider-color) !important;
    padding-bottom: 6px !important;
}}

button[data-baseweb="tab"] {{
    border-radius: 8px !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    padding: 6px 16px !important;
    transition: all 0.15s ease !important;
}}

button[data-baseweb="tab"][aria-selected="true"] {{
    color: #FFFFFF !important;
    background-color: var(--berry-primary) !important;
}}

/* EXPANDERS */
div[data-testid="stExpander"] {{
    background-color: var(--expander-bg) !important;
    border: 1px solid var(--expander-border) !important;
    border-radius: 12px !important;
    box-shadow: var(--card-shadow) !important;
    margin-bottom: 18px !important;
}}

/* RESPONSIVE BREAKPOINTS */
@media (max-width: 768px) {{
    .top-navbar {{
        border-radius: 12px !important;
        flex-wrap: wrap !important;
        padding: 8px 14px !important;
    }}
    div[data-testid="stHorizontalBlock"] {{
        flex-wrap: wrap !important;
        gap: 12px !important;
    }}
    div[data-testid="column"] {{
        flex: 1 1 calc(50% - 12px) !important;
        min-width: 200px !important;
    }}
    .hero-title {{
        font-size: 1.75rem !important;
    }}
}}

@media (max-width: 576px) {{
    div[data-testid="column"] {{
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }}
    .hero-title {{
        font-size: 1.45rem !important;
    }}
}}
</style>""",
        unsafe_allow_html=True,
    )


def _select_card_theme(label: str, explicit_style: str | None) -> str:
    """Determine card theme based on explicit parameter or label semantic cues."""
    if explicit_style and explicit_style in ("yellow", "pink", "green", "blue", "violet"):
        return explicit_style
    if explicit_style == "amber":
        return "yellow"
    if explicit_style == "rose":
        return "pink"
    return "yellow"


def render_top_navbar(
    brand_title: str = "StreamIQ | Executive Overview",
    date_display: str = "All Available History (2026)",
) -> None:
    """Render Zapan-style crisp white top bar with faceted gem logo, page title, and status pills."""
    if " | " in brand_title:
        lead, page_part = brand_title.split(" | ", 1)
    elif " / " in brand_title:
        lead, page_part = brand_title.split(" / ", 1)
    else:
        lead = "StreamIQ"
        page_part = brand_title

    escaped_lead = html.escape(lead)
    escaped_page = html.escape(page_part)
    escaped_date = html.escape(date_display)

    nav_html = (
        '<div class="top-navbar">'
        '<div class="nav-left-box">'
        '<div class="nav-brand-group">'
        '<svg width="26" height="22" viewBox="0 0 28 24" fill="none" style="flex-shrink:0;">'
        '<polygon points="14,2 22,7 14,12 6,7" fill="#C24471" />'
        '<polygon points="6,7 14,12 14,22 6,17" fill="#A92F59" />'
        '<polygon points="14,12 22,7 22,17 14,22" fill="#7E1F40" />'
        '<polygon points="2,9 6,7 6,17 2,19" fill="#D95C85" opacity="0.85" />'
        '<polygon points="22,7 26,9 26,19 22,17" fill="#3A4781" opacity="0.85" />'
        '</svg>'
        f'<span class="nav-brand-lead">{escaped_lead}</span>'
        '</div>'
        '<div class="nav-toggle-badge">'
        '<span class="nav-toggle-btn">≡</span>'
        f'<span class="nav-page-title">{escaped_page}</span>'
        '</div>'
        '</div>'
        '<div class="nav-right-box">'
        '<div class="nav-status-badge">'
        '<span class="nav-status-dot"></span>'
        '<span>Simulated Dataset • 2,000 Accounts</span>'
        '</div>'
        '<div class="nav-date-pill">'
        '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="3" y="4" width="18" height="18" rx="2" ry="2" />'
        '<line x1="16" y1="2" x2="16" y2="6" />'
        '<line x1="8" y1="2" x2="8" y2="6" />'
        '<line x1="3" y1="10" x2="21" y2="10" />'
        '</svg>'
        f'<span>{escaped_date}</span>'
        '</div>'
        '</div>'
        '</div>'
    )
    if hasattr(st, "html"):
        st.html(nav_html)
    else:
        st.markdown(nav_html, unsafe_allow_html=True)


# Base64 encoded SVGs for isometric cube and tooltip to guarantee rendering without sanitizer stripping
_CUBE_WHITE_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIiBmaWxsPSJub25lIiBzdHJva2U9IiNGRkZGRkYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMjEgMTZWOGEyIDIgMCAwIDAtMS0xLjczbC03LTRhMiAyIDAgMCAwLTIgMGwtNyA0QTIgMiAwIDAgMCAzIDh2OGEyIDIgMCAwIDAgMSAxLjczbDcgNGEyIDIgMCAwIDAgMiAwbDctNEEyIDIgMCAwIDAgMjEgMTZ6Ij48L3BhdGg+PHBvbHlsaW5lIHBvaW50cz0iMy4yNyA2Ljk2IDEyIDEyLjAxIDIwLjczIDYuOTYiPjwvcG9seWxpbmU+PGxpbmUgeDE9IjEyIiB5MT0iMjIuMDgiIHgyPSIxMiIgeTI9IjEyIj48L2xpbmU+PC9zdmc+"
_CUBE_BERRY_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIiBmaWxsPSJub25lIiBzdHJva2U9IiNBOTJGNTkiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMjEgMTZWOGEyIDIgMCAwIDAtMS0xLjczbC03LTRhMiAyIDAgMCAwLTIgMGwtNyA0QTIgMiAwIDAgMCAzIDh2OGEyIDIgMCAwIDAgMSAxLjczbDcgNGEyIDIgMCAwIDAgMiAwbDctNEEyIDIgMCAwIDAgMjEgMTZ6Ij48L3BhdGg+PHBvbHlsaW5lIHBvaW50cz0iMy4yNyA2Ljk2IDEyIDEyLjAxIDIwLjczIDYuOTYiPjwvcG9seWxpbmU+PGxpbmUgeDE9IjEyIiB5MT0iMjIuMDgiIHgyPSIxMiIgeTI9IjEyIj48L2xpbmU+PC9zdmc+"
_CUBE_NAVY_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIiBmaWxsPSJub25lIiBzdHJva2U9IiMzQTQ3ODEiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMjEgMTZWOGEyIDIgMCAwIDAtMS0xLjczbC03LTRhMiAyIDAgMCAwLTIgMGwtNyA0QTIgMiAwIDAgMCAzIDh2OGEyIDIgMCAwIDAgMSAxLjczbDcgNGEyIDIgMCAwIDAgMiAwbDctNEEyIDIgMCAwIDAgMjEgMTZ6Ij48L3BhdGg+PHBvbHlsaW5lIHBvaW50cz0iMy4yNyA2Ljk2IDEyIDEyLjAxIDIwLjczIDYuOTYiPjwvcG9seWxpbmU+PGxpbmUgeDE9IjEyIiB5MT0iMjIuMDgiIHgyPSIxMiIgeTI9IjEyIj48L2xpbmU+PC9zdmc+"
_CUBE_SAGE_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIiBmaWxsPSJub25lIiBzdHJva2U9IiMzOTc2NTMiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMjEgMTZWOGEyIDIgMCAwIDAtMS0xLjczbC03LTRhMiAyIDAgMCAwLTIgMGwtNyA0QTIgMiAwIDAgMCAzIDh2OGEyIDIgMCAwIDAgMSAxLjczbDcgNGEyIDIgMCAwIDAgMiAwbDctNEEyIDIgMCAwIDAgMjEgMTZ6Ij48L3BhdGg+PHBvbHlsaW5lIHBvaW50cz0iMy4yNyA2Ljk2IDEyIDEyLjAxIDIwLjczIDYuOTYiPjwvcG9seWxpbmU+PGxpbmUgeDE9IjEyIiB5MT0iMjIuMDgiIHgyPSIxMiIgeTI9IjEyIj48L2xpbmU+PC9zdmc+"
_CUBE_LAVENDER_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIiBmaWxsPSJub25lIiBzdHJva2U9IiM2QjRFOUIiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMjEgMTZWOGEyIDIgMCAwIDAtMS0xLjczbC03LTRhMiAyIDAgMCAwLTIgMGwtNyA0QTIgMiAwIDAgMCAzIDh2OGEyIDIgMCAwIDAgMSAxLjczbDcgNGEyIDIgMCAwIDAgMiAwbDctNEEyIDIgMCAwIDAgMjEgMTZ6Ij48L3BhdGg+PHBvbHlsaW5lIHBvaW50cz0iMy4yNyA2Ljk2IDEyIDEyLjAxIDIwLjczIDYuOTYiPjwvcG9seWxpbmU+PGxpbmUgeDE9IjEyIiB5MT0iMjIuMDgiIHgyPSIxMiIgeTI9IjEyIj48L2xpbmU+PC9zdmc+"
_CUBE_AMBER_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIiBmaWxsPSJub25lIiBzdHJva2U9IiNBNjZCMTkiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMjEgMTZWOGEyIDIgMCAwIDAtMS0xLjczbC03LTRhMiAyIDAgMCAwLTIgMGwtNyA0QTIgMiAwIDAgMCAzIDh2OGEyIDIgMCAwIDAgMSAxLjczbDcgNGEyIDIgMCAwIDAgMiAwbDctNEEyIDIgMCAwIDAgMjEgMTZ6Ij48L3BhdGg+PHBvbHlsaW5lIHBvaW50cz0iMy4yNyA2Ljk2IDEyIDEyLjAxIDIwLjczIDYuOTYiPjwvcG9seWxpbmU+PGxpbmUgeDE9IjEyIiB5MT0iMjIuMDgiIHgyPSIxMiIgeTI9IjEyIj48L2xpbmU+PC9zdmc+"

_INFO_SLATE_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyMCAyMCIgd2lkdGg9IjE0IiBoZWlnaHQ9IjE0IiBmaWxsPSIjODQ5MUEzIj48cGF0aCBmaWxsLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik0xOCAxMGE4IDggMCAxMS0xNiAwIDggOCAwIDAxMTYgMHptLTctNGExIDEgMCAxMS0yIDAgMSAxIDAgMDEyIDB6TTkgOWExIDEgMCAwMDAgMnYzYTEgMSAwIDAwMSAxaDFhMSAxIDAgMTAwLTJ2LTNhMSAxIDAgMDAtMS0xSDl6IiBjbGlwLXJ1bGU9ImV2ZW5vZGQiIC8+PC9zdmc+"
_INFO_PINK_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyMCAyMCIgd2lkdGg9IjE0IiBoZWlnaHQ9IjE0IiBmaWxsPSIjRkNFN0YwIj48cGF0aCBmaWxsLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik0xOCAxMGE4IDggMCAxMS0xNiAwIDggOCAwIDAxMTYgMHptLTctNGExIDEgMCAxMS0yIDAgMSAxIDAgMDEyIDB6TTkgOWExIDEgMCAwMDAgMnYzYTEgMSAwIDAwMSAxaDFhMSAxIDAgMTAwLTJ2LTNhMSAxIDAgMDAtMS0xSDl6IiBjbGlwLXJ1bGU9ImV2ZW5vZGQiIC8+PC9zdmc+"
_INFO_BERRY_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyMCAyMCIgd2lkdGg9IjE0IiBoZWlnaHQ9IjE0IiBmaWxsPSIjQTkyRjU5Ij48cGF0aCBmaWxsLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik0xOCAxMGE4IDggMCAxMS0xNiAwIDggOCAwIDAxMTYgMHptLTctNGExIDEgMCAxMS0yIDAgMSAxIDAgMDEyIDB6TTkgOWExIDEgMCAwMDAgMnYzYTEgMSAwIDAwMSAxaDFhMSAxIDAgMTAwLTJ2LTNhMSAxIDAgMDAtMS0xSDl6IiBjbGlwLXJ1bGU9ImV2ZW5vZGQiIC8+PC9zdmc+"
_INFO_NAVY_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyMCAyMCIgd2lkdGg9IjE0IiBoZWlnaHQ9IjE0IiBmaWxsPSIjM0E0NzgxIj48cGF0aCBmaWxsLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik0xOCAxMGE4IDggMCAxMS0xNiAwIDggOCAwIDAxMTYgMHptLTctNGExIDEgMCAxMS0yIDAgMSAxIDAgMDEyIDB6TTkgOWExIDEgMCAwMDAgMnYzYTEgMSAwIDAwMSAxaDFhMSAxIDAgMTAwLTJ2LTNhMSAxIDAgMDAtMS0xSDl6IiBjbGlwLXJ1bGU9ImV2ZW5vZGQiIC8+PC9zdmc+"
_INFO_SAGE_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyMCAyMCIgd2lkdGg9IjE0IiBoZWlnaHQ9IjE0IiBmaWxsPSIjMzk3NjUzIj48cGF0aCBmaWxsLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik0xOCAxMGE4IDggMCAxMS0xNiAwIDggOCAwIDAxMTYgMHptLTctNGExIDEgMCAxMS0yIDAgMSAxIDAgMDEyIDB6TTkgOWExIDEgMCAwMDAgMnYzYTEgMSAwIDAwMSAxaDFhMSAxIDAgMTAwLTJ2LTNhMSAxIDAgMDAtMS0xSDl6IiBjbGlwLXJ1bGU9ImV2ZW5vZGQiIC8+PC9zdmc+"
_INFO_LAVENDER_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyMCAyMCIgd2lkdGg9IjE0IiBoZWlnaHQ9IjE0IiBmaWxsPSIjNkI0RTlCIj48cGF0aCBmaWxsLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik0xOCAxMGE4IDggMCAxMS0xNiAwIDggOCAwIDAxMTYgMHptLTctNGExIDEgMCAxMS0yIDAgMSAxIDAgMDEyIDB6TTkgOWExIDEgMCAwMDAgMnYzYTEgMSAwIDAwMSAxaDFhMSAxIDAgMTAwLTJ2LTNhMSAxIDAgMDAtMS0xSDl6IiBjbGlwLXJ1bGU9ImV2ZW5vZGQiIC8+PC9zdmc+"
_INFO_AMBER_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyMCAyMCIgd2lkdGg9IjE0IiBoZWlnaHQ9IjE0IiBmaWxsPSIjQTY2QjE5Ij48cGF0aCBmaWxsLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik0xOCAxMGE4IDggMCAxMS0xNiAwIDggOCAwIDAxMTYgMHptLTctNGExIDEgMCAxMS0yIDAgMSAxIDAgMDEyIDB6TTkgOWExIDEgMCAwMDAgMnYzYTEgMSAwIDAwMSAxaDFhMSAxIDAgMTAwLTJ2LTNhMSAxIDAgMDAtMS0xSDl6IiBjbGlwLXJ1bGU9ImV2ZW5vZGQiIC8+PC9zdmc+"


def render_kpi_card(
    label: str,
    value: str | int | float,
    info_text: str | None = None,
    progress_pct: float | int = 60,
    subtext: str | None = None,
    is_accent: bool = False,
    delta: str | None = None,
    delta_color: str = "normal",
    icon_style: str | None = None,
    card_style: str | None = None,
) -> None:
    """Render a Zapan-reference KPI card (white, soft pastel pink, pale sage, muted light blue, soft lavender, light yellow, or selective deep berry accent)."""
    escaped_label = html.escape(str(label))
    str_val = str(value)
    escaped_value = html.escape(str_val)

    try:
        pct_float = max(0.0, min(100.0, float(progress_pct)))
    except (ValueError, TypeError):
        pct_float = 60.0

    # Determine card aesthetic style
    style = "white"
    if is_accent or card_style in ("accent", "berry") or icon_style in ("accent", "berry"):
        style = "accent"
    elif card_style in ("pink", "rose"):
        style = "pink"
    elif card_style in ("sage", "green"):
        style = "sage"
    elif card_style in ("blue", "navy"):
        style = "blue"
    elif card_style in ("lavender", "violet"):
        style = "lavender"
    elif card_style in ("yellow", "amber", "warm_yellow"):
        style = "yellow"
    elif icon_style in ("pink", "rose"):
        style = "pink"
    elif icon_style in ("sage", "green"):
        style = "sage"
    elif icon_style in ("blue", "navy"):
        style = "blue"
    elif icon_style in ("lavender", "violet"):
        style = "lavender"
    elif icon_style in ("yellow", "amber", "warm_yellow"):
        style = "yellow"
    elif card_style == "white" or icon_style == "white":
        style = "white"

    if style == "accent":
        card_cls = "kpi-card-accent"
        cube_b64 = _CUBE_BERRY_B64
        info_b64 = _INFO_PINK_B64
    elif style == "pink":
        card_cls = "kpi-card-pink"
        cube_b64 = _CUBE_BERRY_B64
        info_b64 = _INFO_BERRY_B64
    elif style == "sage":
        card_cls = "kpi-card-sage"
        cube_b64 = _CUBE_SAGE_B64
        info_b64 = _INFO_SAGE_B64
    elif style == "blue":
        card_cls = "kpi-card-blue"
        cube_b64 = _CUBE_NAVY_B64
        info_b64 = _INFO_NAVY_B64
    elif style == "lavender":
        card_cls = "kpi-card-lavender"
        cube_b64 = _CUBE_LAVENDER_B64
        info_b64 = _INFO_LAVENDER_B64
    elif style == "yellow":
        card_cls = "kpi-card-yellow"
        cube_b64 = _CUBE_AMBER_B64
        info_b64 = _INFO_AMBER_B64
    else:
        card_cls = "kpi-card-white"
        cube_b64 = _CUBE_WHITE_B64
        info_b64 = _INFO_SLATE_B64

    info_html = ""
    if info_text:
        escaped_info = html.escape(str(info_text))
        info_html = (
            f'<div class="kpi-info-wrapper" tabindex="0" role="tooltip" aria-label="{escaped_info}" title="{escaped_info}">'
            f'<img src="data:image/svg+xml;base64,{info_b64}" width="14" height="14" alt="info" style="display:inline-block; vertical-align:middle;" />'
            f'<div class="kpi-tooltip-bubble">{escaped_info}</div>'
            f'</div>'
        )

    subtext_str = subtext if subtext is not None else f"{pct_float:.0f} percent completed."
    escaped_subtext = html.escape(subtext_str)

    cube_img = f'<img src="data:image/svg+xml;base64,{cube_b64}" width="18" height="18" alt="cube" style="display:block;" />'

    clean_val = str_val.strip()
    val_len = len(clean_val)
    val_size_cls = ""
    if val_len >= 7:
        val_size_cls = "kpi-val-xs"
    elif val_len >= 5:
        val_size_cls = "kpi-val-sm"

    card_html = (
        f'<div class="kpi-card {card_cls}">'
        f'<div class="kpi-card-header-row">'
        f'<div class="kpi-icon-circle">{cube_img}</div>'
        f'<div class="kpi-card-metric-block">'
        f'<div class="kpi-val {val_size_cls}">{escaped_value}</div>'
        f'<div class="kpi-lbl">{escaped_label}</div>'
        f'</div>'
        f'</div>'
        f'<div class="kpi-progress-track">'
        f'<div class="kpi-progress-fill" style="width: {pct_float:.1f}%;"></div>'
        f'</div>'
        f'<div class="kpi-card-bottom-row">'
        f'<span class="kpi-caption-text">{escaped_subtext}</span>'
        f'{info_html}'
        f'</div>'
        f'</div>'
    )


    if hasattr(st, "html"):
        st.html(card_html)
    else:
        st.markdown(card_html, unsafe_allow_html=True)


def render_hero_header(badge_text: str, title: str, subtitle: str) -> None:
    """Render an elegant headline greeting with clear visual hierarchy."""
    escaped_badge = html.escape(badge_text)
    escaped_title = html.escape(title)
    escaped_subtitle = html.escape(subtitle)
    hero_html = (
        f'<div class="hero-banner">'
        f'<span class="hero-badge">{escaped_badge}</span>'
        f'<h1 class="hero-title">{escaped_title}</h1>'
        f'<p class="hero-subtitle">{escaped_subtitle}</p>'
        f'</div>'
    )
    if hasattr(st, "html"):
        st.html(hero_html)
    else:
        st.markdown(hero_html, unsafe_allow_html=True)


def render_table_footer_controls(records_count: int = 7) -> None:
    """Safely deprecated - removed non-functional mockup controls per user request."""
    return None


def render_sidebar_footer() -> None:
    """Render authentic user session card with 👤 avatar at base of sidebar."""
    user_name = st.session_state.get("user_profile_name", "Product Analyst")
    escaped_user = html.escape(str(user_name))
    dock_html = (
        f'<div class="sidebar-user-card">'
        f'<div class="sidebar-user-avatar">👤</div>'
        f'<div class="sidebar-user-details">'
        f'<div class="sidebar-user-name">{escaped_user}</div>'
        f'<div class="sidebar-user-role"><span class="sidebar-user-dot"></span>Active Workspace</div>'
        f'</div>'
        f'</div>'
    )
    st.sidebar.markdown(dock_html, unsafe_allow_html=True)


def render_blue_feature_card(
    title: str,
    categories: list[dict[str, str | int | float]],
    col_names: tuple[str, str, str] = ("Category", "Metric", "% Share"),
) -> None:
    """Render a category breakdown card with data-driven proportional distribution bar."""
    escaped_title = html.escape(title)
    th_cat, th_val, th_pct = map(html.escape, col_names)

    badge_styles = [
        "background:#FDFBF2; color:#26334D; border:1px solid #F6EAC9;",
        "background:#F0F5FA; color:#26334D; border:1px solid #D2E3F2;",
        "background:#FDF2F5; color:#26334D; border:1px solid #F7D3DE;",
        "background:#F1F7F3; color:#26334D; border:1px solid #D4E7D9;",
        "background:#F6F3FA; color:#26334D; border:1px solid #E3D9F2;",
    ]

    pastel_bar_colors = ["#A92F59", "#3A4781", "#397653", "#6B4E9B", "#A66B19"]

    bar_segments = []
    rows_html = []
    for i, r in enumerate(categories):
        style = badge_styles[i % len(badge_styles)]
        cat_name = html.escape(str(r.get("category", "")))
        val = html.escape(str(r.get("value", "")))
        pct_raw = str(r.get("pct", "0%"))
        pct = html.escape(pct_raw)

        try:
            pct_val = max(0.0, min(100.0, float(pct_raw.replace("%", "").strip())))
        except ValueError:
            pct_val = 0.0

        bar_color = pastel_bar_colors[i % len(pastel_bar_colors)]
        if pct_val > 0:
            bar_segments.append(
                f'<div style="width:{pct_val}%; background:{bar_color}; height:8px;" '
                f'title="{cat_name}: {pct_raw}"></div>'
            )

        rows_html.append(
            f'<tr>'
            f'<td><span style="{style} padding:2px 8px; border-radius:6px; font-weight:600; font-size:0.75rem;">{cat_name}</span></td>'
            f'<td><span style="font-weight:700;">{val}</span></td>'
            f'<td style="text-align:right; font-weight:700; opacity:0.85;">{pct}</td>'
            f'</tr>'
        )
    table_rows = "".join(rows_html)
    proportional_bar = (
        '<div style="display:flex; width:100%; height:8px; border-radius:4px; overflow:hidden; gap:2px; margin:12px 0 14px 0; background:rgba(0,0,0,0.06);">'
        f'{"".join(bar_segments)}'
        '</div>'
    )

    feature_html = (
        f'<div class="glass-feature-card">'
        f'<div class="glass-feature-header">'
        f'<h3 class="glass-feature-title">{escaped_title}</h3>'
        f'<span style="font-size:0.72rem; background:var(--badge-neutral-bg); color:var(--text-subtext); padding:3px 8px; border-radius:6px; font-weight:600;">ACTIVE COHORT</span>'
        f'</div>'
        f'{proportional_bar}'
        f'<table class="glass-feature-table">'
        f'<thead><tr><th>{th_cat}</th><th>{th_val}</th><th style="text-align:right;">{th_pct}</th></tr></thead>'
        f'<tbody>{table_rows}</tbody>'
        f'</table>'
        f'</div>'
    )

    if hasattr(st, "html"):
        st.html(feature_html)
    else:
        st.markdown(feature_html, unsafe_allow_html=True)


def render_module_card(icon: str, title: str, subtitle: str, description: str, bullets: list[str]) -> None:
    """Render a modern pastel module navigation card."""
    escaped_title = html.escape(title)
    escaped_subtitle = html.escape(subtitle)
    escaped_desc = html.escape(description)
    bullets_html = "".join(f"<li>{b}</li>" for b in bullets)

    card_html = (
        f'<div class="module-card">'
        f'<div>'
        f'<div class="module-header">'
        f'<div class="module-icon">{icon}</div>'
        f'<div>'
        f'<h3 class="module-title">{escaped_title}</h3>'
        f'<span style="font-size: 0.8rem; color: var(--text-subtext);">{escaped_subtitle}</span>'
        f'</div>'
        f'</div>'
        f'<div class="module-desc">'
        f'{escaped_desc}'
        f'<ul style="margin: 8px 0 0 0; padding-left: 20px; font-size: 0.85rem; color: var(--text-muted);">'
        f'{bullets_html}'
        f'</ul>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    if hasattr(st, "html"):
        st.html(card_html)
    else:
        st.markdown(card_html, unsafe_allow_html=True)


def apply_plotly_theme(fig: go.Figure, is_dark: bool | None = None) -> go.Figure:
    """Apply Zapan reference-aligned styling to a Plotly figure with Navy & Berry palette."""
    if is_dark is None:
        active_theme = st.session_state.get("app_theme_radio") or st.session_state.get("app_theme", "Light Theme")
        is_dark = (active_theme == "Dark Theme")

    font_color = "#F8FAFC" if is_dark else "#26334D"
    tick_color = "#94A3B8" if is_dark else "#64748B"
    title_color = "#CBD5E1" if is_dark else "#26334D"
    grid_color = "rgba(255, 255, 255, 0.08)" if is_dark else "#EAEFF5"
    line_color = "rgba(255, 255, 255, 0.15)" if is_dark else "#DCE3EC"
    hover_bg = "#182234" if is_dark else "#26334D"

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Plus Jakarta Sans, Inter, -apple-system, sans-serif",
            color=font_color,
            size=11,
        ),
        hoverlabel=dict(
            bgcolor=hover_bg,
            font_size=12,
            font_family="Plus Jakarta Sans, Inter, sans-serif",
            font_color="#FFFFFF",
            bordercolor=hover_bg,
        ),
        margin=dict(l=20, r=20, t=30, b=20),
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        tickfont=dict(color=tick_color, size=10),
        title_font=dict(color=title_color, size=11, weight="bold"),
        linecolor=line_color,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=grid_color,
        gridwidth=1,
        zeroline=False,
        tickfont=dict(color=tick_color, size=10),
        title_font=dict(color=title_color, size=11, weight="bold"),
        linecolor=line_color,
    )
    return fig


def render_simulated_data_badge() -> None:
    """Render mandatory simulated data disclosure banner."""
    badge_html = (
        '<div class="notice-banner">'
        '<strong style="color: var(--text-main);">SIMULATED DATASET:</strong> '
        'All metrics, subscriber journeys, catalog events, and experiment results in StreamIQ are synthetically generated '
        'using a deterministic simulation engine. StreamIQ is a portfolio analytics platform and is not affiliated with any commercial streaming service.'
        '</div>'
    )
    if hasattr(st, "html"):
        st.html(badge_html)
    else:
        st.markdown(badge_html, unsafe_allow_html=True)


def render_traffic_split_card(
    srm: dict[str, Any],
    sample_sizes: dict[str, int],
    expected_split_str: str = "50/50",
) -> None:
    """Render high-contrast, theme-aware Traffic Split Check (SRM) card and table."""
    ctrl_n = sample_sizes.get("control", 0)
    treat_n = sample_sizes.get("treatment", 0)
    total_n = sample_sizes.get("total", ctrl_n + treat_n) or 1
    ctrl_pct = (ctrl_n / total_n) * 100
    treat_pct = (treat_n / total_n) * 100

    is_error = srm.get("detected", False)
    card_cls = "srm-status-card error" if is_error else "srm-status-card"
    status_icon = "🚨" if is_error else "✅"
    status_title = (
        "Traffic Mismatch Detected!"
        if is_error
        else "Traffic Split Confirmed Healthy."
    )
    status_desc = (
        f"Significant deviation from expected {expected_split_str} split detected (p < 0.01 threshold)."
        if is_error
        else f"Variant allocation matches the expected {expected_split_str} split."
    )

    chi2 = srm.get("chi2_stat", 0.0)
    pval = srm.get("p_value", 1.0)

    html_card = f"""
    <div class="{card_cls}">
        <div class="srm-status-title">{status_icon} {status_title}</div>
        <div class="srm-status-desc">{status_desc}</div>
        <div class="srm-stats-row">
            <span class="srm-stats-item"><strong>Chi-square statistic:</strong> {chi2:.2f}</span>
            <span class="srm-stats-item"><strong>SRM p-value:</strong> {pval:.4f}</span>
            <span class="srm-stats-item"><strong>Expected allocation:</strong> {expected_split_str}</span>
        </div>
    </div>
    <table class="custom-themed-table">
        <thead>
            <tr>
                <th>Variant</th>
                <th>Sample Size</th>
                <th>Actual Traffic Share</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="val-bold">Control (A)</td>
                <td>{ctrl_n:,}</td>
                <td>{ctrl_pct:.1f}%</td>
            </tr>
            <tr>
                <td class="val-bold">Treatment (B)</td>
                <td>{treat_n:,}</td>
                <td>{treat_pct:.1f}%</td>
            </tr>
        </tbody>
    </table>
    """
    if hasattr(st, "html"):
        st.html(html_card)
    else:
        st.markdown(html_card, unsafe_allow_html=True)


def render_guardrails_table(comp: dict[str, Any], err: dict[str, Any]) -> None:
    """Render high-contrast, theme-aware Quality Safeguards guardrail table."""
    comp_delta = comp.get("delta_pp", 0.0)
    err_delta = err.get("delta_pp", 0.0)

    comp_healthy = comp_delta >= -1.0
    err_healthy = err_delta <= 0.5

    comp_status_cls = "status-pill-healthy" if comp_healthy else "status-pill-warning"
    comp_status_txt = "Healthy" if comp_healthy else "Warning"
    comp_icon = "✅" if comp_healthy else "⚠️"

    err_status_cls = "status-pill-healthy" if err_healthy else "status-pill-warning"
    err_status_txt = "Healthy" if err_healthy else "Warning"
    err_icon = "✅" if err_healthy else "⚠️"

    html_table = f"""
    <table class="custom-themed-table">
        <thead>
            <tr>
                <th>Guardrail Metric</th>
                <th>Control</th>
                <th>Treatment</th>
                <th>Difference</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="val-bold">Playback Completion Rate</td>
                <td>{comp.get('control_pct', 0.0):.1f}%</td>
                <td>{comp.get('treatment_pct', 0.0):.1f}%</td>
                <td>{comp_delta:+.2f} pp</td>
                <td><span class="status-pill {comp_status_cls}">{comp_icon} {comp_status_txt}</span></td>
            </tr>
            <tr>
                <td class="val-bold">Playback Error Rate</td>
                <td>{err.get('control_pct', 0.0):.2f}%</td>
                <td>{err.get('treatment_pct', 0.0):.2f}%</td>
                <td>{err_delta:+.2f} pp</td>
                <td><span class="status-pill {err_status_cls}">{err_icon} {err_status_txt}</span></td>
            </tr>
        </tbody>
    </table>
    """
    if hasattr(st, "html"):
        st.html(html_table)
    else:
        st.markdown(html_table, unsafe_allow_html=True)


