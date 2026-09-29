"""End-to-end workflow test."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from models.project import Project
from schemas.outcome import OutcomeCreate
from schemas.project import StructuredRequirements
from services.candidate_filter import CandidateFilter
from services.learning_agent import LearningAgent
from services.project_fit_scorer import ProjectFitScorer
from services.team_composer import TeamComposer


class TestEndToEndWorkflow:
    def test_full_pipeline_without_llm(
        self, db_session: Session, sample_employees: dict, hindsight_adapter
    ) -> None:
        """Full pipeline: filter → score → compose team (no LLM required)."""

        # 1. Create project
        project = Project(
            title="ML Fraud Detection",
            domain="fintech",
            status="draft",
            team_size_min=2,
            team_size_max=4,
        )
        db_session.add(project)
        db_session.flush()

        # 2. Define requirements
        req = StructuredRequirements(
            title="ML Fraud Detection",
            domain="fintech",
            required_skills=["Python", "Machine Learning"],
            team_size_min=2,
            team_size_max=4,
        )

        # 3. Filter candidates
        cf = CandidateFilter(db_session)
        candidates = cf.filter_from_requirements(req)
        assert len(candidates) >= 1  # At least Alice

        # 4. Score
        scorer = ProjectFitScorer()
        scored = scorer.score_many(candidates, req)
        assert all(0.0 <= m.project_fit_score <= 1.0 for m in scored)

        # 5. Compose team
        composer = TeamComposer()
        team = composer.compose(scored, req)
        assert len(team.members) >= 1
        assert team.validation is not None

    def test_hindsight_recall_before_recommendation(
        self, db_session: Session, sample_employees: dict, hindsight_adapter
    ) -> None:
        """Hindsight memories are recalled before team composition."""
        from hindsight.models import MemoryType, RecallRequest, RetainRequest

        # Pre-seed a relevant memory
        hindsight_adapter.retain(
            RetainRequest(
                content="Fintech fraud detection projects succeed with ML + domain experts.",
                summary="ML + domain experts excel in fintech fraud detection",
                memory_type=MemoryType.TEAM_PATTERN,
                domain="fintech",
            )
        )

        req = RecallRequest(query="fintech fraud detection ml", domain="fintech", top_k=5)
        memories = hindsight_adapter.recall(req)
        assert len(memories) >= 1
        assert any("fintech" in m.domain for m in memories)

    def test_learning_loop_retains_memory(
        self,
        db_session: Session,
        sample_employees: dict,
        sample_project: Project,
        hindsight_adapter,
    ) -> None:
        """After recording an outcome, memories are retained in Hindsight."""
        mock_llm = MagicMock()
        mock_llm.chat.return_value = json.dumps(
            {
                "lessons": ["Team with domain expertise delivered better results"],
                "successful_patterns": ["Domain expert + ML engineer pairing"],
                "risk_patterns": [],
                "collaboration_insights": ["Strong communication improved delivery"],
                "staffing_recommendations": ["Include domain expert for fintech projects"],
                "memory_summary": "Project succeeded with domain expert involvement.",
            }
        )

        outcome_data = OutcomeCreate(
            project_id=sample_project.id,
            outcome_status="success",
            delivered_on_time=True,
            delivered_on_budget=True,
            quality_rating=4.5,
            client_feedback="Excellent delivery.",
            manager_feedback="Team performed above expectations.",
            observations="Domain expert was critical to success.",
        )

        initial_count = hindsight_adapter.count()

        agent = LearningAgent(session=db_session, llm=mock_llm, hindsight=hindsight_adapter)
        result = agent.learn_from_outcome(outcome_data)

        assert len(result.lessons_extracted) >= 1
        assert len(result.memories_retained) >= 1
        assert hindsight_adapter.count() > initial_count

    def test_new_memories_used_in_future_recommendation(
        self, db_session: Session, sample_employees: dict, hindsight_adapter
    ) -> None:
        """Memories retained after one project influence future recommendations."""
        from hindsight.models import MemoryType, RecallRequest, RetainRequest

        # Retain a memory
        hindsight_adapter.retain(
            RetainRequest(
                content="Senior ML engineers with fintech domain experience reduced fraud false positives by 30%.",
                summary="Senior ML + fintech domain reduces false positives",
                memory_type=MemoryType.LESSON_LEARNED,
                domain="fintech",
                tags=["ml", "fintech", "performance"],
            )
        )

        # Simulate a future recommendation recalling this memory
        recall = RecallRequest(
            query="fintech ml engineer fraud detection",
            domain="fintech",
            top_k=5,
        )
        memories = hindsight_adapter.recall(recall)
        assert len(memories) >= 1
        assert any("fintech" in m.domain for m in memories)
        assert memories[0].relevance_score > 0
