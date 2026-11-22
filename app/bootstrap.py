"""Construction of the production RAG service graph."""

from __future__ import annotations

from app.services.answer_generator import AnswerGenerator
from app.services.citation_validator import CitationValidator
from app.services.context_builder import ContextBuilder
from app.services.llm_service import LLMService
from app.services.rag_pipeline import RAGPipeline
from app.services.refusal_handler import RefusalHandler
from app.services.retrieval_service import RetrievalService
from app.services.reranker import PassageReranker
from app.assets import ensure_runtime_assets


def build_pipeline() -> RAGPipeline:
    """Load the configured models and connect the persisted indexes."""

    runtime_root = ensure_runtime_assets()
    retrieval = RetrievalService.from_paths(
        db_path=runtime_root / "vector_db",
        bm25_path=runtime_root / "bm25_database.db",
    )
    reranker = PassageReranker.from_model_name()
    llm_service = LLMService()
    return RAGPipeline(
        retrieval_service=retrieval,
        reranker=reranker,
        context_builder=ContextBuilder(),
        answer_generator=AnswerGenerator(llm_service),
        citation_validator=CitationValidator(),
        refusal_handler=RefusalHandler(),
    )
