"""SQLAlchemy ORM model for Employee and related tables.

Captures stable, structured facts about employees.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from models.assignment import Assignment


class Skill(Base):
    """A named skill that can be linked to employees or projects."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, default="General")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    employee_skills: Mapped[list[EmployeeSkill]] = relationship(
        "EmployeeSkill", back_populates="skill", cascade="all, delete-orphan"
    )
    project_required_skills: Mapped[list[ProjectRequiredSkill]] = relationship(
        "ProjectRequiredSkill", back_populates="skill", cascade="all, delete-orphan"
    )


class EmployeeSkill(Base):
    """Association: employee ↔ skill with proficiency and years."""

    __tablename__ = "employee_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    proficiency: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    # 1 = Beginner, 2 = Intermediate, 3 = Proficient, 4 = Expert, 5 = Master
    years_with_skill: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    employee: Mapped[Employee] = relationship("Employee", back_populates="employee_skills")
    skill: Mapped[Skill] = relationship("Skill", back_populates="employee_skills")


class Certification(Base):
    """Professional certification held by an employee."""

    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuer: Mapped[str] = mapped_column(String(200), nullable=True)
    issued_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expires_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    employee: Mapped[Employee] = relationship("Employee", back_populates="certifications")


class Employee(Base):
    """Core employee record — structured, stable facts only."""

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(120), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    seniority: Mapped[str] = mapped_column(String(40), nullable=False)
    # junior | mid | senior | lead | principal | staff

    years_of_experience: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    domain_expertise: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Comma-separated domains, e.g. "fintech,cloud,ml"

    # Availability
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    availability_percentage: Mapped[int] = mapped_column(
        Integer, nullable=False, default=100
    )  # 0–100
    available_from: Mapped[datetime.date | None] = mapped_column(DateTime, nullable=True)

    # Performance (structured aggregate from HR system)
    performance_rating: Mapped[float] = mapped_column(Float, nullable=True)
    # 1.0–5.0 scale

    # Work preferences (stable facts)
    work_preferences: Mapped[str] = mapped_column(
        Text, nullable=True, default=""
    )  # e.g. "remote,agile,mentoring"

    # Location
    location: Mapped[str] = mapped_column(String(120), nullable=True, default="")
    timezone: Mapped[str] = mapped_column(String(60), nullable=True, default="UTC")

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    employee_skills: Mapped[list[EmployeeSkill]] = relationship(
        "EmployeeSkill", back_populates="employee", cascade="all, delete-orphan"
    )
    certifications: Mapped[list[Certification]] = relationship(
        "Certification", back_populates="employee", cascade="all, delete-orphan"
    )
    assignments: Mapped[list[Assignment]] = relationship(
        "Assignment", back_populates="employee", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Employee id={self.id} name={self.name!r} role={self.role!r}>"


# Imported here to avoid circular references at module level
from models.assignment import Assignment  # noqa: E402
from models.project import ProjectRequiredSkill  # noqa: E402
