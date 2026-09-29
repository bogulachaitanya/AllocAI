"""Tests for the complete Hindsight learning loop.

Verified pipeline:
    Project 1 (AI Banking Assistant)
        ↓
    Project Outcome (with observations)
        ↓
    LearningAgent (mocked LLM — no real API needed)
        ↓
    Lesson Extraction
        ↓
    Hindsight Retain
        ↓
    Project 2 (AI FinTech Customer Assistant)
        ↓
    Hindsight Recall
        ↓
    Relevant lesson retrieved (verified by metadata/tags, not fragile LLM wording)

All tests use LocalHindsightAdapter and a mocked LLM.
No network connectivity required.
No GROQ_API_KEY required.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hindsight.models import MemoryType, RecallRequest, RetainRequest
from schemas.outcome import LearningResult, OutcomeCreate
from services.learning_agent import LearningAgent

# ── Helpers / Fixtures ────────────────────────────────────────────────────────


def make_mock_llm(lessons: list[str], patterns: list[str], risks: list[str]) -> MagicMock:
    """Return a mock LLM provider that emits a deterministic structured JSON response."""
    import json

    payload = {
        "lessons": lessons,
        "successful_patterns": patterns,
        "risk_patterns": risks,
        "collaboration_insights": [],
        "staffing_recommendations": [],
        "memory_summary": f"Project completed. Lessons: {'; '.join(lessons[:2])}",
    }
    mock = MagicMock()
    mock.chat.return_value = json.dumps(payload)
    return mock


@pytest.fixture
def project1(db_session):
    """Create the first fictional project: AI Banking Assistant."""
    from models.project import Project

    proj = Project(
        title="AI Banking Assistant",
        domain="fintech",
        status="active",
        team_size_min=3,
        team_size_max=5,
        description="Conversational AI for banking operations and compliance.",
    )
    db_session.add(proj)
    db_session.flush()
    return proj


@pytest.fixture
def project2(db_session):
    """Create the second fictional project: AI FinTech Customer Assistant."""
    from models.project import Project

    proj = Project(
        title="AI FinTech Customer Assistant",
        domain="fintech",
        status="draft",
        team_size_min=3,
        team_size_max=5,
        description="Customer support AI for a FinTech startup.",
    )
    db_session.add(proj)
    db_session.flush()
    return proj


# ── Learning loop tests ───────────────────────────────────────────────────────


class TestHindsightLearningLoop:
    """End-to-end learning loop: Outcome → Retain → Recall."""

    def test_learning_agent_retains_memories_from_outcome(
        self, db_session, hindsight_adapter, project1
    ) -> None:
        """LearningAgent retains at least one memory when processing a project outcome."""
        mock_llm = make_mock_llm(
            lessons=[
                "Financial-domain expertise improved requirement understanding.",
                "AWS deployment required dedicated DevOps lead from sprint 1.",
            ],
            patterns=["Pairing domain experts with engineers reduced rework."],
            risks=["AWS deployment without DevOps lead caused delays."],
        )

        agent = LearningAgent(session=db_session, llm=mock_llm, hindsight=hindsight_adapter)

        outcome = OutcomeCreate(
            project_id=project1.id,
            outcome_status="success",
            delivered_on_time=True,
            delivered_on_budget=True,
            quality_rating=5.0,
            client_feedback="Excellent delivery. The AI exceeded our expectations.",
            manager_feedback="Strong collaboration. Financial expertise made a big difference.",
            observations=(
                "AWS deployment caused early delays. "
                "Having a dedicated DevOps engineer resolved this. "
                "Financial domain knowledge accelerated requirements gathering."
            ),
        )

        result: LearningResult = agent.learn_from_outcome(outcome)

        assert isinstance(result, LearningResult)
        assert result.project_id == project1.id
        assert len(result.memories_retained) > 0
        assert hindsight_adapter.count() > 0

    def test_retained_memories_include_lesson_type(
        self, db_session, hindsight_adapter, project1
    ) -> None:
        """Retained memories include at least one LESSON_LEARNED type."""
        mock_llm = make_mock_llm(
            lessons=["FinTech projects benefit from early compliance review."],
            patterns=[],
            risks=[],
        )
        agent = LearningAgent(session=db_session, llm=mock_llm, hindsight=hindsight_adapter)
        outcome = OutcomeCreate(
            project_id=project1.id,
            outcome_status="success",
            quality_rating=4.0,
            client_feedback="Good.",
            manager_feedback="Good.",
            observations="Compliance review at the start saved time.",
        )
        agent.learn_from_outcome(outcome)

        all_memories = hindsight_adapter.list_all(limit=100)
        lesson_types = [m.memory_type for m in all_memories]
        assert MemoryType.LESSON_LEARNED in lesson_types

    def test_retained_memories_tagged_with_project_domain(
        self, db_session, hindsight_adapter, project1
    ) -> None:
        """Retained memories are tagged with the project domain."""
        mock_llm = make_mock_llm(
            lessons=["Test lesson for domain tagging."],
            patterns=[],
            risks=[],
        )
        agent = LearningAgent(session=db_session, llm=mock_llm, hindsight=hindsight_adapter)
        outcome = OutcomeCreate(
            project_id=project1.id,
            outcome_status="success",
            quality_rating=4.0,
            client_feedback="OK",
            manager_feedback="OK",
            observations="Test.",
        )
        agent.learn_from_outcome(outcome)

        all_memories = hindsight_adapter.list_all(limit=100)
        # At least one memory should have the fintech domain
        assert any(m.domain == "fintech" for m in all_memories)

    def test_recall_returns_relevant_lesson_for_similar_project(
        self, db_session, hindsight_adapter, project1, project2
    ) -> None:
        """Core learning-loop test: lesson from Project 1 is recalled for Project 2.

        This is the canonical scenario:
            Project 1 (AI Banking Assistant) → outcome → lesson retained
            Project 2 (AI FinTech Customer Assistant) → recall → lesson retrieved
        """
        mock_llm = make_mock_llm(
            lessons=[
                "FinTech AI projects require financial domain specialists.",
                "AWS deployments need dedicated DevOps from sprint 1.",
            ],
            patterns=["Domain expert pairing reduces rework in FinTech."],
            risks=["DevOps gap causes deployment delays."],
        )
        agent = LearningAgent(session=db_session, llm=mock_llm, hindsight=hindsight_adapter)
        outcome = OutcomeCreate(
            project_id=project1.id,
            outcome_status="success",
            quality_rating=5.0,
            client_feedback="Exceeded expectations.",
            manager_feedback="Great collaboration.",
            observations=(
                "Financial domain knowledge was essential. DevOps gap caused early delays."
            ),
        )
        result = agent.learn_from_outcome(outcome)
        assert result.memories_retained  # memories were retained

        # Now recall for Project 2 (same fintech domain)
        recall_request = RecallRequest(
            query=f"{project2.domain} AI customer assistant fintech",
            domain="fintech",
            memory_types=[
                MemoryType.LESSON_LEARNED,
                MemoryType.RISK_PATTERN,
                MemoryType.TEAM_PATTERN,
                MemoryType.PROJECT_OUTCOME,
            ],
            top_k=5,
        )
        recalled = hindsight_adapter.recall(recall_request)

        # Should retrieve at least one relevant memory
        assert len(recalled) >= 1, "Expected at least one memory recalled for similar project"

        # Memories should be tagged with the fintech domain
        assert any(m.domain == "fintech" for m in recalled), (
            "Recalled memories should be tagged with fintech domain"
        )

    def test_risk_pattern_retained_and_recalled(
        self, db_session, hindsight_adapter, project1
    ) -> None:
        """Risk patterns are retained and can be recalled."""
        mock_llm = make_mock_llm(
            lessons=[],
            patterns=[],
            risks=["AWS deployment without DevOps lead caused two-week delay."],
        )
        agent = LearningAgent(session=db_session, llm=mock_llm, hindsight=hindsight_adapter)
        outcome = OutcomeCreate(
            project_id=project1.id,
            outcome_status="partial_success",
            quality_rating=3.5,
            client_feedback="Delayed but acceptable.",
            manager_feedback="DevOps gap caused problems.",
            observations="AWS deployment was underestimated.",
        )
        agent.learn_from_outcome(outcome)

        # Recall for a risk-related query
        recall_request = RecallRequest(
            query="AWS deployment DevOps risk",
            domain="fintech",
            memory_types=[MemoryType.RISK_PATTERN],
            top_k=5,
        )
        recalled = hindsight_adapter.recall(recall_request)

        assert len(recalled) >= 1
        assert all(m.memory_type == MemoryType.RISK_PATTERN for m in recalled)

    def test_learning_loop_does_not_fabricate_memories(
        self, db_session, hindsight_adapter, project1
    ) -> None:
        """When LLM returns empty lessons, minimal memories are retained (outcome only)."""
        mock_llm = make_mock_llm(lessons=[], patterns=[], risks=[])
        # Manually set memory_summary to empty so no outcome memory is retained either
        import json

        empty_payload = {
            "lessons": [],
            "successful_patterns": [],
            "risk_patterns": [],
            "collaboration_insights": [],
            "staffing_recommendations": [],
            "memory_summary": "",  # empty → no outcome memory retained
        }
        mock_llm.chat.return_value = json.dumps(empty_payload)

        agent = LearningAgent(session=db_session, llm=mock_llm, hindsight=hindsight_adapter)
        outcome = OutcomeCreate(
            project_id=project1.id,
            outcome_status="failure",
            quality_rating=1.0,
            client_feedback="",
            manager_feedback="",
            observations="",
        )
        result = agent.learn_from_outcome(outcome)

        # No client feedback in failure outcome, so minimal memories
        assert isinstance(result, LearningResult)
        # Memory count should be low (0 or minimal — no fabricated entries)
        assert hindsight_adapter.count() <= 1

    def test_hindsight_memories_not_returned_in_bulk(
        self, db_session, hindsight_adapter, project1
    ) -> None:
        """Recall always returns a limited subset — never the full memory store."""
        # Seed many memories manually
        for i in range(20):
            hindsight_adapter.retain(
                RetainRequest(
                    content=f"Fintech lesson {i}: always validate inputs.",
                    summary=f"Fintech lesson {i}",
                    memory_type=MemoryType.LESSON_LEARNED,
                    domain="fintech",
                )
            )

        recall_request = RecallRequest(
            query="fintech lesson validate",
            domain="fintech",
            top_k=5,
        )
        recalled = hindsight_adapter.recall(recall_request)
        assert len(recalled) <= 5, "Recall must respect top_k ceiling"
