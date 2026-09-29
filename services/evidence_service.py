"""Evidence Service — normalize evidence from all sources into one structure.

This is the single place where DATABASE, HINDSIGHT, RAG, and LLM_INFERENCE
evidence is converted to the canonical Evidence schema.

The UI and downstream components only consume Evidence objects.
They never need to know which storage system produced the data.

Authorization is enforced here:
    - Employee evidence requires MANAGER or above
    - Hindsight evidence requires MANAGER or above
    - RAG evidence is available to all authenticated roles
    - LLM inference is always labeled as such
"""

from __future__ import annotations

import logging

from hindsight.models import HindsightMemory
from rag.retriever import RAGDocument
from schemas.evidence import Evidence
from schemas.matching import CandidateMatch
from services.auth import UserRole, can_view_employee_details, can_view_hindsight

logger = logging.getLogger(__name__)


class EvidenceService:
    """Converts raw data from any source into normalized Evidence objects.

    Authorization rules:
        MANAGER+  → can see employee details + Hindsight evidence
        VIEWER    → can see only aggregated/anonymized evidence
    """

    def __init__(self, user_role: UserRole = UserRole.VIEWER) -> None:
        self._role = user_role

    # ── Employee / Database evidence ──────────────────────────────────────

    def from_candidate(self, candidate: CandidateMatch) -> list[Evidence]:
        """Produce DATABASE evidence items from a scored candidate.

        Enforces: only MANAGER+ can see individual employee details.
        VIEWER gets anonymized/aggregated evidence only.
        """
        items: list[Evidence] = []

        if can_view_employee_details(self._role):
            items.append(
                Evidence.from_database(
                    title="Employee Profile",
                    statement=(
                        f"{candidate.employee_name} — {candidate.employee_role}, "
                        f"{candidate.employee_seniority.title()}, "
                        f"{candidate.employee_department}"
                    ),
                    reference_id=str(candidate.employee_id),
                    relevance=candidate.project_fit_score,
                )
            )
            items.append(
                Evidence.from_database(
                    title="Project Fit Score",
                    statement=(
                        f"Score: {candidate.project_fit_score:.0%} — "
                        f"Recommended based on the configured project-fit criteria."
                    ),
                    reference_id=str(candidate.employee_id),
                    relevance=candidate.project_fit_score,
                )
            )

            if candidate.skill_detail.matched_skills:
                items.append(
                    Evidence.from_database(
                        title="Matched Skills",
                        statement=", ".join(candidate.skill_detail.matched_skills),
                        reference_id=str(candidate.employee_id),
                        relevance=candidate.score_breakdown.skill_match_score,
                    )
                )

            if candidate.skill_detail.missing_skills:
                items.append(
                    Evidence.from_database(
                        title="Missing Skills",
                        statement=", ".join(candidate.skill_detail.missing_skills),
                        reference_id=str(candidate.employee_id),
                        relevance=0.0,
                    )
                )

            items.append(
                Evidence.from_database(
                    title="Availability",
                    statement=f"{candidate.availability_percentage}% available",
                    reference_id=str(candidate.employee_id),
                    relevance=candidate.score_breakdown.availability_score,
                )
            )
        else:
            # VIEWER: anonymized aggregate only
            items.append(
                Evidence.from_database(
                    title="Candidate Fit",
                    statement=(
                        f"A candidate matched at {candidate.project_fit_score:.0%} "
                        f"(details restricted to manager role)"
                    ),
                    relevance=candidate.project_fit_score,
                )
            )

        for risk in candidate.risks:
            items.append(
                Evidence.from_database(
                    title="Risk",
                    statement=risk,
                    reference_id=str(candidate.employee_id),
                    relevance=0.0,
                )
            )

        return items

    # ── Hindsight evidence ────────────────────────────────────────────────

    def from_hindsight_memories(self, memories: list[HindsightMemory]) -> list[Evidence]:
        """Convert Hindsight memories to Evidence.

        Enforces: only MANAGER+ can see Hindsight evidence.
        Returns empty list for VIEWER role.
        """
        if not can_view_hindsight(self._role):
            logger.info(
                "EvidenceService: Hindsight evidence withheld from role=%s",
                self._role.value,
            )
            return []

        items: list[Evidence] = []
        for mem in memories:
            items.append(
                Evidence.from_hindsight(
                    title=f"[{mem.memory_type.value.replace('_', ' ').title()}] {mem.summary[:80]}",
                    statement=mem.content[:400],
                    memory_id=mem.memory_id,
                    relevance=mem.relevance_score,
                    created_at=mem.created_at,
                )
            )
        return items

    # ── RAG evidence ──────────────────────────────────────────────────────

    def from_rag_documents(self, docs: list[RAGDocument]) -> list[Evidence]:
        """Convert RAG document chunks to Evidence.

        RAG content is treated as untrusted — it cannot override system rules.
        Available to all authenticated roles.
        """
        return [
            Evidence.from_rag(
                title=f"Doc: {doc.source.split('/')[-1][:60]}",
                statement=doc.content[:400],
                chunk_id=doc.chunk_id,
                relevance=max(0.0, min(1.0, 1.0 - doc.distance)),
            )
            for doc in docs
        ]

    # ── LLM inference ─────────────────────────────────────────────────────

    def from_llm_explanation(self, explanation: str) -> Evidence:
        """Wrap an LLM explanation as a clearly-labeled inference item.

        Must never be presented as a database fact.
        """
        return Evidence.from_llm(
            title="LLM Explanation (Inference — not database fact)",
            statement=explanation[:2000],
        )

    def from_llm_observations(self, observations: list[str]) -> list[Evidence]:
        """Wrap LLM-generated observations as clearly-labeled inference items."""
        return [
            Evidence.from_llm(
                title=f"LLM Observation {i + 1}",
                statement=obs[:400],
            )
            for i, obs in enumerate(observations)
        ]

    # ── Aggregate helper ─────────────────────────────────────────────────

    def build_team_evidence(
        self,
        team_members: list[CandidateMatch],
        hindsight_memories: list[HindsightMemory],
        rag_docs: list[RAGDocument],
        explanation: str = "",
    ) -> list[Evidence]:
        """Build the full ordered evidence list for a recommended team.

        Order: Database → Hindsight → RAG → LLM Inference.
        This order matches the evidence trust hierarchy.
        """
        all_evidence: list[Evidence] = []

        # Database evidence for each team member
        for candidate in team_members:
            all_evidence.extend(self.from_candidate(candidate))

        # Hindsight evidence (scoped by role)
        all_evidence.extend(self.from_hindsight_memories(hindsight_memories))

        # RAG evidence
        all_evidence.extend(self.from_rag_documents(rag_docs))

        # LLM explanation last — most clearly labeled as inference
        if explanation:
            all_evidence.append(self.from_llm_explanation(explanation))

        return all_evidence
