"""AllocAI — Main Streamlit Application Entry Point.

Architecture:
    Public (no auth required):
        landing  → Public landing page
        login    → Sign in
        signup   → Create account

    Protected (requires login):
        dashboard, create_project, candidate_analysis,
        recommended_team, employees, employee_import,
        project_history, hindsight_memory, learning_center,
        dataset_import, system_diagnostics

Run with: streamlit run app.py
"""

from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path

import streamlit as st

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="AllocAI — AI Project Staffing Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── DB initialization (once per app lifecycle) ────────────────────────────────
@st.cache_resource
def initialize() -> None:
    """Initialize DB and seed data once per app lifecycle."""
    from db.init_db import init_db
    init_db(seed=True)
    logger.info("AllocAI initialized.")


initialize()

# ── Global CSS ────────────────────────────────────────────────────────────────
from ui.style import inject_global_css  # noqa: E402

inject_global_css()

# ── Auth imports ──────────────────────────────────────────────────────────────
from services.user_auth import get_session_user, is_authenticated, logout  # noqa: E402

# ── Public pages (no auth) ────────────────────────────────────────────────────
PUBLIC_PAGES = {"landing", "login", "signup"}

# ── Authenticated navigation structure ───────────────────────────────────────
NAV_SECTIONS: dict[str, dict[str, str]] = {
    "STAFFING": {
        "🏠 Overview": "dashboard",
        "📋 Create Staffing Request": "create_project",
        "🔍 Candidate Analysis": "candidate_analysis",
        "👥 Recommended Team": "recommended_team",
    },
    "PEOPLE": {
        "🧑‍💼 Employees": "employees",
        "📥 Employee Import": "employee_import",
    },
    "KNOWLEDGE": {
        "📁 Project History": "project_history",
        "🧠 Organisational Memory": "hindsight_memory",
        "📚 Learning Center": "learning_center",
    },
    "ADMIN": {
        "📥 Dataset Import": "dataset_import",
        "🔧 System Diagnostics": "system_diagnostics",
    },
}

# Flat label→module map
PAGES: dict[str, str] = {}
for _, section in NAV_SECTIONS.items():
    PAGES.update(section)

# Reverse: module → label
MODULE_TO_LABEL: dict[str, str] = {v: k for k, v in PAGES.items()}

# ── Routing logic ─────────────────────────────────────────────────────────────

def _get_current_page() -> str:
    return st.session_state.get("selected_page", "landing")


def _set_page(page: str) -> None:
    st.session_state["selected_page"] = page
    st.rerun()


def _render_page(module_name: str) -> None:
    try:
        module = importlib.import_module(f"ui.pages.{module_name}")
        module.render()
    except Exception as exc:
        st.error(
            "Something went wrong while loading this section. Please try again.",
        )
        logger.exception("Page load error for %s: %s", module_name, exc)


# ── Public layout (no sidebar) ────────────────────────────────────────────────

def _render_public_topbar(current: str) -> None:
    """Minimal top navigation for public pages."""
    col_logo, col_nav, col_cta = st.columns([1, 3, 1])
    with col_logo:
        st.markdown(
            """<div style="padding:0.75rem 0;font-size:1.2rem;font-weight:900;
                          background:linear-gradient(135deg,#6366F1,#3B82F6);
                          -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                          background-clip:text;letter-spacing:-0.02em;">
                🧠 AllocAI
            </div>""",
            unsafe_allow_html=True,
        )
    with col_cta:
        col_s, col_l = st.columns(2)
        with col_s:
            if st.button("Sign Up", type="primary", key="topbar_signup", use_container_width=True):
                _set_page("signup")
        with col_l:
            if st.button("Sign In", key="topbar_login", use_container_width=True):
                _set_page("login")
    st.markdown("<hr style='border-color:rgba(55,65,81,0.4);margin:0 0 1rem 0;'>", unsafe_allow_html=True)


def _render_public_page(page: str) -> None:
    _render_public_topbar(page)
    _render_page(page)


# ── Authenticated sidebar ─────────────────────────────────────────────────────

def _render_sidebar(user) -> None:
    with st.sidebar:
        # ── Logo ──────────────────────────────────────────────────────────────
        st.markdown(
            """<div style="padding:1rem 0 0.75rem 0;">
                <div style="font-size:1.4rem;font-weight:900;
                            background:linear-gradient(135deg,#6366F1,#3B82F6);
                            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                            background-clip:text;letter-spacing:-0.02em;line-height:1.1;">
                    🧠 AllocAI
                </div>
                <div style="font-size:0.7rem;color:#4B5563;margin-top:2px;font-style:italic;">
                    Match the right people.
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        # ── User card ─────────────────────────────────────────────────────────
        initials = "".join(p[0].upper() for p in user.full_name.split()[:2])
        st.markdown(
            f"""<div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.2);
                            border-radius:10px;padding:10px 12px;margin-bottom:0.75rem;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <div style="width:34px;height:34px;border-radius:50%;flex-shrink:0;
                                background:linear-gradient(135deg,#6366F1,#3B82F6);
                                display:flex;align-items:center;justify-content:center;
                                font-weight:700;font-size:0.85rem;color:#fff;">
                        {initials}
                    </div>
                    <div style="overflow:hidden;">
                        <div style="font-size:0.85rem;font-weight:600;color:#E2E8F0;
                                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                            {user.full_name}
                        </div>
                        <div style="font-size:0.7rem;color:#6366F1;">{user.role}</div>
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        st.divider()

        # ── Navigation ────────────────────────────────────────────────────────
        current_module = st.session_state.get("selected_page", "dashboard")

        for section_name, section_pages in NAV_SECTIONS.items():
            st.markdown(
                f"<div style='font-size:0.62rem;font-weight:700;text-transform:uppercase;"
                f"letter-spacing:0.1em;color:#374151;padding:8px 0 4px 0;'>"
                f"{section_name}</div>",
                unsafe_allow_html=True,
            )
            for label, module in section_pages.items():
                is_active = current_module == module
                style = (
                    "background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.25);"
                    "color:#A5B4FC;" if is_active
                    else "background:transparent;border:1px solid transparent;color:#94A3B8;"
                )
                btn_html = f"""<div style="{style}border-radius:7px;padding:7px 10px;
                    font-size:0.82rem;font-weight:500;cursor:pointer;margin:1px 0;
                    transition:all 0.15s;">{label}</div>"""
                if st.button(label, key=f"nav_{module}", use_container_width=True):
                    st.session_state["selected_page"] = module
                    st.rerun()

        st.divider()

        # ── Sign out ──────────────────────────────────────────────────────────
        if st.button("🚪 Sign Out", use_container_width=True, key="signout_btn"):
            logout()
            st.session_state["selected_page"] = "landing"
            st.rerun()

        # ── Version ───────────────────────────────────────────────────────────
        st.markdown(
            "<div style='font-size:0.65rem;color:#374151;margin-top:0.5rem;'>v0.2.0 · AllocAI</div>",
            unsafe_allow_html=True,
        )


def _render_app_header(user) -> None:
    """Top header bar with user context inside the main area."""
    hour = __import__("datetime").datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
    first_name = user.full_name.split()[0]

    st.markdown(
        f"""<div style="display:flex;justify-content:space-between;align-items:center;
                       margin-bottom:0.5rem;">
            <div>
                <div style="font-size:1.4rem;font-weight:800;color:#F1F5F9;">
                    {greeting}, {first_name} 👋
                </div>
                <div style="font-size:0.83rem;color:#64748B;">
                    {user.organization} · {user.role}
                </div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )


# ── Main routing ──────────────────────────────────────────────────────────────

current_page = _get_current_page()

if not is_authenticated():
    # Public: only landing, login, signup
    if current_page not in PUBLIC_PAGES:
        current_page = "landing"
        st.session_state["selected_page"] = "landing"
    _render_public_page(current_page)

else:
    user = get_session_user()

    # Redirect public pages to dashboard after login
    if current_page in PUBLIC_PAGES:
        current_page = "dashboard"
        st.session_state["selected_page"] = "dashboard"

    # Resolve module name (handle label or module keys)
    module_name = PAGES.get(current_page, current_page)

    # Render sidebar
    _render_sidebar(user)

    # Render app header on dashboard
    if module_name == "dashboard":
        _render_app_header(user)

    # Render page content
    _render_page(module_name)
