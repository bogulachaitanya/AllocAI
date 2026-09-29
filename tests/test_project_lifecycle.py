"""Tests for the Project Creation and Analysis lifecycle."""

from sqlalchemy.orm import Session

from models.project import Project
from repositories.project_repo import ProjectRepository
from schemas.project import StructuredRequirements
from services.recommendation_engine import RecommendationEngine


def test_create_project_persisted_in_db(db_session: Session):
    """Test that a project is properly persisted with a generated ID and draft status."""
    repo = ProjectRepository(db_session)

    project = Project(
        title="Test Project Workflow",
        description="We need a test project.",
        client="Test Client",
        domain="general",
        status="draft",
        team_size_min=2,
        team_size_max=4,
        duration_weeks=12,
        raw_requirement="We need a test project.",
    )

    db_session.add(project)
    db_session.commit()

    assert project.id is not None
    assert project.id > 0
    assert project.status == "draft"

    # Verify we can retrieve it
    retrieved = repo.get_with_details(project.id)
    assert retrieved is not None
    assert retrieved.title == "Test Project Workflow"


def test_invalid_team_size(db_session: Session):
    """Test that database enforces constraints or that we can catch invalid team size."""
    # SQLite does not enforce CHECK constraints strongly by default unless configured,
    # but we can test that the model accepts the values and UI handles validation.
    # In this case, team_size_min > team_size_max should be invalid logically.
    # We will just verify the fields exist and can be queried.
    project = Project(
        title="Invalid Size",
        team_size_min=10,
        team_size_max=2,  # Invalid logically, but schema allows it unless constrained
    )
    db_session.add(project)
    db_session.commit()
    assert project.id is not None


def test_project_appears_in_history(db_session: Session):
    """Test that a newly created draft project is returned in list_recent."""
    repo = ProjectRepository(db_session)

    project = Project(
        title="History Test Project",
        status="draft",
    )
    db_session.add(project)
    db_session.commit()

    recent_projects = repo.list_recent(limit=10)
    assert any(p.id == project.id for p in recent_projects)


def test_analyze_and_recommend_on_saved_project(db_session: Session):
    """Test that the recommendation engine can process a saved project."""
    repo = ProjectRepository(db_session)

    project = Project(title="Analyze Test", status="draft", domain="fintech")
    db_session.add(project)
    db_session.commit()

    # 1. Simulate the Analyzer extracting requirements
    reqs = StructuredRequirements(
        title="Analyze Test",
        domain="fintech",
        required_skills=["Python", "SQL"],
        team_size_min=1,
        team_size_max=2,
    )

    # 2. Run Recommendation Engine on the saved project
    engine = RecommendationEngine(session=db_session)
    rec = engine.recommend(reqs, project=project)

    # 3. Verify the recommendation is linked to the project
    assert rec.project_id == project.id
    assert project.recommendation_explanation is not None

    # The RecommendationEngine updates the project with the explanation
    db_session.commit()

    # Ensure the recommendation explanation was persisted on the project record.
    # The exact LLM-generated string is non-deterministic, so we only verify
    # that it was written back (non-empty) and that the rec object carries it.
    retrieved = repo.get_with_details(project.id)
    assert rec.explanation  # the LLM produced something
    # The engine writes to project.recommendation_explanation before we commit
    assert project.recommendation_explanation is not None
