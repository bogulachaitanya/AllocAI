"""Pydantic schemas for candidate matching and project-fit scoring."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class EvidenceSource(StrEnum):
    """Tags every evidence item by its origin — never mixed."""

    DATABASE = "database"
    HINDSIGHT = "hindsight"
    RAG = "rag"
    LLM_INFERENCE = "llm_inference"


class EvidenceItem(BaseModel):
    """A single piece of evidence with a clear source label."""

    source: EvidenceSource
    label: str
    value: str
    weight: float | None = None


class ProjectFitWeights(BaseModel):
    """Configurable weights for the Project Fit Score.

    Never called an 'employee quality score'.
    Weights must sum to 1.0.
    """

    skill_match: float = Field(default=0.30, ge=0.0, le=1.0)
    experience_match: float = Field(default=0.15, ge=0.0, le=1.0)
    relevant_project_experience: float = Field(default=0.15, ge=0.0, le=1.0)
    domain_expertise: float = Field(default=0.10, ge=0.0, le=1.0)
    past_project_performance: float = Field(default=0.10, ge=0.0, le=1.0)
    availability: float = Field(default=0.10, ge=0.0, le=1.0)
    certification_relevance: float = Field(default=0.05, ge=0.0, le=1.0)
    collaboration_relevance: float = Field(default=0.05, ge=0.0, le=1.0)

    def total(self) -> float:
        return (
            self.skill_match
            + self.experience_match
            + self.relevant_project_experience
            + self.domain_expertise
            + self.past_project_performance
            + self.availability
            + self.certification_relevance
            + self.collaboration_relevance
        )


class SkillMatchDetail(BaseModel):
    matched_skills: list[str] = []  # Matched via current employee_skills table
    missing_skills: list[str] = []
    preferred_matched: list[str] = []
    # Historical skill evidence (from assignments manager_notes / tech_history)
    historical_matched: list[str] = []  # Skills found in historical assignment records
    historical_source_notes: list[
        str
    ] = []  # Human-readable evidence lines (e.g. "Used Python on Project X")


class ProjectFitScoreBreakdown(BaseModel):
    """Detailed breakdown of how the project-fit score was calculated."""

    skill_match_score: float
    experience_match_score: float
    relevant_project_experience_score: float
    domain_expertise_score: float
    past_project_performance_score: float
    availability_score: float
    certification_relevance_score: float
    collaboration_relevance_score: float


class CandidateMatch(BaseModel):
    """A single candidate's full project-fit assessment."""

    employee_id: int
    employee_name: str
    employee_role: str
    employee_department: str
    employee_seniority: str

    # The score (0.0–1.0). Never described as "best employee."
    project_fit_score: float = Field(..., ge=0.0, le=1.0, description="Project Fit Score")
    score_breakdown: ProjectFitScoreBreakdown

    # Evidence — each item is tagged by source
    skill_detail: SkillMatchDetail
    evidence: list[EvidenceItem] = []
    hindsight_evidence: list[EvidenceItem] = []
    rag_evidence: list[EvidenceItem] = []
    llm_observations: list[str] = []

    # Effective skill coverage: union of current + historical (for display only, not scoring)
    effective_skill_coverage: list[str] = []

    # Risks from evidence
    risks: list[str] = []

    # Availability
    is_available: bool
    availability_percentage: int

    recommendation_rationale: str = ""
