"""Hindsight Memory page — view, search, and add organizational memories.

Displays memories grouped by type with stats, search, and manual retention.
"""

from __future__ import annotations

import streamlit as st

from hindsight.models import MemoryType
from schemas.matching import EvidenceSource
from services.hindsight_service import HindsightService
from ui.components.evidence_card import render_evidence_badge
from ui.components.hindsight_banner import render_hindsight_mode_banner

# Icons for memory types
_MEMORY_TYPE_ICONS: dict[str, str] = {
    "team_pattern": "👥",
    "lesson_learned": "💡",
    "project_outcome": "🏁",
    "collaboration_pattern": "🤝",
    "tech_transition": "🔄",
    "risk_pattern": "⚠️",
}


def render() -> None:
    st.title("🧠 Hindsight Memory")
    st.caption("Organizational memory that improves future staffing recommendations.")

    # ── Mode banner ───────────────────────────────────────────────────────────
    render_hindsight_mode_banner()

    svc = HindsightService()
    total = svc.count()

    st.metric("Total Organizational Memories", total)
    st.divider()

    tab_browse, tab_recall, tab_add = st.tabs(["📚 Browse Memories", "🔍 Recall", "➕ Add Memory"])

    # ── BROWSE ────────────────────────────────────────────────────────────────
    with tab_browse:
        if total == 0:
            st.info(
                "No organizational memories stored yet.  \n"
                "Use **Learning Center** to record project outcomes and build memory."
            )
        else:
            memories = svc.list_all(limit=100)

            # Group by memory type
            type_groups: dict[str, list] = {}
            for mem in memories:
                key = mem.memory_type.value
                if key not in type_groups:
                    type_groups[key] = []
                type_groups[key].append(mem)

            # Type stats
            cols = st.columns(len(type_groups) if type_groups else 1)
            for i, (mem_type, mems) in enumerate(type_groups.items()):
                icon = _MEMORY_TYPE_ICONS.get(mem_type, "🧠")
                cols[i % len(cols)].metric(
                    f"{icon} {mem_type.replace('_', ' ').title()}",
                    len(mems),
                )
            st.divider()

            # Memories by type
            for mem_type, mems in type_groups.items():
                icon = _MEMORY_TYPE_ICONS.get(mem_type, "🧠")
                with st.expander(
                    f"{icon} {mem_type.replace('_', ' ').title()} ({len(mems)})",
                    expanded=len(type_groups) == 1,
                ):
                    for mem in mems:
                        render_evidence_badge(EvidenceSource.HINDSIGHT)
                        st.markdown(
                            f"<div style='margin-top:6px;font-weight:600;color:#e6edf3;'>"
                            f"{mem.summary}"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                        with st.expander("Details", expanded=False):
                            st.write(mem.content)
                            st.caption(
                                f"Domain: {mem.domain or 'N/A'} "
                                f"| Project: {mem.project_title or 'N/A'}"
                            )
                            st.caption(
                                f"Tags: {', '.join(mem.tags) if mem.tags else 'none'}"
                            )
                            st.caption(
                                f"Created: {mem.created_at.strftime('%Y-%m-%d %H:%M')}"
                            )
                        st.markdown("---")

    # ── RECALL ────────────────────────────────────────────────────────────────
    with tab_recall:
        st.markdown("Query organizational memory for relevant past experiences.")
        col_q, col_d = st.columns(2)
        with col_q:
            query = st.text_input("Search Query", placeholder="fintech fraud detection team")
        with col_d:
            domain = st.text_input("Domain Filter", placeholder="fintech")
        top_k = st.slider("Maximum Results", 1, 20, 5)

        if st.button("🔍 Recall", type="primary") and query:
            results = svc.recall(query=query, domain=domain, top_k=top_k)

            if not results:
                st.warning(
                    "No relevant organizational memory was found.  \n"
                    "Try a different query or domain.",
                    icon="🧠",
                )
            else:
                st.success(f"Found {len(results)} relevant memories")
                for mem in results:
                    icon = _MEMORY_TYPE_ICONS.get(mem.memory_type.value, "🧠")
                    render_evidence_badge(EvidenceSource.HINDSIGHT)
                    st.markdown(
                        f"**Relevance: {mem.relevance_score:.0%}** {icon} "
                        f"[{mem.memory_type.value}] {mem.summary}"
                    )
                    with st.expander("Details"):
                        st.write(mem.content)
                    st.divider()

    # ── ADD MEMORY ────────────────────────────────────────────────────────────
    with tab_add:
        st.markdown(
            "Manually add an organizational memory. "
            "Consider using **Learning Center** to let AI extract memories automatically."
        )
        with st.form("add_memory"):
            content = st.text_area("Memory Content *", height=150)
            summary = st.text_input("Summary *", placeholder="Short summary for display")
            col_t, col_d2 = st.columns(2)
            with col_t:
                mem_type = st.selectbox("Memory Type", [t.value for t in MemoryType])
            with col_d2:
                mem_domain = st.text_input("Domain", placeholder="fintech")
            mem_project = st.text_input("Associated Project", placeholder="Optional")
            tags_input = st.text_input("Tags (comma-separated)", placeholder="risk, collaboration")
            submitted = st.form_submit_button("🧠 Retain Memory", type="primary")

        if submitted:
            if not content.strip() or not summary.strip():
                st.error("Content and summary are required.")
            else:
                tags = [t.strip() for t in tags_input.split(",") if t.strip()]
                mem = svc.retain(
                    content=content.strip(),
                    summary=summary.strip(),
                    memory_type=mem_type,
                    domain=mem_domain.strip(),
                    project_title=mem_project.strip(),
                    tags=tags,
                )
                st.success(f"✅ Memory retained (ID: {mem.memory_id})")

