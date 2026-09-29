"""Tests for employee candidate filtering."""

from __future__ import annotations

from sqlalchemy.orm import Session

from repositories.employee_repo import EmployeeRepository
from schemas.employee import EmployeeFilter, ProficiencyLevel
from schemas.project import StructuredRequirements
from services.candidate_filter import CandidateFilter


class TestCandidateFilter:
    def test_filter_available_only(self, db_session: Session, sample_employees: dict) -> None:
        repo = EmployeeRepository(db_session)
        criteria = EmployeeFilter(must_be_available=True, minimum_availability_percentage=10)
        results = repo.filter_candidates(criteria)
        # carol is unavailable
        names = [e.name for e in results]
        assert "Carol Osei" not in names

    def test_filter_by_skill(self, db_session: Session, sample_employees: dict) -> None:
        repo = EmployeeRepository(db_session)
        criteria = EmployeeFilter(
            required_skill_names=["Machine Learning"],
            minimum_proficiency=ProficiencyLevel.PROFICIENT,
            must_be_available=True,
        )
        results = repo.filter_candidates(criteria)
        names = [e.name for e in results]
        assert "Alice Thornton" in names
        assert "Bob Harrington" not in names  # Bob doesn't have ML

    def test_filter_by_seniority(self, db_session: Session, sample_employees: dict) -> None:
        repo = EmployeeRepository(db_session)
        criteria = EmployeeFilter(
            seniority_levels=["mid"],
            must_be_available=True,
        )
        results = repo.filter_candidates(criteria)
        assert all(e.seniority == "mid" for e in results)

    def test_filter_by_experience(self, db_session: Session, sample_employees: dict) -> None:
        repo = EmployeeRepository(db_session)
        criteria = EmployeeFilter(
            minimum_years_experience=5.0,
            must_be_available=True,
        )
        results = repo.filter_candidates(criteria)
        assert all(e.years_of_experience >= 5.0 for e in results)

    def test_filter_from_requirements(self, db_session: Session, sample_employees: dict) -> None:
        req = StructuredRequirements(
            title="ML Project",
            domain="fintech",
            required_skills=["Python", "Machine Learning"],
        )
        cf = CandidateFilter(db_session)
        results = cf.filter_from_requirements(req)
        names = [e.name for e in results]
        assert "Alice Thornton" in names

    def test_empty_requirements_returns_broad_pool(
        self, db_session: Session, sample_employees: dict
    ) -> None:
        req = StructuredRequirements(title="Any Project", domain="general")
        cf = CandidateFilter(db_session)
        results = cf.filter_from_requirements(req)
        assert len(results) >= 2  # At least available employees
