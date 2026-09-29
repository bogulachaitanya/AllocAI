"""Score card component for displaying Project Fit Score."""

from __future__ import annotations

import streamlit as st

from schemas.matching import CandidateMatch


def render_score_bar(score: float, label: str = "Project Fit Score") -> None:
    """Render a color-coded progress bar for a score."""
    pct = int(score * 100)
    if pct >= 80:
        color = "#2E7D32"  # green
    elif pct >= 60:
        color = "#F57C00"  # orange
    else:
        color = "#C62828"  # red

    st.markdown(
        f"""<div style="margin:4px 0;">
        <div style="display:flex;justify-content:space-between;font-size:0.85rem;">
            <span>{label}</span><span style="font-weight:700;color:{color};">{pct}%</span>
        </div>
        <div style="background:#E0E0E0;border-radius:4px;height:8px;width:100%;">
            <div style="background:{color};width:{pct}%;height:8px;border-radius:4px;"></div>
        </div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_candidate_score_card(candidate: CandidateMatch, show_details: bool = False) -> None:
    """Render a full score card for a candidate."""
    score_pct = int(candidate.project_fit_score * 100)

    if score_pct >= 80:
        border_color = "#2E7D32"
    elif score_pct >= 60:
        border_color = "#F57C00"
    else:
        border_color = "#C62828"

    st.markdown(
        f"""<div style="
            border: 2px solid {border_color};
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
        ">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <strong style="font-size:1.05rem;">{candidate.employee_name}</strong><br/>
                <span style="color:#555;font-size:0.85rem;">
                    {candidate.employee_role} · {candidate.employee_seniority.title()} ·
                    {candidate.employee_department}
                </span>
            </div>
            <div style="text-align:center;">
                <div style="font-size:1.4rem;font-weight:800;color:{border_color};">
                    {score_pct}%
                </div>
                <div style="font-size:0.7rem;color:#777;">Project Fit Score</div>
            </div>
        </div>
        </div>""",
        unsafe_allow_html=True,
    )

    if show_details:
        with st.expander("Score Breakdown"):
            bd = candidate.score_breakdown
            render_score_bar(bd.skill_match_score, "Skill Match (30%)")
            render_score_bar(bd.experience_match_score, "Experience Match (15%)")
            render_score_bar(bd.relevant_project_experience_score, "Project Experience (15%)")
            render_score_bar(bd.domain_expertise_score, "Domain Expertise (10%)")
            render_score_bar(bd.past_project_performance_score, "Past Performance (10%)")
            render_score_bar(bd.availability_score, "Availability (10%)")
            render_score_bar(bd.certification_relevance_score, "Certifications (5%)")
            render_score_bar(bd.collaboration_relevance_score, "Collaboration (5%)")

        if candidate.skill_detail.matched_skills:
            st.success(f"✅ **Current skills:** {', '.join(candidate.skill_detail.matched_skills)}")
        if candidate.skill_detail.historical_matched:
            st.info(
                f"⏳ **Historical skills:** {', '.join(candidate.skill_detail.historical_matched)}"
            )

        effective_coverage = (
            candidate.effective_skill_coverage or candidate.skill_detail.matched_skills
        )
        if effective_coverage:
            st.caption(f"🛡️ **Effective skill coverage:** {', '.join(effective_coverage)}")

        if candidate.skill_detail.missing_skills:
            st.warning(f"⚠️ **Missing skills:** {', '.join(candidate.skill_detail.missing_skills)}")
        if candidate.risks:
            for risk in candidate.risks:
                st.error(f"🚨 {risk}")
        if candidate.recommendation_rationale:
            st.caption(f"ℹ️ {candidate.recommendation_rationale}")
