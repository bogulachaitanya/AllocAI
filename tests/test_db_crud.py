"""Tests for database CRUD operations."""

from __future__ import annotations

from sqlalchemy.orm import Session

from models.employee import Employee
from repositories.employee_repo import EmployeeRepository


class TestEmployeeCRUD:
    def test_create_employee(self, db_session: Session) -> None:
        repo = EmployeeRepository(db_session)
        emp = Employee(
            name="Test User",
            email="testuser@example.test",
            role="Engineer",
            department="Engineering",
            seniority="mid",
            years_of_experience=3.0,
            is_available=True,
            availability_percentage=100,
        )
        created = repo.create(emp)
        assert created.id is not None
        assert created.name == "Test User"

    def test_get_employee(self, db_session: Session, sample_employees: dict) -> None:
        repo = EmployeeRepository(db_session)
        emp = repo.get(sample_employees["emp1"].id)
        assert emp is not None
        assert emp.name == "Alice Thornton"

    def test_get_nonexistent_employee(self, db_session: Session) -> None:
        repo = EmployeeRepository(db_session)
        assert repo.get(999999) is None

    def test_list_employees(self, db_session: Session, sample_employees: dict) -> None:
        repo = EmployeeRepository(db_session)
        all_employees = repo.list_all()
        assert len(all_employees) >= 3

    def test_delete_employee(self, db_session: Session) -> None:
        repo = EmployeeRepository(db_session)
        emp = Employee(
            name="Delete Me",
            email="deleteme@example.test",
            role="Junior Engineer",
            department="Engineering",
            seniority="junior",
            years_of_experience=1.0,
            is_available=True,
            availability_percentage=100,
        )
        created = repo.create(emp)
        emp_id = created.id
        result = repo.delete(emp_id)
        assert result is True
        assert repo.get(emp_id) is None

    def test_get_by_email(self, db_session: Session, sample_employees: dict) -> None:
        repo = EmployeeRepository(db_session)
        emp = repo.get_by_email("alice@example.test")
        assert emp is not None
        assert emp.name == "Alice Thornton"

    def test_get_or_create_skill(self, db_session: Session) -> None:
        repo = EmployeeRepository(db_session)
        skill = repo.get_or_create_skill("Kubernetes", "DevOps")
        assert skill.id is not None
        assert skill.name == "Kubernetes"
        # Get again — should return same
        skill2 = repo.get_or_create_skill("Kubernetes", "DevOps")
        assert skill.id == skill2.id
