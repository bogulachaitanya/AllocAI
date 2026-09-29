"""Pydantic schemas for Employee-related data transfer."""

from __future__ import annotations

import datetime
from enum import IntEnum

from pydantic import BaseModel, Field, field_validator


class ProficiencyLevel(IntEnum):
    BEGINNER = 1
    INTERMEDIATE = 2
    PROFICIENT = 3
    EXPERT = 4
    MASTER = 5


class SkillBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    category: str = Field(default="General", max_length=80)


class SkillRead(SkillBase):
    id: int

    model_config = {"from_attributes": True}


class EmployeeSkillRead(BaseModel):
    skill: SkillRead
    proficiency: ProficiencyLevel
    years_with_skill: float

    model_config = {"from_attributes": True}


class CertificationRead(BaseModel):
    id: int
    name: str
    issuer: str | None
    issued_year: int | None
    expires_year: int | None

    model_config = {"from_attributes": True}


class EmployeeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., max_length=200)
    role: str = Field(..., max_length=120)
    department: str = Field(..., max_length=120)
    seniority: str = Field(..., max_length=40)
    years_of_experience: float = Field(default=0.0, ge=0.0, le=60.0)
    domain_expertise: str = Field(default="")
    is_available: bool = Field(default=True)
    availability_percentage: int = Field(default=100, ge=0, le=100)
    available_from: datetime.date | None = None
    performance_rating: float | None = Field(default=None, ge=1.0, le=5.0)
    work_preferences: str = Field(default="")
    location: str = Field(default="")
    timezone: str = Field(default="UTC")

    @field_validator("seniority")
    @classmethod
    def validate_seniority(cls, v: str) -> str:
        valid = {"junior", "mid", "senior", "lead", "principal", "staff"}
        if v.lower() not in valid:
            raise ValueError(f"seniority must be one of {valid}")
        return v.lower()


class EmployeeRead(EmployeeBase):
    id: int
    employee_skills: list[EmployeeSkillRead] = []
    certifications: list[CertificationRead] = []
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class EmployeeFilter(BaseModel):
    """Parameters for structured DB filtering of candidates."""

    required_skill_names: list[str] = Field(default_factory=list)
    minimum_proficiency: ProficiencyLevel = ProficiencyLevel.PROFICIENT
    minimum_years_experience: float = Field(default=0.0, ge=0.0)
    domains: list[str] = Field(default_factory=list)
    seniority_levels: list[str] = Field(default_factory=list)
    departments: list[str] = Field(default_factory=list)
    must_be_available: bool = Field(default=True)
    minimum_availability_percentage: int = Field(default=50, ge=0, le=100)
    certification_names: list[str] = Field(default_factory=list)
