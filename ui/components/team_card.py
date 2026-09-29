"""Team card component — renders the full recommended team with premium glass cards.

Each employee gets a rich card showing:
  - Identity (name, role, seniority)
  - Project Fit score (color-coded)
  - Score dimension progress bars
  - Matched skills (chips)
  - Previous project experience
  - Organisational Memory (Hindsight evidence)
  - Strengths and risks

Design: 3D glassmorphism consistent with ui/style.py
"""

from __future__ import annotations

import streamlit as st

from schemas.evidence import Evidence, EvidenceSource
from schemas.matching import CandidateMatch
from schemas.recommendation import Recommendation
from ui.components.evidence_card import render_evidence_items, render_no_memory_notice
from ui.components.score_card import _chips, _progress_bar, _score_color, _score_label


def _render_employee_full_card(member: CandidateMatch) -> None:
    """Render a full premium glass card for one recommended employee."""
    score_pct = int(member.project_fit_score * 100)
    color = _score_color(score_pct)
    strength = _score_label(score_pct)

    matched = member.skill_detail.matched_skills if member.skill_detail else []
    historical = member.skill_detail.historical_matched if member.skill_detail else []
    missing = member.skill_detail.missing_skills if member.skill_detail else []

    avail = getattr(member, "employee_availability_percentage", None)
    avail_str = f"{avail}%" if avail is not None else "N/A"

    has_hindsight = bool(member.hindsight_evidence)
    hindsight_tag = (
        """<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 10px;
                        border-radius:20px;font-size:0.68rem;font-weight:600;
                        background:rgba(124,58,237,0.15);border:1px solid rgba(124,58,237,0.3);
                        color:#A78BFA;">🧠 Org Memory</span>"""
        if has_hindsight
        else ""
    )

    # ── Card header ───────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="alloc-employee-card">
            <!-- Top row: identity + score -->
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;">
                <div style="flex:1;min-width:0;">
                    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:4px;">
                        <div style="font-size:1.15rem;font-weight:800;color:#F1F5F9;">
                            {member.employee_name}
                        </div>
                        {hindsight_tag}
                    </div>
                    <div style="font-size:0.82rem;color:#64748B;margin-bottom:10px;">
                        {member.employee_role} &nbsp;·&nbsp; {member.employee_seniority.title()} &nbsp;·&nbsp;
                        {member.employee_department}
                        &nbsp;·&nbsp; <span style="color:#10B981;">Available {avail_str}</span>
                    </div>

                    <!-- Skill chips -->
                    <div class="alloc-section-label">Current Skills</div>
                    <div style="margin-bottom:10px;">{_chips(matched) or '<span style="color:#374151;font-size:0.78rem;">No direct match</span>'}</div>

                    {(f'<div class="alloc-section-label">Historical Skills</div><div style="margin-bottom:10px;">{_chips(historical)}</div>') if historical else ''}
                    {(f'<div style="color:#F59E0B;font-size:0.78rem;margin-top:4px;">⚠️ Missing: {", ".join(missing)}</div>') if missing else ''}
                </div>

                <!-- Score ring -->
                <div style="text-align:center;flex-shrink:0;">
                    <div style="width:72px;height:72px;border-radius:50%;
                                border:3px solid {color};display:flex;flex-direction:column;
                                align-items:center;justify-content:center;">
                        <div style="font-size:1.25rem;font-weight:900;color:{color};line-height:1.1;">
                            {score_pct}%
                        </div>
                    </div>
                    <div style="font-size:0.68rem;font-weight:700;color:{color};margin-top:6px;">
                        {strength} Fit
                    </div>
                </div>
            </div>

            <!-- Project Fit bar -->
            <div style="margin-top:10px;">
                {_progress_bar("Project Fit", member.project_fit_score)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Expandable details ────────────────────────────────────────────────────
    with st.expander(f"📊 Why {member.employee_name.split()[0]}? — Score breakdown & evidence"):

        # Score dimensions
        bd = member.score_breakdown
        st.markdown("**Score Breakdown**")
        st.markdown(
            _progress_bar("Skill Match", bd.skill_match_score, "30%") +
            _progress_bar("Experience", bd.experience_match_score, "15%") +
            _progress_bar("Project Experience", bd.relevant_project_experience_score, "15%") +
            _progress_bar("Domain Expertise", bd.domain_expertise_score, "10%") +
            _progress_bar("Past Performance", bd.past_project_performance_score, "10%") +
            _progress_bar("Availability", bd.availability_score, "10%") +
            _progress_bar("Certifications", bd.certification_relevance_score, "5%") +
            _progress_bar("Collaboration", bd.collaboration_relevance_score, "5%"),
            unsafe_allow_html=True,
        )

        # Hindsight / Organisational Memory
        if member.hindsight_evidence:
            st.divider()
            st.markdown(
                """<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                              letter-spacing:0.08em;color:#A78BFA;margin-bottom:8px;">
                    🧠 Organisational Memory
                </div>""",
                unsafe_allow_html=True,
            )
            for item in member.hindsight_evidence:
                st.markdown(
                    f"""<div style="border-left:3px solid #7C3AED;padding:6px 12px;
                               margin:4px 0;background:rgba(124,58,237,0.06);
                               border-radius:0 6px 6px 0;font-size:0.83rem;color:#C4B5FD;">
                        <b>{item.label}</b><br>
                        <span style="color:#94A3B8;">{item.value}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )

        # RAG evidence
        if member.rag_evidence:
            st.divider()
            st.markdown(
                """<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                              letter-spacing:0.08em;color:#60A5FA;margin-bottom:8px;">
                    📄 Engineering Standards
                </div>""",
                unsafe_allow_html=True,
            )
            for item in member.rag_evidence:
                st.markdown(
                    f"""<div style="border-left:3px solid #3B82F6;padding:6px 12px;
                               margin:4px 0;background:rgba(59,130,246,0.06);
                               border-radius:0 6px 6px 0;font-size:0.83rem;color:#93C5FD;">
                        <b>{item.label}</b><br>
                        <span style="color:#94A3B8;">{item.value}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )

        # Risks
        if member.risks:
            st.divider()
            for risk in member.risks:
                st.error(f"• {risk}", icon="⚠️")

        # Rationale
        if member.recommendation_rationale:
            st.caption(f"ℹ️ {member.recommendation_rationale}")


def render_recommended_team(rec: Recommendation) -> None:
    """Render the full recommended team with summary stats and per-member cards."""
    if not rec.recommended_team:
        st.markdown(
            """<div class="alloc-glass" style="text-align:center;padding:3rem;">
                <div style="font-size:2rem;margin-bottom:0.75rem;">👥</div>
                <div style="font-size:1rem;font-weight:600;color:#94A3B8;margin-bottom:0.5rem;">
                    No team members could be recommended
                </div>
                <div style="font-size:0.85rem;color:#4B5563;">
                    Try broadening your project requirements, reducing required team size,
                    or importing more employee data.
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        return

    # ── Team summary metrics ──────────────────────────────────────────────────
    v = rec.validation
    n = len(rec.recommended_team)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Recommended", n)
    col2.metric("Skill Coverage", f"{v.skill_coverage_percentage:.0f}%" if v else "N/A")
    col3.metric("Availability", "✅ All" if (v and v.availability_satisfied) else "⚠️ Check")
    col4.metric("Skill Gaps", len(v.missing_skills) if v else 0)
    col5.metric(
        "Org Memory",
        "✅ Used" if rec.hindsight_memories_found else "None found",
    )

    # Warnings
    if v:
        for risk in (v.risks or []):
            st.error(f"🚨 {risk}")
        for warn in (v.warnings or []):
            st.warning(f"⚠️ {warn}")

    if v and v.missing_skills:
        st.warning(
            f"**Skills not covered:** {', '.join(v.missing_skills)}.  \n"
            "Consider recruiting or training for these.",
            icon="🔧",
        )

    st.divider()

    # ── Per-member cards ──────────────────────────────────────────────────────
    st.markdown(
        """<div style="font-size:1.1rem;font-weight:700;color:#F1F5F9;margin-bottom:1rem;">
            👥 Recommended Team Members
        </div>""",
        unsafe_allow_html=True,
    )
    for member in rec.recommended_team:
        _render_employee_full_card(member)

    # ── No Hindsight notice ───────────────────────────────────────────────────
    if not rec.hindsight_memories_found:
        render_no_memory_notice()

    # ── Team-level Hindsight ──────────────────────────────────────────────────
    if rec.hindsight_evidence:
        st.divider()
        render_evidence_items(rec.hindsight_evidence, title="🧠 Team-Level Organisational Memory")

    # ── AI Explanation ────────────────────────────────────────────────────────
    if rec.explanation:
        st.divider()
        st.markdown(
            """<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                          letter-spacing:0.08em;color:#6366F1;margin-bottom:6px;">
                AI Explanation
            </div>""",
            unsafe_allow_html=True,
        )
        st.info(
            "ℹ️ The following narrative was generated by AI from the recommendation data. "
            "Individual facts are sourced from the employee database and organisational memory.",
            icon="ℹ️",
        )
        st.markdown(rec.explanation)
