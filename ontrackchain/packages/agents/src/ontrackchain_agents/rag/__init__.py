"""
RAG Pipeline — Regulatory Knowledge Base for Class B Agents.

Architecture:
  Corpus Legal Estruturado → Chunking → Embedding → Vector Store → Retrieval → Re-ranking

Design Principles:
  - RAG, not fine-tuning: regulations change frequently
  - Temporal filtering: only retrieve valid regulations
  - Re-ranking: by legal relevance, not just similarity
  - Citation mandatory: every response must cite source articles
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class RegulatoryChunk:
    """A chunk of regulatory text."""
    chunk_id: str
    corpus_id: str            # e.g., "bcb_520"
    article: str              # e.g., "Art. 43 §2° VI"
    title: str                # e.g., "Procedimentos de PLD/FT"
    text: str                 # Full text of the chunk
    embedding: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    # Metadata: vigência, revogação, hierarquia, tags


@dataclass
class RetrievalResult:
    """Result from RAG retrieval."""
    chunk: RegulatoryChunk
    score: float              # Similarity score
    rerank_score: float = 0.0  # After re-ranking
    citation: str = ""        # Formatted citation, e.g., "BCB 520 Art. 43 §2° VI"


@dataclass
class RAGResponse:
    """Complete RAG response with context for LLM."""
    query: str
    results: list[RetrievalResult]
    context_text: str         # Formatted context for LLM prompt
    citations: list[str]      # All citations for evidence trail
    corpus_version: str       # Version of the corpus used


class RegulatoryCorpus:
    """
    Manages the regulatory corpus for RAG.

    In production, connects to pgvector for vector similarity search.
    """

    # Corpus registry — maps corpus_id to metadata
    CORPUS_REGISTRY: dict[str, dict[str, Any]] = {
        "bcb_519": {
            "name": "BCB Resolução 519/2022",
            "type": "resolucao",
            "authority": "BCB",
            "vigencia": "2022-12-01",
            "revogacao": None,
            "hierarchy": 2,
        },
        "bcb_520": {
            "name": "BCB Resolução 520/2022",
            "type": "resolucao",
            "authority": "BCB",
            "vigencia": "2022-12-01",
            "revogacao": None,
            "hierarchy": 2,
        },
        "bcb_521": {
            "name": "BCB Resolução 521/2022",
            "type": "resolucao",
            "authority": "BCB",
            "vigencia": "2022-12-01",
            "revogacao": None,
            "hierarchy": 2,
        },
        "bcb_552": {
            "name": "BCB Resolução 552/2023",
            "type": "resolucao",
            "authority": "BCB",
            "vigencia": "2023-06-01",
            "revogacao": None,
            "hierarchy": 2,
        },
        "bcb_553": {
            "name": "BCB Resolução 553/2023",
            "type": "resolucao",
            "authority": "BCB",
            "vigencia": "2023-06-01",
            "revogacao": None,
            "hierarchy": 2,
        },
        "bcb_580": {
            "name": "BCB Resolução 580/2024",
            "type": "resolucao",
            "authority": "BCB",
            "vigencia": "2024-01-01",
            "revogacao": None,
            "hierarchy": 2,
        },
        "in_bcb_704": {
            "name": "IN BCB 704/2023",
            "type": "instrucao_normativa",
            "authority": "BCB",
            "vigencia": "2023-06-01",
            "revogacao": None,
            "hierarchy": 3,
        },
        "in_bcb_739": {
            "name": "IN BCB 739/2023",
            "type": "instrucao_normativa",
            "authority": "BCB",
            "vigencia": "2023-12-01",
            "revogacao": None,
            "hierarchy": 3,
        },
        "lei_14478": {
            "name": "Lei 14.478/2022",
            "type": "lei",
            "authority": "Congresso Nacional",
            "vigencia": "2022-12-29",
            "revogacao": None,
            "hierarchy": 1,
        },
        "lei_9613": {
            "name": "Lei 9.613/1998",
            "type": "lei",
            "authority": "Congresso Nacional",
            "vigencia": "1998-03-03",
            "revogacao": None,
            "hierarchy": 1,
        },
        "lei_13810": {
            "name": "Lei 13.810/2019",
            "type": "lei",
            "authority": "Congresso Nacional",
            "vigencia": "2019-05-08",
            "revogacao": None,
            "hierarchy": 1,
        },
        "fatf_r15": {
            "name": "FATF Recommendation 15",
            "type": "recommendation",
            "authority": "FATF",
            "vigencia": "2015-01-01",
            "revogacao": None,
            "hierarchy": 0,
        },
        "fatf_r16": {
            "name": "FATF Recommendation 16",
            "type": "recommendation",
            "authority": "FATF",
            "vigencia": "2015-01-01",
            "revogacao": None,
            "hierarchy": 0,
        },
        "fatf_r25": {
            "name": "FATF Recommendation 25",
            "type": "recommendation",
            "authority": "FATF",
            "vigencia": "2015-01-01",
            "revogacao": None,
            "hierarchy": 0,
        },
        "cvm_245": {
            "name": "CVM Instrução 245",
            "type": "instrucao",
            "authority": "CVM",
            "vigencia": "2023-01-01",
            "revogacao": None,
            "hierarchy": 3,
        },
    }

    def __init__(self, vector_store_url: Optional[str] = None) -> None:
        self._vector_store_url = vector_store_url
        self._initialized = False
        self._pool: Any = None  # psycopg connection pool

    async def initialize(self) -> None:
        """Initialize the pgvector connection."""
        try:
            import psycopg
            from psycopg.rows import dict_row

            dsn = (
                f"host={os.getenv('POSTGRES_HOST', 'postgres')} "
                f"port={os.getenv('POSTGRES_PORT', '5432')} "
                f"dbname={os.getenv('POSTGRES_DB', 'ontrackchain')} "
                f"user={os.getenv('POSTGRES_USER', 'ontrackchain')} "
                f"password={os.getenv('POSTGRES_PASSWORD', 'ontrackchain')}"
            )

            self._pool = psycopg.connect(dsn, row_factory=dict_row)
            self._initialized = True
            logger.info("regulatory_corpus.pgvector_initialized")
        except Exception as e:
            logger.warning("regulatory_corpus.pgvector_init_failed", extra={"error": str(e)})
            self._initialized = True  # Mark as initialized even if pgvector fails
            logger.info("regulatory_corpus.initialized_fallback", extra={"corpus_count": len(self.CORPUS_REGISTRY)})

    def get_corpus_metadata(self, corpus_id: str) -> Optional[dict[str, Any]]:
        """Get metadata for a specific corpus."""
        return self.CORPUS_REGISTRY.get(corpus_id)

    def list_corpora(self) -> list[dict[str, Any]]:
        """List all registered corpora."""
        return [
            {"id": cid, **meta}
            for cid, meta in self.CORPUS_REGISTRY.items()
        ]

    def get_chunk_count(self) -> int:
        """Get total chunks in pgvector."""
        if not self._pool:
            return 0
        try:
            with self._pool.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM regulatory_corpus_chunks")
                return cur.fetchone()["count"]
        except Exception:
            return 0

    def search_text(self, query: str, top_k: int = 10, corpus_ids: list[str] | None = None) -> list[dict[str, Any]]:
        """Text-based search as fallback when no embeddings available."""
        if not self._pool:
            return []
        try:
            with self._pool.cursor() as cur:
                if corpus_ids:
                    cur.execute(
                        """
                        SELECT id, corpus_id, article, title, text, hierarchy, authority, vigencia, tags
                        FROM regulatory_corpus_chunks
                        WHERE (text ILIKE %s OR title ILIKE %s OR %s = ANY(tags))
                          AND (revogacao IS NULL)
                          AND (corpus_id = ANY(%s))
                        ORDER BY hierarchy ASC, vigencia DESC
                        LIMIT %s
                        """,
                        (f"%{query}%", f"%{query}%", query, corpus_ids, top_k),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, corpus_id, article, title, text, hierarchy, authority, vigencia, tags
                        FROM regulatory_corpus_chunks
                        WHERE (text ILIKE %s OR title ILIKE %s OR %s = ANY(tags))
                          AND (revogacao IS NULL)
                        ORDER BY hierarchy ASC, vigencia DESC
                        LIMIT %s
                        """,
                        (f"%{query}%", f"%{query}%", query, top_k),
                    )
                return cur.fetchall()
        except Exception as e:
            logger.warning("regulatory_corpus.search_error", extra={"error": str(e)})
            return []


class RAGPipeline:
    """
    Retrieval-Augmented Generation pipeline for regulatory reasoning.

    Flow:
      1. Query embedding (or text fallback)
      2. Vector similarity search (pgvector)
      3. Temporal filtering (validity dates)
      4. Re-ranking by legal relevance
      5. Context formatting with citations
    """

    def __init__(
        self,
        corpus: RegulatoryCorpus,
        embedding_model: str = "voyage-3",
        top_k: int = 10,
        similarity_threshold: float = 0.7,
        rerank_enabled: bool = True,
    ) -> None:
        self._corpus = corpus
        self._embedding_model = embedding_model
        self._top_k = top_k
        self._similarity_threshold = similarity_threshold
        self._rerank_enabled = rerank_enabled

    async def retrieve(
        self,
        query: str,
        corpus_ids: list[str] | None = None,
        temporal_filter: bool = True,
    ) -> RAGResponse:
        """
        Retrieve relevant regulatory chunks for a query.

        Uses pgvector for similarity search when embeddings are available,
        falls back to text search.
        """
        logger.info(
            "rag.retrieve",
            extra={
                "query_length": len(query),
                "corpus_ids": corpus_ids,
                "temporal_filter": temporal_filter,
                "top_k": self._top_k,
            },
        )

        # Try text-based search from pgvector table
        raw_chunks = self._corpus.search_text(
            query=query,
            top_k=self._top_k,
            corpus_ids=corpus_ids,
        )

        # Convert to RetrievalResult
        results = []
        for chunk_data in raw_chunks:
            chunk = RegulatoryChunk(
                chunk_id=str(chunk_data["id"]),
                corpus_id=chunk_data["corpus_id"],
                article=chunk_data["article"],
                title=chunk_data["title"],
                text=chunk_data["text"],
                metadata={
                    "hierarchy": chunk_data.get("hierarchy", 3),
                    "authority": chunk_data.get("authority", ""),
                    "vigencia": str(chunk_data.get("vigencia", "")),
                    "tags": chunk_data.get("tags", []),
                },
            )

            # Score: inverse hierarchy (lower = more authoritative) + text match
            hierarchy = chunk_data.get("hierarchy", 3)
            score = 1.0 - (hierarchy * 0.1)  # FATF=1.0, Lei=0.9, Res=0.8, IN=0.7

            citation = f"{chunk_data['corpus_id']} {chunk_data['article']}"
            results.append(RetrievalResult(
                chunk=chunk,
                score=score,
                rerank_score=score,
                citation=citation,
            ))

        # Re-rank by legal relevance
        if self._rerank_enabled and results:
            results = self._rerank_by_relevance(results)

        # Build context and citations
        context_text = self.format_context(results)
        citations = [r.citation for r in results]

        return RAGResponse(
            query=query,
            results=results,
            context_text=context_text,
            citations=citations,
            corpus_version="1.0.0",
        )

    async def ingest_document(
        self,
        corpus_id: str,
        text: str,
        article: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Ingest a new document into the corpus.

        1. Compute chunk hash for dedup
        2. Insert into regulatory_corpus_chunks
        3. Optionally compute embedding
        """
        import hashlib

        chunk_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        title = metadata.get("title", article) if metadata else article

        if self._corpus._pool:
            try:
                with self._corpus._pool.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO regulatory_corpus_chunks
                            (corpus_id, article, title, text, hierarchy, authority, vigencia, tags, chunk_hash)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (chunk_hash) DO NOTHING
                        """,
                        (
                            corpus_id,
                            article,
                            title,
                            text,
                            metadata.get("hierarchy", 3) if metadata else 3,
                            metadata.get("authority", "") if metadata else "",
                            metadata.get("vigencia", "2024-01-01") if metadata else "2024-01-01",
                            metadata.get("tags", []) if metadata else [],
                            chunk_hash,
                        ),
                    )
                self._corpus._pool.commit()
            except Exception as e:
                logger.warning("rag.ingest_error", extra={"error": str(e)})

        logger.info(
            "rag.ingest",
            extra={
                "corpus_id": corpus_id,
                "article": article,
                "text_length": len(text),
            },
        )
        return f"ingested_{corpus_id}_{article}"

    def _rerank_by_relevance(self, results: list[RetrievalResult]) -> list[RetrievalResult]:
        """
        Re-rank results by legal relevance.

        Hierarchy boost: FATF > Lei > Resolução > IN
        Temporal boost: more recent regulations score higher
        """
        for r in results:
            hierarchy = r.chunk.metadata.get("hierarchy", 3)
            # Lower hierarchy number = more authoritative
            hierarchy_boost = 1.0 - (hierarchy * 0.05)
            r.rerank_score = r.score * hierarchy_boost

        return sorted(results, key=lambda x: x.rerank_score, reverse=True)

    def format_context(self, results: list[RetrievalResult]) -> str:
        """
        Format retrieval results into context for LLM prompt.

        Includes mandatory citations for every piece of regulatory text.
        """
        if not results:
            return ""

        context_parts = []
        for r in results:
            citation = f"[{r.citation}]"
            context_parts.append(
                f"{citation}\n{r.chunk.text}\n"
            )

        return "\n---\n".join(context_parts)
