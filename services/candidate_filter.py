"""Candidate Filter — pure SQL-based filtering of employees.

No LLM involved. Returns a candidate pool for downstream scoring.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from models.employee import Employee
from repositories.employee_repo import EmployeeRepository
from schemas.employee import EmployeeFilter
from schemas.project import StructuredRequirements

logger = logging.getLogger(__name__)


class CandidateFilter:
    """Applies structured DB filters to produce a candidate pool."""

    def __init__(self, session: Session) -> None:
        self._repo = EmployeeRepository(session)

    def filter_from_requirements(
        self,
        requirements: StructuredRequirements,
        override_filter: EmployeeFilter | None = None,
    ) -> list[Employee]:
        """Derive an EmployeeFilter from extracted requirements and run it.

        Returns all employees that meet the structured DB criteria.
        The candidate pool is intentionally broad — the scorer narrows it.
        """
        if override_filter is not None:
            criteria = override_filter
        else:
            criteria = self._build_filter(requirements)

        candidates = self._repo.filter_candidates(criteria)

        logger.info(
            "CandidateFilter: %d candidates for domain=%s, skills=%s",
            len(candidates),
            requirements.domain,
            requirements.required_skills,
        )
        return candidates

    def _build_filter(self, req: StructuredRequirements) -> EmployeeFilter:
        return EmployeeFilter(
            required_skill_names=req.required_skills,
            minimum_proficiency=3,  # Proficient
            minimum_years_experience=0.0,
            domains=[req.domain] if req.domain and req.domain != "general" else [],
            seniority_levels=req.seniority_levels,
            must_be_available=True,
            minimum_availability_percentage=30,
            certification_names=req.certifications,
        )

    def get_all_candidates(self) -> list[Employee]:
        """Return all available employees (for broad matching)."""
        return self._repo.filter_candidates(
            EmployeeFilter(must_be_available=True, minimum_availability_percentage=20)
        )

    def filter_candidates_direct(self, criteria: EmployeeFilter) -> list[Employee]:
        """Apply a directly-provided EmployeeFilter (used by UI pages)."""
        return self._repo.filter_candidates(criteria)

    def get_pipeline_metrics(self, criteria: EmployeeFilter) -> dict[str, int]:
        """Return the count of employees at each stage of the filtering pipeline.

        Shows: Total -> Available -> Skill Match -> Domain Match -> Eligible
        """
        # 1. Total
        total = self._repo._session.query(Employee).count()

        # 2. Available
        from sqlalchemy.orm import joinedload

        from models.employee import EmployeeSkill

        avail_query = self._repo._session.query(Employee).options(
            joinedload(Employee.employee_skills).joinedload(EmployeeSkill.skill)
        )
        if criteria.must_be_available:
            avail_query = avail_query.filter(
                Employee.is_available.is_(True),
                Employee.availability_percentage >= criteria.minimum_availability_percentage,
            )
        available = avail_query.count()

        # 3. Skill Match
        # In this implementation, SQL does not easily filter skills, so we use Python filtering
        # We will get all available and then filter by skill
        avail_emps = avail_query.all()

        if criteria.required_skill_names:
            required_lower = {s.lower() for s in criteria.required_skill_names}
            min_prof = criteria.minimum_proficiency

            def has_required_skills(emp: Employee) -> bool:
                emp_skills = {
                    es.skill.name.lower(): es.proficiency
                    for es in emp.employee_skills
                    if es.skill is not None
                }
                return all(emp_skills.get(skill, 0) >= min_prof for skill in required_lower)

            skill_matched = [e for e in avail_emps if has_required_skills(e)]
        else:
            skill_matched = avail_emps

        skill_count = len(skill_matched)

        # 4. Domain Match
        if criteria.domains:
            domain_lower = [d.lower() for d in criteria.domains]
            domain_matched = [
                e
                for e in skill_matched
                if any(d in (e.domain_expertise or "").lower() for d in domain_lower)
            ]
        else:
            domain_matched = skill_matched

        domain_count = len(domain_matched)

        # 5. Final Eligible (including seniority, experience, dept which were in SQL)
        # We just run the full filter
        eligible_count = len(self.filter_candidates_direct(criteria))

        return {
            "total_employees": total,
            "available_employees": available,
            "skill_matched": skill_count,
            "domain_matched": domain_count,
            "eligible_candidates": eligible_count,
        }
