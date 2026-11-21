"""Dense, BM25 and hybrid retrieval over the existing QASPER indexes."""

from __future__ import annotations

from dataclasses import dataclass
import re
import sqlite3
from pathlib import Path
from typing import Any, Protocol, Sequence


class EmbeddingModel(Protocol):
    def encode(
        self,
        sentences: Sequence[str],
        *,
        normalize_embeddings: bool,
        show_progress_bar: bool,
    ) -> Any:
        ...


class ChromaCollection(Protocol):
    def query(self, **kwargs: Any) -> dict[str, Any]:
        ...

    def get(self, **kwargs: Any) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class RetrievalConfig:
    """Configurable retrieval limits and RRF constant."""

    dense_k: int = 100
    bm25_k: int = 100
    hybrid_k: int = 50
    rrf_k: int = 60

    def __post_init__(self) -> None:
        if any(value <= 0 for value in (self.dense_k, self.bm25_k, self.hybrid_k)):
            raise ValueError("retrieval limits must be positive")
        if self.rrf_k < 0:
            raise ValueError("rrf_k must not be negative")


@dataclass
class RetrievedPassage:
    """A corpus passage and the rankings that produced it."""

    passage_id: str
    paper_id: str
    title: str
    section_name: str
    text: str
    dense_rank: int | None = None
    bm25_rank: int | None = None
    rrf_score: float = 0.0
    reranker_score: float | None = None


def fuse_rankings(
    dense_ids: Sequence[str],
    bm25_ids: Sequence[str],
    *,
    rrf_k: int = 60,
    limit: int = 50,
) -> list[tuple[str, float, int | None, int | None]]:
    """Fuse two ranked ID lists while retaining source ranks."""

    if rrf_k < 0 or limit <= 0:
        raise ValueError("rrf_k must be non-negative and limit must be positive")

    ranks: dict[str, dict[str, int | None]] = {}
    scores: dict[str, float] = {}
    for rank, passage_id in enumerate(dense_ids, start=1):
        ranks.setdefault(passage_id, {"dense": rank, "bm25": None})
        scores[passage_id] = scores.get(passage_id, 0.0) + 1 / (rrf_k + rank)
    for rank, passage_id in enumerate(bm25_ids, start=1):
        ranks.setdefault(passage_id, {"dense": None, "bm25": rank})
        ranks[passage_id]["bm25"] = rank
        scores[passage_id] = scores.get(passage_id, 0.0) + 1 / (rrf_k + rank)

    fused = sorted(
        scores,
        key=lambda passage_id: (-scores[passage_id], passage_id),
    )
    return [
        (
            passage_id,
            scores[passage_id],
            ranks[passage_id]["dense"],
            ranks[passage_id]["bm25"],
        )
        for passage_id in fused[:limit]
    ]


class RetrievalService:
    """Reusable adapter around the pre-built Chroma and SQLite indexes."""

    def __init__(
        self,
        *,
        collection: ChromaCollection,
        embedding_model: EmbeddingModel,
        sqlite_connection: sqlite3.Connection,
        config: RetrievalConfig | None = None,
    ) -> None:
        self.collection = collection
        self.embedding_model = embedding_model
        self.connection = sqlite_connection
        self.config = config or RetrievalConfig()

    @classmethod
    def from_paths(
        cls,
        *,
        db_path: str | Path = "vector_db",
        bm25_path: str | Path = "bm25_database.db",
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        config: RetrievalConfig | None = None,
    ) -> "RetrievalService":
        """Create a service using the project's existing persisted indexes."""

        import chromadb
        from sentence_transformers import SentenceTransformer

        client = chromadb.PersistentClient(path=str(db_path))
        collection = client.get_collection("qasper_passages")
        connection = sqlite3.connect(str(bm25_path), check_same_thread=False)
        return cls(
            collection=collection,
            embedding_model=SentenceTransformer(model_name),
            sqlite_connection=connection,
            config=config,
        )

    def dense_retrieve(self, question: str) -> list[RetrievedPassage]:
        """Retrieve and hydrate the top dense passages."""

        if not question.strip():
            return []
        embedding = self.embedding_model.encode(
            [question],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        result = self.collection.query(
            query_embeddings=[embedding[0].tolist()],
            n_results=self.config.dense_k,
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        passages: list[RetrievedPassage] = []
        for rank, (passage_id, text, metadata) in enumerate(
            zip(ids, documents, metadatas), start=1
        ):
            passages.append(self._passage(passage_id, text, metadata, dense_rank=rank))
        return passages

    def bm25_retrieve(self, question: str) -> list[RetrievedPassage]:
        """Retrieve keyword matches using the existing FTS5 index."""

        terms = list(dict.fromkeys(re.findall(r"\w+", question.lower())))
        if not terms:
            return []
        fts_query = " OR ".join(f'"{term.replace(chr(34), chr(34) * 2)}"' for term in terms)
        rows = self.connection.execute(
            """
            SELECT id, title, section_name, text
            FROM corpus_fts
            WHERE corpus_fts MATCH ?
            ORDER BY bm25(corpus_fts, 0.0, 2.0, 1.0, 1.0) ASC
            LIMIT ?
            """,
            (fts_query, self.config.bm25_k),
        ).fetchall()
        return [
            self._passage(
                row[0],
                row[3],
                {"title": row[1], "section_name": row[2]},
                bm25_rank=rank,
            )
            for rank, row in enumerate(rows, start=1)
        ]

    def hybrid_retrieve(self, question: str) -> list[RetrievedPassage]:
        """Fuse dense and BM25 rankings and hydrate one copy per passage."""

        dense = self.dense_retrieve(question)
        bm25 = self.bm25_retrieve(question)
        dense_by_id = {passage.passage_id: passage for passage in dense}
        bm25_by_id = {passage.passage_id: passage for passage in bm25}
        fused = fuse_rankings(
            [passage.passage_id for passage in dense],
            [passage.passage_id for passage in bm25],
            rrf_k=self.config.rrf_k,
            limit=self.config.hybrid_k,
        )
        passages: list[RetrievedPassage] = []
        for passage_id, score, dense_rank, bm25_rank in fused:
            source = dense_by_id.get(passage_id) or bm25_by_id[passage_id]
            source.dense_rank = dense_rank
            source.bm25_rank = bm25_rank
            source.rrf_score = score
            passages.append(source)
        return passages

    @staticmethod
    def _passage(
        passage_id: str,
        text: str,
        metadata: dict[str, Any],
        *,
        dense_rank: int | None = None,
        bm25_rank: int | None = None,
    ) -> RetrievedPassage:
        return RetrievedPassage(
            passage_id=passage_id,
            paper_id=str(metadata.get("paper_id") or passage_id.rsplit("_", 1)[0]),
            title=str(metadata.get("title") or ""),
            section_name=str(metadata.get("section_name") or ""),
            text=text,
            dense_rank=dense_rank,
            bm25_rank=bm25_rank,
        )
