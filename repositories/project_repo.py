"""Project repository."""

from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from models.project import Project, ProjectRequiredSkill
from repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session: Session) -> None:
        super().__init__(Project, session)

    def get_with_details(self, project_id: int) -> Project | None:
        return (
            self._session.query(Project)
            .options(
                joinedload(Project.required_skills).joinedload(ProjectRequiredSkill.skill),
                joinedload(Project.assignments),
                joinedload(Project.outcome),
            )
            .filter(Project.id == project_id)
            .first()
        )

    def list_by_status(self, status: str, limit: int = 100) -> list[Project]:
        return (
            self._session.query(Project)
            .filter(Project.status == status)
            .order_by(Project.created_at.desc())
            .limit(limit)
            .all()
        )

    def count_by_status(self, status: str) -> int:
        return self._session.query(Project).filter(Project.status == status).count()

    def list_recent_summaries(self, limit: int = 50) -> list[ProjectSummary]:
        from schemas.project import ProjectSummary

        projects = (
            self._session.query(Project.id, Project.title)
            .order_by(Project.created_at.desc())
            .limit(limit)
            .all()
        )
        return [ProjectSummary(id=p.id, title=p.title) for p in projects]

    def list_recent(self, limit: int = 20) -> list[Project]:
        return self._session.query(Project).order_by(Project.created_at.desc()).limit(limit).all()
