"""Project outcome — collected after a project completes."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.project import Project


class ProjectOutcome(Base):
    """Records post-project outcome, client feedback, and derived lessons."""

    __tablename__ = "project_outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Overall outcome
    outcome_status: Mapped[str] = mapped_column(String(40), nullable=False, default="success")
    # success | partial_success | failure | cancelled

    delivered_on_time: Mapped[bool | None] = mapped_column(Integer, nullable=True)
    delivered_on_budget: Mapped[bool | None] = mapped_column(Integer, nullable=True)
    quality_rating: Mapped[float | None] = mapped_column(Float, nullable=True)  # 1–5

    # Feedback text (from client/manager — untrusted input stored as-is)
    client_feedback: Mapped[str] = mapped_column(Text, nullable=True, default="")
    manager_feedback: Mapped[str] = mapped_column(Text, nullable=True, default="")

    # Observations (human-written)
    observations: Mapped[str] = mapped_column(Text, nullable=True, default="")

    # LLM-extracted lessons (stored as JSON list of strings)
    extracted_lessons: Mapped[str] = mapped_column(Text, nullable=True, default="[]")

    # Hindsight memory IDs retained from this outcome
    retained_memory_ids: Mapped[str] = mapped_column(Text, nullable=True, default="[]")

    completed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship("Project", back_populates="outcome")

    def __repr__(self) -> str:
        return f"<ProjectOutcome project_id={self.project_id} status={self.outcome_status!r}>"
