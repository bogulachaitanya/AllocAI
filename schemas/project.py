"""Pydantic schemas for Project."""

from __future__ import annotations

import datetime

from pydantic import BaseModel, Field


class ProjectRequiredSkillCreate(BaseModel):
    skill_name: str
    minimum_proficiency: int = Field(default=3, ge=1, le=5)
    is_mandatory: bool = True


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    description: str = Field(default="")
    client: str = Field(default="")
    domain: str = Field(default="")
    team_size_min: int = Field(default=1, ge=1)
    team_size_max: int = Field(default=5, ge=1)
    duration_weeks: int | None = None
    start_date: datetime.date | None = None
    raw_requirement: str = Field(default="")


class ProjectSummary(BaseModel):
    id: int
    title: str

    model_config = {"from_attributes": True}


class StructuredRequirements(BaseModel):
    """LLM-extracted structured requirements from raw project text."""

    title: str
    domain: str
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    certifications: list[str] = []
    seniority_levels: list[str] = []
    team_size_min: int = 1
    team_size_max: int = 5
    duration_weeks: int | None = None
    key_responsibilities: list[str] = []
    risks: list[str] = []
    additional_context: str = ""


class ProjectRead(BaseModel):
    id: int
    title: str
    description: str
    client: str
    domain: str
    status: str
    team_size_min: int
    team_size_max: int
    duration_weeks: int | None
    start_date: datetime.date | None
    end_date: datetime.date | None
    raw_requirement: str
    structured_requirements: str
    recommendation_explanation: str
    hindsight_memory_ids: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}
