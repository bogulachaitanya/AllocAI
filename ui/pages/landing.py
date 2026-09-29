"""AllocAI Public Landing Page — High-Performance 3D Animated Hero.

This landing page features an advanced CSS 3D animated hero section,
floating glassmorphism cards, and an interactive intelligence pipeline visual.
"""

from __future__ import annotations

import streamlit as st


def render() -> None:
    # ── Advanced 3D CSS injected for the Landing Page ─────────────────────────
    import textwrap
    st.markdown(
        textwrap.dedent("""
        <style>
        /* 1. Reset container padding for full width impact */
        .main .block-container {
            max-width: 100% !important;
            padding: 0 !important;
        }
        /* 2. Hero 3D Wrapper */
        .hero-3d-wrapper {
            position: relative;
            width: 100%;
            min-height: 85vh;
            display: flex;
            align-items: center;
            justify-content: center;
            perspective: 1200px;
            overflow: hidden;
            background: #040810;
        }
        /* 3. Moving 3D Grid Background */
        .hero-3d-grid {
            position: absolute;
            width: 250%;
            height: 150%;
            bottom: -30%;
            left: -75%;
            background-image: 
                linear-gradient(rgba(99, 102, 241, 0.25) 1px, transparent 1px),
                linear-gradient(90deg, rgba(99, 102, 241, 0.25) 1px, transparent 1px);
            background-size: 60px 60px;
            transform-origin: center top;
            transform: rotateX(75deg) translateY(0);
            animation: grid-move 15s linear infinite;
            z-index: 1;
        }
        @keyframes grid-move {
            0% { transform: rotateX(75deg) translateY(0); }
            100% { transform: rotateX(75deg) translateY(60px); }
        }
        /* 4. Glowing Orbs */
        .orb {
            position: absolute;
            border-radius: 50%;
            filter: blur(80px);
            z-index: 2;
            opacity: 0.6;
            animation: float-orb 10s ease-in-out infinite alternate;
        }
        .orb-1 { width: 400px; height: 400px; background: rgba(124, 58, 237, 0.4); top: 10%; left: 10%; animation-delay: 0s; }
        .orb-2 { width: 500px; height: 500px; background: rgba(59, 130, 246, 0.3); bottom: 10%; right: 5%; animation-delay: -5s; }
        .orb-3 { width: 300px; height: 300px; background: rgba(34, 211, 238, 0.3); top: 40%; left: 45%; animation-delay: -2s; }
        @keyframes float-orb {
            0% { transform: translate(0, 0) scale(1); }
            100% { transform: translate(50px, -50px) scale(1.1); }
        }
        /* 5. Floating 3D Glass Cards */
        .floating-card {
            position: absolute;
            z-index: 3;
            background: rgba(15, 23, 42, 0.65);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 16px;
            padding: 1.25rem;
            color: #E2E8F0;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5), inset 0 0 20px rgba(99,102,241,0.1);
            animation: float-card 8s ease-in-out infinite;
            transform-style: preserve-3d;
            width: 240px;
        }
        .floating-card-title { font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; color: #818CF8; margin-bottom: 8px; }
        .floating-card-value { font-size: 1.8rem; font-weight: 900; background: linear-gradient(135deg, #A5B4FC, #fff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .floating-card-sub { font-size: 0.8rem; color: #94A3B8; margin-top: 4px; }
        .fc-1 { top: 18%; left: 12%; animation-delay: 0s; transform: rotateY(15deg) rotateX(5deg); }
        .fc-2 { bottom: 25%; right: 10%; animation-delay: -2s; transform: rotateY(-15deg) rotateX(-5deg); }
        .fc-3 { top: 60%; left: 8%; animation-delay: -4s; transform: rotateY(20deg) rotateX(10deg); width: 200px; }
        .fc-4 { top: 12%; right: 15%; animation-delay: -6s; transform: rotateY(-10deg) rotateX(15deg); }
        @keyframes float-card {
            0%, 100% { transform: translateY(0) scale(1) translateZ(0); }
            50% { transform: translateY(-25px) scale(1.02) translateZ(30px); }
        }
        /* 6. Central Hero Content */
        .hero-center-content {
            position: relative;
            z-index: 10;
            text-align: center;
            max-width: 800px;
            padding: 4rem 3rem;
            background: rgba(11, 16, 32, 0.4);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 30px;
            backdrop-filter: blur(20px);
            box-shadow: 0 30px 60px rgba(0,0,0,0.6), inset 0 0 40px rgba(99,102,241,0.05);
            animation: fade-up 1s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            opacity: 0;
            transform: translateY(40px);
        }
        @keyframes fade-up {
            to { opacity: 1; transform: translateY(0); }
        }
        .hero-badge {
            display: inline-flex; align-items: center; gap: 8px;
            padding: 6px 18px; border-radius: 30px;
            background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.3);
            font-size: 0.8rem; font-weight: 700; letter-spacing: 0.1em;
            color: #A5B4FC; text-transform: uppercase; margin-bottom: 2rem;
            box-shadow: 0 0 20px rgba(99,102,241,0.2);
        }
        .hero-title {
            font-size: clamp(3rem, 6vw, 5rem); font-weight: 900;
            letter-spacing: -0.04em; line-height: 1.05; margin-bottom: 1.5rem;
            background: linear-gradient(180deg, #FFFFFF 0%, #A5B4FC 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 10px 30px rgba(99,102,241,0.2);
        }
        .hero-desc {
            font-size: 1.2rem; color: #94A3B8; line-height: 1.7;
            max-width: 600px; margin: 0 auto 2.5rem auto; font-weight: 400;
        }
        /* 7. Section Container for Rest of Page */
        .page-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 4rem 2rem;
            position: relative;
            z-index: 10;
        }
        </style>

        <!-- HERO HTML -->
        <div class="hero-3d-wrapper">
            <!-- 3D Elements -->
            <div class="hero-3d-grid"></div>
            <div class="orb orb-1"></div>
            <div class="orb orb-2"></div>
            <div class="orb orb-3"></div>
            <!-- Floating Data Cards -->
            <div class="floating-card fc-1" style="animation-delay: 0s;">
                <div class="floating-card-title">Employee Intelligence</div>
                <div style="display:flex;gap:4px;margin-bottom:6px;flex-wrap:wrap;">
                    <span style="background:rgba(99,102,241,0.2);padding:2px 6px;border-radius:4px;font-size:0.65rem;">Python</span>
                    <span style="background:rgba(99,102,241,0.2);padding:2px 6px;border-radius:4px;font-size:0.65rem;">PostgreSQL</span>
                </div>
                <div class="floating-card-sub">Skills mapped dynamically</div>
            </div>
            <div class="floating-card fc-2" style="animation-delay: -2s;">
                <div class="floating-card-title">Organisational Memory</div>
                <div style="font-size:1.2rem;font-weight:700;color:#A78BFA;margin-top:5px;line-height:1.2;">Lessons Recalled</div>
                <div class="floating-card-sub">Applying past feedback</div>
            </div>
            <div class="floating-card fc-3" style="animation-delay: -4s;">
                <div class="floating-card-title">Team Composition</div>
                <div style="font-size:1.2rem;font-weight:700;color:#34D399;margin-top:5px;line-height:1.2;">Optimal Match</div>
                <div class="floating-card-sub">Complementary skills aligned</div>
            </div>
            <div class="floating-card fc-4" style="animation-delay: -6s;">
                <div class="floating-card-title">Project Fit Score</div>
                <div style="display:flex;align-items:center;gap:6px;margin-top:8px;">
                    <div style="height:6px;width:100%;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden;">
                        <div style="height:100%;width:85%;background:linear-gradient(90deg,#6366F1,#3B82F6);"></div>
                    </div>
                </div>
                <div class="floating-card-sub">Multi-dimensional analysis</div>
            </div>
            <!-- Center Content -->
            <div class="hero-center-content">
                <div class="hero-badge">
                    <span style="font-size:1.2rem;">⚡</span> Next-Gen Staffing Intelligence
                </div>
                <div class="hero-title">
                    Match the right people.<br>Learn from every project.
                </div>
                <div class="hero-desc">
                    AllocAI builds project teams using real employee skills, previous project 
                    experience, and organisational memory — creating an intelligent feedback loop 
                    that makes your company smarter every day.
                </div>
                <div id="cta-container"></div>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    # ── Streamlit CTAs (Injected below hero via CSS positioning trick) ─────────
    # We place the buttons here, but because of the full-width hero, we use a container
    st.markdown("<div style='display:flex;justify-content:center;gap:20px;margin-top:-7rem;position:relative;z-index:20;margin-bottom:6rem;'>", unsafe_allow_html=True)
    
    col_empty1, col_cta1, col_cta2, col_empty2 = st.columns([1, 0.4, 0.4, 1])
    with col_cta1:
        if st.button("🚀 Get Started Free", type="primary", key="hero_get_started", use_container_width=True):
            st.session_state["selected_page"] = "signup"
            st.rerun()
    with col_cta2:
        if st.button("Sign In to Workspace", type="secondary", key="hero_sign_in", use_container_width=True):
            st.session_state["selected_page"] = "login"
            st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Standard Page Content Container ───────────────────────────────────────
    st.markdown("<div class='page-container'>", unsafe_allow_html=True)

    # ── Intelligence Pipeline Visual ──────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center;margin-bottom:3.5rem;">
            <div style="font-size:0.85rem;font-weight:800;text-transform:uppercase;
                        letter-spacing:0.15em;color:#6366F1;margin-bottom:1rem;">
                The AllocAI Pipeline
            </div>
            <div style="font-size:2.2rem;font-weight:800;color:#F1F5F9;letter-spacing:-0.02em;">
                How the intelligence engine works
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    pipeline_steps = [
        ("01", "Project Requirements", "Natural language analysis extracts core skills, domain, and constraints.", "📝"),
        ("02", "Employee Intelligence", "Scans your entire workforce for matching skills, seniority, and availability.", "🔍"),
        ("03", "Previous Experience", "Historical project performance data is weighed heavily in the scoring.", "📂"),
        ("04", "Organisational Memory", "Hindsight recalls qualitative lessons, risks, and feedback from past work.", "🧠"),
        ("05", "Project Fit Score", "A deterministic fit score is generated across 8 dimensions for every candidate.", "⚡"),
        ("06", "Recommended Team", "An optimal, gap-free team is composed with transparent AI explanations.", "👥"),
    ]

    cols = st.columns(3)
    for i, (num, title, desc, icon) in enumerate(pipeline_steps):
        with cols[i % 3]:
            st.markdown(
                f"""<div class="alloc-glass" style="margin:10px 0;min-height:200px;
                            position:relative;overflow:hidden;transition:all 0.3s ease;">
                    <div style="position:absolute;top:-20px;right:-20px;font-size:6rem;opacity:0.04;
                                transform:rotate(15deg);">{icon}</div>
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:15px;">
                        <div class="alloc-step-num" style="width:32px;height:32px;font-size:0.9rem;">{num}</div>
                        <div style="font-weight:800;font-size:1.05rem;color:#E2E8F0;">{title}</div>
                    </div>
                    <div style="font-size:0.9rem;color:#94A3B8;line-height:1.7;">{desc}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin: 6rem 0;'></div>", unsafe_allow_html=True)

    # ── Why AllocAI ───────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center;margin-bottom:3.5rem;">
            <div style="font-size:2.2rem;font-weight:800;color:#F1F5F9;margin-bottom:0.5rem;letter-spacing:-0.02em;">
                Why choose AllocAI?
            </div>
            <div style="color:#64748B;font-size:1.1rem;">
                Evidence-based staffing. No guesswork. No bias.
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
            "Understand exactly what your people can do today — technical skills, proficiencies, and domain expertise — dynamically sourced from HR data.",
        ),
        (
            "📂",
            "Project Experience",
            "accent-blue",
            "Every previous project assignment is used as signal. AllocAI knows who delivers on tight deadlines and who pairs perfectly together.",
        ),
        (
            "🧬",
            "Organisational Memory",
            "accent-violet",
            "Capture lessons from completed projects. Hindsight turns client feedback and manager observations into actionable data for the next project.",
        ),
    ]

    cols2 = st.columns(3)
    for col, (icon, title, color, desc) in zip(cols2, features):
        with col:
            st.markdown(
                f"""<div class="alloc-glass" style="height:100%;padding:2rem;">
                    <div style="width:54px;height:54px;border-radius:14px;
                                background:linear-gradient(135deg, rgba(99,102,241,0.2), rgba(59,130,246,0.1));
                                border:1px solid rgba(99,102,241,0.3);
                                display:flex;align-items:center;justify-content:center;
                                font-size:1.6rem;margin-bottom:1.5rem;
                                box-shadow: 0 10px 20px rgba(0,0,0,0.2);">
                        {icon}
                    </div>
                    <div style="font-size:1.2rem;font-weight:800;color:#F1F5F9;
                                margin-bottom:0.75rem;">{title}</div>
                    <div style="font-size:0.95rem;color:#94A3B8;line-height:1.7;">{desc}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin: 6rem 0;'></div>", unsafe_allow_html=True)

    # ── Footer CTA ────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center;padding:4rem 2rem;background:linear-gradient(180deg, transparent, rgba(99,102,241,0.05));
                    border-radius:30px;border:1px solid rgba(99,102,241,0.1);">
            <div style="font-size:2.5rem;font-weight:900;color:#F1F5F9;margin-bottom:1rem;letter-spacing:-0.03em;">
                Ready to staff smarter?
            </div>
            <div style="color:#94A3B8;font-size:1.1rem;margin-bottom:2.5rem;max-width:500px;margin-left:auto;margin-right:auto;">
                Join the platform that turns everyday project assignments into lasting organisational intelligence.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Re-use buttons layout for bottom CTA
    st.markdown("<div style='display:flex;justify-content:center;gap:20px;margin-top:-3rem;position:relative;z-index:20;'>", unsafe_allow_html=True)
    col_fb1, col_fb2, col_fb3, col_fb4 = st.columns([1, 0.4, 0.4, 1])
    with col_fb2:
        if st.button("🚀 Create Free Account", type="primary", key="footer_cta", use_container_width=True):
            st.session_state["selected_page"] = "signup"
            st.rerun()
    with col_fb3:
        if st.button("Sign In", key="footer_signin", use_container_width=True):
            st.session_state["selected_page"] = "login"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="border-top:1px solid rgba(55,65,81,0.4);margin-top:5rem;
                    padding:2.5rem 0 1rem 0;display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="font-size:1.2rem;font-weight:900;background:linear-gradient(135deg,#6366F1,#3B82F6);
                            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                            background-clip:text;margin-bottom:0.25rem;">
                    AllocAI
                </div>
                <div style="font-size:0.85rem;color:#64748B;">
                    AI Project Staffing Intelligence
                </div>
            </div>
            <div style="font-size:0.8rem;color:#4B5563;text-align:right;">
                © 2026 AllocAI Inc.<br>
                Privacy Policy · Terms of Service
            </div>
        </div>
        </div> <!-- End page-container -->
        """,
        unsafe_allow_html=True,
    )
