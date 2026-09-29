"""Outcome repository."""

from __future__ import annotations

from sqlalchemy.orm import Session

from models.outcome import ProjectOutcome
from repositories.base import BaseRepository


class OutcomeRepository(BaseRepository[ProjectOutcome]):
    def __init__(self, session: Session) -> None:
        super().__init__(ProjectOutcome, session)

    def get_by_project(self, project_id: int) -> ProjectOutcome | None:
        return (
            self._session.query(ProjectOutcome)
            .filter(ProjectOutcome.project_id == project_id)
            .first()
        )

    def list_recent(self, limit: int = 20) -> list[ProjectOutcome]:
        return (
            self._session.query(ProjectOutcome)
            .order_by(ProjectOutcome.completed_at.desc())
            .limit(limit)
            .all()
        )
