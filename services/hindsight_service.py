"""Hindsight service layer.

Provides a service boundary for Hindsight interactions, preventing the UI layer
from directly calling adapter functions and ensuring authorization checks can
be centralized if necessary.
"""

from __future__ import annotations

import logging

from hindsight.adapter import get_hindsight_adapter
from hindsight.models import HindsightMemory, RecallRequest, RetainRequest
from services.auth import ServiceGuard, UserRole

logger = logging.getLogger(__name__)


class HindsightService:
    """Service layer for Hindsight operations."""

    def __init__(self, user_role: UserRole = UserRole.PROJECT_MANAGER) -> None:
        self._hindsight = get_hindsight_adapter()
        self._user_role = user_role

    def count(self) -> int:
        """Return the total number of memories."""
        return self._hindsight.count()

    def list_all(self, limit: int = 100) -> list[HindsightMemory]:
        """List stored memories. Requires MANAGER access or higher."""
        guard = ServiceGuard(self._user_role)
        guard.require_hindsight_access()
        return self._hindsight.list_all(limit=limit)

    def recall(self, query: str, domain: str = "", top_k: int = 5) -> list[HindsightMemory]:
        """Recall relevant memories. Requires MANAGER access or higher."""
        guard = ServiceGuard(self._user_role)
        guard.require_hindsight_access()

        request = RecallRequest(query=query, domain=domain, top_k=top_k)
        try:
            return self._hindsight.recall(request)
        except Exception as e:
            logger.error("HindsightService recall failed: %s", e)
            return []

    def retain(
        self,
        content: str,
        summary: str,
        memory_type: str,
        domain: str = "",
        project_title: str = "",
        tags: list[str] | None = None,
    ) -> HindsightMemory:
        """Retain a new organizational memory. Requires MANAGER access or higher."""
        from hindsight.models import MemoryType

        guard = ServiceGuard(self._user_role)
        guard.require_hindsight_access()

        request = RetainRequest(
            content=content.strip(),
            summary=summary.strip(),
            memory_type=MemoryType(memory_type),
            domain=domain.strip(),
            project_title=project_title.strip(),
            tags=tags or [],
        )
        return self._hindsight.retain(request)
