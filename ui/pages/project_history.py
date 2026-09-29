"""Project History page."""

from __future__ import annotations

import streamlit as st

from db.session import get_db
from repositories.project_repo import ProjectRepository


def render() -> None:
    st.title("📁 Project History")

    status_filter = st.selectbox(
        "Filter by status", ["all", "draft", "completed", "cancelled"]
    )

    with get_db() as session:
        repo = ProjectRepository(session)
        if status_filter == "all":
            projects = repo.list_recent(50)
        else:
            projects = repo.list_by_status(status_filter, limit=50)

        if not projects:
            st.info("No projects found.")
            return

        st.markdown(f"**{len(projects)} projects**")
        st.divider()

        for proj in projects:
            status_icon = {"draft": "📝", "completed": "✅", "cancelled": "❌"}.get(
                proj.status, "❓"
            )

            with st.expander(f"{status_icon} {proj.title} — {proj.status.upper()}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Client:** {proj.client or 'N/A'}")
                    st.write(f"**Domain:** {proj.domain or 'N/A'}")
                    st.write(f"**Team Size:** {proj.team_size_min}-{proj.team_size_max}")
                with col2:
                    st.write(f"**Duration:** {proj.duration_weeks or 'N/A'} weeks")
                    st.write(f"**Created:** {proj.created_at.strftime('%Y-%m-%d')}")
                    st.write(f"**ID:** {proj.id}")

                if proj.recommendation_explanation:
                    with st.expander("🤖 Recommendation Explanation (LLM Inference)"):
                        st.info("⚠️ The following is LLM inference — not database fact.")
                        st.markdown(proj.recommendation_explanation)
