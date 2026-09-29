"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.base import Base

# Use in-memory SQLite for all tests
TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session", autouse=True)
def configure_test_env() -> None:
    """Set environment variables before any test imports settings."""
    os.environ["APP_ENV"] = "testing"
    os.environ["DATABASE_URL"] = TEST_DB_URL
    os.environ["HINDSIGHT_ADAPTER"] = "local"
    os.environ["HINDSIGHT_DB_PATH"] = ":memory:"


@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped in-memory SQLite engine."""
    import models.assignment
    import models.employee
    import models.outcome
    import models.project  # noqa: F401

    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine) -> Session:
    """Function-scoped transactional session that rolls back after each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_employees(db_session: Session):
    """Create a small set of test employees."""
    from models.employee import Employee, EmployeeSkill, Skill

    # Skills
    skill_py = Skill(name="Python", category="Backend")
    skill_ml = Skill(name="Machine Learning", category="AI/ML")
    skill_aws = Skill(name="AWS", category="Cloud")
    skill_react = Skill(name="React", category="Frontend")
    db_session.add_all([skill_py, skill_ml, skill_aws, skill_react])
    db_session.flush()

    # Employees
    emp1 = Employee(
        name="Alice Thornton",
        email="alice@example.test",
        role="Senior ML Engineer",
        department="AI / Machine Learning",
        seniority="senior",
        years_of_experience=7.0,
        domain_expertise="fintech,ml",
        is_available=True,
        availability_percentage=100,
        performance_rating=4.5,
    )
    emp2 = Employee(
        name="Bob Harrington",
        email="bob@example.test",
        role="Software Engineer",
        department="Engineering",
        seniority="mid",
        years_of_experience=3.0,
        domain_expertise="general",
        is_available=True,
        availability_percentage=75,
        performance_rating=3.8,
    )
    emp3 = Employee(
        name="Carol Osei",
        email="carol@example.test",
        role="DevOps Engineer",
        department="DevOps & Infrastructure",
        seniority="senior",
        years_of_experience=6.0,
        domain_expertise="cloud",
        is_available=False,
        availability_percentage=0,
        performance_rating=4.2,
    )
    db_session.add_all([emp1, emp2, emp3])
    db_session.flush()

    # Skills for emp1
    db_session.add_all(
        [
            EmployeeSkill(
                employee_id=emp1.id, skill_id=skill_py.id, proficiency=5, years_with_skill=6
            ),
            EmployeeSkill(
                employee_id=emp1.id, skill_id=skill_ml.id, proficiency=5, years_with_skill=5
            ),
        ]
    )
    # Skills for emp2
    db_session.add_all(
        [
            EmployeeSkill(
                employee_id=emp2.id, skill_id=skill_py.id, proficiency=3, years_with_skill=3
            ),
            EmployeeSkill(
                employee_id=emp2.id, skill_id=skill_react.id, proficiency=4, years_with_skill=2
            ),
        ]
    )
    # Skills for emp3 (unavailable)
    db_session.add_all(
        [
            EmployeeSkill(
                employee_id=emp3.id, skill_id=skill_aws.id, proficiency=4, years_with_skill=5
            ),
        ]
    )
    db_session.flush()

    return {
        "emp1": emp1,
        "emp2": emp2,
        "emp3": emp3,
        "skills": {"Python": skill_py, "ML": skill_ml, "AWS": skill_aws},
    }


@pytest.fixture
def sample_project(db_session: Session):
    """Create a sample project."""
    from models.project import Project

    proj = Project(
        title="Test Fraud Detection Project",
        domain="fintech",
        status="draft",
        team_size_min=2,
        team_size_max=4,
    )
    db_session.add(proj)
    db_session.flush()
    return proj


@pytest.fixture
def hindsight_adapter():
    """Local Hindsight adapter backed by a temp file."""
    import tempfile
    from pathlib import Path

    from hindsight.local_adapter import LocalHindsightAdapter

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp_path = Path(f.name)

    adapter = LocalHindsightAdapter(db_path=tmp_path)
    yield adapter

    try:
        tmp_path.unlink(missing_ok=True)
    except PermissionError:
        pass  # On Windows, SQLite might still hold a lock. We ignore temp file cleanup errors.
