"""AllocAI — Main Streamlit Application Entry Point.

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
    page_title="AllocAI",
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
    logger.info("AllocAI initialized.")


initialize()

# ── Navigation ────────────────────────────────────────────────────────────────
PAGES = {
    "📊 Dashboard": "dashboard",
    "📋 Create Project": "create_project",
    "🔍 Candidate Analysis": "candidate_analysis",
    "👥 Recommended Team": "recommended_team",
    "👤 Employees": "employees",
    "📥 Employee Import": "employee_import",
    "📥 Dataset Import": "dataset_import",
    "📁 Project History": "project_history",
    "🧠 Hindsight Memory": "hindsight_memory",
    "📚 Learning Center": "learning_center",
    "🔧 System Diagnostics": "system_diagnostics",
}

with st.sidebar:
    st.markdown("# 🧠 AllocAI")
    st.caption("Match the right people. Learn from every project.")
    st.divider()

    selected = st.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")

    st.divider()
    st.caption("Evidence Sources")
    st.markdown("🗄️ **Database** — structured facts")
    st.markdown("🧠 **Hindsight** — organizational memory")
    st.markdown("📄 **RAG** — company documentation")
    st.markdown("🤖 **LLM** — inference (not fact)")
    st.divider()
    st.caption("v0.1.0 | AllocAI")

# ── Page routing ──────────────────────────────────────────────────────────────
page_module_name = PAGES[selected]

import importlib

try:
    module = importlib.import_module(f"ui.pages.{page_module_name}")
    module.render()
except Exception as e:
    st.error(f"Error loading page '{page_module_name}': {e}")
    logger.exception("Page load error for %s", page_module_name)
    raise
