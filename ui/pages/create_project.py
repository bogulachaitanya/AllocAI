"""Create Project page — accepts raw requirement, extracts structure, runs recommendation.

Implements the Hindsight skill's Before/After demo requirement:
  1. Run recommendation WITHOUT Hindsight (pure database + scoring).
  2. Run recommendation WITH Hindsight (adds lessons, patterns, risks from memory).
  3. Show the difference side-by-side.

The Mock Mode banner is displayed whenever HINDSIGHT_ADAPTER=local.
"""

from __future__ import annotations

import json

import streamlit as st

from db.session import get_db
from models.project import Project
from schemas.matching import ProjectFitWeights
from schemas.project import StructuredRequirements
from services.project_analyzer import ProjectAnalyzer
from services.recommendation_engine import RecommendationEngine
from ui.components.hindsight_banner import (
    render_before_after_comparison,
    render_hindsight_mode_banner,
)
from ui.components.team_card import render_recommended_team


def render() -> None:
    st.title("📋 Create Project & Get Recommendations")
    st.caption("Describe your project requirements and let AllocAI find the right team.")

    # ── Hindsight mode banner (always visible) ────────────────────────────────
    render_hindsight_mode_banner()

    st.divider()

    # ── Current Staffing Request (from session) ──────────────────────────────
    active_project_id = st.session_state.get("current_project_id")
    if active_project_id:
        with get_db() as session:
            active_project = session.get(Project, active_project_id)
            if active_project:
                st.info(
                    f"📁 **Current Request:** {active_project.title} (ID: {active_project.id})"
                )
                if st.button("Start New Project"):
                    del st.session_state["current_project_id"]
                    st.session_state.pop("last_recommended_team", None)
                    st.session_state.pop("last_recommended_team_without_hindsight", None)
                    st.rerun()

    with st.form("project_form"):
        st.subheader("Project Details")

        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Project Title *", placeholder="e.g. Fraud Detection Platform")
            client = st.text_input("Client", placeholder="e.g. Meridian Financial")
        with col2:
            domain = st.selectbox(
                "Domain",
                [
                    "general",
                    "fintech",
                    "healthcare",
                    "e-commerce",
                    "cloud",
                    "ml",
                    "cybersecurity",
                    "logistics",
                    "saas",
                ],
            )
            duration = st.number_input("Duration (weeks)", min_value=1, max_value=104, value=12)

        col3, col4 = st.columns(2)
        with col3:
            team_size = st.number_input("Team Size", min_value=1, max_value=20, value=4)
        with col4:
            st.empty()  # keep layout balanced

        st.subheader("Project Requirements")
        raw_requirement = st.text_area(
            "Describe the project requirements *",
            height=200,
            placeholder=(
                "e.g. We need to build a real-time fraud detection system for a major bank. "
                "The system must process 10,000 transactions per second, detect anomalies using ML, "
                "and integrate with our existing payment infrastructure. "
                "We need senior Python engineers with ML experience and Kafka expertise."
            ),
        )

        st.subheader("⚙️ Options")
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            show_before_after = st.checkbox(
                "🔬 Show Before / After Hindsight comparison",
                value=True,
                help=(
                    "Run the pipeline twice — once without Hindsight (baseline) and once with "
                    "Hindsight — and show the difference side-by-side."
                ),
            )
        with col_opt2:
            show_weights = st.checkbox("⚙️ Configure score weights", value=False)

        if show_weights:
            st.subheader("Score Weights")
            st.caption("Weights must sum to 1.0. Default weights are pre-filled.")
            col_w1, col_w2, col_w3, col_w4 = st.columns(4)
            w_skill = col_w1.slider("Skill Match", 0.0, 1.0, 0.30, 0.05)
            w_exp = col_w2.slider("Experience", 0.0, 1.0, 0.15, 0.05)
            w_proj = col_w3.slider("Project Exp", 0.0, 1.0, 0.15, 0.05)
            w_domain = col_w4.slider("Domain", 0.0, 1.0, 0.10, 0.05)
            col_w5, col_w6, col_w7, col_w8 = st.columns(4)
            w_perf = col_w5.slider("Performance", 0.0, 1.0, 0.10, 0.05)
            w_avail = col_w6.slider("Availability", 0.0, 1.0, 0.10, 0.05)
            w_cert = col_w7.slider("Certifications", 0.0, 1.0, 0.05, 0.05)
            w_collab = col_w8.slider("Collaboration", 0.0, 1.0, 0.05, 0.05)
        else:
            w_skill, w_exp, w_proj, w_domain = 0.30, 0.15, 0.15, 0.10
            w_perf, w_avail, w_cert, w_collab = 0.10, 0.10, 0.05, 0.05

        # We separate Create and Analyze actions
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            create_submitted = st.form_submit_button("💾 Create Project", type="primary")
        with col_btn2:
            analyze_submitted = st.form_submit_button(
                "🔍 Analyze & Recommend Team", disabled="current_project_id" not in st.session_state
            )

    # ── Action: Create Project ────────────────────────────────────────────────
    if create_submitted:
        if not title.strip() or not raw_requirement.strip():
            st.error("Project title and requirements are required.")
            return

        with get_db() as session:
            # Prevent duplicate creation if we already created it (simple title check or session state)
            existing = (
                session.query(Project)
                .filter(Project.title == title.strip(), Project.status == "draft")
                .first()
            )
            if existing and st.session_state.get("current_project_id") == existing.id:
                st.info(f"Project '{title}' already exists as Draft (ID: {existing.id}).")
                project_id = existing.id
            else:
                project = Project(
                    title=title.strip(),
                    description=raw_requirement[:500],
                    client=client.strip(),
                    domain=domain,
                    status="draft",
                    team_size_min=team_size,
                    team_size_max=team_size,
                    duration_weeks=duration,
                    raw_requirement=raw_requirement[:8000],
                    structured_requirements="",  # Will be filled during analysis
                )
                session.add(project)
                session.commit()
                project_id = project.id
                st.session_state["current_project_id"] = project_id

        st.success("✅ Project created successfully!")
        st.info(f"**Project ID:** {project_id} | **Name:** {title} | **Status:** Draft")
        st.rerun()  # Rerun to enable the Analyze button

    # ── Action: Analyze & Recommend Team ──────────────────────────────────────
    if analyze_submitted:
        project_id = st.session_state.get("current_project_id")
        if not project_id:
            st.error("Please create a project first.")
            return

        weights = ProjectFitWeights(
            skill_match=w_skill,
            experience_match=w_exp,
            relevant_project_experience=w_proj,
            domain_expertise=w_domain,
            past_project_performance=w_perf,
            availability=w_avail,
            certification_relevance=w_cert,
            collaboration_relevance=w_collab,
        )

        with get_db() as session:
            project = session.get(Project, project_id)
            if not project:
                st.error("Project not found in database.")
                return

            # ── Step 1: Extract structured requirements ───────────────────────────────
            with st.spinner("🔍 Extracting structured requirements…"):
                analyzer = ProjectAnalyzer()
                extracted: StructuredRequirements = analyzer.analyze(project.raw_requirement)

                # Prioritize explicit UI input over LLM extracted output
                update_dict = {
                    "team_size_min": project.team_size_min,
                    "team_size_max": project.team_size_max,
                }
                # Override form domain if LLM extracted "general"
                if extracted.domain == "general" and project.domain != "general":
                    update_dict["domain"] = project.domain

                extracted = extracted.model_copy(update=update_dict)

                # Update project with extracted requirements
                project.structured_requirements = json.dumps(extracted.model_dump())
                session.commit()

            st.success("✅ Requirements extracted")
            with st.expander("📋 Extracted Requirements (LLM Inference)"):
                st.info(
                    "⚠️ The following was extracted by LLM — verify before relying on it as fact."
                )
                st.json(extracted.model_dump())

            # ── Step 2: Run recommendations ───────────────────────────────────────────
            engine = RecommendationEngine(session=session, weights=weights)

            if show_before_after:
                with st.spinner("⚙️ Step 1/2 — Recommendation WITHOUT Hindsight…"):
                    rec_without = engine.recommend_without_hindsight(
                        requirements=extracted,
                        project=None,
                    )

                with st.spinner("🧠 Step 2/2 — Recommendation WITH Hindsight…"):
                    rec_with = engine.recommend(requirements=extracted, project=project)

                project.recommendation_explanation = rec_with.explanation
                st.session_state["last_recommended_team"] = rec_with
                st.session_state["last_recommended_team_without_hindsight"] = rec_without
                session.commit()

            else:
                with st.spinner(
                    "👥 Running pipeline (Filter → Score → Hindsight → RAG → Compose)…"
                ):
                    rec_with = engine.recommend(requirements=extracted, project=project)

                project.recommendation_explanation = rec_with.explanation
                st.session_state["last_recommended_team"] = rec_with
                st.session_state.pop("last_recommended_team_without_hindsight", None)
                rec_without = None
                session.commit()

        st.success(f"✅ Team recommended for Project {project_id}!")
        st.divider()

        if show_before_after:
            render_before_after_comparison(rec_without, rec_with)
            st.divider()
            st.markdown("### 🧠 Final Recommendation (With Hindsight)")
            render_recommended_team(rec_with)
        else:
            render_recommended_team(rec_with)
