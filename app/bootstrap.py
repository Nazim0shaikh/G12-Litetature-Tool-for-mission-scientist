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


def build_pipeline() -> RAGPipeline:
    """Load the configured models and connect the persisted indexes."""

    retrieval = RetrievalService.from_paths()
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
