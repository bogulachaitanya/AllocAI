"""Explicit Recommendation output schema.

The final output of the recommendation pipeline is a single Recommendation
object. The Streamlit UI consumes this directly without needing to understand
the internal pipeline structure.

Structure:
    Recommendation
    ├── project_id
    ├── project_title
    ├── project_domain
    ├── recommended_team        (list[CandidateMatch])
    ├── team_score              (aggregate float 0–1)
    ├── skill_coverage          (%)
    ├── role_coverage           (list of distinct roles)
    ├── domain_coverage         (list of domains represented)
    ├── availability_coverage   (% of team that is available)
    ├── evidence                (list[Evidence] — all sources, normalized)
    ├── hindsight_memories      (list[HindsightMemory] that influenced this)
    ├── risks                   (list[str])
    ├── skill_gaps              (list[str])
    ├── explanation             (str — LLM inference, clearly labeled)
    ├── explanation_source      ("llm_inference")
    └── weights_used            (ProjectFitWeights)
"""

from __future__ import annotations

import datetime

from pydantic import BaseModel, Field

from schemas.evidence import Evidence
from schemas.matching import CandidateMatch, ProjectFitWeights
from schemas.team import TeamValidation


class Recommendation(BaseModel):
    """The complete, self-contained output of the recommendation pipeline.

    Designed so the UI only needs to consume this one object.
    Evidence is pre-normalized: UI never needs to know storage origin.
    """

    # ── Context ───────────────────────────────────────────────────────────
    project_id: int | None = None
    project_title: str = ""
    project_domain: str = ""
    generated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    # ── Team ─────────────────────────────────────────────────────────────
    recommended_team: list[CandidateMatch] = Field(default_factory=list)

    # ── Coverage metrics ─────────────────────────────────────────────────
    team_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Mean Project Fit Score across team members",
    )
    skill_coverage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="% of required skills covered by the team",
    )
    role_coverage: list[str] = Field(
        default_factory=list,
        description="Distinct roles present in the recommended team",
    )
    domain_coverage: list[str] = Field(
        default_factory=list,
        description="Domains represented across team members",
    )
    availability_coverage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="% of team members with is_available=True",
    )

    # ── Normalized evidence (all sources) ────────────────────────────────
    evidence: list[Evidence] = Field(
        default_factory=list,
        description=(
            "All evidence items, normalized to Evidence schema. "
            "UI renders badge by evidence.source — no source-specific logic needed."
        ),
    )

    # ── Hindsight ─────────────────────────────────────────────────────────
    hindsight_memories_found: bool = False
    no_memory_message: str | None = "No relevant organizational memory was found."

    # ── Risks & gaps ─────────────────────────────────────────────────────
    risks: list[str] = Field(default_factory=list)
    skill_gaps: list[str] = Field(default_factory=list)

    # ── Validation (from TeamComposer) ───────────────────────────────────
    validation: TeamValidation | None = None

    # ── LLM explanation ──────────────────────────────────────────────────
    explanation: str = ""
    explanation_source: str = "llm_inference"
    # ⚠ Must always display with a clear "LLM Inference" badge in the UI.

    # ── Configuration used ───────────────────────────────────────────────
    weights_used: ProjectFitWeights = Field(default_factory=ProjectFitWeights)

    # ── Computed helpers ─────────────────────────────────────────────────

    def evidence_by_source(self, source: str) -> list[Evidence]:
        """Return evidence items filtered to a single source type."""
        return [e for e in self.evidence if e.source.value == source]

    @property
    def database_evidence(self) -> list[Evidence]:
        return self.evidence_by_source("database")

    @property
    def hindsight_evidence(self) -> list[Evidence]:
        return self.evidence_by_source("hindsight")

    @property
    def rag_evidence(self) -> list[Evidence]:
        return self.evidence_by_source("rag")

    @property
    def llm_evidence(self) -> list[Evidence]:
        return self.evidence_by_source("llm_inference")
