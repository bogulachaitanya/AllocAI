"""Dashboard page — Organizational Staffing Intelligence.

Metrics shown:
  - Total Employees
  - Available Employees
  - Staffing Requests (all stored projects)
  - Completed Projects (with recorded outcomes)
  - Hindsight Memories
  - Recent Project Outcomes

NOT shown:
  - Active Projects (this is a staffing tool, not a PM tracker)
"""

from __future__ import annotations

import streamlit as st

from db.session import get_db
from hindsight.adapter import get_hindsight_adapter
from repositories.employee_repo import EmployeeRepository
from repositories.outcome_repo import OutcomeRepository
from repositories.project_repo import ProjectRepository


def render() -> None:
    st.title("📊 AllocAI Dashboard")
    st.caption("AI-powered staffing intelligence and organizational memory")

    st.divider()

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

    hindsight = get_hindsight_adapter()
    memory_count = hindsight.count()

    # ── KPI row ───────────────────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("👤 Total Employees", total_employees)
    col2.metric("✅ Available Now", available_employees)
    col3.metric("📁 Staffing Requests", total_projects)
    col4.metric("🏁 Completed Projects", completed_projects)
    col5.metric("🧠 Hindsight Memories", memory_count)

    st.divider()

    col_left, col_right = st.columns(2)

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
                    f"{status_icon} **Project {outcome['project_id']}** — "
                    f"{outcome['outcome_status']} | Quality: {rating_str}"
                )
        else:
            st.info(
                "No project outcomes recorded yet. "
                "Use **Learning Center** after a project completes."
            )

    with col_right:
        st.subheader("💡 Staffing Workflow")
        st.markdown(
            """
        1. 📋 **Create Staffing Request** — describe project requirements
        2. 🔍 **Analyze Requirements** — LLM extracts structured needs
        3. 👥 **Get Team Recommendation** — scored candidates + Hindsight
        4. 📚 **Record Outcome** — feed the organizational learning loop
        5. 🧠 **Hindsight Improves** — future recommendations get smarter
        """
        )

    st.divider()
    st.subheader("🏛️ Staffing Intelligence Pipeline")
    st.code(
        """
Project Requirements
    → Project Analyzer (LLM)
    → Candidate Filter (SQL)
    → Project Fit Scorer (deterministic)
    → Hindsight Recall (organizational memory)
    → RAG Retrieval (documentation)
    → Team Composer
    → LLM Explanation
    → Recommended Team

Completed Project
    → Outcome Recording (Learning Center)
    → Learning Agent (LLM lesson extraction)
    → Hindsight Retain
    → Better Future Recommendations
    """,
        language="text",
    )
