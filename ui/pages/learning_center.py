"""Learning Center — record project outcomes and trigger the organizational learning loop.

Sections:
  A. Select Completed Project
  B. Project Outcome
  C. Client Feedback
  D. Manager Feedback
  E. Project Observations
  F. Lessons Learned
  G. Learn From Project (trigger Learning Agent → Hindsight Retain)
"""

from __future__ import annotations

import streamlit as st

from db.session import get_db
from repositories.project_repo import ProjectRepository
from schemas.outcome import OutcomeCreate
from services.learning_agent import LearningAgent


def _section_header(icon: str, title: str, subtitle: str = "") -> None:
    """Render a styled section header."""
    st.markdown(
        f"""<div style='margin:1.5rem 0 0.5rem 0;'>
            <span style='font-size:0.75rem;font-weight:700;text-transform:uppercase;
                         letter-spacing:0.08em;color:#58a6ff;'>{icon} {title}</span>
            {"<div style='color:#8b949e;font-size:0.82rem;margin-top:2px;'>" + subtitle + "</div>" if subtitle else ""}
        </div>""",
        unsafe_allow_html=True,
    )


def render() -> None:
    st.title("📚 Learning Center")
    st.caption(
        "Record project outcomes, capture lessons, and build organizational memory "
        "that improves future staffing recommendations."
    )

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION A — Select Project
    # ══════════════════════════════════════════════════════════════════════════
    _section_header("A.", "Select Completed Project", "Choose the project to record learning for.")

    with get_db() as session:
        proj_repo = ProjectRepository(session)
        projects = proj_repo.list_recent_summaries(100)

    if not projects:
        st.info(
            "No projects found yet.  \n"
            "Create a staffing request first using **Create Staffing Request**."
        )
        return

    project_map = {f"[{p.id}] {p.title}": p.id for p in projects}
    selected_label = st.selectbox(
        "Select Project",
        list(project_map.keys()),
        help="Select the project whose outcome you want to record.",
    )
    selected_project_id = project_map[selected_label]

    st.divider()

    with st.form("learning_center_form"):

        # ════════════════════════════════════════════════════════════════════
        # SECTION B — Project Outcome
        # ════════════════════════════════════════════════════════════════════
        st.markdown(
            "<div style='font-size:0.8rem;font-weight:700;text-transform:uppercase;"
            "letter-spacing:0.08em;color:#58a6ff;margin-bottom:8px;'>B. Project Outcome</div>",
            unsafe_allow_html=True,
        )

        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            outcome_status = st.selectbox(
                "Overall Result",
                ["success", "partial_success", "failure", "cancelled"],
                help="The final outcome of the project.",
            )
        with col_b2:
            delivered_on_time = st.selectbox(
                "Delivered On Time?",
                [None, True, False],
                format_func=lambda x: "Unknown" if x is None else ("Yes" if x else "No"),
            )
        with col_b3:
            delivered_on_budget = st.selectbox(
                "Delivered On Budget?",
                [None, True, False],
                format_func=lambda x: "Unknown" if x is None else ("Yes" if x else "No"),
            )

        quality_rating = st.slider(
            "Overall Quality Rating",
            min_value=1.0,
            max_value=5.0,
            value=4.0,
            step=0.1,
            help="1 = Poor, 5 = Excellent",
        )

        st.divider()

        # ════════════════════════════════════════════════════════════════════
        # SECTION C — Client Feedback
        # ════════════════════════════════════════════════════════════════════
        st.markdown(
            "<div style='font-size:0.8rem;font-weight:700;text-transform:uppercase;"
            "letter-spacing:0.08em;color:#58a6ff;margin-bottom:8px;'>C. Client Feedback</div>",
            unsafe_allow_html=True,
        )

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            client_rating = st.slider(
                "Client Satisfaction Rating",
                min_value=1.0,
                max_value=5.0,
                value=4.0,
                step=0.1,
                help="Client's overall satisfaction rating.",
            )
        with col_c2:
            client_strengths = st.text_input(
                "Client-Highlighted Strengths",
                placeholder="e.g. Fast delivery, strong communication",
            )

        client_feedback = st.text_area(
            "Client Feedback",
            placeholder="What did the client say about the project outcome and team performance?",
            height=100,
        )
        client_concerns = st.text_area(
            "Client Concerns / Improvement Areas",
            placeholder="What concerns did the client raise?",
            height=80,
        )

        st.divider()

        # ════════════════════════════════════════════════════════════════════
        # SECTION D — Manager Feedback
        # ════════════════════════════════════════════════════════════════════
        st.markdown(
            "<div style='font-size:0.8rem;font-weight:700;text-transform:uppercase;"
            "letter-spacing:0.08em;color:#58a6ff;margin-bottom:8px;'>D. Manager Feedback</div>",
            unsafe_allow_html=True,
        )

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            tech_performance = st.text_input(
                "Technical Performance",
                placeholder="e.g. Strong ML delivery, clean code",
            )
            delivery_quality = st.text_input(
                "Delivery Quality",
                placeholder="e.g. Delivered all features, minor bugs",
            )
            mgr_strengths = st.text_input(
                "Team Strengths",
                placeholder="e.g. Collaboration, problem-solving",
            )
        with col_d2:
            communication = st.text_input(
                "Communication",
                placeholder="e.g. Clear updates, good stakeholder management",
            )
            leadership = st.text_input(
                "Leadership",
                placeholder="e.g. Strong lead, good delegation",
            )
            improvement_areas = st.text_input(
                "Improvement Areas",
                placeholder="e.g. Needs more AWS expertise next time",
            )

        manager_feedback = st.text_area(
            "Manager Observations",
            placeholder="Overall observations about the team performance and dynamics.",
            height=100,
        )

        st.divider()

        # ════════════════════════════════════════════════════════════════════
        # SECTION E — Project Observations
        # ════════════════════════════════════════════════════════════════════
        st.markdown(
            "<div style='font-size:0.8rem;font-weight:700;text-transform:uppercase;"
            "letter-spacing:0.08em;color:#58a6ff;margin-bottom:8px;'>E. Project Observations</div>",
            unsafe_allow_html=True,
        )

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            what_worked = st.text_area(
                "What Worked Well?",
                placeholder="e.g. Agile process, daily standups",
                height=80,
            )
            challenges = st.text_area(
                "Challenges Faced",
                placeholder="e.g. AWS IAM setup delayed start",
                height=80,
            )
        with col_e2:
            what_failed = st.text_area(
                "What Didn't Work?",
                placeholder="e.g. Initial scope too broad, needed clearer requirements",
                height=80,
            )
            successful_approaches = st.text_area(
                "Successful Approaches",
                placeholder="e.g. Paired programming for ML components",
                height=80,
            )

        tech_issues = st.text_input(
            "Technology Issues",
            placeholder="e.g. FastAPI version conflicts, upgrade needed",
        )
        team_collaboration = st.text_area(
            "Team Collaboration Observations",
            placeholder="e.g. Strong pairing between ML and backend engineers",
            height=80,
        )

        # Build combined observations field
        observations_parts = []
        if what_worked:
            observations_parts.append(f"What worked: {what_worked}")
        if what_failed:
            observations_parts.append(f"What didn't work: {what_failed}")
        if challenges:
            observations_parts.append(f"Challenges: {challenges}")
        if successful_approaches:
            observations_parts.append(f"Successful approaches: {successful_approaches}")
        if tech_issues:
            observations_parts.append(f"Tech issues: {tech_issues}")
        if team_collaboration:
            observations_parts.append(f"Collaboration: {team_collaboration}")

        st.divider()

        # ════════════════════════════════════════════════════════════════════
        # SECTION F — Lessons Learned
        # ════════════════════════════════════════════════════════════════════
        st.markdown(
            "<div style='font-size:0.8rem;font-weight:700;text-transform:uppercase;"
            "letter-spacing:0.08em;color:#58a6ff;margin-bottom:8px;'>F. Lessons Learned</div>",
            unsafe_allow_html=True,
        )

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            key_lesson = st.text_area(
                "Key Lesson Learned",
                placeholder="e.g. Always include a dedicated DevOps person for cloud-heavy projects",
                height=80,
            )
            what_to_repeat = st.text_area(
                "What Should Be Repeated?",
                placeholder="e.g. Paired ML + Backend from day 1",
                height=80,
            )
        with col_f2:
            what_to_avoid = st.text_area(
                "What Should Be Avoided?",
                placeholder="e.g. Starting without IAM access configured",
                height=80,
            )
            recommended_improvement = st.text_area(
                "Recommended Improvement",
                placeholder="e.g. Add cloud infrastructure checklist to project kickoff",
                height=80,
            )

        # Combine lessons into structured text
        lessons_parts = []
        if key_lesson:
            lessons_parts.append(f"Key lesson: {key_lesson}")
        if what_to_repeat:
            lessons_parts.append(f"Repeat: {what_to_repeat}")
        if what_to_avoid:
            lessons_parts.append(f"Avoid: {what_to_avoid}")
        if recommended_improvement:
            lessons_parts.append(f"Improvement: {recommended_improvement}")

        # Build enriched manager feedback combining all manager fields
        mgr_feedback_parts = []
        if tech_performance:
            mgr_feedback_parts.append(f"Technical performance: {tech_performance}")
        if communication:
            mgr_feedback_parts.append(f"Communication: {communication}")
        if delivery_quality:
            mgr_feedback_parts.append(f"Delivery: {delivery_quality}")
        if leadership:
            mgr_feedback_parts.append(f"Leadership: {leadership}")
        if mgr_strengths:
            mgr_feedback_parts.append(f"Strengths: {mgr_strengths}")
        if improvement_areas:
            mgr_feedback_parts.append(f"Improvement areas: {improvement_areas}")
        if manager_feedback:
            mgr_feedback_parts.append(f"Observations: {manager_feedback}")

        # Build enriched client feedback combining all client fields
        client_feedback_parts = []
        if client_rating:
            client_feedback_parts.append(f"Client rating: {client_rating}/5")
        if client_strengths:
            client_feedback_parts.append(f"Strengths noted by client: {client_strengths}")
        if client_feedback:
            client_feedback_parts.append(f"Feedback: {client_feedback}")
        if client_concerns:
            client_feedback_parts.append(f"Concerns: {client_concerns}")

        st.divider()

        # ════════════════════════════════════════════════════════════════════
        # SECTION G — Learn From Project
        # ════════════════════════════════════════════════════════════════════
        st.markdown(
            "<div style='font-size:0.8rem;font-weight:700;text-transform:uppercase;"
            "letter-spacing:0.08em;color:#58a6ff;margin-bottom:8px;'>G. Learn From Project</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='color:#8b949e;font-size:0.85rem;margin-bottom:12px;'>"
            "Click the button below to extract lessons and store them in Hindsight organizational memory. "
            "These memories will influence future staffing recommendations for similar projects."
            "</div>",
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button("🧠 Learn From Project", type="primary")

    # ── Processing ────────────────────────────────────────────────────────────
    if not submitted:
        return

    # Assemble all text fields
    combined_observations = " | ".join(observations_parts) if observations_parts else ""
    combined_client_feedback = " | ".join(client_feedback_parts) if client_feedback_parts else ""
    combined_manager_feedback = " | ".join(mgr_feedback_parts) if mgr_feedback_parts else ""
    combined_lessons = " | ".join(lessons_parts) if lessons_parts else ""

    # Append lessons to observations for the Learning Agent
    full_observations = combined_observations
    if combined_lessons:
        full_observations += f" | Lessons: {combined_lessons}"

    outcome_data = OutcomeCreate(
        project_id=selected_project_id,
        outcome_status=outcome_status,
        delivered_on_time=delivered_on_time,
        delivered_on_budget=delivered_on_budget,
        quality_rating=quality_rating,
        client_feedback=combined_client_feedback[:2000] if combined_client_feedback else None,
        manager_feedback=combined_manager_feedback[:2000] if combined_manager_feedback else None,
        observations=full_observations[:4000] if full_observations else None,
    )

    with st.spinner("🧠 Extracting lessons and storing in organizational memory…"):
        try:
            with get_db() as session:
                agent = LearningAgent(session=session)
                result = agent.learn_from_outcome(outcome_data)
        except Exception as exc:
            st.error(
                f"Learning process encountered an error: {exc}  \n"
                "Please check the project details and try again."
            )
            return

    st.success("✅ Organizational learning stored in Hindsight.")
    st.divider()

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Lessons Extracted", len(result.lessons_extracted))
    col_m2.metric("Memories Retained", len(result.memories_retained))
    col_m3.metric("Patterns Found", len(result.patterns_identified))

    if result.lessons_extracted:
        st.subheader("💡 Lessons Extracted")
        st.info(
            "ℹ️ Lessons extracted by AI — review before treating as definitive fact.",
            icon="ℹ️",
        )
        for lesson in result.lessons_extracted:
            st.markdown(
                f"<div style='border-left:3px solid #58a6ff;padding:6px 12px;"
                f"margin:4px 0;background:rgba(88,166,255,0.05);border-radius:0 6px 6px 0;'>"
                f"• {lesson}</div>",
                unsafe_allow_html=True,
            )

    if result.summary:
        st.subheader("🧠 Memory Summary")
        st.markdown(result.summary)
        st.caption(
            "This summary has been retained in Hindsight and will influence "
            "future staffing recommendations for similar projects."
        )

