"""Candidate Analysis page — user-friendly employee matching view.

Shows the full employee pool with filtering and scoring.
Language is HR-friendly — no SQL, database IDs, or technical jargon.
"""

from __future__ import annotations

import streamlit as st

from db.session import get_db
from models.employee import Employee
from schemas.employee import EmployeeFilter, ProficiencyLevel
from schemas.project import StructuredRequirements
from services.auth import UserRole
from services.candidate_filter import CandidateFilter
from services.evidence_service import EvidenceService
from services.project_fit_scorer import ProjectFitScorer
from ui.components.evidence_card import render_evidence_items
from ui.components.score_card import render_candidate_score_card


def render() -> None:
    st.title("🔍 Candidate Analysis")
    st.caption(
        "Filter and score your employee pool against project requirements. "
        "Use the filters to find people with the right skills, experience, and availability."
    )

    st.divider()

    # ── Filters (in sidebar) ──────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            """<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                          letter-spacing:0.08em;color:#6366F1;margin-bottom:8px;">
                Filters
            </div>""",
            unsafe_allow_html=True,
        )
        required_skills_input = st.text_input(
            "Required Skills",
            placeholder="Python, SQL, AWS",
            help="Comma-separated list of skills employees must have.",
        )
        seniority = st.multiselect(
            "Seniority Level",
            ["junior", "mid", "senior", "lead", "principal", "staff"],
            default=[],
        )
        min_years = st.slider("Minimum Experience (years)", 0.0, 20.0, 0.0, 0.5)
        domain_input = st.text_input("Domain", placeholder="fintech")
        must_available = st.checkbox("Available Only", value=True)
        min_avail = st.slider("Min Availability %", 0, 100, 30)
        project_domain = st.selectbox(
            "Score Against Domain",
            ["general", "fintech", "healthcare", "e-commerce", "cloud", "ml",
             "cybersecurity", "logistics", "saas"],
            help="Domain used for scoring relevance.",
        )

    required_skills = (
        [s.strip() for s in required_skills_input.split(",") if s.strip()]
        if required_skills_input
        else []
    )

    criteria = EmployeeFilter(
        required_skill_names=required_skills,
        minimum_proficiency=ProficiencyLevel.PROFICIENT,
        minimum_years_experience=min_years,
        domains=[domain_input] if domain_input else [],
        seniority_levels=seniority,
        must_be_available=must_available,
        minimum_availability_percentage=min_avail,
    )

    dummy_req = StructuredRequirements(
        title="Candidate Analysis",
        domain=project_domain,
        required_skills=required_skills,
    )

    with get_db() as session:
        candidate_filter = CandidateFilter(session)

        # ── Pipeline metrics ──────────────────────────────────────────────────
        try:
            metrics = candidate_filter.get_pipeline_metrics(criteria)
        except Exception:
            metrics = {}

        st.markdown(
            """<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                          letter-spacing:0.08em;color:#6366F1;margin-bottom:8px;">
                Employee Matching Pipeline
            </div>""",
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("All Employees", metrics.get("total_employees", "—"))
        col2.metric("Available", metrics.get("available_employees", "—"))
        col3.metric("Skills Match", metrics.get("skill_matched", "—"))
        col4.metric("Domain Match", metrics.get("domain_matched", "—"))
        col5.metric("Eligible", metrics.get("eligible_candidates", "—"))

        st.divider()

        # ── Tabs ──────────────────────────────────────────────────────────────
        tab_eligible, tab_all = st.tabs(["✅ Eligible Candidates", "👥 All Employees"])

        # Fetch all employees
        try:
            all_emps = (
                session.query(Employee)
                .options(
                    __import__("sqlalchemy").orm.joinedload(Employee.employee_skills)
                    .joinedload(__import__("models.employee").employee.EmployeeSkill.skill),
                    __import__("sqlalchemy").orm.joinedload(Employee.assignments),
                )
                .all()
            )
        except Exception:
            all_emps = []

        candidates = candidate_filter.filter_candidates_direct(criteria)
        eligible_ids = {c.id for c in candidates}
        scorer = ProjectFitScorer()

        with tab_eligible:
            count = len(candidates)
            total = metrics.get("total_employees", "?")
            st.markdown(
                f"<div style='color:#64748B;font-size:0.83rem;margin-bottom:0.75rem;'>"
                f"Showing <b style='color:#E2E8F0;'>{count}</b> eligible employees "
                f"from {total} total</div>",
                unsafe_allow_html=True,
            )

            if not candidates:
                st.markdown(
                    """<div class="alloc-glass" style="padding:2rem;text-align:center;">
                        <div style="font-size:1.5rem;margin-bottom:0.5rem;">🔍</div>
                        <div style="font-size:0.95rem;font-weight:600;color:#94A3B8;margin-bottom:0.4rem;">
                            No employees match the current criteria
                        </div>
                        <div style="font-size:0.82rem;color:#4B5563;">
                            Try broadening your skills list, reducing the minimum experience,
                            or allowing more availability levels.
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            else:
                scored = scorer.score_many(candidates, dummy_req)
                for candidate in scored[:50]:
                    render_candidate_score_card(candidate, show_details=True)
                    evidence_svc = EvidenceService(UserRole.MANAGER)
                    normalized_ev = evidence_svc.from_candidate(candidate)
                    if normalized_ev:
                        render_evidence_items(normalized_ev, title="Evidence", collapsed=True)
                    st.markdown("<hr style='border-color:rgba(55,65,81,0.3);margin:6px 0;'>",
                                unsafe_allow_html=True)

        with tab_all:
            st.markdown(
                f"<div style='color:#64748B;font-size:0.83rem;margin-bottom:0.75rem;'>"
                f"All <b style='color:#E2E8F0;'>{len(all_emps)}</b> employees</div>",
                unsafe_allow_html=True,
            )

            data = []
            for emp in all_emps:
                reason = ""
                if emp.id not in eligible_ids:
                    if (not emp.is_available
                            or emp.availability_percentage < criteria.minimum_availability_percentage):
                        reason = "Unavailable"
                    elif criteria.required_skill_names:
                        emp_skills = {es.skill.name.lower() for es in emp.employee_skills if es.skill}
                        req_skills = {s.lower() for s in criteria.required_skill_names}
                        if not req_skills.issubset(emp_skills):
                            reason = "Missing skills"
                    if not reason and criteria.domains:
                        domain_lower = [d.lower() for d in criteria.domains]
                        if not any(d in (emp.domain_expertise or "").lower() for d in domain_lower):
                            reason = "Domain mismatch"
                    if not reason and criteria.minimum_years_experience > emp.years_of_experience:
                        reason = "Insufficient experience"
                    if not reason:
                        reason = "Other criteria"

                tech_stack = ", ".join(es.skill.name for es in emp.employee_skills if es.skill)
                data.append({
                    "Name": emp.name,
                    "Role": emp.role,
                    "Department": emp.department,
                    "Experience (yrs)": emp.years_of_experience,
                    "Skills": tech_stack,
                    "Availability": f"{emp.availability_percentage}%",
                    "Location": emp.location or "N/A",
                    "Projects Completed": len(emp.assignments),
                    "Eligibility": "✅ Eligible" if emp.id in eligible_ids else f"❌ {reason}",
                })

            st.dataframe(data, use_container_width=True)
