"""Reusable evidence card component.

Every evidence item is clearly labeled by source:
DATABASE | HINDSIGHT | RAG | LLM_INFERENCE

The UI must never present LLM inference as database fact.
"""

from __future__ import annotations

import streamlit as st

from schemas.evidence import Evidence, EvidenceSource

_SOURCE_CONFIG: dict[EvidenceSource, dict[str, str]] = {
    EvidenceSource.DATABASE: {
        "icon": "🗄️",
        "label": "Database Evidence",
        "color": "#1E88E5",
        "bg": "#E3F2FD",
        "border": "#1E88E5",
    },
    EvidenceSource.HINDSIGHT: {
        "icon": "🧠",
        "label": "Hindsight Evidence",
        "color": "#7B1FA2",
        "bg": "#F3E5F5",
        "border": "#7B1FA2",
    },
    EvidenceSource.RAG: {
        "icon": "📄",
        "label": "RAG Evidence",
        "color": "#2E7D32",
        "bg": "#E8F5E9",
        "border": "#2E7D32",
    },
    EvidenceSource.LLM_INFERENCE: {
        "icon": "🤖",
        "label": "LLM Inference",
        "color": "#E65100",
        "bg": "#FFF3E0",
        "border": "#E65100",
    },
}


def render_evidence_badge(source: EvidenceSource) -> None:
    """Render a small colored badge showing evidence source."""
    config = _SOURCE_CONFIG.get(source, _SOURCE_CONFIG[EvidenceSource.LLM_INFERENCE])
    st.markdown(
        f"""<span style="
            background-color: {config["bg"]};
            color: {config["color"]};
            border: 1px solid {config["border"]};
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 0.75rem;
            font-weight: 600;
        ">{config["icon"]} {config["label"]}</span>""",
        unsafe_allow_html=True,
    )


def render_evidence_items(
    items: list[Evidence],
    title: str = "Evidence",
    collapsed: bool = False,
) -> None:
    """Render a list of evidence items grouped by source."""
    if not items:
        return

    with st.expander(title, expanded=not collapsed):
        for item in items:
            config = _SOURCE_CONFIG.get(item.source, _SOURCE_CONFIG[EvidenceSource.LLM_INFERENCE])

            meta_parts = []
            if item.relevance:
                meta_parts.append(f"Relevance: {item.relevance:.0%}")
            if item.reference_id and item.source == EvidenceSource.HINDSIGHT:
                meta_parts.append(f"Memory ID: <code>{item.reference_id}</code>")
            if item.created_at:
                meta_parts.append(f"Retained: {item.created_at.strftime('%Y-%m-%d')}")

            meta_html = (
                f"<br/><small style='color:#666;'>{' | '.join(meta_parts)}</small>"
                if meta_parts
                else ""
            )

            st.markdown(
                f"""<div style="
                    border-left: 4px solid {config["border"]};
                    padding: 8px 12px;
                    margin: 4px 0;
                    background: {config["bg"]};
                    border-radius: 0 4px 4px 0;
                ">
                <span style="font-size:0.75rem;color:{config["color"]};font-weight:600;">
                    {config["icon"]} {config["label"]}
                </span><br/>
                <strong>{item.title}</strong><br/>
                <span style="font-size:0.9rem;">{item.statement}</span>
                {meta_html}
                </div>""",
                unsafe_allow_html=True,
            )


def render_no_memory_notice() -> None:
    """Display the explicit 'no organizational memory' notice."""
    st.info("🧠 **No relevant organizational memory was found.**", icon="ℹ️")
