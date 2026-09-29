"""SQLAlchemy ORM model for Project."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.assignment import Assignment
    from models.employee import Skill


class ProjectRequiredSkill(Base):
    """Skill required for a project, with optional minimum proficiency."""

    __tablename__ = "project_required_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    minimum_proficiency: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    is_mandatory: Mapped[bool] = mapped_column(Integer, nullable=False, default=1)

    project: Mapped[Project] = relationship("Project", back_populates="required_skills")
    skill: Mapped[Skill] = relationship("Skill", back_populates="project_required_skills")


class Project(Base):
    """Project record — requirements, status, team composition context."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    client: Mapped[str] = mapped_column(String(200), nullable=True, default="")
    domain: Mapped[str] = mapped_column(String(120), nullable=True, default="")
    # e.g. "fintech", "healthcare", "e-commerce"

    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
    # draft | active | completed | cancelled

    team_size_min: Mapped[int] = mapped_column(Integer, nullable=True, default=1)
    team_size_max: Mapped[int] = mapped_column(Integer, nullable=True, default=5)

    duration_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)

    start_date: Mapped[datetime.date | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime.date | None] = mapped_column(DateTime, nullable=True)

    # Raw requirement text (user input — treated as untrusted)
    raw_requirement: Mapped[str] = mapped_column(Text, nullable=True, default="")

    # Structured requirements extracted by LLM (stored as JSON string)
    structured_requirements: Mapped[str] = mapped_column(Text, nullable=True, default="")

    # LLM recommendation explanation
    recommendation_explanation: Mapped[str] = mapped_column(Text, nullable=True, default="")

    # Hindsight memory IDs that influenced this recommendation (JSON list)
    hindsight_memory_ids: Mapped[str] = mapped_column(Text, nullable=True, default="[]")

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    required_skills: Mapped[list[ProjectRequiredSkill]] = relationship(
        "ProjectRequiredSkill", back_populates="project", cascade="all, delete-orphan"
    )
    assignments: Mapped[list[Assignment]] = relationship(
        "Assignment", back_populates="project", cascade="all, delete-orphan"
    )
    outcome: Mapped[ProjectOutcome | None] = relationship(
        "ProjectOutcome", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} title={self.title!r} status={self.status!r}>"


from models.assignment import Assignment  # noqa: E402
from models.outcome import ProjectOutcome  # noqa: E402
