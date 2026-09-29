"""Tests for the Learning Center and Project Outcomes."""

from sqlalchemy.orm import Session, sessionmaker

from hindsight.models import MemoryType
from models.project import Project
from repositories.project_repo import ProjectRepository
from schemas.outcome import OutcomeCreate
from services.learning_agent import LearningAgent


def test_list_recent_summaries_no_session_dependency(db_session: Session):
    """Test that ProjectSummary objects can be accessed after session closes."""
    # 1. Create a project using the active session
    project = Project(
        title="Learning Center Test Project",
        description="A project for testing the learning center.",
        status="completed",
        domain="fintech",
    )
    db_session.add(project)
    db_session.commit()
    project_id = project.id

    # 2. Open a new temporary session using the test engine
    SessionLocal = sessionmaker(bind=db_session.get_bind())
    temp_session = SessionLocal()
    try:
        repo = ProjectRepository(temp_session)
        summaries = repo.list_recent_summaries(limit=10)
    finally:
        temp_session.close()

    # 3. Access attributes OUTSIDE the session block
    # If we were using ORM objects, this would raise DetachedInstanceError.
    # Since we use ProjectSummary, it should succeed.
    found = False
    for s in summaries:
        if s.id == project_id:
            found = True
            # Verify attributes are fully accessible
            assert s.title == "Learning Center Test Project"
            assert isinstance(s.id, int)
            assert isinstance(s.title, str)

    assert found, "The newly created project summary should be in the list."


def test_learning_agent_processes_outcome(db_session: Session):
    """Test that submitting an outcome triggers the learning agent and retains hindsight memory."""
    # 1. Create project
    project = Project(
        title="AI Banking Assistant",
        description="A chatbot for banking.",
        status="completed",
        domain="fintech",
    )
    db_session.add(project)
    db_session.commit()

    # 2. Create an outcome payload (as UI would)
    outcome_data = OutcomeCreate(
        project_id=project.id,
        outcome_status="success",
        delivered_on_time=True,
        delivered_on_budget=True,
        quality_rating=4.5,
        client_feedback="The AI was very responsive and helpful.",
        manager_feedback="Team collaborated well, but had some initial issues with AWS permissions.",
        observations="AWS IAM is tricky. We should create a baseline IAM template for future AI projects.",
    )

    # 3. Run Learning Agent
    agent = LearningAgent(session=db_session)
    result = agent.learn_from_outcome(outcome_data)

    # 4. Assertions
    assert result is not None
    # We should have extracted at least one lesson based on the structured prompt (though Groq mock might return arbitrary or 0 if mocked, but usually it returns some)
    # The LearningAgent processes the outcome, extracts lessons, and retains a memory.

    # Verify the project outcome was persisted
    db_session.refresh(project)
    assert project.outcome is not None
    assert project.outcome.outcome_status == "success"
    assert project.outcome.quality_rating == 4.5

    # Verify Hindsight memory was retained
    from hindsight.adapter import get_hindsight_adapter

    hindsight = get_hindsight_adapter()

    # The Learning Agent creates a PROJECT_OUTCOME memory
    memories = hindsight.lookup_by_project(str(project.id))
    assert len(memories) > 0
    outcome_memory = next(
        (m for m in memories if m.memory_type == MemoryType.PROJECT_OUTCOME), None
    )
    assert outcome_memory is not None
    assert outcome_memory.domain == "fintech"
    assert "AI Banking Assistant" in outcome_memory.project_title
