"""Create Staffing Request page — HR-friendly 4-step staffing recommendation flow.

Flow:
  Step 1 — Project Information (title, client, domain, duration)
  Step 2 — Project Requirements (free-text description)
  Step 3 — Team Size
  Step 4 — Analyze & Recommend
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
from ui.components.hindsight_banner import render_hindsight_mode_banner
from ui.components.team_card import render_recommended_team


def render() -> None:
    st.title("📋 Create Staffing Request")
    st.caption("Describe your project and let AllocAI find the right team.")

    # ── Hindsight mode banner ─────────────────────────────────────────────────
    render_hindsight_mode_banner()
    st.divider()

    # ── Active staffing request indicator ────────────────────────────────────
    active_project_id = st.session_state.get("current_project_id")
    if active_project_id:
        with get_db() as session:
            active_project = session.get(Project, active_project_id)
            if active_project:
                col_info, col_btn = st.columns([5, 1])
                with col_info:
                    st.info(
                        f"📁 **Active Request:** {active_project.title}  "
                        f"(ID: {active_project.id})"
                    )
                with col_btn:
                    if st.button("🔄 New Request", type="secondary"):
                        del st.session_state["current_project_id"]
                        st.session_state.pop("last_recommended_team", None)
                        st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 1 — Project Information
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(
        "<div style='font-size:0.8rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.08em;color:#58a6ff;margin-bottom:4px;'>Step 1 — Project Information"
        "</div>",
        unsafe_allow_html=True,
    )

    with st.form("staffing_request_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input(
                "Project Title *",
                placeholder="e.g. AI-Powered Banking Assistant",
            )
            client = st.text_input(
                "Client / Department",
                placeholder="e.g. Meridian Financial",
            )
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
            duration = st.number_input(
                "Estimated Duration (weeks)",
                min_value=1,
                max_value=104,
                value=12,
            )

        st.divider()

        # ══════════════════════════════════════════════════════════════════════
        # STEP 2 — Project Requirements
        # ══════════════════════════════════════════════════════════════════════
        st.markdown(
            "<div style='font-size:0.8rem;font-weight:700;text-transform:uppercase;"
            "letter-spacing:0.08em;color:#58a6ff;margin-bottom:4px;'>Step 2 — Project Requirements"
            "</div>",
            unsafe_allow_html=True,
        )
        raw_requirement = st.text_area(
            "Describe the project requirements *",
            height=180,
            placeholder=(
                "e.g. We need to build an AI-powered banking assistant for retail customers. "
                "The system should use Python, NLP, FastAPI, SQL and AWS. "
                "Candidates should have relevant banking or FinTech experience. "
                "We need a strong ML engineer and a backend developer."
            ),
        )

        st.divider()

        # ══════════════════════════════════════════════════════════════════════
        # STEP 3 — Team Size
        # ══════════════════════════════════════════════════════════════════════
        st.markdown(
            "<div style='font-size:0.8rem;font-weight:700;text-transform:uppercase;"
            "letter-spacing:0.08em;color:#58a6ff;margin-bottom:4px;'>Step 3 — Team Size"
            "</div>",
            unsafe_allow_html=True,
        )
        col_ts, col_adv = st.columns([1, 2])
        with col_ts:
            team_size = st.number_input(
                "Requested Team Size *",
                min_value=1,
                max_value=20,
                value=4,
                help="The recommendation will return exactly this many people.",
            )
        with col_adv:
            show_weights = st.checkbox(
                "⚙️ Advanced: Configure scoring weights",
                value=False,
                help="Adjust the relative importance of each scoring criterion.",
            )

        if show_weights:
            st.markdown("**Scoring Weights** *(must sum ≈ 1.0)*")
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

        st.divider()

        # ══════════════════════════════════════════════════════════════════════
        # STEP 4 — Submit
        # ══════════════════════════════════════════════════════════════════════
        st.markdown(
            "<div style='font-size:0.8rem;font-weight:700;text-transform:uppercase;"
            "letter-spacing:0.08em;color:#58a6ff;margin-bottom:4px;'>Step 4 — Analyze & Recommend"
            "</div>",
            unsafe_allow_html=True,
        )
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            create_submitted = st.form_submit_button("💾 Save Staffing Request", type="secondary")
        with col_btn2:
            analyze_submitted = st.form_submit_button(
                "🚀 Analyze & Find Team",
                type="primary",
                disabled="current_project_id" not in st.session_state,
            )

    # ── Action: Create Staffing Request ──────────────────────────────────────
    if create_submitted:
        if not title.strip() or not raw_requirement.strip():
            st.error("Project title and requirements are required.")
            return

        with get_db() as session:
            existing = (
                session.query(Project)
                .filter(Project.title == title.strip(), Project.status == "draft")
                .first()
            )
            if existing and st.session_state.get("current_project_id") == existing.id:
                st.info(f"Request '{title}' already exists (ID: {existing.id}).")
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
                    structured_requirements="",
                )
                session.add(project)
                session.commit()
                project_id = project.id
                st.session_state["current_project_id"] = project_id

        st.success(
            f"✅ Staffing request saved — **{title}** (ID: {project_id})  \n"
            "Click **Analyze & Find Team** to get recommendations."
        )
        st.rerun()

    # ── Action: Analyze & Recommend ───────────────────────────────────────────
    if analyze_submitted:
        project_id = st.session_state.get("current_project_id")
        if not project_id:
            st.error("Please save a staffing request first.")
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
                st.error("Staffing request not found in database.")
                return

            # ── Extract structured requirements ───────────────────────────
            with st.spinner("🔍 Analyzing project requirements…"):
                try:
                    analyzer = ProjectAnalyzer()
                    extracted: StructuredRequirements = analyzer.analyze(project.raw_requirement)

                    # Honour user-selected team size and domain over LLM extraction
                    update_dict: dict = {
                        "team_size_min": project.team_size_min,
                        "team_size_max": project.team_size_max,
                    }
                    if extracted.domain == "general" and project.domain != "general":
                        update_dict["domain"] = project.domain

                    extracted = extracted.model_copy(update=update_dict)
                    project.structured_requirements = json.dumps(extracted.model_dump())
                    session.commit()

                except Exception as exc:
                    st.warning(
                        f"AI requirement extraction is temporarily unavailable ({exc}). "
                        "Using project description directly."
                    )
                    extracted = StructuredRequirements(
                        title=project.title or "Untitled",
                        domain=project.domain or "general",
                        required_skills=[],
                        team_size_min=project.team_size_min or 1,
                        team_size_max=project.team_size_max or 4,
                    )

            with st.expander("📋 Extracted Requirements (AI Analysis)", expanded=False):
                st.info(
                    "ℹ️ Requirements extracted by AI — verify before relying on as fact.",
                    icon="ℹ️",
                )
                st.json(extracted.model_dump())

            # ── Run recommendation pipeline ───────────────────────────────
            with st.spinner(
                "👥 Finding candidates → Recalling organizational memory → Composing team…"
            ):
                try:
                    engine = RecommendationEngine(session=session, weights=weights)
                    rec = engine.recommend(requirements=extracted, project=project)
                    project.recommendation_explanation = rec.explanation
                    st.session_state["last_recommended_team"] = rec
                    session.commit()
                except Exception as exc:
                    st.error(
                        f"Recommendation pipeline encountered an error: {exc}  \n"
                        "Please check your project requirements and try again."
                    )
                    return

        # ── Display recommendation ────────────────────────────────────────
        st.success(
            f"✅ Recommendation complete — team of "
            f"**{len(rec.recommended_team)}** found for *{rec.project_title}*"
        )
        st.divider()
        render_recommended_team(rec)

