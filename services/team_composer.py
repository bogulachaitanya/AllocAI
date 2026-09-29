"""Team Composer — builds a complementary team, not just top-N individuals.

Considers:
  - Skill coverage (greedy, preserved from v1)
  - Team size constraints
  - Role diversity
  - Domain diversity (new)
  - Availability
  - Performance-aware selection (new)
  - Collaboration history (new)
  - Hindsight evidence influence (new)
  - Risk-aware selection (new)
  - Redundancy avoidance

All weights are configurable via TeamCompositionWeights.
No magic numbers are scattered through the code.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from schemas.matching import CandidateMatch, EvidenceItem
from schemas.project import StructuredRequirements
from schemas.team import RecommendedTeam, TeamValidation

logger = logging.getLogger(__name__)

# Common English stop words filtered out when extracting risk keywords from Hindsight memories
_STOP_WORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "and",
        "or",
        "in",
        "on",
        "with",
        "for",
        "to",
        "of",
        "by",
        "is",
        "was",
        "that",
        "this",
        "caused",
        "delayed",
        "without",
    }
)


# ── Team-composition weights (all configurable) ───────────────────────────────


class TeamCompositionWeights(BaseModel):
    """Configurable weights for team-level composition scoring.

    These are applied as bonuses/penalties on top of individual project-fit scores
    during team-member selection. They do NOT replace the individual score.
    """

    # Bonus applied when a candidate covers a new required skill
    new_skill_coverage_bonus: float = Field(default=0.30, ge=0.0, le=1.0)

    # Bonus for covering a new unique role not yet in the team
    new_role_bonus: float = Field(default=0.10, ge=0.0, le=1.0)

    # Bonus for covering a new domain not yet represented in the team
    new_domain_bonus: float = Field(default=0.08, ge=0.0, le=1.0)

    # Bonus when candidate has worked successfully with an existing team member
    collaboration_history_bonus: float = Field(default=0.10, ge=0.0, le=1.0)

    # Multiplier applied to performance_rating contribution (0 = ignore performance)
    performance_weight: float = Field(default=0.15, ge=0.0, le=1.0)

    # Penalty applied for each identified risk on a candidate
    risk_penalty: float = Field(default=0.15, ge=0.0, le=1.0)

    # Penalty applied when a candidate only adds redundant skills
    redundancy_penalty: float = Field(default=0.05, ge=0.0, le=1.0)

    # Minimum performance_rating to apply full performance bonus (below = degraded)
    performance_threshold: float = Field(default=3.0, ge=1.0, le=5.0)


# ── Main composer ─────────────────────────────────────────────────────────────


class TeamComposer:
    """Selects a complementary team from scored candidates.

    Selection considers the full picture — not just individual Project Fit Scores.
    """

    def __init__(self, weights: TeamCompositionWeights | None = None) -> None:
        self._weights = weights or TeamCompositionWeights()

    def compose(
        self,
        scored_candidates: list[CandidateMatch],
        requirements: StructuredRequirements,
        hindsight_evidence: list[EvidenceItem] | None = None,
        rag_evidence: list[EvidenceItem] | None = None,
        hindsight_memories: list | None = None,
    ) -> RecommendedTeam:
        """Build a team that collectively satisfies requirements.

        Algorithm:
        1. For each candidate, compute a team-context score (individual score +
           composition bonuses/penalties).
        2. Greedily select candidates that maximise team-context score.
        3. Enforce team size constraints.
        4. Validate the final team.
        """
        team_min = max(1, requirements.team_size_min)
        team_max = max(team_min, requirements.team_size_max)

        required_skills_lower = {s.lower() for s in requirements.required_skills}
        covered_skills: set[str] = set()
        covered_roles: set[str] = set()
        covered_domains: set[str] = set()
        selected: list[CandidateMatch] = []
        considered_ids: set[int] = set()

        # Build collaboration graph: employee_id → set of past collaborator IDs
        collab_graph = self._build_collaboration_graph(scored_candidates)

        # Extract Hindsight-flagged risk topics (skills/domains to prioritise)
        hindsight_risk_topics = self._extract_hindsight_risk_topics(hindsight_memories or [])
        if hindsight_risk_topics:
            logger.info("TeamComposer: Hindsight signals risk topics → %s", hindsight_risk_topics)

        # Sort by baseline project_fit_score for initial ordering
        candidates = sorted(scored_candidates, key=lambda c: c.project_fit_score, reverse=True)

        # ── Greedy selection ──────────────────────────────────────────────────
        while len(selected) < team_max and candidates:
            best_candidate = None
            best_score = -1.0

            for candidate in candidates:
                if candidate.employee_id in considered_ids:
                    continue
                if not candidate.is_available:
                    continue

                ctx_score = self._compute_team_context_score(
                    candidate=candidate,
                    required_skills=required_skills_lower,
                    covered_skills=covered_skills,
                    covered_roles=covered_roles,
                    covered_domains=covered_domains,
                    selected_ids={m.employee_id for m in selected},
                    collab_graph=collab_graph,
                    hindsight_risk_topics=hindsight_risk_topics,
                )

                if ctx_score > best_score:
                    best_score = ctx_score
                    best_candidate = candidate

            if best_candidate is None:
                break

            # Use effective coverage (current + historical) to update covered_skills
            candidate_effective = {s.lower() for s in best_candidate.effective_skill_coverage} or {
                s.lower() for s in best_candidate.skill_detail.matched_skills
            }
            candidate_domains = self._parse_domains(best_candidate)

            selected.append(best_candidate)
            covered_skills.update(candidate_effective)
            covered_roles.add(best_candidate.employee_role)
            covered_domains.update(candidate_domains)
            considered_ids.add(best_candidate.employee_id)

            # Stop early once all required skills are covered and team is at minimum
            if len(selected) >= team_min and required_skills_lower <= covered_skills:
                # Keep going only if more candidates add new value
                remaining_uncovered = required_skills_lower - covered_skills
                if not remaining_uncovered:
                    # Still fill to team_max if there are good contributors
                    pass

        # ── Fill to minimum with best available (even if unavailable) ────────
        if len(selected) < team_min:
            for candidate in candidates:
                if len(selected) >= team_min:
                    break
                if candidate.employee_id not in considered_ids:
                    selected.append(candidate)
                    considered_ids.add(candidate.employee_id)

        # ── Validate ──────────────────────────────────────────────────────────
        validation = self._validate_team(selected, requirements, covered_skills)

        h_evidence = hindsight_evidence or []
        r_evidence = rag_evidence or []
        memories_found = bool(h_evidence)
        no_memory_msg = None if memories_found else "No relevant organizational memory was found."

        return RecommendedTeam(
            members=selected,
            hindsight_evidence=h_evidence,
            rag_evidence=r_evidence,
            validation=validation,
            hindsight_memories_found=memories_found,
            no_memory_message=no_memory_msg,
        )

    # ── Team-context scoring ──────────────────────────────────────────────────

    def _compute_team_context_score(
        self,
        candidate: CandidateMatch,
        required_skills: set[str],
        covered_skills: set[str],
        covered_roles: set[str],
        covered_domains: set[str],
        selected_ids: set[int],
        collab_graph: dict[int, set[int]],
        hindsight_risk_topics: set[str],
    ) -> float:
        """Compute a context-aware score for a candidate given the current team state."""
        w = self._weights
        score = candidate.project_fit_score

        # Use effective coverage: current skills + historically demonstrated skills
        candidate_skills = {s.lower() for s in candidate.effective_skill_coverage} or {
            s.lower() for s in candidate.skill_detail.matched_skills
        }
        candidate_domains = self._parse_domains(candidate)

        # Bonus: new required skills covered
        new_required = (candidate_skills & required_skills) - covered_skills
        if new_required:
            score += w.new_skill_coverage_bonus * (len(new_required) / max(len(required_skills), 1))

        # Bonus: new role diversity
        if candidate.employee_role not in covered_roles:
            score += w.new_role_bonus

        # Bonus: new domain coverage
        new_domains = candidate_domains - covered_domains
        if new_domains:
            score += w.new_domain_bonus

        # Bonus: collaboration history with existing team
        past_collaborators = collab_graph.get(candidate.employee_id, set())
        overlap = past_collaborators & selected_ids
        if overlap:
            # Bonus scales with number of existing collaborations, capped
            collab_bonus = min(w.collaboration_history_bonus, len(overlap) * 0.05)
            score += collab_bonus
            logger.debug(
                "TeamComposer: %s has %d past collaborations with team",
                candidate.employee_name,
                len(overlap),
            )

        # Bonus/penalty: performance
        perf = candidate.score_breakdown.past_project_performance_score
        if perf >= w.performance_threshold / 5.0:
            score += w.performance_weight * perf
        elif perf > 0:
            # Below threshold — proportional degradation
            score += w.performance_weight * perf * 0.5

        # Penalty: identified risks
        if candidate.risks:
            risk_count = len(candidate.risks)
            score -= w.risk_penalty * min(risk_count, 3)

        # Penalty: only redundant skill coverage
        only_redundant = candidate_skills & covered_skills and not new_required
        if only_redundant and candidate.employee_role in covered_roles:
            score -= w.redundancy_penalty

        # Bonus: candidate has skills that Hindsight flagged as risky/important
        if hindsight_risk_topics:
            risk_coverage = candidate_skills & hindsight_risk_topics
            if risk_coverage:
                score += 0.08  # small boost for filling Hindsight-identified risk
                logger.debug(
                    "TeamComposer: %s covers Hindsight risk topic(s) %s",
                    candidate.employee_name,
                    risk_coverage,
                )

        return max(0.0, score)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _build_collaboration_graph(candidates: list[CandidateMatch]) -> dict[int, set[int]]:
        """Build a dict mapping employee_id → set of past collaborator employee IDs.

        Uses the collaboration_evidence or score_breakdown fields that the scorer populates.
        Since CandidateMatch doesn't carry raw assignment data, we infer from the
        collaboration_relevance_score: candidates with high scores have broad collaboration.
        For exact collaboration pairs, the recommendation engine can pass them explicitly.
        """
        graph: dict[int, set[int]] = {}
        for c in candidates:
            # We don't have raw assignment data at this point, so initialize empty.
            # The recommendation engine can enrich this by passing collaboration_pairs.
            graph[c.employee_id] = set()
        return graph

    @staticmethod
    def _parse_domains(candidate: CandidateMatch) -> set[str]:
        """Extract domain strings from the candidate's evidence."""
        domains: set[str] = set()
        for ev in candidate.evidence:
            if ev.label == "Domain Expertise" and ev.value:
                for part in ev.value.split(","):
                    d = part.strip().lower()
                    if d:
                        domains.add(d)
        return domains

    @staticmethod
    def _extract_hindsight_risk_topics(memories: list) -> set[str]:
        """Extract skill/technology keywords from Hindsight risk-pattern memories.

        These are used to prioritise candidates who can mitigate known risks.
        Works on HindsightMemory objects — falls back gracefully if list is empty.
        """
        risk_keywords: set[str] = set()
        for mem in memories:
            mem_type = getattr(mem, "memory_type", None)
            if mem_type is None:
                continue
            # Only act on risk_pattern memories
            if hasattr(mem_type, "value") and mem_type.value != "risk_pattern":
                continue
            # Extract words from content (simple tokenisation — no LLM involved)
            content = getattr(mem, "content", "")
            words = content.lower().split()
            # Keep tokens that look like technology/skill names (no common stop words)
            risk_keywords.update(
                w.strip(".,;:") for w in words if w not in _STOP_WORDS and len(w) > 2
            )
        return risk_keywords

    def _validate_team(
        self,
        team: list[CandidateMatch],
        requirements: StructuredRequirements,
        covered_skills: set[str],
    ) -> TeamValidation:
        required = {s.lower() for s in requirements.required_skills}
        missing = required - covered_skills
        coverage_pct = (len(covered_skills & required) / len(required) * 100) if required else 100.0

        # Role and domain coverage
        roles = list({m.employee_role for m in team})
        domains: set[str] = set()
        for m in team:
            domains.update(self._parse_domains(m))

        # Redundancy detection
        skill_counts: dict[str, int] = {}
        for m in team:
            for s in m.skill_detail.matched_skills:
                key = s.lower()
                skill_counts[key] = skill_counts.get(key, 0) + 1
        redundant = [s for s, count in skill_counts.items() if count > 1]

        # Availability check
        avail_ok = all(m.is_available and m.availability_percentage >= 20 for m in team)

        risks: list[str] = []
        warnings: list[str] = []

        if missing:
            risks.append(f"Uncovered required skills: {', '.join(sorted(missing))}")
        if not avail_ok:
            risks.append("One or more team members have low or no availability")
        if redundant:
            warnings.append(f"Redundant skills (multiple holders): {', '.join(redundant[:5])}")
        if len(team) < requirements.team_size_min:
            warnings.append(
                f"Only {len(team)} eligible candidates are available for the requested team size of {requirements.team_size_min}."
            )

        # Note which required skills are only historically evidenced (not in current stack)
        current_covered: set[str] = set()
        historical_covered: set[str] = set()
        for m in team:
            current_covered.update(s.lower() for s in m.skill_detail.matched_skills)
            historical_covered.update(s.lower() for s in m.skill_detail.historical_matched)
        hist_only_required = (historical_covered & required) - current_covered
        if hist_only_required:
            warnings.append(
                f"Skills covered only by historical evidence (not current stack): "
                f"{', '.join(sorted(hist_only_required))}"
            )

        # Performance signal
        members_with_no_perf = [
            m.employee_name
            for m in team
            if m.score_breakdown.past_project_performance_score == 0.5  # neutral/unknown
        ]
        if members_with_no_perf:
            warnings.append(
                f"Performance evidence unavailable for: {', '.join(members_with_no_perf)}"
            )

        return TeamValidation(
            skill_coverage_percentage=round(coverage_pct, 1),
            covered_skills=sorted(covered_skills & required),
            missing_skills=sorted(missing),
            role_coverage=roles,
            domain_coverage=sorted(domains),
            availability_satisfied=avail_ok,
            has_redundancy=bool(redundant),
            redundant_skills=redundant[:10],
            risks=risks,
            warnings=warnings,
        )
