"""Pydantic models for Hindsight memories.

Kept separate from DB ORM — Hindsight is an independent memory system.
"""

from __future__ import annotations

import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class MemoryType(StrEnum):
    PROJECT_OUTCOME = "project_outcome"
    TEAM_PATTERN = "team_pattern"
    LESSON_LEARNED = "lesson_learned"
    RISK_PATTERN = "risk_pattern"
    CLIENT_FEEDBACK = "client_feedback"
    COLLABORATION_PATTERN = "collaboration_pattern"
    ORGANIZATIONAL_INSIGHT = "organizational_insight"
    TECH_TRANSITION = "Tech Transition"


class HindsightMemory(BaseModel):
    """A single organizational memory stored in Hindsight."""

    memory_id: str
    memory_type: MemoryType
    content: str  # The memory text — never fabricated
    summary: str  # Short summary for display
    domain: str = ""
    project_title: str = ""
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    tags: list[str] = []
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    metadata: dict[str, str] = {}


class RetainRequest(BaseModel):
    """Request to retain a memory in Hindsight."""

    memory_id: str | None = None
    content: str
    summary: str
    memory_type: MemoryType
    domain: str = ""
    project_title: str = ""
    tags: list[str] = []
    metadata: dict[str, str] = {}


class RecallRequest(BaseModel):
    """Request to recall relevant memories from Hindsight."""

    query: str
    domain: str = ""
    memory_types: list[MemoryType] = []
    top_k: int = Field(default=5, ge=1, le=20)


class ReflectRequest(BaseModel):
    """Request to reflect on a set of memories and distill insights."""

    memories: list[HindsightMemory]
    context: str = ""
