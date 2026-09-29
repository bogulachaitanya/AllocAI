"""AllocAI Public Landing Page.

This is the first screen every visitor sees.
Shows hero section, features, how it works, and CTAs to sign in / sign up.
No database data is loaded here — purely marketing/informational content.
"""

from __future__ import annotations

import streamlit as st


def render() -> None:
    # ── Hero Section ──────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center;padding:3.5rem 1rem 2rem 1rem;">
            <div style="display:inline-block;padding:5px 16px;border-radius:20px;
                        background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.3);
                        font-size:0.78rem;font-weight:600;letter-spacing:0.06em;
                        color:#A5B4FC;margin-bottom:1.5rem;text-transform:uppercase;">
                AI Project Staffing Intelligence
            </div>
            <div style="font-size:clamp(2.2rem,5vw,3.5rem);font-weight:900;
                        letter-spacing:-0.03em;line-height:1.1;margin-bottom:1rem;
                        background:linear-gradient(135deg,#E2E8F0 0%,#A5B4FC 50%,#818CF8 100%);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                        background-clip:text;">
                Match the right people.<br>Learn from every project.
            </div>
            <div style="font-size:1.1rem;color:#94A3B8;max-width:580px;margin:0 auto 2rem auto;
                        line-height:1.7;">
                AllocAI builds project teams using real employee skills, previous project
                experience, availability, and organisational memory — so your staffing
                decisions get smarter over time.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_cta1, col_cta2, col_cta3 = st.columns([1, 0.4, 0.4])
    with col_cta2:
        if st.button("🚀 Get Started", type="primary", key="hero_get_started", use_container_width=True):
            st.session_state["selected_page"] = "signup"
            st.rerun()
    with col_cta3:
        if st.button("Sign In", type="secondary", key="hero_sign_in", use_container_width=True):
            st.session_state["selected_page"] = "login"
            st.rerun()

    st.divider()

    # ── Intelligence Pipeline Visual ──────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center;margin:1.5rem 0 2.5rem 0;">
            <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.1em;color:#6366F1;margin-bottom:1rem;">
                How AllocAI Works
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    pipeline_steps = [
        ("01", "Project Requirements", "Describe your project in plain language — technologies, domain, team size, timeline."),
        ("02", "Employee Intelligence", "AllocAI analyses your full employee roster — skills, experience, seniority, certifications."),
        ("03", "Previous Experience", "Past project assignments and performance data are factored into every recommendation."),
        ("04", "Organisational Memory", "Hindsight surfaces lessons from previous outcomes — patterns, risks, and what worked."),
        ("05", "Project Fit Score", "Each candidate receives a deterministic fit score across 8 weighted dimensions."),
        ("06", "Recommended Team", "The optimal complementary team is composed and explained with full evidence."),
    ]

    cols = st.columns(3)
    for i, (num, title, desc) in enumerate(pipeline_steps):
        with cols[i % 3]:
            st.markdown(
                f"""<div class="alloc-glass" style="margin:6px 0;min-height:160px;">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                        <div class="alloc-step-num">{num}</div>
                        <div style="font-weight:700;font-size:0.92rem;color:#E2E8F0;">{title}</div>
                    </div>
                    <div style="font-size:0.82rem;color:#64748B;line-height:1.6;">{desc}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Why AllocAI ───────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center;margin:1.5rem 0;">
            <div style="font-size:1.6rem;font-weight:800;color:#F1F5F9;margin-bottom:0.5rem;">
                Why AllocAI?
            </div>
            <div style="color:#64748B;font-size:0.95rem;">
                Evidence-based staffing — not guesswork.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    features = [
        (
            "🧠",
            "Skills Intelligence",
            "accent-indigo",
            "Understand what your people can actually do today — technical skills, proficiency levels, certifications, and domain expertise — all sourced from your employee data.",
        ),
        (
            "📂",
            "Project Experience",
            "accent-blue",
            "Every previous project assignment is used as signal. AllocAI knows who has worked in fintech, who has delivered on tight deadlines, and who pairs well with whom.",
        ),
        (
            "🧬",
            "Organisational Memory",
            "accent-violet",
            "Hindsight captures lessons from completed projects — client feedback, manager observations, team patterns, and risks — and applies them to future staffing decisions.",
        ),
    ]

    cols2 = st.columns(3)
    for col, (icon, title, color, desc) in zip(cols2, features):
        color_map = {
            "accent-indigo": "#6366F1",
            "accent-blue": "#3B82F6",
            "accent-violet": "#7C3AED",
        }
        hex_color = color_map[color]
        with col:
            st.markdown(
                f"""<div class="alloc-glass" style="height:100%;padding:1.75rem 1.5rem;">
                    <div style="width:44px;height:44px;border-radius:10px;
                                background:rgba(99,102,241,0.12);
                                border:1px solid rgba(99,102,241,0.2);
                                display:flex;align-items:center;justify-content:center;
                                font-size:1.4rem;margin-bottom:1rem;">
                        {icon}
                    </div>
                    <div style="font-size:1rem;font-weight:700;color:#E2E8F0;
                                margin-bottom:0.5rem;">{title}</div>
                    <div style="font-size:0.83rem;color:#64748B;line-height:1.65;">{desc}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Trust / Evidence section ───────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center;padding:1.5rem 0 1rem 0;">
            <div style="max-width:640px;margin:0 auto;">
                <div style="font-size:1.5rem;font-weight:800;color:#F1F5F9;margin-bottom:0.75rem;">
                    Evidence-based staffing
                </div>
                <div style="color:#64748B;font-size:0.95rem;line-height:1.7;">
                    Every recommendation AllocAI produces is backed by real employee data,
                    historical project assignments, and organisational memory — not guesswork.
                    You can see exactly why each person was selected.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_trust1, col_trust2, col_trust3 = st.columns(3)
    trust_items = [
        ("Employee Data", "Skills, experience, availability, performance — all from your HR records."),
        ("Project History", "Previous assignments, outcomes, and client feedback from your completed projects."),
        ("Organisational Learning", "Lessons learned from past staffing decisions, stored in Hindsight memory."),
    ]
    for col, (title, desc) in zip([col_trust1, col_trust2, col_trust3], trust_items):
        with col:
            st.markdown(
                f"""<div style="text-align:center;padding:1.25rem 0.75rem;">
                    <div style="width:8px;height:8px;border-radius:50%;
                                background:linear-gradient(135deg,#7C3AED,#3B82F6);
                                margin:0 auto 0.75rem auto;"></div>
                    <div style="font-weight:700;color:#E2E8F0;font-size:0.9rem;margin-bottom:0.5rem;">{title}</div>
                    <div style="color:#64748B;font-size:0.8rem;line-height:1.6;">{desc}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Footer CTA ────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center;padding:2rem 0 1rem 0;">
            <div style="font-size:1.4rem;font-weight:800;color:#F1F5F9;margin-bottom:0.5rem;">
                Ready to staff smarter?
            </div>
            <div style="color:#64748B;font-size:0.9rem;margin-bottom:1.5rem;">
                Create your AllocAI workspace in under a minute.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_f1, col_f2, col_f3 = st.columns([1, 0.4, 0.4])
    with col_f2:
        if st.button("🚀 Create Account", type="primary", key="footer_cta", use_container_width=True):
            st.session_state["selected_page"] = "signup"
            st.rerun()
    with col_f3:
        if st.button("Sign In", key="footer_signin", use_container_width=True):
            st.session_state["selected_page"] = "login"
            st.rerun()

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="border-top:1px solid rgba(55,65,81,0.5);margin-top:3rem;
                    padding:2rem 0 1rem 0;text-align:center;">
            <div style="font-size:1rem;font-weight:700;background:linear-gradient(135deg,#6366F1,#3B82F6);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                        background-clip:text;margin-bottom:0.25rem;">
                AllocAI
            </div>
            <div style="font-size:0.78rem;color:#4B5563;margin-bottom:0.75rem;">
                AI Project Staffing Intelligence
            </div>
            <div style="font-size:0.72rem;color:#374151;">
                © 2026 AllocAI · Privacy · Terms
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
