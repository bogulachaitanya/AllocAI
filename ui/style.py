"""Global CSS injection for AllocAI — glassmorphism enterprise theme."""

from __future__ import annotations

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --bg-primary:   #0d1117;
    --bg-secondary: #161b22;
    --bg-card:      rgba(22, 27, 34, 0.85);
    --border:       rgba(48, 54, 61, 0.8);
    --border-glow:  rgba(88, 166, 255, 0.3);
    --text-primary: #e6edf3;
    --text-secondary:#8b949e;
    --text-muted:   #6e7681;
    --accent-blue:  #58a6ff;
    --accent-purple:#a371f7;
    --accent-green: #3fb950;
    --accent-red:   #f85149;
    --glass-bg:     rgba(255,255,255,0.03);
    --glass-border: rgba(255,255,255,0.08);
    --shadow-md:    0 4px 12px rgba(0,0,0,0.5);
    --shadow-lg:    0 8px 32px rgba(0,0,0,0.6);
    --radius-sm:    6px;
    --radius-md:    10px;
    --radius-lg:    16px;
    --transition:   all 0.2s ease;
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

[data-testid="stAppViewContainer"] > .main {
    background: linear-gradient(135deg, #0d1117 0%, #0f1923 50%, #0d1117 100%);
    min-height: 100vh;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #111827 100%) !important;
    border-right: 1px solid var(--border) !important;
}

h1 {
    font-size: 1.9rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
h2 { font-size: 1.4rem !important; font-weight: 700 !important; color: var(--text-primary) !important; }
h3 { font-size: 1.1rem !important; font-weight: 600 !important; color: var(--text-secondary) !important; }
p, li, label { color: var(--text-secondary) !important; }

[data-testid="stMetric"] {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-md);
    padding: 1rem 1.2rem;
    transition: var(--transition);
    backdrop-filter: blur(8px);
}
[data-testid="stMetric"]:hover {
    border-color: var(--border-glow);
    box-shadow: 0 0 20px rgba(88,166,255,0.1);
    transform: translateY(-2px);
}
[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    color: var(--accent-blue) !important;
}

.stButton > button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    border: 1px solid var(--border) !important;
    transition: var(--transition) !important;
    background: var(--glass-bg) !important;
    color: var(--text-primary) !important;
}
.stButton > button:hover {
    border-color: var(--accent-blue) !important;
    color: var(--accent-blue) !important;
    box-shadow: 0 0 12px rgba(88,166,255,0.2) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1f6feb, #388bfd) !important;
    border-color: transparent !important;
    color: #ffffff !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #388bfd, #58a6ff) !important;
    box-shadow: 0 4px 16px rgba(88,166,255,0.35) !important;
    color: #ffffff !important;
}

[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 2px rgba(88,166,255,0.15) !important;
}

[data-testid="stExpander"] {
    background: var(--glass-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: var(--text-primary) !important;
}

hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

[data-testid="stTabs"] [data-baseweb="tab"] {
    font-weight: 600 !important;
    color: var(--text-secondary) !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--accent-blue) !important;
    border-bottom-color: var(--accent-blue) !important;
}

[data-testid="stRadio"] label {
    font-size: 0.9rem !important;
    color: var(--text-secondary) !important;
    transition: var(--transition) !important;
}
[data-testid="stRadio"] label:hover { color: var(--text-primary) !important; }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
</style>
"""


def inject_global_css() -> None:
    """Inject the global glassmorphism CSS theme into Streamlit."""
    st.markdown(_CSS, unsafe_allow_html=True)
