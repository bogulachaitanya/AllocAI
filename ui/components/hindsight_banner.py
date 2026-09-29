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
            "🧪 **Mock Hindsight Mode** — Using local SQLite adapter. "
            "Memories are stored locally on this machine and are not connected "
            "to the real Hindsight service.",
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
            st.error(
                f"🧠 **Hindsight Unavailable** — Remote service could not be reached: {exc}",
                icon="❌",
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


def render_before_after_comparison(
    rec_without: object | None,
    rec_with: object | None,
) -> None:
    """Render a side-by-side Before / After Hindsight comparison.

    Skill rule: The UI must clearly show the difference between recommendations
    made with and without Hindsight.

    Args:
        rec_without: Recommendation produced WITHOUT Hindsight recall.
        rec_with:    Recommendation produced WITH Hindsight recall.
    """
    if rec_without is None and rec_with is None:
        return

    st.markdown("## 📊 Before / After Hindsight Comparison")
    st.caption("This view shows how organizational memory (Hindsight) changes the recommendation.")

    col_before, col_after = st.columns(2, gap="large")

    with col_before:
        st.markdown("### ⚙️ Without Hindsight")
        st.caption("Based on: skills · experience · availability · performance")
        if rec_without is None:
            st.info("Run a recommendation to see this view.")
        else:
            _render_rec_summary(rec_without, mode="without")

    with col_after:
        st.markdown("### 🧠 With Hindsight")
        st.caption("Additionally uses: lessons · outcomes · team patterns · risks · feedback")
        if rec_with is None:
            st.info("Run a recommendation to see this view.")
        else:
            _render_rec_summary(rec_with, mode="with")


def _render_rec_summary(rec: object, mode: str) -> None:
    """Render a compact summary card for a single Recommendation."""
    from schemas.recommendation import Recommendation

    if not isinstance(rec, Recommendation):
        st.warning("Invalid recommendation object.")
        return

    members = rec.recommended_team or []
    st.metric("Team Size", len(members))

    if rec.validation:
        st.metric("Skill Coverage", f"{rec.validation.skill_coverage_percentage:.0f}%")

    # Hindsight contribution
    if mode == "with":
        mem_count = len(
            [
                ev
                for ev in (rec.evidence or [])
                if hasattr(ev, "source") and str(ev.source).lower() == "hindsight"
            ]
        )
        if mem_count:
            st.success(f"🧠 {mem_count} Hindsight evidence item(s) influenced this recommendation")
        elif not rec.hindsight_memories_found:
            st.warning(rec.no_memory_message or "No relevant organizational memory was found.")

    elif mode == "without":
        st.info("No Hindsight recall — pure database + scoring.")

    # Members
    if members:
        with st.expander("Team Members", expanded=True):
            for m in members:
                badge = "🧠 " if (mode == "with" and m.hindsight_evidence) else ""
                st.markdown(
                    f"**{badge}{m.employee_name}** — {m.employee_role} "
                    f"({m.employee_seniority}) · fit={m.project_fit_score:.0%}"
                )

    # Risks
    if rec.risks:
        with st.expander("⚠️ Risks", expanded=False):
            for r in rec.risks:
                st.error(f"• {r}")

    # Skill gaps
    if rec.skill_gaps:
        with st.expander("🔧 Skill Gaps", expanded=False):
            st.write(", ".join(rec.skill_gaps))
