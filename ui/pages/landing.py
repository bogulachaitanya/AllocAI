"""AllocAI Landing Page — Immersive 3D animated experience.

Uses st.components.v1.html() to render a full-screen Three.js particle network
with glassmorphism cards, animated pipeline, and premium micro-interactions.

The entire landing page is a single HTML component for maximum visual control.
Navigation buttons communicate back to Streamlit via query params + session state.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


def render() -> None:
    # Hide Streamlit chrome for immersive landing
    st.markdown(
        """<style>
        [data-testid="stHeader"] { display: none !important; }
        .main .block-container { padding: 0 !important; max-width: 100% !important; }
        [data-testid="stSidebar"] { display: none !important; }
        footer { display: none !important; }
        </style>""",
        unsafe_allow_html=True,
    )

    # Check for navigation from the HTML component
    qp = st.query_params
    nav_to = qp.get("nav")
    if nav_to in ("login", "signup"):
        st.session_state["selected_page"] = nav_to
        st.query_params.clear()
        st.rerun()

    LANDING_HTML = _build_landing_html()
    components.html(LANDING_HTML, height=4200, scrolling=True)


def _build_landing_html() -> str:
    return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

* { margin:0; padding:0; box-sizing:border-box; }

:root {
  --bg: #030712;
  --surface: rgba(15,23,42,0.6);
  --glass: rgba(255,255,255,0.03);
  --glass-border: rgba(255,255,255,0.06);
  --glass-hover: rgba(255,255,255,0.08);
  --text: #F8FAFC;
  --text-dim: #94A3B8;
  --text-muted: #475569;
  --accent: #7C3AED;
  --accent2: #6366F1;
  --accent3: #3B82F6;
  --cyan: #22D3EE;
  --gradient: linear-gradient(135deg, #7C3AED 0%, #6366F1 40%, #3B82F6 100%);
}

html, body {
  font-family: 'Inter', -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
}

/* ═══ THREE.JS CANVAS ═══ */
#bg-canvas {
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  z-index: 0;
  pointer-events: none;
}

/* ═══ NAVBAR ═══ */
.navbar {
  position: fixed; top: 0; left: 0; right: 0;
  z-index: 100;
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 48px;
  background: rgba(3,7,18,0.7);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.nav-logo {
  font-size: 1.3rem; font-weight: 900;
  background: var(--gradient);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  letter-spacing: -0.02em;
}
.nav-links { display: flex; gap: 32px; align-items: center; }
.nav-link {
  font-size: 0.82rem; font-weight: 500; color: var(--text-dim);
  text-decoration: none; transition: color 0.2s;
  cursor: pointer;
}
.nav-link:hover { color: var(--text); }
.nav-btns { display: flex; gap: 10px; }
.btn {
  padding: 9px 22px; border-radius: 8px; font-size: 0.82rem;
  font-weight: 600; cursor: pointer; transition: all 0.25s;
  text-decoration: none; display: inline-flex; align-items: center; gap: 6px;
  border: none; font-family: 'Inter', sans-serif;
}
.btn-ghost {
  background: transparent; color: var(--text-dim);
  border: 1px solid rgba(255,255,255,0.1);
}
.btn-ghost:hover { background: rgba(255,255,255,0.06); color: var(--text); border-color: rgba(255,255,255,0.2); }
.btn-primary {
  background: var(--gradient); color: #fff;
  box-shadow: 0 4px 20px rgba(99,102,241,0.4);
}
.btn-primary:hover {
  box-shadow: 0 6px 30px rgba(99,102,241,0.55);
  transform: translateY(-2px);
}
.btn-lg { padding: 14px 36px; font-size: 0.95rem; border-radius: 10px; }

/* ═══ SECTIONS ═══ */
section { position: relative; z-index: 1; }

/* ═══ HERO ═══ */
.hero {
  min-height: 100vh;
  display: flex; align-items: center; justify-content: center;
  padding: 120px 48px 80px;
  position: relative;
}
.hero-content {
  max-width: 1200px; width: 100%;
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 60px; align-items: center;
}
.hero-left { z-index: 2; }
.hero-badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 16px; border-radius: 24px;
  background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.25);
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em;
  text-transform: uppercase; color: #A5B4FC;
  margin-bottom: 24px;
  animation: fadeInUp 0.8s ease both;
}
.hero-badge::before {
  content: ''; width: 6px; height: 6px; border-radius: 50%;
  background: #818CF8; animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100% { opacity:1; transform:scale(1); } 50% { opacity:0.5; transform:scale(1.5); } }
.hero-title {
  font-size: clamp(2.5rem, 5vw, 4rem);
  font-weight: 900; line-height: 1.05; letter-spacing: -0.03em;
  margin-bottom: 20px;
  animation: fadeInUp 0.8s ease 0.15s both;
}
.hero-title .gradient-text {
  background: linear-gradient(135deg, #E2E8F0 0%, #A5B4FC 50%, #818CF8 80%, #22D3EE 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: gradientShift 6s ease infinite;
}
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
.hero-subtitle {
  font-size: 1.05rem; color: var(--text-dim); line-height: 1.7;
  max-width: 480px; margin-bottom: 36px;
  animation: fadeInUp 0.8s ease 0.3s both;
}
.hero-ctas {
  display: flex; gap: 14px;
  animation: fadeInUp 0.8s ease 0.45s both;
}
@keyframes fadeInUp {
  from { opacity:0; transform:translateY(30px); }
  to { opacity:1; transform:translateY(0); }
}

/* ═══ 3D PIPELINE VISUAL ═══ */
.hero-right {
  perspective: 1200px;
  display: flex; align-items: center; justify-content: center;
  animation: fadeInUp 1s ease 0.5s both;
}
.pipeline-3d {
  transform: rotateY(-8deg) rotateX(4deg);
  transform-style: preserve-3d;
  animation: float3d 8s ease-in-out infinite;
}
@keyframes float3d {
  0%,100% { transform: rotateY(-8deg) rotateX(4deg) translateY(0); }
  50% { transform: rotateY(-5deg) rotateX(2deg) translateY(-15px); }
}
.pipe-node {
  background: rgba(15,23,42,0.85);
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: 14px; padding: 18px 24px;
  margin: 8px 0;
  backdrop-filter: blur(12px);
  transition: all 0.4s cubic-bezier(0.4,0,0.2,1);
  position: relative;
  cursor: default;
  animation: nodeAppear 0.6s ease both;
}
.pipe-node:nth-child(1) { animation-delay: 0.6s; }
.pipe-node:nth-child(2) { animation-delay: 0.8s; transform: translateX(20px); }
.pipe-node:nth-child(3) { animation-delay: 1.0s; }
.pipe-node:nth-child(4) { animation-delay: 1.2s; transform: translateX(20px); }
.pipe-node:nth-child(5) { animation-delay: 1.4s; }
@keyframes nodeAppear {
  from { opacity:0; transform:translateX(-20px) scale(0.95); }
  to { opacity:1; transform:translateX(0) scale(1); }
}
.pipe-node:hover {
  border-color: rgba(99,102,241,0.5);
  box-shadow: 0 0 40px rgba(99,102,241,0.15);
  transform: translateX(8px) scale(1.02) !important;
}
.pipe-node::before {
  content: ''; position: absolute; left: -1px; top: 20%; bottom: 20%;
  width: 3px; border-radius: 2px;
  background: var(--gradient);
  opacity: 0; transition: opacity 0.3s;
}
.pipe-node:hover::before { opacity: 1; }
.pipe-num {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--gradient); color: #fff;
  font-size: 0.65rem; font-weight: 800; margin-right: 12px;
  flex-shrink: 0;
}
.pipe-label { font-size: 0.88rem; font-weight: 700; color: var(--text); }
.pipe-sub { font-size: 0.72rem; color: var(--text-muted); margin-top: 4px; }
.pipe-connector {
  width: 2px; height: 20px; margin: 0 0 0 35px;
  background: linear-gradient(180deg, rgba(99,102,241,0.4), rgba(99,102,241,0.1));
  position: relative;
}
.pipe-connector::after {
  content: ''; position: absolute; bottom: -3px; left: -3px;
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--accent2);
  animation: connectorPulse 2s ease-in-out infinite;
}
@keyframes connectorPulse {
  0%,100% { opacity:0.3; transform:scale(0.8); }
  50% { opacity:1; transform:scale(1.2); }
}

/* ═══ GLOW ORBS ═══ */
.orb {
  position: absolute; border-radius: 50%; filter: blur(80px);
  pointer-events: none; z-index: 0;
}
.orb-1 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, rgba(99,102,241,0.15), transparent 70%);
  top: -100px; right: -100px;
  animation: orbFloat 12s ease-in-out infinite;
}
.orb-2 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, rgba(124,58,237,0.12), transparent 70%);
  bottom: -50px; left: -50px;
  animation: orbFloat 15s ease-in-out infinite reverse;
}
.orb-3 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, rgba(34,211,238,0.08), transparent 70%);
  top: 40%; left: 30%;
  animation: orbFloat 18s ease-in-out infinite 3s;
}
@keyframes orbFloat {
  0%,100% { transform: translate(0,0) scale(1); }
  33% { transform: translate(30px,-20px) scale(1.1); }
  66% { transform: translate(-20px,30px) scale(0.95); }
}

/* ═══ FEATURES SECTION ═══ */
.features { padding: 100px 48px; max-width: 1200px; margin: 0 auto; }
.section-badge {
  display: inline-flex; padding: 5px 14px; border-radius: 20px;
  background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.2);
  font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.1em; color: #818CF8; margin-bottom: 16px;
}
.section-title {
  font-size: 2.4rem; font-weight: 900; letter-spacing: -0.03em;
  margin-bottom: 12px;
}
.section-sub { font-size: 1rem; color: var(--text-dim); max-width: 500px; margin-bottom: 56px; line-height:1.6; }
.features-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 20px; }
.feature-card {
  background: var(--glass); border: 1px solid var(--glass-border);
  border-radius: 18px; padding: 32px 28px;
  transition: all 0.4s cubic-bezier(0.4,0,0.2,1);
  position: relative; overflow: hidden;
}
.feature-card::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba(99,102,241,0.06), transparent);
  opacity: 0; transition: opacity 0.4s;
}
.feature-card:hover::before { opacity: 1; }
.feature-card:hover {
  border-color: rgba(99,102,241,0.3);
  box-shadow: 0 8px 40px rgba(99,102,241,0.1);
  transform: translateY(-6px);
}
.feature-icon {
  width: 52px; height: 52px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; margin-bottom: 20px; position: relative; z-index: 1;
}
.fi-purple { background: rgba(124,58,237,0.15); border: 1px solid rgba(124,58,237,0.25); }
.fi-blue { background: rgba(59,130,246,0.15); border: 1px solid rgba(59,130,246,0.25); }
.fi-cyan { background: rgba(34,211,238,0.15); border: 1px solid rgba(34,211,238,0.25); }
.feature-title {
  font-size: 1.1rem; font-weight: 800; margin-bottom: 10px;
  position: relative; z-index: 1;
}
.feature-desc {
  font-size: 0.83rem; color: var(--text-muted); line-height: 1.7;
  position: relative; z-index: 1;
}

/* ═══ HOW IT WORKS ═══ */
.how-section { padding: 100px 48px; max-width: 1200px; margin: 0 auto; }
.how-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 24px; counter-reset: step; }
.how-card {
  background: var(--glass); border: 1px solid var(--glass-border);
  border-radius: 16px; padding: 28px 24px;
  transition: all 0.35s; position: relative;
}
.how-card:hover {
  border-color: rgba(99,102,241,0.3);
  transform: translateY(-4px);
  box-shadow: 0 12px 30px rgba(0,0,0,0.3);
}
.how-num {
  font-size: 3rem; font-weight: 900; line-height: 1;
  background: linear-gradient(135deg, rgba(99,102,241,0.3), rgba(59,130,246,0.15));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  margin-bottom: 12px;
}
.how-title { font-size: 1rem; font-weight: 700; margin-bottom: 8px; }
.how-desc { font-size: 0.8rem; color: var(--text-muted); line-height: 1.6; }

/* ═══ TRUST ═══ */
.trust-section {
  padding: 80px 48px; max-width: 900px; margin: 0 auto; text-align: center;
}
.trust-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 36px; margin-top: 48px; }
.trust-item { text-align: center; }
.trust-dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--gradient); margin: 0 auto 14px;
  box-shadow: 0 0 20px rgba(99,102,241,0.4);
}
.trust-name { font-weight: 700; font-size: 0.92rem; margin-bottom: 6px; }
.trust-desc { font-size: 0.78rem; color: var(--text-muted); line-height: 1.6; }

/* ═══ CTA ═══ */
.cta-section {
  padding: 100px 48px; text-align: center;
  position: relative;
}
.cta-section .orb {
  width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(99,102,241,0.1), transparent 70%);
  top: -200px; left: 50%; transform: translateX(-50%);
}
.cta-title { font-size: 2.2rem; font-weight: 900; margin-bottom: 12px; letter-spacing: -0.02em; }
.cta-sub { color: var(--text-dim); margin-bottom: 36px; font-size: 1rem; }
.cta-btns { display: flex; gap: 14px; justify-content: center; }

/* ═══ FOOTER ═══ */
.footer {
  padding: 48px; text-align: center;
  border-top: 1px solid rgba(255,255,255,0.04);
}
.footer-logo {
  font-size: 1.1rem; font-weight: 900;
  background: var(--gradient);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  margin-bottom: 6px;
}
.footer-sub { font-size: 0.75rem; color: var(--text-muted); margin-bottom: 8px; }
.footer-copy { font-size: 0.68rem; color: rgba(255,255,255,0.15); }

/* ═══ SCROLL REVEAL ═══ */
.reveal {
  opacity: 0; transform: translateY(40px);
  transition: all 0.8s cubic-bezier(0.4,0,0.2,1);
}
.reveal.visible {
  opacity: 1; transform: translateY(0);
}

/* ═══ FLOATING PARTICLES CSS FALLBACK ═══ */
.particle {
  position: absolute;
  width: 3px; height: 3px;
  border-radius: 50%;
  background: rgba(99,102,241,0.4);
  pointer-events: none;
  animation: particleDrift linear infinite;
}
@keyframes particleDrift {
  0% { transform: translateY(0) translateX(0); opacity:0; }
  10% { opacity:1; }
  90% { opacity:1; }
  100% { transform: translateY(-100vh) translateX(50px); opacity:0; }
}
</style>
</head>
<body>

<!-- ═══ THREE.JS BACKGROUND ═══ -->
<canvas id="bg-canvas"></canvas>

<!-- ═══ GLOW ORBS ═══ -->
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>

<!-- ═══ NAVBAR ═══ -->
<nav class="navbar">
  <div class="nav-logo">🧠 AllocAI</div>
  <div class="nav-links">
    <a class="nav-link" onclick="scrollTo('.features')">Features</a>
    <a class="nav-link" onclick="scrollTo('.how-section')">How It Works</a>
    <a class="nav-link" onclick="scrollTo('.trust-section')">Why AllocAI</a>
  </div>
  <div class="nav-btns">
    <button class="btn btn-ghost" onclick="navigate('login')">Sign In</button>
    <button class="btn btn-primary" onclick="navigate('signup')">Get Started</button>
  </div>
</nav>

<!-- ═══ HERO ═══ -->
<section class="hero">
  <div class="hero-content">
    <div class="hero-left">
      <div class="hero-badge">AI Project Staffing Intelligence</div>
      <h1 class="hero-title">
        <span class="gradient-text">Match the right people.</span><br>
        <span class="gradient-text">Learn from every project.</span>
      </h1>
      <p class="hero-subtitle">
        Build project teams using real employee skills, previous project experience,
        availability, and organisational memory — so your staffing decisions get
        smarter over time.
      </p>
      <div class="hero-ctas">
        <button class="btn btn-primary btn-lg" onclick="navigate('signup')">
          🚀 Get Started
        </button>
        <button class="btn btn-ghost btn-lg" onclick="scrollTo('.how-section')">
          See How It Works ↓
        </button>
      </div>
    </div>

    <div class="hero-right">
      <div class="pipeline-3d">
        <div class="pipe-node">
          <div style="display:flex;align-items:center;">
            <span class="pipe-num">01</span>
            <span class="pipe-label">Project Requirements</span>
          </div>
          <div class="pipe-sub">Natural language → structured needs</div>
        </div>
        <div class="pipe-connector"></div>
        <div class="pipe-node">
          <div style="display:flex;align-items:center;">
            <span class="pipe-num">02</span>
            <span class="pipe-label">Employee Intelligence</span>
          </div>
          <div class="pipe-sub">Skills · experience · availability</div>
        </div>
        <div class="pipe-connector"></div>
        <div class="pipe-node">
          <div style="display:flex;align-items:center;">
            <span class="pipe-num">03</span>
            <span class="pipe-label">Organisational Memory</span>
          </div>
          <div class="pipe-sub">Hindsight: lessons · patterns · outcomes</div>
        </div>
        <div class="pipe-connector"></div>
        <div class="pipe-node">
          <div style="display:flex;align-items:center;">
            <span class="pipe-num">04</span>
            <span class="pipe-label">Project Fit Scoring</span>
          </div>
          <div class="pipe-sub">8-dimension deterministic scoring</div>
        </div>
        <div class="pipe-connector"></div>
        <div class="pipe-node">
          <div style="display:flex;align-items:center;">
            <span class="pipe-num">05</span>
            <span class="pipe-label">Recommended Team</span>
          </div>
          <div class="pipe-sub">Optimal composition with full evidence</div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ═══ FEATURES ═══ -->
<section class="features reveal">
  <div class="section-badge">Core Capabilities</div>
  <h2 class="section-title">Why AllocAI?</h2>
  <p class="section-sub">Evidence-based staffing intelligence — not guesswork.</p>
  <div class="features-grid">
    <div class="feature-card">
      <div class="feature-icon fi-purple">🧠</div>
      <div class="feature-title">Skills Intelligence</div>
      <div class="feature-desc">
        Deep understanding of your employees' technical skills, proficiency levels,
        certifications, and domain expertise — all sourced from your actual HR data.
      </div>
    </div>
    <div class="feature-card">
      <div class="feature-icon fi-blue">📂</div>
      <div class="feature-title">Project Experience</div>
      <div class="feature-desc">
        Every past project assignment is signal. AllocAI knows who delivered in fintech,
        who pairs well together, and who thrives under tight deadlines.
      </div>
    </div>
    <div class="feature-card">
      <div class="feature-icon fi-cyan">🧬</div>
      <div class="feature-title">Organisational Memory</div>
      <div class="feature-desc">
        Hindsight captures lessons from completed projects — client feedback, manager
        observations, team patterns, risks — and applies them to future staffing.
      </div>
    </div>
  </div>
</section>

<!-- ═══ HOW IT WORKS ═══ -->
<section class="how-section reveal">
  <div style="text-align:center;margin-bottom:56px;">
    <div class="section-badge">The Staffing Loop</div>
    <h2 class="section-title">How It Works</h2>
    <p class="section-sub" style="margin:0 auto;">
      From requirement to recommendation to learning — one connected cycle.
    </p>
  </div>
  <div class="how-grid">
    <div class="how-card">
      <div class="how-num">01</div>
      <div class="how-title">Describe Your Project</div>
      <div class="how-desc">Tell AllocAI what you need in plain language — technologies, domain, team size, timeline.</div>
    </div>
    <div class="how-card">
      <div class="how-num">02</div>
      <div class="how-title">AI Analyses Requirements</div>
      <div class="how-desc">AllocAI extracts structured needs and maps them to your employee data automatically.</div>
    </div>
    <div class="how-card">
      <div class="how-num">03</div>
      <div class="how-title">Find Relevant People</div>
      <div class="how-desc">Filter and score every employee across 8 dimensions — skills, experience, domain, availability, and more.</div>
    </div>
    <div class="how-card">
      <div class="how-num">04</div>
      <div class="how-title">Recall Org Memory</div>
      <div class="how-desc">Hindsight surfaces relevant lessons from past projects — what worked, what didn't, who excelled.</div>
    </div>
    <div class="how-card">
      <div class="how-num">05</div>
      <div class="how-title">Get Your Team</div>
      <div class="how-desc">An optimal, complementary team is composed with full evidence explaining each selection.</div>
    </div>
    <div class="how-card">
      <div class="how-num">06</div>
      <div class="how-title">Learn & Improve</div>
      <div class="how-desc">After the project, capture outcomes and lessons. AllocAI gets smarter with every cycle.</div>
    </div>
  </div>
</section>

<!-- ═══ TRUST ═══ -->
<section class="trust-section reveal">
  <div class="section-badge">Evidence-Based</div>
  <h2 class="section-title">Every recommendation is traceable</h2>
  <p class="section-sub" style="margin:12px auto 0;max-width:560px;">
    No black boxes. Every staffing recommendation is backed by real employee data,
    historical project assignments, and organisational memory.
  </p>
  <div class="trust-grid">
    <div class="trust-item">
      <div class="trust-dot"></div>
      <div class="trust-name">Employee Data</div>
      <div class="trust-desc">Skills, experience, availability, performance — all from your HR records.</div>
    </div>
    <div class="trust-item">
      <div class="trust-dot"></div>
      <div class="trust-name">Project History</div>
      <div class="trust-desc">Assignments, outcomes, and client feedback from every completed project.</div>
    </div>
    <div class="trust-item">
      <div class="trust-dot"></div>
      <div class="trust-name">Org Learning</div>
      <div class="trust-desc">Lessons from past staffing decisions, stored in Hindsight memory.</div>
    </div>
  </div>
</section>

<!-- ═══ CTA ═══ -->
<section class="cta-section reveal">
  <div class="orb"></div>
  <h2 class="cta-title" style="position:relative;z-index:1;">Ready to staff smarter?</h2>
  <p class="cta-sub" style="position:relative;z-index:1;">Create your AllocAI workspace in under a minute.</p>
  <div class="cta-btns" style="position:relative;z-index:1;">
    <button class="btn btn-primary btn-lg" onclick="navigate('signup')">🚀 Create Account</button>
    <button class="btn btn-ghost btn-lg" onclick="navigate('login')">Sign In</button>
  </div>
</section>

<!-- ═══ FOOTER ═══ -->
<footer class="footer">
  <div class="footer-logo">AllocAI</div>
  <div class="footer-sub">AI Project Staffing Intelligence</div>
  <div class="footer-copy">© 2026 AllocAI · Privacy · Terms</div>
</footer>

<!-- ═══ THREE.JS ═══ -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
// ─── 3D Particle Network ───
(function() {
  const canvas = document.getElementById('bg-canvas');
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth/window.innerHeight, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // Particles
  const PARTICLE_COUNT = 180;
  const positions = new Float32Array(PARTICLE_COUNT * 3);
  const velocities = [];
  const SPREAD = 60;

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    positions[i*3]     = (Math.random()-0.5) * SPREAD;
    positions[i*3 + 1] = (Math.random()-0.5) * SPREAD;
    positions[i*3 + 2] = (Math.random()-0.5) * SPREAD;
    velocities.push({
      x: (Math.random()-0.5) * 0.008,
      y: (Math.random()-0.5) * 0.008,
      z: (Math.random()-0.5) * 0.008,
    });
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

  const material = new THREE.PointsMaterial({
    color: 0x6366F1, size: 0.15, transparent: true, opacity: 0.7,
    blending: THREE.AdditiveBlending, depthWrite: false,
  });
  const points = new THREE.Points(geometry, material);
  scene.add(points);

  // Lines between nearby particles
  const lineMaterial = new THREE.LineBasicMaterial({
    color: 0x6366F1, transparent: true, opacity: 0.06,
    blending: THREE.AdditiveBlending, depthWrite: false,
  });

  let lines = null;
  function updateLines() {
    if (lines) scene.remove(lines);
    const linePositions = [];
    const pos = geometry.attributes.position.array;
    const MAX_DIST = 12;
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      for (let j = i+1; j < PARTICLE_COUNT; j++) {
        const dx = pos[i*3]-pos[j*3];
        const dy = pos[i*3+1]-pos[j*3+1];
        const dz = pos[i*3+2]-pos[j*3+2];
        const dist = Math.sqrt(dx*dx+dy*dy+dz*dz);
        if (dist < MAX_DIST) {
          linePositions.push(pos[i*3],pos[i*3+1],pos[i*3+2]);
          linePositions.push(pos[j*3],pos[j*3+1],pos[j*3+2]);
        }
      }
    }
    const lineGeo = new THREE.BufferGeometry();
    lineGeo.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));
    lines = new THREE.LineSegments(lineGeo, lineMaterial);
    scene.add(lines);
  }

  camera.position.z = 35;
  let mouseX = 0, mouseY = 0;
  document.addEventListener('mousemove', (e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
  });

  let frame = 0;
  function animate() {
    requestAnimationFrame(animate);
    frame++;

    const pos = geometry.attributes.position.array;
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      pos[i*3]     += velocities[i].x;
      pos[i*3 + 1] += velocities[i].y;
      pos[i*3 + 2] += velocities[i].z;
      // Bounds
      for (let a = 0; a < 3; a++) {
        if (Math.abs(pos[i*3+a]) > SPREAD/2) velocities[i][['x','y','z'][a]] *= -1;
      }
    }
    geometry.attributes.position.needsUpdate = true;

    // Update lines every 3 frames
    if (frame % 3 === 0) updateLines();

    // Camera follows mouse gently
    camera.position.x += (mouseX * 4 - camera.position.x) * 0.02;
    camera.position.y += (-mouseY * 3 - camera.position.y) * 0.02;
    camera.lookAt(scene.position);

    // Gentle rotation
    points.rotation.y += 0.0003;
    points.rotation.x += 0.0001;

    renderer.render(scene, camera);
  }
  animate();

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });
})();

// ─── Scroll Reveal ───
const reveals = document.querySelectorAll('.reveal');
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
    }
  });
}, { threshold: 0.15 });
reveals.forEach(el => observer.observe(el));

// ─── Smooth scroll ───
function scrollTo(selector) {
  document.querySelector(selector)?.scrollIntoView({ behavior: 'smooth' });
}

// ─── Navigation (via query params → Streamlit) ───
function navigate(page) {
  // Update URL so Streamlit picks up the query param on next rerun
  const url = new URL(window.parent.location);
  url.searchParams.set('nav', page);
  window.parent.history.pushState({}, '', url);
  // Also trigger a Streamlit rerun
  window.parent.postMessage({ type: 'streamlit:setComponentValue', value: page }, '*');
  // Fallback: reload after short delay
  setTimeout(() => { window.parent.location.reload(); }, 100);
}
</script>

</body>
</html>
"""
