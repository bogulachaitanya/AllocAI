"""Generic base repository providing common CRUD operations."""

from __future__ import annotations

from typing import TypeVar

from sqlalchemy.orm import Session

from db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository[ModelType: Base]:
    """Provides get, list, create, update, delete for any ORM model."""

    def __init__(self, model: type[ModelType], session: Session) -> None:
        self._model = model
        self._session = session

    def get(self, record_id: int) -> ModelType | None:
        return self._session.get(self._model, record_id)

    def list_all(self, limit: int = 500, offset: int = 0) -> list[ModelType]:
        return self._session.query(self._model).offset(offset).limit(limit).all()

    def create(self, obj: ModelType) -> ModelType:
        self._session.add(obj)
        self._session.flush()
        self._session.refresh(obj)
        return obj

    def delete(self, record_id: int) -> bool:
        obj = self.get(record_id)
        if obj is None:
            return False
        self._session.delete(obj)
        self._session.flush()
        return True

    def count(self) -> int:
        return self._session.query(self._model).count()
