"""Pydantic schemas for project outcomes and learning."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OutcomeCreate(BaseModel):
    project_id: int
    outcome_status: str = Field(default="success")
    delivered_on_time: bool | None = None
    delivered_on_budget: bool | None = None
    quality_rating: float | None = Field(default=None, ge=1.0, le=5.0)
    client_feedback: str = ""
    manager_feedback: str = ""
    observations: str = ""


class OutcomeRead(OutcomeCreate):
    id: int
    extracted_lessons: str
    retained_memory_ids: str

    model_config = {"from_attributes": True}


class LearningResult(BaseModel):
    """Result of running the learning agent on a project outcome."""

    project_id: int
    lessons_extracted: list[str] = []
    memories_retained: list[str] = []
    patterns_identified: list[str] = []
    risks_identified: list[str] = []
    summary: str = ""
