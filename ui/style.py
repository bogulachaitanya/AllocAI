"""Global CSS injection for AllocAI — premium 3D glassmorphism SaaS theme.

Design system:
  - Deep dark background (#070B14 → #0B1020)
  - Semi-transparent glass cards with backdrop-filter
  - Inter font family
  - Violet/blue/cyan primary palette
  - Restrained enterprise aesthetics
"""

from __future__ import annotations

import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# Full CSS design system
# ──────────────────────────────────────────────────────────────────────────────

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ─── Design tokens ──────────────────────────────────────────────────────── */
:root {
  --bg-deep:       #070B14;
  --bg-base:       #0B1020;
  --bg-elevated:   #111827;
  --bg-card:       rgba(17, 24, 39, 0.7);
  --bg-card-hover: rgba(22, 31, 52, 0.85);
  --glass-bg:      rgba(255,255,255,0.04);
  --glass-border:  rgba(255,255,255,0.08);
  --glass-hover:   rgba(255,255,255,0.07);
  --border:        rgba(55, 65, 81, 0.6);
  --border-accent: rgba(99, 102, 241, 0.4);
  --text-primary:  #F1F5F9;
  --text-secondary:#94A3B8;
  --text-muted:    #64748B;
  --accent-violet: #7C3AED;
  --accent-indigo: #6366F1;
  --accent-blue:   #3B82F6;
  --accent-cyan:   #22D3EE;
  --accent-green:  #10B981;
  --accent-amber:  #F59E0B;
  --accent-red:    #EF4444;
  --grad-primary:  linear-gradient(135deg, #7C3AED, #6366F1, #3B82F6);
  --grad-subtle:   linear-gradient(135deg, rgba(99,102,241,0.15), rgba(59,130,246,0.1));
  --shadow-sm:     0 1px 3px rgba(0,0,0,0.5);
  --shadow-md:     0 4px 16px rgba(0,0,0,0.6);
  --shadow-lg:     0 12px 40px rgba(0,0,0,0.7);
  --shadow-glow:   0 0 30px rgba(99,102,241,0.15);
  --radius-sm:     6px;
  --radius-md:     12px;
  --radius-lg:     18px;
  --radius-xl:     24px;
  --transition:    all 0.2s cubic-bezier(0.4,0,0.2,1);
}

/* ─── Reset / base ───────────────────────────────────────────────────────── */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  background-color: var(--bg-deep) !important;
  color: var(--text-primary) !important;
  overflow-x: hidden !important;
}

[data-testid="stAppViewContainer"] > .main {
  background: radial-gradient(ellipse 80% 60% at 50% -10%,
    rgba(99,102,241,0.12) 0%, transparent 70%),
    radial-gradient(ellipse 60% 40% at 85% 90%,
    rgba(59,130,246,0.08) 0%, transparent 60%),
    linear-gradient(180deg, var(--bg-deep) 0%, var(--bg-base) 50%, var(--bg-deep) 100%);
}

.main .block-container {
  padding-top: 1.5rem !important;
  padding-bottom: 3rem !important;
  max-width: 1200px;
}

/* ─── Sidebar ────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #08101E 0%, #0B1420 100%) !important;
  border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] > div { padding-top: 0 !important; }

/* ─── Typography ─────────────────────────────────────────────────────────── */
h1 {
  font-size: 1.85rem !important;
  font-weight: 800 !important;
  letter-spacing: -0.02em !important;
  color: var(--text-primary) !important;
  line-height: 1.2 !important;
}
h2 { font-size: 1.35rem !important; font-weight: 700 !important; color: var(--text-primary) !important; }
h3 { font-size: 1.05rem !important; font-weight: 600 !important; color: var(--text-secondary) !important; }
p  { color: var(--text-secondary) !important; line-height: 1.65 !important; }
label { color: var(--text-secondary) !important; font-size: 0.875rem !important; font-weight: 500 !important; }
small, .stCaption { color: var(--text-muted) !important; }

/* ─── Metric cards ───────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
  background: var(--glass-bg) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: var(--radius-md) !important;
  padding: 1rem 1.25rem !important;
  backdrop-filter: blur(16px) !important;
  transition: var(--transition) !important;
}
[data-testid="stMetric"]:hover {
  background: var(--glass-hover) !important;
  border-color: var(--border-accent) !important;
  box-shadow: var(--shadow-glow) !important;
  transform: translateY(-2px) !important;
}
[data-testid="stMetricLabel"] {
  font-size: 0.72rem !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
  color: var(--text-muted) !important;
}
[data-testid="stMetricValue"] {
  font-size: 2rem !important;
  font-weight: 800 !important;
  background: var(--grad-primary) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
}

/* ─── Buttons ────────────────────────────────────────────────────────────── */
.stButton > button {
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.875rem !important;
  border-radius: var(--radius-sm) !important;
  transition: var(--transition) !important;
  background: var(--glass-bg) !important;
  border: 1px solid var(--glass-border) !important;
  color: var(--text-primary) !important;
  padding: 0.5rem 1.25rem !important;
}
.stButton > button:hover {
  background: var(--glass-hover) !important;
  border-color: var(--border-accent) !important;
  color: #A5B4FC !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}
.stButton > button[kind="primary"] {
  background: var(--grad-primary) !important;
  border: none !important;
  color: #fff !important;
  box-shadow: 0 4px 14px rgba(99,102,241,0.4) !important;
}
.stButton > button[kind="primary"]:hover {
  background: linear-gradient(135deg, #6D28D9, #4F46E5, #2563EB) !important;
  box-shadow: 0 6px 20px rgba(99,102,241,0.5) !important;
  transform: translateY(-1px) !important;
  color: #fff !important;
}

/* ─── Form inputs ────────────────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input,
[data-testid="stPasswordInput"] input {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-primary) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.9rem !important;
  transition: var(--transition) !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus,
[data-testid="stPasswordInput"] input:focus {
  border-color: var(--accent-indigo) !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.2) !important;
  background: rgba(255,255,255,0.06) !important;
}
input::placeholder, textarea::placeholder { color: var(--text-muted) !important; }

/* ─── Selectbox ──────────────────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-primary) !important;
}
[data-baseweb="popover"] { background: var(--bg-elevated) !important; }
[data-baseweb="option"] { background: var(--bg-elevated) !important; color: var(--text-primary) !important; }
[data-baseweb="option"]:hover { background: rgba(99,102,241,0.15) !important; }

/* ─── Tabs ───────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] {
  border-bottom: 1px solid var(--border) !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
  font-weight: 600 !important;
  font-size: 0.875rem !important;
  color: var(--text-muted) !important;
  padding: 0.6rem 1rem !important;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
  color: var(--accent-indigo) !important;
  background: rgba(99,102,241,0.08) !important;
}
[data-testid="stTabContent"] {
  padding-top: 1.25rem !important;
}

/* ─── Expanders ──────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
  background: var(--glass-bg) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: var(--radius-md) !important;
  margin: 0.5rem 0 !important;
}
[data-testid="stExpander"] summary {
  font-weight: 600 !important;
  font-size: 0.875rem !important;
  color: var(--text-primary) !important;
  padding: 0.75rem 1rem !important;
}

/* ─── Alert messages ─────────────────────────────────────────────────────── */
[data-testid="stAlert"] {
  background: var(--glass-bg) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-primary) !important;
}
[data-testid="stAlert"][data-type="success"] {
  border-left: 3px solid var(--accent-green) !important;
  background: rgba(16,185,129,0.07) !important;
}
[data-testid="stAlert"][data-type="warning"] {
  border-left: 3px solid var(--accent-amber) !important;
  background: rgba(245,158,11,0.07) !important;
}
[data-testid="stAlert"][data-type="error"] {
  border-left: 3px solid var(--accent-red) !important;
  background: rgba(239,68,68,0.07) !important;
}
[data-testid="stAlert"][data-type="info"] {
  border-left: 3px solid var(--accent-indigo) !important;
  background: rgba(99,102,241,0.07) !important;
}

/* ─── Dividers ───────────────────────────────────────────────────────────── */
hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* ─── Sliders ────────────────────────────────────────────────────────────── */
[data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stSlider-thumb"] {
  background: var(--accent-indigo) !important;
}

/* ─── Radio buttons (sidebar nav) ────────────────────────────────────────── */
[data-testid="stRadio"] label {
  font-size: 0.875rem !important;
  color: var(--text-secondary) !important;
  padding: 3px 0 !important;
  transition: var(--transition) !important;
}
[data-testid="stRadio"] label:hover { color: var(--text-primary) !important; }

/* ─── Checkboxes ─────────────────────────────────────────────────────────── */
[data-testid="stCheckbox"] label { color: var(--text-secondary) !important; }

/* ─── Dataframes ─────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
  background: var(--glass-bg) !important;
  border-radius: var(--radius-md) !important;
  overflow: hidden !important;
}

/* ─── Code blocks ────────────────────────────────────────────────────────── */
code, pre {
  background: rgba(255,255,255,0.05) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  font-size: 0.82rem !important;
  color: #A5B4FC !important;
}

/* ─── Scrollbar ──────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ─── Spinner ────────────────────────────────────────────────────────────── */
.stSpinner { color: var(--accent-indigo) !important; }

/* ─── Forms ──────────────────────────────────────────────────────────────── */
[data-testid="stForm"] {
  background: var(--glass-bg) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: var(--radius-lg) !important;
  padding: 1.5rem !important;
}

/* ─── Utility classes (used inline via unsafe_allow_html) ────────────────── */
.alloc-glass {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  backdrop-filter: blur(20px);
  box-shadow: var(--shadow-md);
  transition: var(--transition);
}
.alloc-glass:hover {
  background: var(--glass-hover);
  border-color: var(--border-accent);
  box-shadow: var(--shadow-glow);
}
.alloc-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}
.alloc-step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px; height: 26px;
  border-radius: 50%;
  background: var(--grad-primary);
  color: white;
  font-size: 0.7rem;
  font-weight: 700;
  flex-shrink: 0;
}
.alloc-gradient-text {
  background: var(--grad-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.alloc-employee-card {
  background: rgba(17,24,39,0.8);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1.5rem;
  margin: 0.75rem 0;
  position: relative;
  overflow: hidden;
  transition: var(--transition);
}
.alloc-employee-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 4px; height: 100%;
  background: var(--grad-primary);
}
.alloc-employee-card:hover {
  border-color: var(--border-accent);
  box-shadow: 0 0 25px rgba(99,102,241,0.1);
}
.alloc-score-ring {
  width: 60px; height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid;
  font-weight: 800;
  font-size: 1rem;
}
.alloc-section-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  margin-bottom: 6px;
}
.alloc-chip {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 0.72rem;
  font-weight: 500;
  background: rgba(99,102,241,0.12);
  border: 1px solid rgba(99,102,241,0.25);
  color: #A5B4FC;
  margin: 2px 2px;
}
.alloc-progress-bar {
  height: 6px;
  border-radius: 3px;
  background: rgba(255,255,255,0.08);
  overflow: hidden;
}
.alloc-progress-fill {
  height: 100%;
  border-radius: 3px;
  background: var(--grad-primary);
  transition: width 0.6s ease;
}
</style>
"""


def inject_global_css() -> None:
    """Inject the global AllocAI design system into Streamlit."""
    st.markdown(_CSS, unsafe_allow_html=True)
