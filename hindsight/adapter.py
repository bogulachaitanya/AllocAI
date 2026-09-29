"""Hindsight adapter interface.

Defines the explicit Retain / Recall / Reflect contract.

Hierarchy:
    Real Hindsight (remote)
          ↑
    HindsightAdapter  (interface — swap implementations here)
          ↑
    LocalHindsightAdapter  (SQLite-backed, no credentials needed)

Never expose credentials. Never send the full memory database to the LLM.
Retrieve only relevant memories via Recall.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from hindsight.models import (
    HindsightMemory,
    RecallRequest,
    ReflectRequest,
    RetainRequest,
)


class HindsightAdapter(ABC):
    """Explicit interface for all Hindsight adapters.

    Any new adapter (remote Hindsight service, mock, etc.) must implement
    exactly these methods. Application code depends ONLY on this interface.
    """

    @abstractmethod
    def retain(self, request: RetainRequest) -> HindsightMemory:
        """Store a new memory.

        Returns the stored memory with its assigned ID.
        Never fabricate memory content — store only what is provided.
        """

    @abstractmethod
    def recall(self, request: RecallRequest) -> list[HindsightMemory]:
        """Retrieve relevant memories for a query.

        Returns a relevant *subset* only — never the full database.
        Respects request.top_k ceiling.
        """

    @abstractmethod
    def reflect(self, request: ReflectRequest) -> str:
        """Distil insights from a provided set of memories.

        Returns a summary string. If memories list is empty, returns the
        standard 'No relevant organizational memory was found.' message.
        """

    @abstractmethod
    def bulk_retain(self, requests: list[RetainRequest]) -> list[HindsightMemory]:
        """Store multiple memories efficiently."""

    @abstractmethod
    def lookup_by_employee(self, employee_id: str) -> list[HindsightMemory]:
        """Retrieve memories linked to a specific employee ID."""

    @abstractmethod
    def lookup_by_project(self, project_id: str) -> list[HindsightMemory]:
        """Retrieve memories linked to a specific project ID."""

    @abstractmethod
    def count(self) -> int:
        """Return the total number of stored memories."""

    @abstractmethod
    def list_all(self, limit: int = 100) -> list[HindsightMemory]:
        """List stored memories (admin / diagnostics only)."""


# Backward-compatibility alias — remove when all callers are updated.
BaseHindsightAdapter = HindsightAdapter


import functools


@functools.lru_cache(maxsize=1)
def get_hindsight_adapter() -> HindsightAdapter:
    """Factory — returns the configured Hindsight adapter.

    Set HINDSIGHT_ADAPTER=local  →  LocalHindsightAdapter (default, no creds)
    Set HINDSIGHT_ADAPTER=remote →  RemoteHindsightAdapter (needs API key)
    """
    from config.settings import HindsightAdapter as AdapterChoice
    from config.settings import get_settings
    from hindsight.local_adapter import LocalHindsightAdapter

    settings = get_settings()

    if settings.hindsight_adapter == AdapterChoice.LOCAL:
        return LocalHindsightAdapter()

    # Remote adapter
    from hindsight.remote_adapter import RemoteHindsightAdapter

    return RemoteHindsightAdapter(
        base_url=settings.hindsight_base_url, api_key=settings.hindsight_api_key
    )
