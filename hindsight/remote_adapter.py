"""Remote HTTP-backed Hindsight adapter.

Used when HINDSIGHT_ADAPTER=remote.
Provides full Retain / Recall / Reflect functionality by calling the remote Hindsight API.
"""

from __future__ import annotations

import logging

import requests

from hindsight.adapter import HindsightAdapter
from hindsight.models import (
    HindsightMemory,
    RecallRequest,
    ReflectRequest,
    RetainRequest,
)

logger = logging.getLogger(__name__)


class RemoteHindsightAdapter(HindsightAdapter):
    """HTTP-backed remote Hindsight adapter."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        )

    def retain(self, request: RetainRequest) -> HindsightMemory:
        url = f"{self.base_url}/api/v1/memories"
        payload = request.model_dump(mode="json")
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        logger.info("Hindsight: remotely retained memory %s", data.get("memory_id"))
        return HindsightMemory.model_validate(data)

    def recall(self, request: RecallRequest) -> list[HindsightMemory]:
        url = f"{self.base_url}/api/v1/recall"
        payload = request.model_dump(mode="json")
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        memories = data.get("memories", [])
        logger.info("Hindsight: remotely recalled %d memories", len(memories))
        return [HindsightMemory.model_validate(m) for m in memories]

    def bulk_retain(self, requests: list[RetainRequest]) -> list[HindsightMemory]:
        url = f"{self.base_url}/api/v1/memories/bulk"
        payload = [req.model_dump(mode="json") for req in requests]
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        memories = data.get("memories", [])
        return [HindsightMemory.model_validate(m) for m in memories]

    def lookup_by_employee(self, employee_id: str) -> list[HindsightMemory]:
        url = f"{self.base_url}/api/v1/memories/search"
        response = self.session.get(url, params={"metadata.employee_id": employee_id})
        response.raise_for_status()
        return [HindsightMemory.model_validate(m) for m in response.json().get("memories", [])]

    def lookup_by_project(self, project_id: str) -> list[HindsightMemory]:
        url = f"{self.base_url}/api/v1/memories/search"
        response = self.session.get(url, params={"metadata.project_id": project_id})
        response.raise_for_status()
        return [HindsightMemory.model_validate(m) for m in response.json().get("memories", [])]

    def reflect(self, request: ReflectRequest) -> str:
        url = f"{self.base_url}/api/v1/reflect"
        payload = request.model_dump(mode="json")
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("summary", "No relevant organizational memory was found.")

    def count(self) -> int:
        url = f"{self.base_url}/api/v1/memories/count"
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("count", 0)

    def list_all(self, limit: int = 100) -> list[HindsightMemory]:
        url = f"{self.base_url}/api/v1/memories"
        response = self.session.get(url, params={"limit": limit})
        response.raise_for_status()
        data = response.json()
        memories = data.get("memories", [])
        return [HindsightMemory.model_validate(m) for m in memories]
