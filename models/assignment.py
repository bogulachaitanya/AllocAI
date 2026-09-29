"""Assignment — link between an Employee and a Project."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.employee import Employee
    from models.project import Project


class Assignment(Base):
    """Records that an employee was assigned to a project with a specific role."""

    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    role_on_project: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    allocation_percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    start_date: Mapped[datetime.date | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime.date | None] = mapped_column(DateTime, nullable=True)

    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")
    # active | completed | removed

    # Structured performance record for this assignment (from HR)
    individual_performance_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    manager_notes: Mapped[str] = mapped_column(Text, nullable=True, default="")

    # Collaboration partners during this project (JSON list of employee IDs)
    collaborated_with: Mapped[str] = mapped_column(Text, nullable=True, default="[]")

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    employee: Mapped[Employee] = relationship("Employee", back_populates="assignments")
    project: Mapped[Project] = relationship("Project", back_populates="assignments")

    def __repr__(self) -> str:
        return (
            f"<Assignment employee_id={self.employee_id} "
            f"project_id={self.project_id} role={self.role_on_project!r}>"
        )
