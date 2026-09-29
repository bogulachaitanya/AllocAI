"""AllocAI Signup Page — create workspace form."""

from __future__ import annotations

import streamlit as st

from services.user_auth import ROLE_OPTIONS, signup


def render() -> None:
    col_l, col_c, col_r = st.columns([1, 1.4, 1])
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
                    Create your AllocAI workspace
                </div>
                <div style="color:#64748B;font-size:0.85rem;margin-bottom:1.5rem;">
                    Get started in under a minute.
                </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("signup_form", clear_on_submit=False):
            full_name = st.text_input("Full Name *", placeholder="Chaitanya Bogula")

            col_a, col_b = st.columns(2)
            with col_a:
                email = st.text_input("Work Email *", placeholder="you@company.com")
            with col_b:
                organization = st.text_input("Organisation *", placeholder="Acme Corp")

            role = st.selectbox(
                "Your Role *",
                ROLE_OPTIONS,
                help="This determines your default access level in AllocAI.",
            )

            col_c2, col_d = st.columns(2)
            with col_c2:
                password = st.text_input("Password *", type="password", placeholder="Min 8 characters")
            with col_d:
                confirm = st.text_input("Confirm Password *", type="password", placeholder="Repeat password")

            submitted = st.form_submit_button(
                "Create Account →", type="primary", use_container_width=True
            )

        if submitted:
            with st.spinner("Creating your workspace…"):
                ok, err = signup(
                    full_name=full_name,
                    email=email,
                    organization=organization,
                    role=role,
                    password=password,
                    confirm_password=confirm,
                )
            if ok:
                st.success(f"Welcome to AllocAI, {full_name.split()[0]}! Redirecting…")
                st.session_state["selected_page"] = "dashboard"
                st.rerun()
            else:
                st.error(err)

        # close card
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Footer ────────────────────────────────────────────────────────────
        st.markdown(
            """
            <div style="text-align:center;margin-top:1.25rem;">
                <div style="color:#4B5563;font-size:0.82rem;">
                    Already have an account?
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Sign In", use_container_width=True, key="signup_to_login"):
            st.session_state["selected_page"] = "login"
            st.rerun()

        if st.button("← Back to AllocAI Home", key="signup_to_landing", use_container_width=True):
            st.session_state["selected_page"] = "landing"
            st.rerun()
