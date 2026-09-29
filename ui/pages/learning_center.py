"""Learning Center — record project outcomes and trigger the learning loop."""

from __future__ import annotations

import streamlit as st

from db.session import get_db
from repositories.project_repo import ProjectRepository
from schemas.outcome import OutcomeCreate
from services.learning_agent import LearningAgent


def render() -> None:
    st.title("📚 Learning Center")
    st.caption("Record project outcomes and trigger organizational learning.")

    st.divider()

    with get_db() as session:
        proj_repo = ProjectRepository(session)
        projects = proj_repo.list_recent_summaries(50)

    if not projects:
        st.info("No projects found. Create a project first.")
        return

    project_map = {f"[{p.id}] {p.title}": p.id for p in projects}
    selected_label = st.selectbox("Select Project", list(project_map.keys()))
    selected_project_id = project_map[selected_label]

    st.divider()
    st.subheader("📝 Record Outcome")

    with st.form("outcome_form"):
        col1, col2 = st.columns(2)
        with col1:
            outcome_status = st.selectbox(
                "Outcome Status",
                ["success", "partial_success", "failure", "cancelled"],
            )
            delivered_on_time = st.selectbox("Delivered On Time?", [None, True, False])
            delivered_on_budget = st.selectbox("Delivered On Budget?", [None, True, False])
        with col2:
            quality_rating = st.slider("Quality Rating", 1.0, 5.0, 4.0, 0.1)

        client_feedback = st.text_area(
            "Client Feedback",
            placeholder="What did the client say about the project?",
        )
        manager_feedback = st.text_area(
            "Manager Feedback",
            placeholder="What did the manager observe?",
        )
        observations = st.text_area(
            "Observations",
            placeholder="What worked well? What didn't? Team dynamics?",
        )

        submitted = st.form_submit_button("🎓 Record & Learn", type="primary")

    if not submitted:
        return

    outcome_data = OutcomeCreate(
        project_id=selected_project_id,
        outcome_status=outcome_status,
        delivered_on_time=delivered_on_time,
        delivered_on_budget=delivered_on_budget,
        quality_rating=quality_rating,
        client_feedback=client_feedback,
        manager_feedback=manager_feedback,
        observations=observations,
    )

    with st.spinner("🎓 Extracting lessons and retaining organizational memory..."):
        with get_db() as session:
            agent = LearningAgent(session=session)
            result = agent.learn_from_outcome(outcome_data)

    st.success("✅ Learning complete!")

    col1, col2, col3 = st.columns(3)
    col1.metric("Lessons Extracted", len(result.lessons_extracted))
    col2.metric("Memories Retained", len(result.memories_retained))
    col3.metric("Patterns Found", len(result.patterns_identified))

    if result.lessons_extracted:
        st.subheader("💡 Lessons Extracted")
        st.info("⚠️ The following lessons were extracted by LLM — verify before treating as fact.")
        for lesson in result.lessons_extracted:
            st.markdown(f"- {lesson}")

    if result.summary:
        st.subheader("🧠 Memory Summary")
        st.markdown(result.summary)
        st.caption("This summary has been retained in Hindsight for future recommendations.")
