"""Hindsight Memory page — view, search, and add organizational memories."""

from __future__ import annotations

import streamlit as st

from hindsight.models import MemoryType
from schemas.matching import EvidenceSource
from services.hindsight_service import HindsightService
from ui.components.evidence_card import render_evidence_badge
from ui.components.hindsight_banner import render_hindsight_mode_banner


def render() -> None:
    st.title("🧠 Hindsight Memory")
    st.caption("Organizational memory that improves future project recommendations.")

    # ── Mode banner ───────────────────────────────────────────────────────────
    render_hindsight_mode_banner()

    svc = HindsightService()
    total = svc.count()

    st.metric("Total Memories", total)
    st.divider()

    tab_browse, tab_recall, tab_add = st.tabs(["📚 Browse", "🔍 Recall", "➕ Add Memory"])

    with tab_browse:
        memories = svc.list_all(limit=100)
        if not memories:
            st.info("No memories stored yet.")
        else:
            for mem in memories:
                render_evidence_badge(EvidenceSource.HINDSIGHT)
                st.markdown(f"**[{mem.memory_type.value}]** {mem.summary}")
                with st.expander("Full content"):
                    st.write(mem.content)
                    st.caption(
                        f"Domain: {mem.domain or 'N/A'} | Project: {mem.project_title or 'N/A'}"
                    )
                    st.caption(f"Tags: {', '.join(mem.tags) if mem.tags else 'none'}")
                    st.caption(f"Created: {mem.created_at.strftime('%Y-%m-%d %H:%M')}")
                st.divider()

    with tab_recall:
        query = st.text_input("Search query", placeholder="fintech fraud detection team")
        domain = st.text_input("Domain filter", placeholder="fintech")
        top_k = st.slider("Max results", 1, 20, 5)

        if st.button("🔍 Recall") and query:
            results = svc.recall(query=query, domain=domain, top_k=top_k)

            if not results:
                st.warning("No relevant organizational memory was found.")
            else:
                st.success(f"Found {len(results)} relevant memories")
                for mem in results:
                    render_evidence_badge(EvidenceSource.HINDSIGHT)
                    st.markdown(
                        f"**Relevance: {mem.relevance_score:.0%}** | "
                        f"[{mem.memory_type.value}] {mem.summary}"
                    )
                    with st.expander("Details"):
                        st.write(mem.content)
                    st.divider()

    with tab_add:
        st.info("Manually add an organizational memory.")
        with st.form("add_memory"):
            content = st.text_area("Memory Content *", height=150)
            summary = st.text_input("Summary *", placeholder="Short summary for display")
            mem_type = st.selectbox("Memory Type", [t.value for t in MemoryType])
            mem_domain = st.text_input("Domain", placeholder="fintech")
            mem_project = st.text_input("Associated Project", placeholder="Optional")
            tags_input = st.text_input("Tags (comma-separated)", placeholder="risk, collaboration")
            submitted = st.form_submit_button("Retain Memory")

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
