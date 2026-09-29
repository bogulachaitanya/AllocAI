"""User model for AllocAI authentication."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from db.base import Base


class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    full_name: str = Column(String(120), nullable=False)
    email: str = Column(String(254), nullable=False, unique=True, index=True)
    organization: str = Column(String(120), nullable=False, default="")
    role: str = Column(String(60), nullable=False, default="Project Manager")
    password_hash: str = Column(String(256), nullable=False)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"
