"""Candidate Analysis page."""

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
    st.caption("Analyze individual candidates against project requirements.")

    st.divider()

    with st.sidebar:
        st.subheader("Filter Criteria")
        required_skills_input = st.text_input(
            "Required Skills (comma-separated)",
            placeholder="Python, Machine Learning, AWS",
        )
        seniority = st.multiselect(
            "Seniority",
            ["junior", "mid", "senior", "lead", "principal", "staff"],
            default=[],
        )
        min_years = st.slider("Min Years Experience", 0.0, 20.0, 0.0, 0.5)
        domain_input = st.text_input("Domain", placeholder="fintech")
        must_available = st.checkbox("Must be available", value=True)
        min_avail = st.slider("Min Availability %", 0, 100, 30)
        project_domain = st.selectbox(
            "Project Domain (for scoring)",
            [
                "general",
                "fintech",
                "healthcare",
                "e-commerce",
                "cloud",
                "ml",
                "cybersecurity",
                "logistics",
            ],
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

        # 1. Pipeline Metrics
        metrics = candidate_filter.get_pipeline_metrics(criteria)

        st.markdown("### Candidate Pipeline Metrics")
        cols = st.columns(6)
        cols[0].metric("Total Employees", metrics["total_employees"])
        cols[1].metric("Available", metrics["available_employees"])
        cols[2].metric("Skill Match", metrics["skill_matched"])
        cols[3].metric("Domain Match", metrics["domain_matched"])
        cols[4].metric("Eligible", metrics["eligible_candidates"])
        cols[5].metric("Scored", metrics["eligible_candidates"])  # Scored is same as eligible

        st.divider()

        # 2. View Selection (Tabs)
        tab_eligible, tab_all = st.tabs(["✅ Eligible Candidates", "👥 All Employees"])

        # Fetch data
        all_employees = candidate_filter.get_all_candidates()  # Wait, get_all_candidates applies an availability filter. We should get actually ALL employees
        # We can just query them directly or use the repository
        all_emps = (
            session.query(Employee)
            .options(
                __import__("sqlalchemy")
                .orm.joinedload(Employee.employee_skills)
                .joinedload(__import__("models.employee").employee.EmployeeSkill.skill),
                __import__("sqlalchemy").orm.joinedload(Employee.assignments),
            )
            .all()
        )

        candidates = candidate_filter.filter_candidates_direct(criteria)
        eligible_ids = {c.id for c in candidates}

        scorer = ProjectFitScorer()

        with tab_eligible:
            st.markdown(f"**Showing {len(candidates)} of {metrics['total_employees']} employees**")

            if not candidates:
                st.info("No candidates match the current filter. Try broadening criteria.")
            else:
                scored = scorer.score_many(candidates, dummy_req)
                for candidate in scored[:50]:
                    render_candidate_score_card(candidate, show_details=True)
                    evidence_svc = EvidenceService(UserRole.MANAGER)
                    normalized_ev = evidence_svc.from_candidate(candidate)
                    if normalized_ev:
                        render_evidence_items(
                            normalized_ev, title="Database Evidence", collapsed=True
                        )
                    st.divider()

        with tab_all:
            st.markdown(f"**Showing all {len(all_emps)} employees**")

            # Create a simple table view for all employees
            data = []
            for emp in all_emps:
                # Basic exclusion reason
                reason = ""
                if emp.id not in eligible_ids:
                    if (
                        not emp.is_available
                        or emp.availability_percentage < criteria.minimum_availability_percentage
                    ):
                        reason = "Unavailable"
                    elif criteria.required_skill_names:
                        emp_skills = {
                            es.skill.name.lower() for es in emp.employee_skills if es.skill
                        }
                        req_skills = {s.lower() for s in criteria.required_skill_names}
                        if not req_skills.issubset(emp_skills):
                            reason = "Missing mandatory skills"

                    if not reason and criteria.domains:
                        domain_lower = [d.lower() for d in criteria.domains]
                        if not any(d in (emp.domain_expertise or "").lower() for d in domain_lower):
                            reason = "Domain mismatch"

                    if not reason and criteria.minimum_years_experience > emp.years_of_experience:
                        reason = "Insufficient experience"

                    if not reason:
                        reason = "Other constraint (e.g., seniority, department)"

                # Just grab current tech stack
                tech_stack = ", ".join([es.skill.name for es in emp.employee_skills if es.skill])

                data.append(
                    {
                        "Employee ID": emp.id,
                        "Name": emp.name,
                        "Role": emp.role,
                        "Department": emp.department,
                        "Experience": emp.years_of_experience,
                        "Current Tech Stack": tech_stack,
                        "Availability": f"{emp.availability_percentage}%",
                        "Location": emp.location or "N/A",
                        "Projects Completed": len(emp.assignments),
                        "Eligibility": "✅ Eligible" if emp.id in eligible_ids else f"❌ {reason}",
                    }
                )

            st.dataframe(data, use_container_width=True)
