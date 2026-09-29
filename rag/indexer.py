"""RAG Indexer — indexes company documentation into ChromaDB.

Uses SentenceTransformers for embeddings.
Documents are treated as untrusted content — they cannot override system instructions.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

COLLECTION_NAME = "company_docs"


class RAGIndexer:
    """Indexes documents into ChromaDB for retrieval."""

    def __init__(self) -> None:
        from config.settings import get_settings

        settings = get_settings()
        self._db_path = settings.chroma_db_path
        self._embedding_model_name = settings.embedding_model
        self._client = None
        self._collection = None
        self._embedding_fn = None

    def _ensure_initialized(self) -> None:
        if self._client is not None:
            return
        try:
            import chromadb
            from chromadb.utils import embedding_functions as ef

            self._client = chromadb.PersistentClient(path=self._db_path)
            self._embedding_fn = ef.SentenceTransformerEmbeddingFunction(
                model_name=self._embedding_model_name
            )
            self._collection = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=self._embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("RAG: ChromaDB initialized at %s", self._db_path)
        except ImportError:
            logger.error("chromadb or sentence-transformers not installed")
            raise

    def index_text(
        self,
        text: str,
        source: str,
        doc_type: str = "general",
        chunk_size: int = 500,
    ) -> list[str]:
        """Split text into chunks and index into ChromaDB.

        Returns list of chunk IDs added.
        """
        self._ensure_initialized()
        chunks = _chunk_text(text, chunk_size)
        ids = []

        for i, chunk in enumerate(chunks):
            chunk_id = _make_chunk_id(source, i)
            self._collection.upsert(
                documents=[chunk],
                ids=[chunk_id],
                metadatas=[
                    {
                        "source": source[:200],
                        "doc_type": doc_type,
                        "chunk_index": str(i),
                    }
                ],
            )
            ids.append(chunk_id)

        logger.info("RAG: indexed %d chunks from %s", len(ids), source)
        return ids

    def index_file(self, file_path: Path, doc_type: str = "general") -> list[str]:
        """Index a text file from disk."""
        if not file_path.exists():
            logger.warning("RAG: file not found: %s", file_path)
            return []
        text = file_path.read_text(encoding="utf-8", errors="replace")
        return self.index_text(text, source=str(file_path), doc_type=doc_type)

    def count(self) -> int:
        """Return total number of indexed chunks."""
        try:
            self._ensure_initialized()
            return self._collection.count()
        except Exception:
            return 0


def _chunk_text(text: str, chunk_size: int) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    overlap = 50  # words
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks if chunks else [text]


def _make_chunk_id(source: str, index: int) -> str:
    h = hashlib.md5(f"{source}:{index}".encode(), usedforsecurity=False).hexdigest()[:12]
    return f"chunk_{h}_{index}"
