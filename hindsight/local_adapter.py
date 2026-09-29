"""Local SQLite-backed Hindsight adapter.

Used when HINDSIGHT_ADAPTER=local or when remote credentials are unavailable.
Provides full Retain / Recall / Reflect functionality without external dependencies.
"""

from __future__ import annotations

import datetime
import json
import logging
import sqlite3
import uuid
from pathlib import Path

from hindsight.adapter import HindsightAdapter
from hindsight.models import (
    HindsightMemory,
    MemoryType,
    RecallRequest,
    ReflectRequest,
    RetainRequest,
)

logger = logging.getLogger(__name__)

_DB_PATH = Path("./hindsight_local.db")


class LocalHindsightAdapter(HindsightAdapter):
    """SQLite-backed local Hindsight adapter.

    Implements Retain / Recall / Reflect without any external credentials.
    Swap for RemoteHindsightAdapter to connect to the real Hindsight service.
    """

    def __init__(self, db_path: Path = _DB_PATH) -> None:
        self._db_path = db_path
        self._conn = self._init_db()

    def _init_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT NOT NULL,
                domain TEXT DEFAULT '',
                project_title TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
        return conn

    def retain(self, request: RetainRequest) -> HindsightMemory:
        memory_id = request.memory_id or str(uuid.uuid4())
        now = datetime.datetime.utcnow().isoformat()

        self._conn.execute(
            """
            INSERT OR REPLACE INTO memories
              (memory_id, memory_type, content, summary, domain, project_title,
               tags, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                request.memory_type.value,
                request.content,
                request.summary,
                request.domain,
                request.project_title,
                json.dumps(request.tags),
                json.dumps(request.metadata),
                now,
            ),
        )
        self._conn.commit()

        logger.info("Hindsight: retained memory %s (%s)", memory_id, request.memory_type.value)

        return HindsightMemory(
            memory_id=memory_id,
            memory_type=request.memory_type,
            content=request.content,
            summary=request.summary,
            domain=request.domain,
            project_title=request.project_title,
            tags=request.tags,
            metadata=request.metadata,
            created_at=datetime.datetime.fromisoformat(now),
        )

    def bulk_retain(self, requests: list[RetainRequest]) -> list[HindsightMemory]:
        memories = []
        rows = []
        now = datetime.datetime.utcnow().isoformat()
        for req in requests:
            memory_id = req.memory_id or str(uuid.uuid4())
            rows.append(
                (
                    memory_id,
                    req.memory_type.value,
                    req.content,
                    req.summary,
                    req.domain,
                    req.project_title,
                    json.dumps(req.tags),
                    json.dumps(req.metadata),
                    now,
                )
            )
            memories.append(
                HindsightMemory(
                    memory_id=memory_id,
                    memory_type=req.memory_type,
                    content=req.content,
                    summary=req.summary,
                    domain=req.domain,
                    project_title=req.project_title,
                    tags=req.tags,
                    metadata=req.metadata,
                    created_at=datetime.datetime.fromisoformat(now),
                )
            )

        self._conn.executemany(
            """
            INSERT OR REPLACE INTO memories
              (memory_id, memory_type, content, summary, domain, project_title,
               tags, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self._conn.commit()
        logger.info("Hindsight: bulk retained %d memories", len(memories))
        return memories

    def lookup_by_employee(self, employee_id: str) -> list[HindsightMemory]:
        rows = self._conn.execute(
            "SELECT * FROM memories ORDER BY created_at DESC LIMIT 5000"
        ).fetchall()
        return [
            m
            for m in (self._row_to_memory(r) for r in rows)
            if m.metadata.get("employee_id") == employee_id
        ]

    def lookup_by_project(self, project_id: str) -> list[HindsightMemory]:
        rows = self._conn.execute(
            "SELECT * FROM memories ORDER BY created_at DESC LIMIT 5000"
        ).fetchall()
        return [
            m
            for m in (self._row_to_memory(r) for r in rows)
            if m.metadata.get("project_id") == project_id
        ]

    def recall(self, request: RecallRequest) -> list[HindsightMemory]:
        """Simple keyword-based recall.

        Retrieves memories whose content or summary contains query terms.
        Returns at most request.top_k memories ordered by relevance score.
        Never returns the full memory database to any caller.
        """
        rows = self._conn.execute(
            "SELECT * FROM memories ORDER BY created_at DESC LIMIT 5000"
        ).fetchall()

        memories = [self._row_to_memory(r) for r in rows]

        if request.memory_types:
            type_values = {t.value for t in request.memory_types}
            memories = [m for m in memories if m.memory_type.value in type_values]

        if request.domain:
            domain_lower = request.domain.lower()
            domain_matches = [m for m in memories if domain_lower in m.domain.lower()]
            if domain_matches:
                memories = domain_matches

        # Score by keyword overlap
        query_terms = set(request.query.lower().split())
        scored = []
        for mem in memories:
            text = (mem.content + " " + mem.summary).lower()
            overlap = sum(1 for t in query_terms if t in text)
            score = overlap / max(len(query_terms), 1)
            if score > 0:
                scored.append((score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        result = []
        for score, mem in scored[: request.top_k]:
            mem.relevance_score = min(score, 1.0)
            result.append(mem)

        logger.info("Hindsight: recalled %d memories for query %r", len(result), request.query[:60])
        return result

    def reflect(self, request: ReflectRequest) -> str:
        """Produce a text summary of provided memories.

        Local implementation: concatenate summaries with context.
        In a remote adapter, this would call the Hindsight Reflect API.
        """
        if not request.memories:
            return "No relevant organizational memory was found."

        parts = [f"Organizational memory reflection ({len(request.memories)} memories):"]
        for mem in request.memories:
            parts.append(f"- [{mem.memory_type.value}] {mem.summary}")

        if request.context:
            parts.append(f"\nContext: {request.context}")

        return "\n".join(parts)

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM memories").fetchone()
        return row[0] if row else 0

    def list_all(self, limit: int = 100) -> list[HindsightMemory]:
        rows = self._conn.execute(
            "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    @staticmethod
    def _row_to_memory(row: tuple) -> HindsightMemory:
        (
            memory_id,
            memory_type,
            content,
            summary,
            domain,
            project_title,
            tags_json,
            metadata_json,
            created_at,
        ) = row
        return HindsightMemory(
            memory_id=memory_id,
            memory_type=MemoryType(memory_type),
            content=content,
            summary=summary,
            domain=domain,
            project_title=project_title,
            tags=json.loads(tags_json) if tags_json else [],
            metadata=json.loads(metadata_json) if metadata_json else {},
            created_at=datetime.datetime.fromisoformat(created_at),
        )
