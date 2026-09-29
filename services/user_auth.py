"""User authentication service for AllocAI.

Lightweight session-based auth using Streamlit session_state.
Passwords are hashed with PBKDF2-HMAC-SHA256 (Python stdlib — no extra deps).

Architecture:
    Landing / Login / Signup  (public)
          ↓
    UserAuthService.login() / .signup()
          ↓
    Session state: logged_in, user_name, user_email, user_role
          ↓
    Protected application pages
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
from dataclasses import dataclass

import streamlit as st
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.session import get_db
from models.user import User

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

_PBKDF2_ITERATIONS = 390_000  # OWASP 2023 recommended minimum
_HASH_ALGO = "sha256"

ROLE_OPTIONS = [
    "Project Manager",
    "HR Manager",
    "Engineering Manager",
    "Resource Manager",
    "Administrator",
]


# ── Password hashing ──────────────────────────────────────────────────────────


def _hash_password(password: str) -> str:
    """Hash password with PBKDF2-HMAC-SHA256 + random salt.

    Returns a single storable string: hex(salt):hex(hash)
    """
    salt = os.urandom(32)
    dk = hashlib.pbkdf2_hmac(_HASH_ALGO, password.encode(), salt, _PBKDF2_ITERATIONS)
    return f"{salt.hex()}:{dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    """Verify a plaintext password against a stored hash string."""
    try:
        salt_hex, dk_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac(_HASH_ALGO, password.encode(), salt, _PBKDF2_ITERATIONS)
        return secrets.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


# ── Session helpers ───────────────────────────────────────────────────────────


@dataclass
class SessionUser:
    """Lightweight, serialisable user object stored in session_state."""

    user_id: int
    full_name: str
    email: str
    organization: str
    role: str


def get_session_user() -> SessionUser | None:
    """Return the currently logged-in user from session_state, or None."""
    return st.session_state.get("_alloc_user")


def is_authenticated() -> bool:
    """Return True if a user is currently logged in."""
    return st.session_state.get("_alloc_logged_in", False)


def _set_session(user: User) -> None:
    """Write user into session_state (called after successful auth)."""
    st.session_state["_alloc_logged_in"] = True
    st.session_state["_alloc_user"] = SessionUser(
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        organization=user.organization,
        role=user.role,
    )
    # Reset navigation to dashboard on login
    st.session_state.pop("selected_page", None)


def logout() -> None:
    """Clear auth session state."""
    for key in ["_alloc_logged_in", "_alloc_user", "selected_page",
                "current_project_id", "last_recommended_team"]:
        st.session_state.pop(key, None)


# ── Auth operations ───────────────────────────────────────────────────────────


def login(email: str, password: str) -> tuple[bool, str]:
    """Attempt login. Returns (success, error_message).

    Does NOT raise — always returns a safe result tuple.
    """
    email = email.strip().lower()
    if not email or not password:
        return False, "Email and password are required."

    try:
        with get_db() as session:
            user = session.query(User).filter(User.email == email).first()
            if user is None or not user.is_active:
                return False, "Invalid email or password."
            if not _verify_password(password, user.password_hash):
                return False, "Invalid email or password."
            _set_session(user)
            logger.info("Login successful for email=%s", email)
            return True, ""
    except Exception as exc:
        logger.error("Login error: %s", exc)
        return False, "An error occurred. Please try again."


def signup(
    full_name: str,
    email: str,
    organization: str,
    role: str,
    password: str,
    confirm_password: str,
) -> tuple[bool, str]:
    """Register a new user. Returns (success, error_message)."""
    full_name = full_name.strip()
    email = email.strip().lower()
    organization = organization.strip()

    # Validation
    if not full_name:
        return False, "Full name is required."
    if not email or "@" not in email:
        return False, "A valid work email is required."
    if not organization:
        return False, "Organisation name is required."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if password != confirm_password:
        return False, "Passwords do not match."

    try:
        with get_db() as session:
            existing = session.query(User).filter(User.email == email).first()
            if existing:
                return False, "An account with this email already exists."

            user = User(
                full_name=full_name,
                email=email,
                organization=organization,
                role=role,
                password_hash=_hash_password(password),
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            _set_session(user)
            logger.info("New user registered: email=%s role=%s org=%s", email, role, organization)
            return True, ""
    except IntegrityError:
        return False, "An account with this email already exists."
    except Exception as exc:
        logger.error("Signup error: %s", exc)
        return False, "An error occurred. Please try again."
