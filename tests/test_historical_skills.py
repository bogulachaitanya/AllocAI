"""Tests for the historical skill matching separation (Current vs Historical)."""

from models.assignment import Assignment
from models.employee import Employee, EmployeeSkill, Skill
from models.project import Project
from schemas.project import StructuredRequirements
from services.project_fit_scorer import ProjectFitScorer
from services.team_composer import TeamComposer


def test_historical_skill_extraction(db_session):
    """Test that ProjectFitScorer extracts historical skills from manager_notes."""
    # 1. Create a dummy employee
    emp = Employee(
        name="Test Dev",
        email="test@example.com",
        role="Backend Engineer",
        department="Engineering",
        seniority="mid",
        years_of_experience=4.0,
        domain_expertise="Java | Spring",
        work_preferences="",
        is_available=True,
        availability_percentage=100,
    )
    db_session.add(emp)

    # 2. Add current skills
    java = Skill(name="Java", category="Technology")
    spring = Skill(name="Spring", category="Technology")
    db_session.add_all([java, spring])
    db_session.flush()

    db_session.add(
        EmployeeSkill(employee_id=emp.id, skill_id=java.id, proficiency=3, years_with_skill=2)
    )
    db_session.add(
        EmployeeSkill(employee_id=emp.id, skill_id=spring.id, proficiency=3, years_with_skill=2)
    )

    # 3. Add historical project with completely different tech stack in notes
    proj = Project(
        title="Legacy Python Service",
        domain="fintech",
        status="completed",
        team_size_min=1,
        team_size_max=1,
        duration_weeks=10,
    )
    db_session.add(proj)
    db_session.flush()

    assign = Assignment(
        employee_id=emp.id,
        project_id=proj.id,
        role_on_project="Developer",
        status="completed",
        manager_notes="Contribution: API build\nTech Stack Used: Python | FastAPI | PostgreSQL\nProject Outcome: Success",
    )
    db_session.add(assign)
    db_session.commit()

    # 4. Score against a requirement demanding Python and FastAPI
    req = StructuredRequirements(
        title="New Python Project",
        domain="fintech",
        required_skills=["Python", "FastAPI"],
        preferred_skills=["Java"],
        team_size_min=1,
        team_size_max=2,
        duration_weeks=4,
        key_responsibilities=[],
        risks=[],
    )

    scorer = ProjectFitScorer()
    scored = scorer.score_many([emp], req)

    assert len(scored) == 1
    match = scored[0]

    # Python/FastAPI should be recognized as historical, NOT current
    assert "java" not in [s.lower() for s in match.skill_detail.missing_skills]

    historical_lower = [s.lower() for s in match.skill_detail.historical_matched]
    assert "python" in historical_lower
    assert "fastapi" in historical_lower

    current_lower = [s.lower() for s in match.skill_detail.matched_skills]
    assert "python" not in current_lower
    assert "fastapi" not in current_lower

    # Effective coverage should include both
    effective_lower = [s.lower() for s in match.effective_skill_coverage]
    assert "python" in effective_lower
    assert "fastapi" in effective_lower

    # 5. Verify TeamComposer counts it towards full coverage
    composer = TeamComposer()
    team = composer.compose([match], req, [], [], [])

    # Validation should say missing_skills is empty (since effective covered it)
    assert not team.validation.missing_skills
    assert team.validation.skill_coverage_percentage == 100.0

    # But it should warn that it relied on historical skills
    warnings = team.validation.warnings
    assert any("historical evidence" in w for w in warnings)
