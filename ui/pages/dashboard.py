"""Dashboard page — Organizational Staffing Intelligence.

Metrics shown (real database data only):
  - Total Employees
  - Available Employees
  - Staffing Requests (all stored projects)
  - Completed Projects (with recorded outcomes)
  - Hindsight Memories
  - Recent Project Outcomes
  - Recent Organizational Learning

NOT shown:
  - Active Projects (this is a staffing tool, not a PM tracker)
  - Fabricated or hard-coded numbers
"""

from __future__ import annotations

import streamlit as st

from db.session import get_db
from hindsight.adapter import get_hindsight_adapter
from repositories.employee_repo import EmployeeRepository
from repositories.outcome_repo import OutcomeRepository
from repositories.project_repo import ProjectRepository


def render() -> None:
    # ── Hero header ───────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="padding: 2rem 0 1rem 0;">
            <div style="font-size:2.4rem;font-weight:800;letter-spacing:-0.03em;
                        background:linear-gradient(135deg,#58a6ff,#a371f7);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                        background-clip:text;line-height:1.1;">
                AllocAI
            </div>
            <div style="font-size:1.1rem;font-weight:600;color:#8b949e;margin-top:4px;">
                AI Project Staffing Intelligence & Organizational Memory
            </div>
            <div style="font-size:0.9rem;color:#6e7681;margin-top:4px;font-style:italic;">
                "Match the right people. Learn from every project."
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Load real data ────────────────────────────────────────────────────────
    try:
        with get_db() as session:
            emp_repo = EmployeeRepository(session)
            proj_repo = ProjectRepository(session)
            outcome_repo = OutcomeRepository(session)

            total_employees = emp_repo.count()
            available_employees = emp_repo.count_available(minimum_availability_pct=30)
            total_projects = proj_repo.count()
            completed_projects = proj_repo.count_by_status("completed")
            recent_outcomes = outcome_repo.list_recent(5)
            recent_outcomes_data = [
                {
                    "project_id": o.project_id,
                    "outcome_status": o.outcome_status,
                    "quality_rating": o.quality_rating,
                }
                for o in recent_outcomes
            ]
    except Exception as exc:
        st.error(f"Unable to load dashboard data: {exc}")
        return

    try:
        hindsight = get_hindsight_adapter()
        memory_count = hindsight.count()
    except Exception:
        memory_count = 0

    # ── KPI row ───────────────────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("👤 Total Employees", total_employees)
    col2.metric("✅ Available Now", available_employees)
    col3.metric("📋 Staffing Requests", total_projects)
    col4.metric("🏁 Completed Projects", completed_projects)
    col5.metric("🧠 Organizational Memories", memory_count)

    st.divider()

    # ── Two column layout ─────────────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("🕐 Recent Project Outcomes")
        if recent_outcomes_data:
            for outcome in recent_outcomes_data:
                status_icon = {
                    "success": "✅",
                    "partial_success": "🟡",
                    "failure": "❌",
                    "cancelled": "🚫",
                }.get(outcome["outcome_status"], "❓")
                rating = outcome["quality_rating"]
                rating_str = f"{rating:.1f}/5.0" if rating is not None else "N/A"
                st.markdown(
                    f"<div style='padding:8px 12px;border-left:3px solid #30363d;"
                    f"margin:4px 0;background:rgba(255,255,255,0.02);border-radius:0 6px 6px 0;'>"
                    f"{status_icon} <b>Project {outcome['project_id']}</b> — "
                    f"{outcome['outcome_status']} · Quality: {rating_str}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info(
                "No project outcomes recorded yet.  \n"
                "Use **Learning Center** after a project completes to capture lessons."
            )

    with col_right:
        st.subheader("💡 Staffing Workflow")
        steps = [
            ("1", "Create Staffing Request", "Describe your project needs"),
            ("2", "Analyze Requirements", "AI extracts structured requirements"),
            ("3", "Find Suitable People", "Scored against current & historical data"),
            ("4", "Recall Organizational Memory", "Hindsight surfaces relevant lessons"),
            ("5", "Get Recommended Team", "Complementary team sized to your request"),
            ("6", "Record Project Learning", "Capture outcomes to improve future staffing"),
        ]
        for num, title, desc in steps:
            st.markdown(
                f"<div style='display:flex;align-items:flex-start;gap:10px;"
                f"padding:6px 0;border-bottom:1px solid rgba(48,54,61,0.5);'>"
                f"<div style='min-width:20px;height:20px;border-radius:50%;"
                f"background:linear-gradient(135deg,#1f6feb,#388bfd);"
                f"display:flex;align-items:center;justify-content:center;"
                f"font-size:0.65rem;font-weight:700;color:#fff;margin-top:1px;'>{num}</div>"
                f"<div><div style='font-size:0.85rem;font-weight:600;color:#e6edf3;'>{title}</div>"
                f"<div style='font-size:0.75rem;color:#6e7681;'>{desc}</div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Architecture diagram ───────────────────────────────────────────────────
    with st.expander("🏛️ How AllocAI Works — Technical Pipeline", expanded=False):
        st.code(
            """
Staffing Request
    → Project Analyzer (AI requirement extraction)
    → Candidate Filter (SQL — database skills & availability)
    → Project Fit Scorer (deterministic weighted scoring)
    → Hindsight Recall (relevant organizational memories)
    → RAG Retrieval (company engineering standards)
    → Team Composer (complementary team selection)
    → AI Explanation (evidence-based rationale)
    → Recommended Team

Project Completion
    → Learning Center (outcome + feedback + lessons)
    → Learning Agent (AI lesson extraction)
    → Hindsight Retain (organizational memory)
    → Better Future Staffing Recommendations
            """,
            language="text",
        )

