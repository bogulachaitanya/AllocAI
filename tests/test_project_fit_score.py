"""Tests for Project Fit Score calculation."""

from __future__ import annotations

from sqlalchemy.orm import Session

from schemas.matching import ProjectFitWeights
from schemas.project import StructuredRequirements
from services.project_fit_scorer import ProjectFitScorer


class TestProjectFitScorer:
    def test_score_returns_value_0_to_1(self, db_session: Session, sample_employees: dict) -> None:
        scorer = ProjectFitScorer()
        req = StructuredRequirements(
            title="Test", domain="fintech", required_skills=["Python", "Machine Learning"]
        )
        match = scorer.score(sample_employees["emp1"], req)
        assert 0.0 <= match.project_fit_score <= 1.0

    def test_available_employee_scores_higher_than_unavailable(
        self, db_session: Session, sample_employees: dict
    ) -> None:
        scorer = ProjectFitScorer()
        req = StructuredRequirements(title="Test", domain="cloud", required_skills=["AWS"])
        # emp3 is unavailable but has AWS; emp2 is available but doesn't
        match_carol = scorer.score(sample_employees["emp3"], req)
        match_bob = scorer.score(sample_employees["emp2"], req)
        # Carol has availability_score = 0 (unavailable)
        assert match_carol.score_breakdown.availability_score == 0.0
        assert match_bob.score_breakdown.availability_score > 0.0

    def test_full_skill_match_gives_higher_score(
        self, db_session: Session, sample_employees: dict
    ) -> None:
        scorer = ProjectFitScorer()
        req = StructuredRequirements(
            title="Test", domain="ml", required_skills=["Python", "Machine Learning"]
        )
        match_alice = scorer.score(sample_employees["emp1"], req)
        match_bob = scorer.score(sample_employees["emp2"], req)
        # Alice has both skills; Bob only has Python
        assert (
            match_alice.score_breakdown.skill_match_score
            > match_bob.score_breakdown.skill_match_score
        )

    def test_missing_skills_recorded(self, db_session: Session, sample_employees: dict) -> None:
        scorer = ProjectFitScorer()
        req = StructuredRequirements(
            title="Test", domain="ml", required_skills=["Python", "Kubernetes", "Kafka"]
        )
        match = scorer.score(sample_employees["emp2"], req)
        assert (
            "Kubernetes" in match.skill_detail.missing_skills
            or "Kafka" in match.skill_detail.missing_skills
        )

    def test_custom_weights_applied(self, db_session: Session, sample_employees: dict) -> None:
        weights = ProjectFitWeights(
            skill_match=0.0,
            experience_match=0.0,
            relevant_project_experience=0.0,
            domain_expertise=0.0,
            past_project_performance=0.0,
            availability=1.0,  # Only availability matters
            certification_relevance=0.0,
            collaboration_relevance=0.0,
        )
        scorer = ProjectFitScorer(weights=weights)
        req = StructuredRequirements(title="Test", domain="general")
        match_alice = scorer.score(sample_employees["emp1"], req)
        # emp1 is 100% available → score should be close to 1.0
        assert match_alice.project_fit_score > 0.9

    def test_score_many_sorted(self, db_session: Session, sample_employees: dict) -> None:
        scorer = ProjectFitScorer()
        req = StructuredRequirements(
            title="Test", domain="fintech", required_skills=["Python", "Machine Learning"]
        )
        employees = list(sample_employees.values())
        employees = [e for e in employees if hasattr(e, "name")]
        matches = scorer.score_many(employees, req)
        scores = [m.project_fit_score for m in matches]
        assert scores == sorted(scores, reverse=True)

    def test_evidence_labeled_as_database(
        self, db_session: Session, sample_employees: dict
    ) -> None:
        from schemas.matching import EvidenceSource

        scorer = ProjectFitScorer()
        req = StructuredRequirements(title="Test", domain="general")
        match = scorer.score(sample_employees["emp1"], req)
        for item in match.evidence:
            assert item.source == EvidenceSource.DATABASE

    def test_recommendation_rationale_uses_correct_language(
        self, db_session: Session, sample_employees: dict
    ) -> None:
        scorer = ProjectFitScorer()
        req = StructuredRequirements(title="Test", domain="general")
        match = scorer.score(sample_employees["emp1"], req)
        assert "project-fit criteria" in match.recommendation_rationale.lower()
        # Must not use forbidden language
        assert "best employee" not in match.recommendation_rationale.lower()
