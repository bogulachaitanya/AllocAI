"""Tests for team composition."""

from __future__ import annotations

from schemas.matching import (
    CandidateMatch,
    EvidenceItem,
    EvidenceSource,
    ProjectFitScoreBreakdown,
    SkillMatchDetail,
)
from schemas.project import StructuredRequirements
from services.team_composer import TeamComposer


def make_candidate(
    employee_id: int,
    name: str,
    skills: list[str],
    score: float = 0.7,
    available: bool = True,
    avail_pct: int = 100,
) -> CandidateMatch:
    return CandidateMatch(
        employee_id=employee_id,
        employee_name=name,
        employee_role="Engineer",
        employee_department="Engineering",
        employee_seniority="senior",
        project_fit_score=score,
        score_breakdown=ProjectFitScoreBreakdown(
            skill_match_score=score,
            experience_match_score=score,
            relevant_project_experience_score=score,
            domain_expertise_score=score,
            past_project_performance_score=score,
            availability_score=1.0 if available else 0.0,
            certification_relevance_score=0.5,
            collaboration_relevance_score=0.5,
        ),
        skill_detail=SkillMatchDetail(matched_skills=skills, missing_skills=[]),
        is_available=available,
        availability_percentage=avail_pct,
    )


class TestTeamComposer:
    def test_team_size_within_bounds(self) -> None:
        composer = TeamComposer()
        candidates = [
            make_candidate(i, f"Emp{i}", ["Python"], score=0.9 - i * 0.05) for i in range(10)
        ]
        req = StructuredRequirements(
            title="Test", domain="general", team_size_min=2, team_size_max=4
        )
        team = composer.compose(candidates, req)
        assert 2 <= len(team.members) <= 4

    def test_skill_coverage_maximized(self) -> None:
        composer = TeamComposer()
        # Candidate A has Python; Candidate B has Kubernetes
        candidates = [
            make_candidate(1, "Alice", ["Python"], score=0.9),
            make_candidate(2, "Bob", ["Kubernetes"], score=0.7),
            make_candidate(3, "Carol", ["Python"], score=0.6),  # redundant
        ]
        req = StructuredRequirements(
            title="Test",
            domain="general",
            required_skills=["Python", "Kubernetes"],
            team_size_min=2,
            team_size_max=3,
        )
        team = composer.compose(candidates, req)
        team_names = [m.employee_name for m in team.members]
        # Both Alice (Python) and Bob (Kubernetes) should be selected
        assert "Alice" in team_names
        assert "Bob" in team_names

    def test_no_duplicate_members(self) -> None:
        composer = TeamComposer()
        candidates = [make_candidate(i, f"E{i}", ["Python"]) for i in range(5)]
        req = StructuredRequirements(title="Test", domain="general", team_size_max=5)
        team = composer.compose(candidates, req)
        ids = [m.employee_id for m in team.members]
        assert len(ids) == len(set(ids))

    def test_validation_detects_missing_skills(self) -> None:
        composer = TeamComposer()
        candidates = [make_candidate(1, "Alice", ["Python"], score=0.9)]
        req = StructuredRequirements(
            title="Test",
            domain="general",
            required_skills=["Python", "Kubernetes"],
            team_size_min=1,
            team_size_max=3,
        )
        team = composer.compose(candidates, req)
        assert team.validation is not None
        assert "kubernetes" in team.validation.missing_skills

    def test_no_memory_message_when_no_hindsight(self) -> None:
        composer = TeamComposer()
        candidates = [make_candidate(1, "Alice", ["Python"])]
        req = StructuredRequirements(title="Test", domain="general", team_size_min=1)
        team = composer.compose(candidates, req, hindsight_evidence=[])
        assert team.hindsight_memories_found is False
        assert team.no_memory_message == "No relevant organizational memory was found."

    def test_hindsight_evidence_propagated(self) -> None:
        composer = TeamComposer()
        candidates = [make_candidate(1, "Alice", ["Python"])]
        req = StructuredRequirements(title="Test", domain="general", team_size_min=1)
        h_evidence = [EvidenceItem(source=EvidenceSource.HINDSIGHT, label="Pattern", value="Test")]
        team = composer.compose(candidates, req, hindsight_evidence=h_evidence)
        assert team.hindsight_memories_found is True
        assert len(team.hindsight_evidence) == 1
