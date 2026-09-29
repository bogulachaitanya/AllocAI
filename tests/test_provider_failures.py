"""Tests for external provider failures (LLM, Hindsight, RAG, Database)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from llm.provider import BaseLLMProvider
from schemas.project import StructuredRequirements
from services.project_analyzer import ProjectAnalyzer
from services.recommendation_engine import RecommendationEngine


class TestProviderFailures:
    def test_llm_timeout_handled_gracefully(self) -> None:
        """If the LLM times out, it should fail safely and use deterministic fallback."""
        mock_provider = MagicMock(spec=BaseLLMProvider)
        # Simulate a timeout exception
        mock_provider.chat.side_effect = TimeoutError("LLM connection timed out")

        analyzer = ProjectAnalyzer(provider=mock_provider)

        # Should not raise an unhandled exception, should return fallback requirements
        result = analyzer.analyze("Build a banking app")

        assert isinstance(result, StructuredRequirements)
        assert result.title == "Untitled Project"  # Default fallback title

    def test_hindsight_unavailable(self, db_session, sample_employees) -> None:
        """If Hindsight is unavailable, it should not crash the recommendation pipeline."""
        mock_hindsight = MagicMock()
        mock_hindsight.recall.side_effect = ConnectionError("Hindsight service down")

        mock_llm = MagicMock()
        mock_llm.chat.return_value = "Mock explanation"

        req = StructuredRequirements(title="Test", domain="fintech")
        engine = RecommendationEngine(session=db_session, hindsight=mock_hindsight, llm=mock_llm)

        # Should catch the error internally and continue without Hindsight evidence
        rec = engine.recommend(requirements=req)

        assert rec is not None
        assert rec.hindsight_memories_found is False

    def test_rag_unavailable(self, db_session, sample_employees, hindsight_adapter) -> None:
        """If RAG is unavailable, it should not crash the recommendation pipeline."""
        mock_llm = MagicMock()
        mock_llm.chat.return_value = "Mock explanation"

        req = StructuredRequirements(title="Test", domain="fintech")
        engine = RecommendationEngine(session=db_session, hindsight=hindsight_adapter, llm=mock_llm)

        # Patch the RAG retriever to raise an exception
        with patch.object(engine._rag, "retrieve", side_effect=Exception("ChromaDB down")):
            rec = engine.recommend(requirements=req)

        assert rec is not None
        # RAG failure shouldn't prevent recommendation
        assert len(rec.recommended_team) > 0

    def test_database_failure(self, db_session) -> None:
        """If the database fails during filtering, the error should propagate cleanly."""
        from services.candidate_filter import CandidateFilter

        # Mock the session to raise an OperationalError when queried
        db_session.execute = MagicMock(
            side_effect=OperationalError("DB down", params={}, orig=Exception())
        )

        req = StructuredRequirements(title="Test", domain="fintech")
        cf = CandidateFilter(db_session)

        # A hard DB failure should raise
        with pytest.raises(OperationalError):
            cf.filter_from_requirements(req)
