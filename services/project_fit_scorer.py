"""Project Fit Scorer — deterministic, configurable weighted scoring.

Never called an 'employee quality score'.
Weights are configurable. All evidence is labeled by source.
The LLM does not participate in scoring — scoring is purely deterministic.
"""

from __future__ import annotations

import json
import logging

from models.employee import Employee
from schemas.matching import (
    CandidateMatch,
    EvidenceItem,
    EvidenceSource,
    ProjectFitScoreBreakdown,
    ProjectFitWeights,
    SkillMatchDetail,
)
from schemas.project import StructuredRequirements

logger = logging.getLogger(__name__)


class ProjectFitScorer:
    """Calculates the Project Fit Score for each candidate.

    Score = weighted sum of:
    - Skill Match (30%)
    - Experience Match (15%)
    - Relevant Project Experience (15%)
    - Domain Expertise (10%)
    - Past Project Performance (10%)
    - Availability (10%)
    - Certification Relevance (5%)
    - Collaboration Relevance (5%)

    All weights are configurable via ProjectFitWeights.
    """

    def __init__(self, weights: ProjectFitWeights | None = None) -> None:
        self._weights = weights or ProjectFitWeights()

    def score(
        self,
        employee: Employee,
        requirements: StructuredRequirements,
    ) -> CandidateMatch:
        """Calculate the project-fit score for a single employee.

        All evidence is labeled as DATABASE source.
        Never fabricates facts.
        """
        w = self._weights

        # ── 1. Skill Match ─────────────────────────────────────────────────
        skill_detail, skill_score = self._score_skills(employee, requirements)

        # ── 2. Experience Match ────────────────────────────────────────────
        exp_score = self._score_experience(employee, requirements)

        # ── 3. Relevant Project Experience ────────────────────────────────
        proj_exp_score = self._score_project_experience(employee, requirements)

        # ── 4. Domain Expertise ───────────────────────────────────────────
        domain_score = self._score_domain(employee, requirements)

        # ── 5. Past Project Performance ───────────────────────────────────
        perf_score = self._score_performance(employee)

        # ── 6. Availability ───────────────────────────────────────────────
        avail_score = self._score_availability(employee)

        # ── 7. Certification Relevance ────────────────────────────────────
        cert_score = self._score_certifications(employee, requirements)

        # ── 8. Collaboration Relevance ────────────────────────────────────
        collab_score = self._score_collaboration(employee, requirements)

        # ── Weighted Total ────────────────────────────────────────────────
        total = (
            w.skill_match * skill_score
            + w.experience_match * exp_score
            + w.relevant_project_experience * proj_exp_score
            + w.domain_expertise * domain_score
            + w.past_project_performance * perf_score
            + w.availability * avail_score
            + w.certification_relevance * cert_score
            + w.collaboration_relevance * collab_score
        )
        total = max(0.0, min(1.0, total))

        breakdown = ProjectFitScoreBreakdown(
            skill_match_score=round(skill_score, 3),
            experience_match_score=round(exp_score, 3),
            relevant_project_experience_score=round(proj_exp_score, 3),
            domain_expertise_score=round(domain_score, 3),
            past_project_performance_score=round(perf_score, 3),
            availability_score=round(avail_score, 3),
            certification_relevance_score=round(cert_score, 3),
            collaboration_relevance_score=round(collab_score, 3),
        )

        # ── Evidence Assembly ─────────────────────────────────────────────
        evidence = self._build_evidence(employee, breakdown, requirements, skill_detail)
        risks = self._identify_risks(employee, skill_detail, requirements)

        return CandidateMatch(
            employee_id=employee.id,
            employee_name=employee.name,
            employee_role=employee.role,
            employee_department=employee.department,
            employee_seniority=employee.seniority,
            project_fit_score=round(total, 3),
            score_breakdown=breakdown,
            skill_detail=skill_detail,
            evidence=evidence,
            hindsight_evidence=[],  # Filled by recommendation engine
            rag_evidence=[],  # Filled by recommendation engine
            llm_observations=[],  # Filled by recommendation engine
            risks=risks,
            is_available=employee.is_available,
            availability_percentage=employee.availability_percentage,
            recommendation_rationale="Recommended based on the configured project-fit criteria.",
            effective_skill_coverage=sorted(
                set(skill_detail.matched_skills) | set(skill_detail.historical_matched)
            ),
        )

    def score_many(
        self,
        employees: list[Employee],
        requirements: StructuredRequirements,
    ) -> list[CandidateMatch]:
        """Score all candidates and return sorted by Project Fit Score (descending)."""
        matches = [self.score(emp, requirements) for emp in employees]
        matches.sort(key=lambda m: m.project_fit_score, reverse=True)
        return matches

    # ── Private scoring helpers ───────────────────────────────────────────────

    def _score_skills(
        self, emp: Employee, req: StructuredRequirements
    ) -> tuple[SkillMatchDetail, float]:
        # ── Current skills from employee_skills table ──────────────────
        current_skills: dict[str, int] = {
            es.skill.name.lower(): es.proficiency
            for es in emp.employee_skills
            if es.skill is not None
        }
        required_lower = [s.lower() for s in req.required_skills]
        preferred_lower = [s.lower() for s in req.preferred_skills]

        current_matched = [s for s in required_lower if s in current_skills]
        preferred_matched = [s for s in preferred_lower if s in current_skills]

        # ── Historical skills from assignments + tech_history ───────────
        historical_tech: set[str] = set()
        historical_source_notes: list[str] = []
        for assignment in emp.assignments:
            notes = assignment.manager_notes or ""
            proj_name = getattr(assignment.project, "title", f"Project {assignment.project_id}")
            for line in notes.splitlines():
                if line.startswith("Tech Stack Used:") or line.startswith("Tech After Project:"):
                    prefix, _, raw = line.partition(":")
                    for tech in raw.split("|"):
                        t = tech.strip().lower()
                        if t:
                            historical_tech.add(t)
                            historical_source_notes.append(
                                f"{prefix.strip()} '{tech.strip()}' on {proj_name}"
                            )

        # Also parse employee work_preferences (stores tech_history field)
        tech_history_raw = emp.work_preferences or ""
        for entry in tech_history_raw.replace(";", "|").split("|"):
            t = entry.strip().lower()
            if t:
                historical_tech.add(t)

        # Required skills missing from current but found in history
        missing_from_current = [s for s in required_lower if s not in current_skills]
        historical_matched = [s for s in missing_from_current if s in historical_tech]
        truly_missing = [s for s in missing_from_current if s not in historical_tech]

        # ── Scoring ─────────────────────────────────────────────
        if not required_lower:
            skill_score = 1.0 if preferred_matched else 0.7
        else:
            current_ratio = len(current_matched) / len(required_lower)
            # Historical matches get 0.6 partial credit (demonstrated past use, not current)
            historical_ratio = len(historical_matched) / len(required_lower) * 0.6
            pref_bonus = min(0.2, len(preferred_matched) / max(len(preferred_lower), 1) * 0.2)
            skill_score = min(1.0, current_ratio + historical_ratio + pref_bonus)

        # Deduplicate source notes (keep first mention per tech)
        seen: set[str] = set()
        deduped_notes: list[str] = []
        for note in historical_source_notes:
            key = note.split("'")[1].lower() if "'" in note else note
            if key not in seen:
                seen.add(key)
                deduped_notes.append(note)

        return (
            SkillMatchDetail(
                matched_skills=[s for s in req.required_skills if s.lower() in current_skills],
                missing_skills=[s for s in req.required_skills if s.lower() in truly_missing],
                preferred_matched=[s for s in req.preferred_skills if s.lower() in current_skills],
                historical_matched=[
                    s for s in req.required_skills if s.lower() in historical_matched
                ],
                historical_source_notes=deduped_notes[:10],  # cap at 10 evidence notes
            ),
            skill_score,
        )

    def _score_experience(self, emp: Employee, req: StructuredRequirements) -> float:
        years = emp.years_of_experience
        # Scale: 0 yrs → 0.2, 3 yrs → 0.6, 7 yrs → 0.9, 10+ yrs → 1.0
        if years >= 10:
            return 1.0
        if years >= 7:
            return 0.9
        if years >= 5:
            return 0.75
        if years >= 3:
            return 0.6
        if years >= 1:
            return 0.4
        return 0.2

    def _score_project_experience(self, emp: Employee, req: StructuredRequirements) -> float:
        """Score based on number of completed assignments."""
        completed = sum(1 for a in emp.assignments if a.status == "completed")
        if completed >= 5:
            return 1.0
        if completed >= 3:
            return 0.8
        if completed >= 1:
            return 0.5
        return 0.1

    def _score_domain(self, emp: Employee, req: StructuredRequirements) -> float:
        if not req.domain or req.domain == "general":
            return 0.7  # No domain constraint
        domain_lower = req.domain.lower()
        emp_domains = emp.domain_expertise.lower()
        if domain_lower in emp_domains:
            return 1.0
        # Partial match
        for word in domain_lower.split(","):
            if word.strip() and word.strip() in emp_domains:
                return 0.7
        return 0.2

    def _score_performance(self, emp: Employee) -> float:
        if emp.performance_rating is None:
            return 0.5  # No data → neutral
        # 1–5 → 0.0–1.0
        return (emp.performance_rating - 1.0) / 4.0

    def _score_availability(self, emp: Employee) -> float:
        if not emp.is_available:
            return 0.0
        return emp.availability_percentage / 100.0

    def _score_certifications(self, emp: Employee, req: StructuredRequirements) -> float:
        if not req.certifications:
            return 0.5  # No cert requirement → neutral
        cert_names_lower = {c.name.lower() for c in emp.certifications}
        req_lower = [c.lower() for c in req.certifications]
        matched = sum(1 for c in req_lower if any(c in ec for ec in cert_names_lower))
        return min(1.0, matched / len(req_lower))

    def _score_collaboration(self, emp: Employee, req: StructuredRequirements) -> float:
        """Score based on collaboration breadth (number of unique collaborators)."""
        collaborator_ids: set[int] = set()
        for assignment in emp.assignments:
            try:
                ids = json.loads(assignment.collaborated_with or "[]")
                collaborator_ids.update(ids)
            except (json.JSONDecodeError, TypeError):
                pass
        count = len(collaborator_ids)
        if count >= 10:
            return 1.0
        if count >= 5:
            return 0.7
        if count >= 2:
            return 0.5
        return 0.3

    def _build_evidence(
        self,
        emp: Employee,
        breakdown: ProjectFitScoreBreakdown,
        req: StructuredRequirements,
        skill_detail: SkillMatchDetail | None = None,
    ) -> list[EvidenceItem]:
        items = [
            EvidenceItem(
                source=EvidenceSource.DATABASE,
                label="Years of Experience",
                value=f"{emp.years_of_experience:.1f} years",
                weight=self._weights.experience_match,
            ),
            EvidenceItem(
                source=EvidenceSource.DATABASE,
                label="Seniority",
                value=emp.seniority,
            ),
            EvidenceItem(
                source=EvidenceSource.DATABASE,
                label="Department",
                value=emp.department,
            ),
            EvidenceItem(
                source=EvidenceSource.DATABASE,
                label="Availability",
                value=f"{emp.availability_percentage}%",
                weight=self._weights.availability,
            ),
        ]
        if emp.performance_rating:
            items.append(
                EvidenceItem(
                    source=EvidenceSource.DATABASE,
                    label="Performance Rating",
                    value=f"{emp.performance_rating:.1f} / 5.0",
                    weight=self._weights.past_project_performance,
                )
            )
        if emp.domain_expertise:
            items.append(
                EvidenceItem(
                    source=EvidenceSource.DATABASE,
                    label="Current Tech Stack",
                    value=emp.domain_expertise,
                    weight=self._weights.domain_expertise,
                )
            )
        # Historical skill evidence from assignment records
        if skill_detail.historical_matched:
            items.append(
                EvidenceItem(
                    source=EvidenceSource.DATABASE,
                    label="Historical Skill Match",
                    value=(
                        "Previously used on projects: " + ", ".join(skill_detail.historical_matched)
                    ),
                    weight=self._weights.relevant_project_experience,
                )
            )
        if skill_detail.historical_source_notes:
            items.append(
                EvidenceItem(
                    source=EvidenceSource.DATABASE,
                    label="Project Technology Evidence",
                    value=" | ".join(skill_detail.historical_source_notes[:5]),
                    weight=self._weights.relevant_project_experience,
                )
            )
        return items

    def _identify_risks(
        self,
        emp: Employee,
        skill_detail: SkillMatchDetail,
        req: StructuredRequirements,
    ) -> list[str]:
        risks = []
        if skill_detail.missing_skills:
            risks.append(f"Missing required skills: {', '.join(skill_detail.missing_skills)}")
        if skill_detail.historical_matched:
            risks.append(
                f"Skills only in history (not current stack): {', '.join(skill_detail.historical_matched)}"
            )
        if emp.availability_percentage < 50:
            risks.append(f"Low availability: {emp.availability_percentage}%")
        if (
            emp.years_of_experience < 2
            and req.seniority_levels
            and "senior" in req.seniority_levels
        ):
            risks.append("Employee seniority may not meet senior requirement")
        return risks
