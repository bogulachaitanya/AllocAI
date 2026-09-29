"""ALLOC — Main Streamlit Application Entry Point.

Run with: streamlit run app.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent))

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AllocAI — AI Project Staffing Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Database initialization (runs once per session) ───────────────────────────
@st.cache_resource
def initialize() -> None:
    """Initialize DB and seed data once per app lifecycle."""
    from db.init_db import init_db

    init_db(seed=True)
    logger.info("ALLOC initialized.")


initialize()

# ── Inject global CSS ──────────────────────────────────────────────────────────
from ui.style import inject_global_css  # noqa: E402

inject_global_css()

# ── Navigation ────────────────────────────────────────────────────────────────
NAV_SECTIONS = {
    "🎯 Staffing": {
        "📊 Dashboard": "dashboard",
        "📋 Create Staffing Request": "create_project",
        "🔍 Candidate Analysis": "candidate_analysis",
        "👥 Recommended Team": "recommended_team",
    },
    "👤 People": {
        "🧑‍💼 Employees": "employees",
        "📥 Employee Import": "employee_import",
    },
    "🧠 Organizational Knowledge": {
        "📁 Project History": "project_history",
        "🧠 Hindsight Memory": "hindsight_memory",
        "📚 Learning Center": "learning_center",
    },
    "⚙️ Administration": {
        "📥 Dataset Import": "dataset_import",
        "🔧 System Diagnostics": "system_diagnostics",
    },
}

# Flat map for routing
PAGES: dict[str, str] = {}
for _, pages in NAV_SECTIONS.items():
    PAGES.update(pages)

with st.sidebar:
    st.markdown(
        """
        <div style="padding: 0.5rem 0 1rem 0;">
            <div style="font-size:1.5rem;font-weight:800;
                        background:linear-gradient(135deg,#58a6ff,#a371f7);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                        background-clip:text;">
                🧠 AllocAI
            </div>
            <div style="font-size:0.72rem;color:#6e7681;margin-top:2px;font-weight:500;">
                AI Project Staffing Intelligence
            </div>
            <div style="font-size:0.72rem;color:#8b949e;margin-top:1px;font-style:italic;">
                "Match the right people. Learn from every project."
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    # Grouped navigation
    all_labels = list(PAGES.keys())
    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = all_labels[0]

    for section_name, section_pages in NAV_SECTIONS.items():
        st.markdown(
            f"<div style='font-size:0.68rem;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:0.08em;color:#6e7681;padding:8px 0 4px 0;'>"
            f"{section_name}</div>",
            unsafe_allow_html=True,
        )
        for label in section_pages:
            is_active = st.session_state.get("selected_page") == label
            btn_style = (
                "background:rgba(88,166,255,0.1);border:1px solid rgba(88,166,255,0.3);"
                "color:#58a6ff;" if is_active
                else "background:transparent;border:1px solid transparent;color:#8b949e;"
            )
            if st.button(
                label,
                key=f"nav_{label}",
                use_container_width=True,
            ):
                st.session_state["selected_page"] = label
                st.rerun()

    st.divider()
    st.markdown(
        """
        <div style="font-size:0.7rem;color:#6e7681;line-height:1.6;">
            <div>🗄️ <b>Database</b> — structured facts</div>
            <div>🧠 <b>Hindsight</b> — organizational memory</div>
            <div>📄 <b>RAG</b> — company documentation</div>
            <div>🤖 <b>LLM</b> — inference (not fact)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown(
        "<div style='font-size:0.68rem;color:#6e7681;'>v0.1.0 · AllocAI</div>",
        unsafe_allow_html=True,
    )

# ── Page routing ──────────────────────────────────────────────────────────────
selected = st.session_state.get("selected_page", all_labels[0])
page_module_name = PAGES.get(selected, "dashboard")

import importlib  # noqa: E402

try:
    module = importlib.import_module(f"ui.pages.{page_module_name}")
    module.render()
except Exception as e:
    st.error(f"Error loading page '{page_module_name}': {e}")
    logger.exception("Page load error for %s", page_module_name)
    raise

