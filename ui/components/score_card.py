"""Premium employee score card — glassmorphism design.

Renders a full-featured employee card with:
  - Name, role, seniority, department
  - Project Fit score ring
  - Progress bars (8 dimensions)
  - Skill chips
  - Previous experience
  - Availability indicator

Design: 3D glassmorphism consistent with ui/style.py
"""

from __future__ import annotations

import streamlit as st

from schemas.matching import CandidateMatch


def _score_color(pct: int) -> str:
    if pct >= 80:
        return "#10B981"   # green
    elif pct >= 60:
        return "#F59E0B"   # amber
    else:
        return "#EF4444"   # red


def _score_label(pct: int) -> str:
    if pct >= 80:
        return "Strong"
    elif pct >= 60:
        return "Good"
    elif pct >= 40:
        return "Moderate"
    else:
        return "Low"


def _progress_bar(label: str, score: float, weight_label: str = "") -> str:
    pct = int(score * 100)
    color = _score_color(pct)
    wt = f" <span style='color:#374151;font-size:0.68rem;'>({weight_label})</span>" if weight_label else ""
    return f"""
    <div style="margin:6px 0;">
        <div style="display:flex;justify-content:space-between;font-size:0.75rem;
                    font-weight:500;color:#94A3B8;margin-bottom:3px;">
            <span>{label}{wt}</span>
            <span style="color:{color};font-weight:700;">{pct}%</span>
        </div>
        <div class="alloc-progress-bar">
            <div class="alloc-progress-fill" style="width:{pct}%;background:{color};"></div>
        </div>
    </div>"""


def _chips(items: list[str], color: str = "#6366F1") -> str:
    if not items:
        return ""
    chips = "".join(
        f"<span class='alloc-chip'>{item}</span>"
        for item in items[:8]
    )
    suffix = f"<span style='color:#374151;font-size:0.72rem;margin-left:4px;'>+{len(items)-8} more</span>" if len(items) > 8 else ""
    return chips + suffix


def render_score_bar(score: float, label: str = "Project Fit Score") -> None:
    """Legacy compatibility — render a score bar via st.markdown."""
    pct = int(score * 100)
    color = _score_color(pct)
    st.markdown(
        f"""<div style="margin:6px 0;">
            <div style="display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:3px;">
                <span style="color:#94A3B8;">{label}</span>
                <span style="font-weight:700;color:{color};">{pct}%</span>
            </div>
            <div class="alloc-progress-bar">
                <div class="alloc-progress-fill" style="width:{pct}%;background:{color};"></div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_candidate_score_card(
    candidate: CandidateMatch,
    show_details: bool = False,
) -> None:
    """Render a premium glass employee card.

    This is the primary component shown in Candidate Analysis.
    Recommended Team uses render_employee_card_full().
    """
    score_pct = int(candidate.project_fit_score * 100)
    color = _score_color(score_pct)
    strength = _score_label(score_pct)

    matched = candidate.skill_detail.matched_skills if candidate.skill_detail else []
    missing = candidate.skill_detail.missing_skills if candidate.skill_detail else []

    avail = getattr(candidate, "employee_availability_percentage", None)
    avail_str = f"{avail}%" if avail is not None else "N/A"

    st.markdown(
        f"""<div class="alloc-employee-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
                <div style="flex:1;min-width:0;">
                    <div style="font-size:1.05rem;font-weight:800;color:#F1F5F9;
                                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        {candidate.employee_name}
                    </div>
                    <div style="font-size:0.8rem;color:#64748B;margin-top:2px;">
                        {candidate.employee_role} · {candidate.employee_seniority.title()} ·
                        {candidate.employee_department}
                    </div>
                    <div style="margin-top:8px;">{_chips(matched)}</div>
                </div>
                <div style="text-align:center;flex-shrink:0;">
                    <div style="width:58px;height:58px;border-radius:50%;
                                border:3px solid {color};
                                display:flex;flex-direction:column;align-items:center;
                                justify-content:center;gap:0;">
                        <div style="font-size:1rem;font-weight:800;color:{color};line-height:1.1;">
                            {score_pct}%
                        </div>
                    </div>
                    <div style="font-size:0.65rem;color:#4B5563;margin-top:4px;font-weight:600;">
                        {strength}
                    </div>
                    <div style="font-size:0.65rem;color:#374151;margin-top:1px;">
                        Avail: {avail_str}
                    </div>
                </div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    if show_details:
        with st.expander("📊 Score Breakdown & Details", expanded=False):
            bd = candidate.score_breakdown
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
            if missing:
                st.warning(f"**Missing skills:** {', '.join(missing)}", icon="⚠️")
            if candidate.risks:
                for risk in candidate.risks:
                    st.error(f"• {risk}", icon="🚨")
            if candidate.recommendation_rationale:
                st.caption(f"ℹ️ {candidate.recommendation_rationale}")
