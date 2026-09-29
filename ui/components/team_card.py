"""Team card component for displaying the recommended team."""

from __future__ import annotations

import streamlit as st

from schemas.evidence import Evidence, EvidenceSource
from schemas.recommendation import Recommendation
from ui.components.evidence_card import (
    render_evidence_items,
    render_no_memory_notice,
)
from ui.components.score_card import render_candidate_score_card


def render_recommended_team(rec: Recommendation) -> None:
    """Render the full recommendation with team and evidence labels."""
    st.markdown("## 👥 Recommended Team")
    st.caption("ℹ️ Recommended based on the configured project-fit criteria.")

    if not rec.recommended_team:
        st.warning("No team members could be recommended for these requirements.")
        return

    # Team validation summary
    if rec.validation:
        v = rec.validation
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Team Size", len(rec.recommended_team))
        col2.metric("Skill Coverage", f"{v.skill_coverage_percentage:.0f}%")
        col3.metric("Availability OK", "✅" if v.availability_satisfied else "❌")
        col4.metric("Skill Gaps", len(v.missing_skills))

        if v.risks:
            for risk in v.risks:
                st.error(f"🚨 {risk}")
        if v.warnings:
            for warn in v.warnings:
                st.warning(f"⚠️ {warn}")

    st.divider()

    # Team member cards
    for member in rec.recommended_team:
        render_candidate_score_card(member, show_details=True)

        # Hindsight evidence for this member
        if member.hindsight_evidence:
            hindsight_evidence = [
                Evidence(
                    source=EvidenceSource.HINDSIGHT,
                    title=item.label,
                    statement=item.value,
                    relevance=getattr(item, "weight", None) or 1.0,
                )
                for item in member.hindsight_evidence
            ]
            render_evidence_items(
                hindsight_evidence,
                title="🧠 Hindsight Evidence",
                collapsed=True,
            )
        if member.rag_evidence:
            rag_evidence = [
                Evidence(
                    source=EvidenceSource.RAG,
                    title=item.label,
                    statement=item.value,
                    relevance=getattr(item, "weight", None) or 1.0,
                )
                for item in member.rag_evidence
            ]
            render_evidence_items(
                rag_evidence,
                title="📄 RAG Evidence",
                collapsed=True,
            )
        st.divider()

    # Hindsight notice
    if not rec.hindsight_memories_found:
        render_no_memory_notice()

    # Team-level Hindsight evidence
    if rec.hindsight_evidence:
        render_evidence_items(
            rec.hindsight_evidence,
            title="🧠 Team-Level Hindsight Evidence",
        )

    # LLM Explanation — clearly labeled as inference
    if rec.explanation:
        st.markdown("### 🤖 LLM Explanation")
        st.info(
            "⚠️ **The following is LLM inference — not a database fact.**",
            icon="⚠️",
        )
        st.markdown(rec.explanation)
