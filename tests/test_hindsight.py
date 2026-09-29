"""Tests for Hindsight adapter — Retain, Recall, Reflect."""

from __future__ import annotations

from hindsight.models import MemoryType, RecallRequest, ReflectRequest, RetainRequest


class TestHindsightRetain:
    def test_retain_stores_memory(self, hindsight_adapter) -> None:
        req = RetainRequest(
            content="Teams with domain experts outperform pure technical teams in fintech.",
            summary="Domain expertise critical in fintech",
            memory_type=MemoryType.LESSON_LEARNED,
            domain="fintech",
            tags=["fintech", "team_pattern"],
        )
        mem = hindsight_adapter.retain(req)
        assert mem.memory_id is not None
        assert mem.memory_type == MemoryType.LESSON_LEARNED
        assert hindsight_adapter.count() == 1

    def test_retain_multiple(self, hindsight_adapter) -> None:
        for i in range(5):
            hindsight_adapter.retain(
                RetainRequest(
                    content=f"Memory {i}",
                    summary=f"Summary {i}",
                    memory_type=MemoryType.PROJECT_OUTCOME,
                )
            )
        assert hindsight_adapter.count() == 5


class TestHindsightRecall:
    def test_recall_returns_relevant(self, hindsight_adapter) -> None:
        hindsight_adapter.retain(
            RetainRequest(
                content="Healthcare projects need HIPAA compliance lead from day 1.",
                summary="HIPAA compliance lead required",
                memory_type=MemoryType.LESSON_LEARNED,
                domain="healthcare",
                tags=["healthcare", "compliance"],
            )
        )
        hindsight_adapter.retain(
            RetainRequest(
                content="Cloud migration benefits from early architect involvement.",
                summary="Early architect involvement in cloud",
                memory_type=MemoryType.LESSON_LEARNED,
                domain="cloud",
            )
        )

        request = RecallRequest(query="healthcare HIPAA compliance", domain="healthcare", top_k=5)
        results = hindsight_adapter.recall(request)
        assert len(results) >= 1
        assert any(
            "healthcare" in m.domain.lower() or "hipaa" in m.content.lower() for m in results
        )

    def test_recall_respects_top_k(self, hindsight_adapter) -> None:
        for i in range(10):
            hindsight_adapter.retain(
                RetainRequest(
                    content=f"Python project lesson {i}",
                    summary=f"Python lesson {i}",
                    memory_type=MemoryType.LESSON_LEARNED,
                )
            )
        request = RecallRequest(query="Python project", top_k=3)
        results = hindsight_adapter.recall(request)
        assert len(results) <= 3

    def test_recall_returns_empty_for_no_match(self, hindsight_adapter) -> None:
        hindsight_adapter.retain(
            RetainRequest(
                content="Healthcare project lesson",
                summary="Healthcare",
                memory_type=MemoryType.LESSON_LEARNED,
                domain="healthcare",
            )
        )
        # Query for something completely unrelated
        request = RecallRequest(query="xyzzy quantum blockchain nft", top_k=5)
        results = hindsight_adapter.recall(request)
        assert len(results) == 0

    def test_recall_does_not_return_full_database(self, hindsight_adapter) -> None:
        for i in range(20):
            hindsight_adapter.retain(
                RetainRequest(
                    content=f"Memory {i} about various topics",
                    summary=f"Memory {i}",
                    memory_type=MemoryType.PROJECT_OUTCOME,
                )
            )
        request = RecallRequest(query="various", top_k=5)
        results = hindsight_adapter.recall(request)
        assert len(results) <= 5  # Never returns full database


class TestHindsightReflect:
    def test_reflect_no_memories_returns_standard_message(self, hindsight_adapter) -> None:
        result = hindsight_adapter.reflect(ReflectRequest(memories=[]))
        assert "No relevant organizational memory was found." in result

    def test_reflect_with_memories_returns_summary(self, hindsight_adapter) -> None:
        mem = hindsight_adapter.retain(
            RetainRequest(
                content="Test memory for reflection",
                summary="Test summary",
                memory_type=MemoryType.LESSON_LEARNED,
            )
        )
        result = hindsight_adapter.reflect(ReflectRequest(memories=[mem]))
        assert len(result) > 0
        assert "No relevant organizational memory was found." not in result
