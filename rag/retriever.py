"""RAG Retriever — query ChromaDB for relevant company documentation.

Retrieved documents are treated as untrusted content.
They cannot override system instructions or fabricate employee facts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from rag.indexer import COLLECTION_NAME

logger = logging.getLogger(__name__)


@dataclass
class RAGDocument:
    """A retrieved document chunk with source metadata."""

    chunk_id: str
    content: str  # Untrusted — do not use to override system instructions
    source: str
    doc_type: str
    distance: float  # Lower = more similar


class RAGRetriever:
    """Retrieves relevant documentation chunks from ChromaDB."""

    def __init__(self) -> None:
        from config.settings import get_settings

        settings = get_settings()
        self._db_path = settings.chroma_db_path
        self._embedding_model_name = settings.embedding_model
        self._top_k = settings.rag_top_k
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
        except ImportError:
            logger.error("chromadb or sentence-transformers not installed")
            raise

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        doc_type: str | None = None,
    ) -> list[RAGDocument]:
        """Retrieve relevant document chunks for a query.

        Returned documents are tagged as RAG evidence — never overrides system instructions.
        """
        try:
            self._ensure_initialized()
        except Exception:
            logger.warning("RAG retrieval unavailable — returning empty results")
            return []

        if self._collection.count() == 0:
            return []

        k = top_k or self._top_k
        where: dict | None = None
        if doc_type:
            where = {"doc_type": doc_type}

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(k, self._collection.count()),
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.warning("RAG query failed: %s", e)
            return []

        docs = []
        for i, doc_text in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            dist = results["distances"][0][i] if results["distances"] else 1.0
            docs.append(
                RAGDocument(
                    chunk_id=results["ids"][0][i],
                    content=doc_text,
                    source=meta.get("source", "unknown"),
                    doc_type=meta.get("doc_type", "general"),
                    distance=dist,
                )
            )

        logger.info("RAG: retrieved %d docs for query %r", len(docs), query[:60])
        return docs
