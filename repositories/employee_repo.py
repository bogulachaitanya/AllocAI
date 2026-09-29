"""Employee repository — structured DB queries only, no LLM calls."""

from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from models.assignment import Assignment
from models.employee import Employee, EmployeeSkill, Skill
from repositories.base import BaseRepository
from schemas.employee import EmployeeFilter


class EmployeeRepository(BaseRepository[Employee]):
    def __init__(self, session: Session) -> None:
        super().__init__(Employee, session)

    def get_with_skills(self, employee_id: int) -> Employee | None:
        return (
            self._session.query(Employee)
            .options(
                joinedload(Employee.employee_skills).joinedload(EmployeeSkill.skill),
                joinedload(Employee.certifications),
                joinedload(Employee.assignments).joinedload(Assignment.project),
            )
            .filter(Employee.id == employee_id)
            .first()
        )

    def list_with_skills(self, limit: int = 500, offset: int = 0) -> list[Employee]:
        return (
            self._session.query(Employee)
            .options(
                joinedload(Employee.employee_skills).joinedload(EmployeeSkill.skill),
                joinedload(Employee.certifications),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

    def filter_candidates(self, criteria: EmployeeFilter) -> list[Employee]:
        """Apply structured DB filters to produce a candidate pool.

        Returns employees that:
        - have ALL required skills at or above minimum proficiency
        - are available (if must_be_available)
        - meet seniority/domain/department constraints

        All filtering is deterministic SQL — no LLM involved.
        """
        query = self._session.query(Employee).options(
            joinedload(Employee.employee_skills).joinedload(EmployeeSkill.skill),
            joinedload(Employee.certifications),
            joinedload(Employee.assignments).joinedload(Assignment.project),
        )

        if criteria.must_be_available:
            query = query.filter(
                Employee.is_available.is_(True),
                Employee.availability_percentage >= criteria.minimum_availability_percentage,
            )

        if criteria.minimum_years_experience > 0:
            query = query.filter(Employee.years_of_experience >= criteria.minimum_years_experience)

        if criteria.seniority_levels:
            lower = [s.lower() for s in criteria.seniority_levels]
            query = query.filter(Employee.seniority.in_(lower))

        if criteria.departments:
            query = query.filter(Employee.department.in_(criteria.departments))

        if criteria.domains:
            domain_filters = [Employee.domain_expertise.ilike(f"%{d}%") for d in criteria.domains]
            query = query.filter(or_(*domain_filters))

        candidates = query.all()

        # Skill filtering in Python (SQLAlchemy many-to-many filter is complex)
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

            candidates = [e for e in candidates if has_required_skills(e)]

        # Certification filtering
        if criteria.certification_names:
            cert_lower = {c.lower() for c in criteria.certification_names}

            def has_certifications(emp: Employee) -> bool:
                emp_certs = {c.name.lower() for c in emp.certifications}
                return bool(emp_certs.intersection(cert_lower))

            candidates = [e for e in candidates if has_certifications(e)]

        return candidates

    def get_by_email(self, email: str) -> Employee | None:
        return self._session.query(Employee).filter(Employee.email == email).first()

    def count_available(self, minimum_availability_pct: int = 30) -> int:
        """Return the number of employees currently flagged as available."""
        return (
            self._session.query(Employee)
            .filter(
                Employee.is_available.is_(True),
                Employee.availability_percentage >= minimum_availability_pct,
            )
            .count()
        )

    def get_skill_by_name(self, name: str) -> Skill | None:
        return self._session.query(Skill).filter(Skill.name.ilike(name)).first()

    def get_or_create_skill(self, name: str, category: str = "General") -> Skill:
        skill = self.get_skill_by_name(name)
        if skill is None:
            skill = Skill(name=name, category=category)
            self._session.add(skill)
            self._session.flush()
        return skill

    def list_skills(self) -> list[Skill]:
        return self._session.query(Skill).order_by(Skill.name).all()
