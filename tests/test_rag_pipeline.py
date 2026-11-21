import sqlite3

import numpy as np

from app.services.answer_generator import AnswerGenerator
from app.services.citation_validator import CitationValidator
from app.services.context_builder import ContextBuilder
from app.services.rag_pipeline import RAGPipeline
from app.services.refusal_handler import RefusalHandler
from app.services.retrieval_service import RetrievalConfig, RetrievalService
from app.services.reranker import PassageReranker, RerankerConfig


class FakeEmbeddingModel:
    def encode(self, sentences, *, normalize_embeddings, show_progress_bar):
        return np.array([[0.1, 0.2]])


class FakeCollection:
    def query(self, **kwargs):
        return {
            "ids": [["paper_00001"]],
            "documents": [["The treatment improved accuracy."]],
            "metadatas": [[
                {"title": "Paper", "section_name": "Results", "paper_id": "paper"}
            ]],
        }


class FakeRerankerModel:
    def predict(self, pairs, *, batch_size, show_progress_bar):
        return [0.8]


class FakeLLM:
    def complete(self, system_prompt, user_prompt):
        return (
            '{"status":"answered","answer":"Accuracy improved.",'
            '"citations":[{"passage_id":"paper_00001","claim":"Accuracy improved."}],'
            '"reasoning_summary":"The Results passage states this.",'
            '"insufficient_evidence":false}'
        )


def test_pipeline_returns_grounded_answer_with_timings() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE VIRTUAL TABLE corpus_fts USING fts5(id UNINDEXED, title, section_name, text)"
    )
    retrieval = RetrievalService(
        collection=FakeCollection(),
        embedding_model=FakeEmbeddingModel(),
        sqlite_connection=connection,
        config=RetrievalConfig(dense_k=1, bm25_k=1, hybrid_k=1),
    )
    pipeline = RAGPipeline(
        retrieval,
        PassageReranker(FakeRerankerModel(), RerankerConfig(top_k=1)),
        ContextBuilder(),
        AnswerGenerator(FakeLLM()),
        CitationValidator(),
        RefusalHandler(),
    )

    result = pipeline.answer_question("What changed?")

    assert result["question"] == "What changed?"
    assert result["status"] == "answered"
    assert result["answer"] == "Accuracy improved."
    assert result["citations"][0]["citation_valid"] is True
    assert result["evidence"][0]["passage_id"] == "paper_00001"
    assert result["processing_metadata"]["total_time"] >= 0
