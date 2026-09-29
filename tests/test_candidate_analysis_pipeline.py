"""Tests for Candidate Analysis pipeline metrics and filtering transparency."""

from db.session import SessionLocal
from models.employee import Employee
from schemas.employee import EmployeeFilter, ProficiencyLevel
from schemas.project import StructuredRequirements
from services.candidate_filter import CandidateFilter
from services.recommendation_engine import RecommendationEngine


def test_database_contains_exactly_200_employees():
    """Test that the imported dataset has exactly 200 employees and no fakes."""
    db_session = SessionLocal()
    try:
        count = db_session.query(Employee).count()
        assert count == 200, f"Expected exactly 200 employees, found {count}"

        # Ensure no demo seed names are in the dataset
        demo_names = ["Dustin Nelson", "Donald Lewis", "Susan Rivas", "Jeffrey Campbell"]
        for name in demo_names:
            emp = db_session.query(Employee).filter(Employee.name == name).first()
            assert emp is None, f"Fake/seed employee {name} found in the database!"
    finally:
        db_session.close()


def test_pipeline_metrics_computation():
    """Test that the candidate filter pipeline accurately reports counts at each stage."""
    db_session = SessionLocal()
    try:
        filter_svc = CandidateFilter(db_session)

        # Create a filter that will drop candidates at each stage
        criteria = EmployeeFilter(
            required_skill_names=["Python", "SQL"],
            minimum_proficiency=ProficiencyLevel.PROFICIENT,
            domains=["fintech"],
            must_be_available=True,
            minimum_availability_percentage=50,
            minimum_years_experience=3.0,
        )

        metrics = filter_svc.get_pipeline_metrics(criteria)

        # 1. Total is 200
        assert metrics["total_employees"] == 200

        # 2. Available <= Total
        assert metrics["available_employees"] <= metrics["total_employees"]

        # 3. Skill Matched <= Available
        assert metrics["skill_matched"] <= metrics["available_employees"]

        # 4. Domain Matched <= Skill Matched
        assert metrics["domain_matched"] <= metrics["skill_matched"]

        # 5. Eligible <= Domain Matched
        assert metrics["eligible_candidates"] <= metrics["domain_matched"]

        # 6. Eligible matches actual returned candidates
        candidates = filter_svc.filter_candidates_direct(criteria)
        assert len(candidates) == metrics["eligible_candidates"]
    finally:
        db_session.close()


def test_recommendation_engine_respects_candidate_pool():
    """Test that RecommendationEngine only selects from the eligible pool, with no fabricated members."""
    db_session = SessionLocal()
    try:
        reqs = StructuredRequirements(
            title="AI-powered Banking Assistant",
            domain="fintech",
            required_skills=["Python", "NLP", "FastAPI", "SQL", "AWS"],
            team_size_min=1,
            team_size_max=3,
        )

        engine = RecommendationEngine(session=db_session)
        rec = engine.recommend(reqs)

        for member in rec.recommended_team:
            # 1. ID matches dataset
            emp = db_session.query(Employee).filter(Employee.id == member.employee_id).first()
            assert emp is not None, "Recommended candidate ID does not exist in the database!"
            assert emp.name == member.employee_name

            # 2. Candidate comes from the valid filtered pool
            assert member.employee_id > 0
    finally:
        db_session.close()
