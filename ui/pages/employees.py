"""Employees page — browse and search the employee database."""

from __future__ import annotations

import streamlit as st

from db.session import get_db
from repositories.employee_repo import EmployeeRepository


def render() -> None:
    st.title("👤 Employees")
    st.caption("Browse the structured employee database.")

    search = st.text_input(
        "Search by name, role, or department", placeholder="e.g. Python engineer"
    )
    seniority_filter = st.multiselect(
        "Seniority",
        ["junior", "mid", "senior", "lead", "principal", "staff"],
    )
    available_only = st.checkbox("Available only", value=False)

    with get_db() as session:
        repo = EmployeeRepository(session)
        employees = repo.list_with_skills(limit=500)

        # Apply filters
        if search:
            q = search.lower()
            employees = [
                e
                for e in employees
                if q in e.name.lower() or q in e.role.lower() or q in e.department.lower()
            ]
        if seniority_filter:
            employees = [e for e in employees if e.seniority in seniority_filter]
        if available_only:
            employees = [e for e in employees if e.is_available]

        st.markdown(f"**{len(employees)} employees** found")
        st.divider()

        for emp in employees[:100]:
            with st.expander(f"{emp.name} — {emp.role} ({emp.seniority.title()})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Department:** {emp.department}")
                    st.write(f"**Experience:** {emp.years_of_experience:.1f} years")
                    st.write(f"**Domain:** {emp.domain_expertise or 'N/A'}")
                    st.write(f"**Location:** {emp.location or 'N/A'}")
                with col2:
                    avail_str = (
                        f"{emp.availability_percentage}%" if emp.is_available else "Unavailable"
                    )
                    st.write(f"**Availability:** {avail_str}")
                    if emp.performance_rating:
                        st.write(f"**Performance:** {emp.performance_rating:.1f}/5.0")
                    st.write(f"**Timezone:** {emp.timezone or 'UTC'}")

                if emp.employee_skills:
                    skills_str = ", ".join(
                        f"{es.skill.name} (L{es.proficiency})"
                        for es in emp.employee_skills
                        if es.skill
                    )
                    st.write(f"**Skills:** {skills_str}")

                if emp.certifications:
                    certs_str = ", ".join(c.name for c in emp.certifications)
                    st.write(f"**Certifications:** {certs_str}")
