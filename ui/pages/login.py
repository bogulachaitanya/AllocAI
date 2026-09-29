"""AllocAI Login Page — professional glass sign-in UI."""

from __future__ import annotations

import streamlit as st

from services.user_auth import login


def render() -> None:
    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        # ── Logo ──────────────────────────────────────────────────────────────
        st.markdown(
            """
            <div style="text-align:center;margin-bottom:2rem;">
                <div style="font-size:1.6rem;font-weight:900;
                            background:linear-gradient(135deg,#6366F1,#3B82F6);
                            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                            background-clip:text;letter-spacing:-0.02em;">
                    AllocAI
                </div>
                <div style="color:#94A3B8;font-size:0.82rem;margin-top:4px;">
                    AI Project Staffing Intelligence
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Glass Card ────────────────────────────────────────────────────────
        st.markdown(
            """
            <div style="background:rgba(17,24,39,0.75);border:1px solid rgba(255,255,255,0.08);
                        border-radius:18px;padding:2.25rem 2rem 1.75rem 2rem;
                        backdrop-filter:blur(20px);box-shadow:0 12px 40px rgba(0,0,0,0.6);">
                <div style="font-size:1.35rem;font-weight:800;color:#F1F5F9;margin-bottom:4px;">
                    Welcome back
                </div>
                <div style="color:#64748B;font-size:0.85rem;margin-bottom:1.5rem;">
                    Sign in to your workspace
                </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Work Email", placeholder="you@company.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button(
                "Sign In →", type="primary", use_container_width=True
            )

        if submitted:
            if not email or not password:
                st.error("Please enter your email and password.")
            else:
                with st.spinner("Signing in…"):
                    ok, err = login(email, password)
                if ok:
                    st.success("Signed in successfully!")
                    st.session_state["selected_page"] = "dashboard"
                    st.rerun()
                else:
                    st.error(err or "Invalid credentials. Please try again.")

        # close card div
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Footer links ──────────────────────────────────────────────────────
        st.markdown(
            """
            <div style="text-align:center;margin-top:1.25rem;">
                <div style="color:#4B5563;font-size:0.82rem;">
                    Don't have an account?
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Create Account", use_container_width=True, key="login_to_signup"):
            st.session_state["selected_page"] = "signup"
            st.rerun()

        st.markdown(
            """
            <div style="text-align:center;margin-top:0.75rem;">
                <div style="color:#374151;font-size:0.78rem;">← Back to</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("← AllocAI Home", key="login_to_landing", use_container_width=True):
            st.session_state["selected_page"] = "landing"
            st.rerun()
