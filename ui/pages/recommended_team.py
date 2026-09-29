"""Recommended Team page — shows the last recommended team from session state.

Displays:
  - Hindsight mode indicator
  - Full team recommendation with evidence (single result, Hindsight always included)
"""

from __future__ import annotations

import streamlit as st

from ui.components.hindsight_banner import render_hindsight_mode_banner
from ui.components.team_card import render_recommended_team


def render() -> None:
    st.title("👥 Recommended Team")
    st.caption(
        "The most recently recommended team. "
        "Go to **Create Staffing Request** to generate a new recommendation."
    )

    # ── Hindsight mode banner ─────────────────────────────────────────────────
    render_hindsight_mode_banner()

    rec = st.session_state.get("last_recommended_team")

    if rec is None:
        st.info(
            "No team has been recommended yet.  \n"
            "Go to **Create Staffing Request** to describe a project and get recommendations."
        )
        return

    project_id = st.session_state.get("current_project_id")
    if project_id:
        st.caption(f"Project ID: {project_id}")

    st.divider()
    render_recommended_team(rec)

