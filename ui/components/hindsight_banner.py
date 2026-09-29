"""Hindsight UI banner and mode indicator components.

Responsibility:
  - Render a clear "Mock Hindsight Mode" banner when local adapter is active.
  - Render Hindsight memory count and quality indicators.
  - Never fabricate or obscure the adapter type.
"""

from __future__ import annotations

import streamlit as st


def render_hindsight_mode_banner() -> None:
    """Display which Hindsight adapter is active.

    Skill rule: The UI must clearly state "Mock Hindsight Mode" when the
    local adapter is used. Never pretend mock memories came from the real service.
    """
    from config.settings import HindsightAdapter, get_settings
    from services.hindsight_service import HindsightService

    settings = get_settings()
    is_mock = settings.hindsight_adapter == HindsightAdapter.LOCAL

    if is_mock:
        st.info(
            "🧪 **Development Mode** — Using local SQLite Hindsight adapter. "
            "Organizational memories are stored locally and are not connected "
            "to a remote Hindsight service.",
            icon="🧪",
        )
    else:
        try:
            svc = HindsightService()
            count = svc.count()
            st.success(
                f"🧠 **Hindsight Connected** — Remote service active. "
                f"{count} organizational memories available.",
                icon="🧠",
            )
        except Exception as exc:
            st.warning(
                f"Organizational memory is temporarily unavailable. "
                f"The recommendation can continue using available structured employee "
                f"and project data. ({exc})",
                icon="⚠️",
            )


def render_hindsight_memory_count() -> int:
    """Return and display the current memory count (safe — no PII exposed)."""
    from services.hindsight_service import HindsightService

    try:
        svc = HindsightService()
        count = svc.count()
        return count
    except Exception:
        return 0

