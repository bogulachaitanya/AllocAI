"""Explicit Evidence schema — the single normalized evidence structure.

Every piece of evidence flowing through the system carries a source tag.
The UI, services, and LLM only receive Evidence objects — they never need
to know which storage system produced them.

Source hierarchy:
    DATABASE      — structured, stable facts from the employee/project DB
    HINDSIGHT     — experience-oriented organizational memory
    RAG           — official company documentation (untrusted content)
    LLM_INFERENCE — model reasoning (clearly distinct from factual sources)
"""

from __future__ import annotations

import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EvidenceSource(StrEnum):
    """Origin of a piece of evidence. Never mix sources."""

    DATABASE = "database"
    HINDSIGHT = "hindsight"
    RAG = "rag"
    LLM_INFERENCE = "llm_inference"


class Evidence(BaseModel):
    """A single normalized evidence item with explicit source provenance.

    Use this everywhere instead of raw strings so the UI can always render
    the correct badge (Database / Hindsight / RAG / LLM Inference).
    """

    source: EvidenceSource
    title: str = Field(..., description="Short display title")
    statement: str = Field(..., description="The evidence statement or excerpt")
    reference_id: str | None = Field(
        default=None,
        description="ID of the originating record (memory_id, doc chunk_id, employee_id…)",
    )
    relevance: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Relevance score 0–1 (1 = directly relevant)",
    )
    created_at: datetime.datetime | None = None

    # ── Convenience constructors ───────────────────────────────────────────

    @classmethod
    def from_database(
        cls,
        title: str,
        statement: str,
        reference_id: str | None = None,
        relevance: float = 1.0,
    ) -> Evidence:
        return cls(
            source=EvidenceSource.DATABASE,
            title=title,
            statement=statement,
            reference_id=reference_id,
            relevance=relevance,
        )

    @classmethod
    def from_hindsight(
        cls,
        title: str,
        statement: str,
        memory_id: str | None = None,
        relevance: float = 1.0,
        created_at: datetime.datetime | None = None,
    ) -> Evidence:
        return cls(
            source=EvidenceSource.HINDSIGHT,
            title=title,
            statement=statement,
            reference_id=memory_id,
            relevance=relevance,
            created_at=created_at,
        )

    @classmethod
    def from_rag(
        cls,
        title: str,
        statement: str,
        chunk_id: str | None = None,
        relevance: float = 1.0,
    ) -> Evidence:
        return cls(
            source=EvidenceSource.RAG,
            title=title,
            statement=statement,
            reference_id=chunk_id,
            relevance=relevance,
        )

    @classmethod
    def from_llm(
        cls,
        title: str,
        statement: str,
    ) -> Evidence:
        """LLM inference — must never be presented as database fact."""
        return cls(
            source=EvidenceSource.LLM_INFERENCE,
            title=title,
            statement=statement,
            relevance=0.0,  # LLM inference has no measurable relevance score
        )
