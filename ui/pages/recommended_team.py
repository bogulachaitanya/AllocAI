"""Recommended Team page — shows the last recommended team from session.

Displays:
  - Mock Hindsight Mode banner (Hindsight skill requirement)
  - Before / After Hindsight comparison when available
  - Full team recommendation with evidence
"""

from __future__ import annotations

import streamlit as st

from ui.components.hindsight_banner import (
    render_before_after_comparison,
    render_hindsight_mode_banner,
)
from ui.components.team_card import render_recommended_team


def render() -> None:
    st.title("👥 Recommended Team")
    st.caption(
        "The most recently recommended team. "
        "Go to **Create Project** to generate a new recommendation."
    )

    # ── Hindsight mode banner ─────────────────────────────────────────────────
    render_hindsight_mode_banner()

    rec_with = st.session_state.get("last_recommended_team")
    rec_without = st.session_state.get("last_recommended_team_without_hindsight")

    if rec_with is None:
        st.info("No team has been recommended yet. Go to **Create Project** to get started.")
        return

    project_id = st.session_state.get("last_project_id")
    if project_id:
        st.caption(f"Project ID: {project_id}")

    st.divider()

    # ── Before / After comparison (if both runs were performed) ──────────────
    if rec_without is not None:
        render_before_after_comparison(rec_without, rec_with)
        st.divider()
        st.markdown("### 🧠 Final Recommendation (With Hindsight)")

    render_recommended_team(rec_with)
