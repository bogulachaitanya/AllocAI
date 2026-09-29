"""Tests for strict team size enforcement."""

from schemas.matching import CandidateMatch, ProjectFitScoreBreakdown, SkillMatchDetail
from schemas.project import StructuredRequirements
from services.team_composer import TeamComposer


def create_mock_candidate(employee_id: int, name: str, is_available: bool = True) -> CandidateMatch:
    return CandidateMatch(
        employee_id=employee_id,
        employee_name=name,
        employee_role="Engineer",
        employee_department="Engineering",
        employee_seniority="mid",
        project_fit_score=0.8,
        is_available=is_available,
        availability_percentage=100 if is_available else 0,
        score_breakdown=ProjectFitScoreBreakdown(
            skill_match_score=0.8,
            experience_match_score=0.8,
            relevant_project_experience_score=0.8,
            domain_expertise_score=0.8,
            past_project_performance_score=0.8,
            availability_score=1.0 if is_available else 0.0,
            certification_relevance_score=0.0,
            collaboration_relevance_score=0.0,
        ),
        skill_detail=SkillMatchDetail(
            matched_skills=["Python"],
            missing_skills=[],
            historical_matched=[],
        ),
        effective_skill_coverage=["Python"],
        evidence=[],
    )


def test_team_composer_respects_exact_team_size():
    composer = TeamComposer()

    # 25 eligible candidates
    candidates = [create_mock_candidate(i, f"Emp {i}") for i in range(1, 26)]

    sizes = [1, 3, 4, 5, 10]

    for size in sizes:
        reqs = StructuredRequirements(
            title="Test", domain="general", team_size_min=size, team_size_max=size
        )

        team = composer.compose(
            scored_candidates=candidates,
            requirements=reqs,
            hindsight_evidence=[],
            rag_evidence=[],
            hindsight_memories=[],
        )

        # Even with 25 candidates, it must return exactly the requested size
        assert len(team.members) == size, (
            f"Expected {size}, got {len(team.members)}"
        )


def test_team_composer_fallback_fewer_candidates():
    composer = TeamComposer()

    # Only 2 candidates exist
    candidates = [create_mock_candidate(1, "Alice"), create_mock_candidate(2, "Bob")]

    reqs = StructuredRequirements(title="Test", domain="general", team_size_min=4, team_size_max=4)

    team = composer.compose(
        scored_candidates=candidates,
        requirements=reqs,
        hindsight_evidence=[],
        rag_evidence=[],
        hindsight_memories=[],
    )

    # Must return exactly 2 and display the correct warning
    assert len(team.members) == 2

    warnings = team.validation.warnings
    assert any(
        "Only 2 eligible candidates are available for the requested team size of 4." in w
        for w in warnings
    )


def test_team_size_override_logic():
    # This simulates the UI logic to ensure LLM cannot override

    # UI explicit inputs
    ui_size = 4

    # LLM hallucinates 1 and 5
    llm_extracted = StructuredRequirements(
        title="AI App", domain="fintech", team_size_min=1, team_size_max=5
    )

    # UI forces explicit values
    update_dict = {
        "team_size_min": ui_size,
        "team_size_max": ui_size,
    }

    final_reqs = llm_extracted.model_copy(update=update_dict)

    assert final_reqs.team_size_min == 4
    assert final_reqs.team_size_max == 4
