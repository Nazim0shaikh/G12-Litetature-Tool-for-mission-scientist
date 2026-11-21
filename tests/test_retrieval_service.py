import sqlite3

import numpy as np

from app.services.retrieval_service import RetrievalConfig, RetrievalService, fuse_rankings


def test_fuse_rankings_deduplicates_and_preserves_source_ranks() -> None:
    fused = fuse_rankings(["a", "shared"], ["shared", "b"], rrf_k=60, limit=3)

    assert [row[0] for row in fused] == ["shared", "a", "b"]
    assert fused[0][2:] == (2, 1)


def test_bm25_retrieval_returns_corpus_metadata() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE VIRTUAL TABLE corpus_fts USING fts5(id UNINDEXED, title, section_name, text)"
    )
    connection.execute(
        "INSERT INTO corpus_fts VALUES (?, ?, ?, ?)",
        ("paper_00001", "A Paper", "Methods", "neural retrieval evidence"),
    )
    service = RetrievalService(
        collection=None,  # type: ignore[arg-type]
        embedding_model=None,  # type: ignore[arg-type]
        sqlite_connection=connection,
        config=RetrievalConfig(bm25_k=5),
    )

    results = service.bm25_retrieve("neural retrieval")

    assert len(results) == 1
    assert results[0].passage_id == "paper_00001"
    assert results[0].paper_id == "paper"
    assert results[0].title == "A Paper"
    assert results[0].bm25_rank == 1


def test_dense_retrieval_preserves_metadata() -> None:
    class Model:
        def encode(self, sentences, *, normalize_embeddings, show_progress_bar):
            return np.array([[0.1, 0.2]])

    class Collection:
        def query(self, **kwargs):
            return {
                "ids": [["paper_00001"]],
                "documents": [["passage text"]],
                "metadatas": [[
                    {"title": "A Paper", "section_name": "Abstract", "paper_id": "paper"}
                ]],
                "distances": [[0.1]],
            }

    service = RetrievalService(
        collection=Collection(),
        embedding_model=Model(),
        sqlite_connection=sqlite3.connect(":memory:"),
    )

    result = service.dense_retrieve("What is this?")

    assert result[0].passage_id == "paper_00001"
    assert result[0].dense_rank == 1
    assert result[0].text == "passage text"
