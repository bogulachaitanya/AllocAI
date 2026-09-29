"""Recommendation Engine — orchestrates the full recommendation pipeline.

Critical flow (from spec):
    PROJECT REQUIREMENT
           │
           ▼
  Project Analyzer (LLM)
           │
           ▼
 Candidate Filtering (SQL)
           │
           ▼
  Project Fit Scorer
           │
           ▼
  Hindsight Recall
           │
           ▼
   Team Composer
           │
  ┌────────┴────────┐
  ▼                 ▼
Team Validation   Evidence (via EvidenceService)
  │                 │
  └────────┬────────┘
           ▼
         LLM
           │
           ▼
  RECOMMENDED TEAM → Recommendation object
"""

from __future__ import annotations

import json
import logging
import time

from sqlalchemy.orm import Session

from hindsight.adapter import HindsightAdapter, get_hindsight_adapter
from hindsight.models import HindsightMemory, MemoryType, RecallRequest
from llm.prompts import TEAM_EXPLANATION_SYSTEM, TEAM_EXPLANATION_USER
from llm.provider import BaseLLMProvider, get_llm_provider
from models.project import Project
from rag.retriever import RAGDocument, RAGRetriever
from schemas.evidence import Evidence
from schemas.matching import EvidenceItem, EvidenceSource, ProjectFitWeights
from schemas.project import StructuredRequirements
from schemas.recommendation import Recommendation
from schemas.team import RecommendedTeam
from services.auth import ServiceGuard, UserRole
from services.candidate_filter import CandidateFilter
from services.evidence_service import EvidenceService
from services.project_fit_scorer import ProjectFitScorer
from services.team_composer import TeamComposer

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Orchestrates the full staffing recommendation pipeline.

    Authorization is enforced via ServiceGuard at the service boundary,
    not solely by caller decorators.
    """

    def __init__(
        self,
        session: Session,
        llm: BaseLLMProvider | None = None,
        hindsight: HindsightAdapter | None = None,
        weights: ProjectFitWeights | None = None,
        user_role: UserRole = UserRole.PROJECT_MANAGER,
    ) -> None:
        self._session = session
        self._llm = llm or get_llm_provider()
        self._hindsight = hindsight or get_hindsight_adapter()
        self._weights = weights or ProjectFitWeights()
        self._rag = RAGRetriever()
        self._user_role = user_role
        self._evidence_svc = EvidenceService(user_role=user_role)

    def recommend(
        self,
        requirements: StructuredRequirements,
        project: Project | None = None,
    ) -> Recommendation:
        """Run the full recommendation pipeline and return a Recommendation.

        Service boundary authorization is checked here before any data access.
        """
        # ── Service boundary authorization ────────────────────────────────
        guard = ServiceGuard(self._user_role)
        guard.require_project_creation()  # must be PM+ to run recommendations
        guard.require_employee_access()  # must be MANAGER+ to see candidates
        guard.require_hindsight_access()  # must be MANAGER+ to use Hindsight

        # ── 1. Filter candidates ──────────────────────────────────────────
        candidate_filter = CandidateFilter(self._session)
        candidates = candidate_filter.filter_from_requirements(requirements)

        if not candidates:
            logger.warning("No candidates passed the filter — widening search")
            candidates = candidate_filter.get_all_candidates()

        # ── 2. Score candidates ───────────────────────────────────────────
        scorer = ProjectFitScorer(weights=self._weights)
        scored = scorer.score_many(candidates, requirements)

        # ── 3. Recall Hindsight memories ──────────────────────────────────
        hindsight_query = f"{requirements.domain} {' '.join(requirements.required_skills[:5])}"
        recall_request = RecallRequest(
            query=hindsight_query,
            domain=requirements.domain,
            memory_types=[
                MemoryType.TEAM_PATTERN,
                MemoryType.LESSON_LEARNED,
                MemoryType.PROJECT_OUTCOME,
                MemoryType.COLLABORATION_PATTERN,
                MemoryType.TECH_TRANSITION,
            ],
            top_k=5,
        )
        try:
            hindsight_memories: list[HindsightMemory] = self._hindsight.recall(recall_request)
        except Exception as e:
            logger.error("Hindsight recall failed: %s", e)
            hindsight_memories = []

        # ── 4. RAG retrieval ──────────────────────────────────────────────
        rag_query = (
            f"{requirements.title} {requirements.domain} "
            f"{' '.join(requirements.required_skills[:3])}"
        )
        try:
            rag_docs: list[RAGDocument] = self._rag.retrieve(rag_query)
        except Exception as e:
            logger.error("RAG retrieval failed: %s", e)
            rag_docs = []

        # ── 5. Build legacy EvidenceItem lists for TeamComposer ───────────
        # (TeamComposer still uses EvidenceItem — kept for backward compat)
        hindsight_evidence_items = [
            EvidenceItem(
                source=EvidenceSource.HINDSIGHT,
                label=f"[{m.memory_type.value}] {m.summary[:80]}",
                value=m.content[:300],
            )
            for m in hindsight_memories
        ]
        rag_evidence_items = [
            EvidenceItem(
                source=EvidenceSource.RAG,
                label=f"Doc: {doc.source.split('/')[-1][:60]}",
                value=doc.content[:300],
            )
            for doc in rag_docs
        ]

        # Attach to top candidates for backward-compat UI paths
        if hindsight_evidence_items:
            for candidate in scored[:10]:
                candidate.hindsight_evidence = hindsight_evidence_items
                candidate.rag_evidence = rag_evidence_items

        # ── 6. Compose complementary team ─────────────────────────────────
        composer = TeamComposer()
        team: RecommendedTeam = composer.compose(
            scored_candidates=scored,
            requirements=requirements,
            hindsight_evidence=hindsight_evidence_items,
            rag_evidence=rag_evidence_items,
            hindsight_memories=hindsight_memories,
        )

        # ── 7. Generate LLM explanation ───────────────────────────────────
        explanation = self._generate_explanation(team, requirements, hindsight_memories, rag_docs)
        team.explanation = explanation
        team.explanation_source = "llm_inference"

        if project:
            team.project_id = project.id
        team.weights_used = self._weights

        # ── 8. Normalize evidence via EvidenceService ─────────────────────
        normalized_evidence: list[Evidence] = self._evidence_svc.build_team_evidence(
            team_members=team.members,
            hindsight_memories=hindsight_memories,
            rag_docs=rag_docs,
            explanation=explanation,
        )

        # ── 9. Persist Hindsight memory IDs to project ───────────────────
        if project and hindsight_memories:
            memory_ids = [m.memory_id for m in hindsight_memories]
            project.hindsight_memory_ids = json.dumps(memory_ids)
            self._session.flush()

        # ── 10. Assemble the Recommendation object ────────────────────────
        recommendation = self._assemble_recommendation(
            project=project,
            requirements=requirements,
            team=team,
            normalized_evidence=normalized_evidence,
            hindsight_memories=hindsight_memories,
        )

        logger.info(
            "RecommendationEngine: %d members, skill_coverage=%.0f%%, "
            "hindsight_memories=%d, domain=%s",
            len(team.members),
            recommendation.skill_coverage,
            len(hindsight_memories),
            requirements.domain,
        )
        return recommendation

    def recommend_without_hindsight(
        self,
        requirements: StructuredRequirements,
        project: Project | None = None,
    ) -> Recommendation:
        """Run the recommendation pipeline with Hindsight recall intentionally disabled.

        Used by the Before/After demo to show the baseline recommendation
        (skills + experience + availability + performance only).

        Hindsight skill rule:
            The UI must clearly show the difference between recommendations
            with and without Hindsight.
        """
        # ── Service boundary authorization ────────────────────────────────
        guard = ServiceGuard(self._user_role)
        guard.require_project_creation()
        guard.require_employee_access()

        # ── 1. Filter candidates ──────────────────────────────────────────
        candidate_filter = CandidateFilter(self._session)
        candidates = candidate_filter.filter_from_requirements(requirements)
        if not candidates:
            logger.warning("No candidates (no-Hindsight path) — widening search")
            candidates = candidate_filter.get_all_candidates()

        # ── 2. Score candidates ───────────────────────────────────────────
        scorer = ProjectFitScorer(weights=self._weights)
        scored = scorer.score_many(candidates, requirements)

        # ── 3. Compose team — NO Hindsight memories passed ───────────────
        composer = TeamComposer()
        team: RecommendedTeam = composer.compose(
            scored_candidates=scored,
            requirements=requirements,
            hindsight_evidence=[],
            rag_evidence=[],
            hindsight_memories=[],
        )

        # ── 4. LLM explanation (no Hindsight context) ─────────────────────
        explanation = self._generate_explanation(
            team=team,
            requirements=requirements,
            hindsight_memories=[],
            rag_docs=[],
        )
        team.explanation = explanation
        team.explanation_source = "llm_inference"

        if project:
            team.project_id = project.id
        team.weights_used = self._weights

        # ── 5. Normalize evidence (DATABASE + LLM only) ───────────────────
        normalized_evidence = self._evidence_svc.build_team_evidence(
            team_members=team.members,
            hindsight_memories=[],
            rag_docs=[],
            explanation=explanation,
        )

        recommendation = self._assemble_recommendation(
            project=project,
            requirements=requirements,
            team=team,
            normalized_evidence=normalized_evidence,
            hindsight_memories=[],
        )

        logger.info(
            "RecommendationEngine (no-Hindsight): %d members, skill_coverage=%.0f%%, domain=%s",
            len(team.members),
            recommendation.skill_coverage,
            requirements.domain,
        )
        return recommendation

    # ── Private helpers ───────────────────────────────────────────────────────

    def _generate_explanation(
        self,
        team: RecommendedTeam,
        requirements: StructuredRequirements,
        hindsight_memories: list[HindsightMemory],
        rag_docs: list[RAGDocument],
    ) -> str:
        """Call LLM to explain the recommendation — labeled as inference."""
        team_summary_parts: list[str] = []
        for m in team.members:
            skills_str = ", ".join(m.skill_detail.matched_skills[:5])
            team_summary_parts.append(
                f"- {m.employee_name} ({m.employee_role}, {m.employee_seniority}): "
                f"Project Fit Score={m.project_fit_score:.2f}, "
                f"Skills matched: {skills_str or 'none'}, "
                f"Availability: {m.availability_percentage}%"
            )

        h_str = (
            "\n".join(
                f"- [{m.memory_type.value}] {m.summary}: {m.content[:120]}"
                for m in hindsight_memories
            )
            or "No relevant organizational memory was found."
        )
        r_str = (
            "\n".join(f"- {doc.source.split('/')[-1]}: {doc.content[:120]}" for doc in rag_docs)
            or "No RAG documentation retrieved."
        )

        messages = [
            {"role": "system", "content": TEAM_EXPLANATION_SYSTEM},
            {
                "role": "user",
                "content": TEAM_EXPLANATION_USER.format(
                    project_title=requirements.title,
                    project_domain=requirements.domain,
                    structured_requirements=str(requirements.model_dump()),
                    team_members_evidence="\n".join(team_summary_parts) or "No members.",
                    hindsight_evidence=h_str,
                    rag_evidence=r_str,
                ),
            },
        ]

        start_time = time.time()
        explanation = self._llm.chat(messages=messages)
        elapsed = time.time() - start_time
        logger.info("LLM team explanation generation: %.1fs", elapsed)

        if not explanation:
            return (
                "Team recommended based on the configured project-fit criteria. "
                "LLM explanation unavailable."
            )
        return explanation

    def _assemble_recommendation(
        self,
        project: Project | None,
        requirements: StructuredRequirements,
        team: RecommendedTeam,
        normalized_evidence: list[Evidence],
        hindsight_memories: list[HindsightMemory],
    ) -> Recommendation:
        """Package all pipeline outputs into the canonical Recommendation object."""
        members = team.members

        # Team score: mean of member scores
        team_score = sum(m.project_fit_score for m in members) / len(members) if members else 0.0

        # Coverage metrics
        skill_coverage = team.validation.skill_coverage_percentage if team.validation else 0.0
        role_coverage = list({m.employee_role for m in members})
        domain_coverage: list[str] = []
        for m in members:
            for ev in m.evidence:
                if ev.label == "Domain Expertise" and ev.value:
                    domain_coverage.extend([d.strip() for d in ev.value.split(",") if d.strip()])
        domain_coverage = sorted(set(domain_coverage))

        avail_count = sum(1 for m in members if m.is_available)
        avail_pct = (avail_count / len(members) * 100) if members else 0.0

        # Risks and gaps
        all_risks: list[str] = []
        for m in members:
            all_risks.extend(m.risks)
        if team.validation:
            all_risks.extend(team.validation.risks)
        all_risks = list(dict.fromkeys(all_risks))  # deduplicate preserving order

        skill_gaps = team.validation.missing_skills if team.validation else []

        return Recommendation(
            project_id=project.id if project else None,
            project_title=requirements.title,
            project_domain=requirements.domain,
            recommended_team=members,
            team_score=round(team_score, 3),
            skill_coverage=round(skill_coverage, 1),
            role_coverage=role_coverage,
            domain_coverage=domain_coverage,
            availability_coverage=round(avail_pct, 1),
            evidence=normalized_evidence,
            hindsight_memories_found=bool(hindsight_memories),
            no_memory_message=(
                None if hindsight_memories else "No relevant organizational memory was found."
            ),
            risks=all_risks,
            skill_gaps=skill_gaps,
            validation=team.validation,
            explanation=team.explanation,
            explanation_source="llm_inference",
            weights_used=self._weights,
        )
