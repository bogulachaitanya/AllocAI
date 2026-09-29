"""Dashboard page — AllocAI Workspace Overview.

Metrics come exclusively from real database data.
No hard-coded numbers. No fabricated statistics.

Shows:
  - KPI metric cards (employees, availability, requests, completed, memories)
  - CTA hero card (Create Staffing Request)
  - Staffing workflow visual
  - Recent project outcomes
  - Pipeline architecture expandable
"""

from __future__ import annotations

import streamlit as st


def render() -> None:
    # ── CTA Hero Card ─────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(59,130,246,0.1));
                    border:1px solid rgba(99,102,241,0.25);border-radius:18px;
                    padding:2rem 2.5rem;margin-bottom:1.5rem;
                    box-shadow:0 0 30px rgba(99,102,241,0.08);">
            <div style="font-size:1.3rem;font-weight:800;color:#F1F5F9;margin-bottom:0.5rem;">
                Need to build a project team?
            </div>
            <div style="color:#94A3B8;font-size:0.9rem;max-width:520px;line-height:1.6;margin-bottom:1.25rem;">
                Describe your project requirements and AllocAI will identify suitable people
                using your organisation's employee data and organisational memory.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_cta, col_rest = st.columns([1, 3])
    with col_cta:
        if st.button("📋 Create Staffing Request", type="primary", use_container_width=True, key="dash_cta"):
            st.session_state["selected_page"] = "create_project"
            st.rerun()

    st.divider()

    # ── Load real data ────────────────────────────────────────────────────────
    try:
        from db.session import get_db
        from hindsight.adapter import get_hindsight_adapter
        from repositories.employee_repo import EmployeeRepository
        from repositories.outcome_repo import OutcomeRepository
        from repositories.project_repo import ProjectRepository

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
        st.error(f"Unable to load workspace data. Please try again. ({exc})")
        return

    try:
        hindsight = get_hindsight_adapter()
        memory_count = hindsight.count()
    except Exception:
        memory_count = 0

    # ── KPI row ───────────────────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("👤 Total Employees", total_employees)
    col2.metric("✅ Available", available_employees)
    col3.metric("📋 Staffing Requests", total_projects)
    col4.metric("🏁 Completed", completed_projects)
    col5.metric("🧠 Org Memories", memory_count)

    st.divider()

    # ── Two-column layout ─────────────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown(
            """<div style="font-size:1rem;font-weight:700;color:#F1F5F9;margin-bottom:0.75rem;">
                🕐 Recent Project Outcomes
            </div>""",
            unsafe_allow_html=True,
        )
        if recent_outcomes_data:
            for outcome in recent_outcomes_data:
                status_icon = {
                    "success": "✅",
                    "partial_success": "🟡",
                    "failure": "❌",
                    "cancelled": "🚫",
                }.get(outcome["outcome_status"], "❓")
                rating = outcome["quality_rating"]
                rating_str = f"{rating:.1f}/5.0" if rating is not None else "Not rated"
                st.markdown(
                    f"""<div style="padding:10px 14px;border-left:3px solid rgba(99,102,241,0.4);
                               margin:5px 0;background:rgba(255,255,255,0.02);
                               border-radius:0 8px 8px 0;">
                        {status_icon} <b style="color:#E2E8F0;">Project {outcome['project_id']}</b>
                        <span style="color:#64748B;font-size:0.82rem;"> — {outcome['outcome_status']} ·
                        Quality: {rating_str}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                """<div class="alloc-glass" style="padding:1.5rem;text-align:center;">
                    <div style="font-size:1.5rem;margin-bottom:0.5rem;">📂</div>
                    <div style="color:#64748B;font-size:0.85rem;">
                        No project outcomes recorded yet.<br>
                        Use <b>Learning Center</b> after a project completes to capture lessons.
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

    with col_right:
        st.markdown(
            """<div style="font-size:1rem;font-weight:700;color:#F1F5F9;margin-bottom:0.75rem;">
                🔄 Staffing Workflow
            </div>""",
            unsafe_allow_html=True,
        )
        steps = [
            ("01", "Create Staffing Request", "Describe project needs"),
            ("02", "Analyse Requirements", "AI extracts structured needs"),
            ("03", "Find Relevant People", "Scored against employee data"),
            ("04", "Recall Org Memory", "Hindsight surfaces lessons"),
            ("05", "Get Recommended Team", "Optimal team composed"),
            ("06", "Record Learning", "Outcomes improve future staffing"),
        ]
        for num, title, desc in steps:
            st.markdown(
                f"""<div style="display:flex;align-items:flex-start;gap:10px;
                               padding:6px 0;border-bottom:1px solid rgba(55,65,81,0.4);">
                    <div class="alloc-step-num">{num}</div>
                    <div>
                        <div style="font-size:0.82rem;font-weight:600;color:#E2E8F0;">{title}</div>
                        <div style="font-size:0.72rem;color:#4B5563;">{desc}</div>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Architecture diagram ──────────────────────────────────────────────────
    with st.expander("🏛️ How AllocAI Works — Technical Pipeline", expanded=False):
        st.code(
            """
Staffing Request
    → Project Analyser (AI requirement extraction)
    → Candidate Filter (SQL — database skills & availability)
    → Project Fit Scorer (deterministic weighted scoring: 8 dimensions)
    → Hindsight Recall (relevant organisational memories)
    → RAG Retrieval (company engineering standards)
    → Team Composer (complementary team selection)
    → AI Explanation (evidence-based rationale)
    → Recommended Team

Project Completion
    → Learning Center (outcome + feedback + lessons)
    → Learning Agent (AI lesson extraction)
    → Hindsight Retain (organisational memory)
    → Better Future Staffing Recommendations
            """,
            language="text",
        )
