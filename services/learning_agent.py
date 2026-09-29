"""Learning Agent — processes project outcomes and retains organizational memory.

Pipeline:
Outcome + Feedback → LLM Extract Lessons → Identify Patterns →
Retain in Hindsight → Update ProjectOutcome record
"""

from __future__ import annotations

import json
import logging

from pydantic import BaseModel
from sqlalchemy.orm import Session

from hindsight.adapter import BaseHindsightAdapter, get_hindsight_adapter
from hindsight.models import MemoryType, RetainRequest
from llm.prompts import LESSON_EXTRACTION_SYSTEM, LESSON_EXTRACTION_USER
from llm.provider import BaseLLMProvider, get_llm_provider
from llm.structured_output import parse_structured_output
from models.outcome import ProjectOutcome
from models.project import Project
from repositories.outcome_repo import OutcomeRepository
from repositories.project_repo import ProjectRepository
from schemas.outcome import LearningResult, OutcomeCreate

logger = logging.getLogger(__name__)


class _LessonExtractionOutput(BaseModel):
    lessons: list[str] = []
    successful_patterns: list[str] = []
    risk_patterns: list[str] = []
    collaboration_insights: list[str] = []
    staffing_recommendations: list[str] = []
    memory_summary: str = ""


class LearningAgent:
    """Processes completed project outcomes and retains organizational memory."""

    def __init__(
        self,
        session: Session,
        llm: BaseLLMProvider | None = None,
        hindsight: BaseHindsightAdapter | None = None,
    ) -> None:
        self._session = session
        self._llm = llm or get_llm_provider()
        self._hindsight = hindsight or get_hindsight_adapter()
        self._outcome_repo = OutcomeRepository(session)
        self._project_repo = ProjectRepository(session)

    def learn_from_outcome(self, outcome_data: OutcomeCreate) -> LearningResult:
        """Record a project outcome and extract organizational learning."""

        # ── 1. Load project context ───────────────────────────────────────
        project = self._project_repo.get_with_details(outcome_data.project_id)
        if project is None:
            raise ValueError(f"Project {outcome_data.project_id} not found")

        # ── 2. Persist outcome record ─────────────────────────────────────
        existing = self._outcome_repo.get_by_project(outcome_data.project_id)
        if existing is None:
            outcome = ProjectOutcome(
                project_id=outcome_data.project_id,
                outcome_status=outcome_data.outcome_status,
                delivered_on_time=outcome_data.delivered_on_time,
                delivered_on_budget=outcome_data.delivered_on_budget,
                quality_rating=outcome_data.quality_rating,
                client_feedback=outcome_data.client_feedback,
                manager_feedback=outcome_data.manager_feedback,
                observations=outcome_data.observations,
            )
            self._outcome_repo.create(outcome)
        else:
            outcome = existing
            outcome.outcome_status = outcome_data.outcome_status
            outcome.delivered_on_time = outcome_data.delivered_on_time
            outcome.delivered_on_budget = outcome_data.delivered_on_budget
            outcome.quality_rating = outcome_data.quality_rating
            outcome.client_feedback = outcome_data.client_feedback
            outcome.manager_feedback = outcome_data.manager_feedback
            outcome.observations = outcome_data.observations
            self._session.flush()

        # ── 3. Build team summary for LLM ─────────────────────────────────
        team_summary = self._build_team_summary(project)

        # ── 4. Extract lessons via LLM ────────────────────────────────────
        extracted = self._extract_lessons(outcome_data, project, team_summary)

        # ── 5. Store lessons in outcome record ────────────────────────────
        outcome.extracted_lessons = json.dumps(extracted.lessons)

        # ── 6. Retain memories in Hindsight ──────────────────────────────
        retained_ids = self._retain_memories(extracted, outcome_data, project)
        outcome.retained_memory_ids = json.dumps(retained_ids)
        self._session.flush()

        # Update project status to completed
        project.status = "completed"
        self._session.flush()

        logger.info(
            "LearningAgent: processed outcome for project %d — %d lessons, %d memories retained",
            project.id,
            len(extracted.lessons),
            len(retained_ids),
        )

        return LearningResult(
            project_id=project.id,
            lessons_extracted=extracted.lessons,
            memories_retained=retained_ids,
            patterns_identified=extracted.successful_patterns + extracted.risk_patterns,
            risks_identified=extracted.risk_patterns,
            summary=extracted.memory_summary,
        )

    def _extract_lessons(
        self,
        outcome: OutcomeCreate,
        project: Project,
        team_summary: str,
    ) -> _LessonExtractionOutput:
        """Ask LLM to extract lessons from outcome data.

        Fallback: return empty lessons if LLM unavailable.
        """
        messages = [
            {"role": "system", "content": LESSON_EXTRACTION_SYSTEM},
            {
                "role": "user",
                "content": LESSON_EXTRACTION_USER.format(
                    project_title=project.title,
                    project_domain=project.domain or "general",
                    outcome_status=outcome.outcome_status,
                    delivered_on_time=str(outcome.delivered_on_time),
                    delivered_on_budget=str(outcome.delivered_on_budget),
                    quality_rating=str(outcome.quality_rating),
                    client_feedback=outcome.client_feedback[:1000],
                    manager_feedback=outcome.manager_feedback[:1000],
                    observations=outcome.observations[:2000],
                    team_summary=team_summary[:2000],
                ),
            },
        ]

        fallback = _LessonExtractionOutput(
            lessons=["Outcome recorded — manual lesson extraction required."],
            memory_summary=f"Project '{project.title}' completed with status: {outcome.outcome_status}.",
        )

        result = parse_structured_output(
            provider=self._llm,
            messages=messages,
            schema=_LessonExtractionOutput,
            fallback=fallback,
        )

        return result or fallback

    def _retain_memories(
        self,
        extracted: _LessonExtractionOutput,
        outcome: OutcomeCreate,
        project: Project,
    ) -> list[str]:
        """Retain meaningful memories in Hindsight.

        Only retains if there is real content — never fabricates.
        """
        retained_ids: list[str] = []
        domain = project.domain or "general"

        # Retain outcome summary
        if extracted.memory_summary:
            mem = self._hindsight.retain(
                RetainRequest(
                    content=extracted.memory_summary,
                    summary=f"Project outcome: {project.title[:80]}",
                    memory_type=MemoryType.PROJECT_OUTCOME,
                    domain=domain,
                    project_title=project.title,
                    tags=["outcome", outcome.outcome_status],
                    metadata={"project_id": str(project.id)},
                )
            )
            retained_ids.append(mem.memory_id)

        # Retain successful patterns
        for pattern in extracted.successful_patterns[:3]:
            if pattern.strip():
                mem = self._hindsight.retain(
                    RetainRequest(
                        content=pattern,
                        summary=f"Successful pattern: {pattern[:80]}",
                        memory_type=MemoryType.TEAM_PATTERN,
                        domain=domain,
                        project_title=project.title,
                        tags=["pattern", "success"],
                    )
                )
                retained_ids.append(mem.memory_id)

        # Retain risk patterns
        for risk in extracted.risk_patterns[:3]:
            if risk.strip():
                mem = self._hindsight.retain(
                    RetainRequest(
                        content=risk,
                        summary=f"Risk pattern: {risk[:80]}",
                        memory_type=MemoryType.RISK_PATTERN,
                        domain=domain,
                        project_title=project.title,
                        tags=["risk"],
                    )
                )
                retained_ids.append(mem.memory_id)

        # Retain lessons
        for lesson in extracted.lessons[:5]:
            if lesson.strip():
                mem = self._hindsight.retain(
                    RetainRequest(
                        content=lesson,
                        summary=f"Lesson: {lesson[:80]}",
                        memory_type=MemoryType.LESSON_LEARNED,
                        domain=domain,
                        project_title=project.title,
                        tags=["lesson"],
                    )
                )
                retained_ids.append(mem.memory_id)

        # Retain client feedback if positive
        if outcome.client_feedback and outcome.outcome_status in ("success", "partial_success"):
            mem = self._hindsight.retain(
                RetainRequest(
                    content=f"Client feedback for {project.title}: {outcome.client_feedback[:500]}",
                    summary=f"Client feedback ({outcome.outcome_status}): {project.title[:60]}",
                    memory_type=MemoryType.CLIENT_FEEDBACK,
                    domain=domain,
                    project_title=project.title,
                    tags=["client_feedback", outcome.outcome_status],
                )
            )
            retained_ids.append(mem.memory_id)

        return retained_ids

    def _build_team_summary(self, project: Project) -> str:
        parts = [f"Team for project: {project.title}"]
        for assignment in project.assignments:
            if hasattr(assignment, "employee") and assignment.employee:
                emp = assignment.employee
                parts.append(
                    f"- {emp.name} ({emp.role}, {emp.seniority}): "
                    f"role on project={assignment.role_on_project}, "
                    f"performance={assignment.individual_performance_rating}"
                )
        return "\n".join(parts) if len(parts) > 1 else "Team composition not recorded."
