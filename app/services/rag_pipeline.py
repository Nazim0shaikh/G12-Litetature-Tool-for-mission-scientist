"""End-to-end orchestration of the evidence-grounded RAG pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import time
from typing import Any

from app.services.answer_generator import AnswerGenerator, GeneratedAnswer
from app.services.citation_validator import CitationValidator, ValidatedCitation
from app.services.context_builder import ContextBuilder
from app.services.query_processor import process_question
from app.services.refusal_handler import EvidenceStatus, RefusalHandler
from app.services.retrieval_service import RetrievalService, RetrievedPassage
from app.services.reranker import PassageReranker


@dataclass(frozen=True)
class ProcessingMetadata:
    retrieval_time: float
    reranking_time: float
    generation_time: float
    total_time: float


class RAGPipeline:
    """Coordinate all core services while keeping diagnostic details internal."""

    def __init__(
        self,
        retrieval_service: RetrievalService,
        reranker: PassageReranker,
        context_builder: ContextBuilder,
        answer_generator: AnswerGenerator,
        citation_validator: CitationValidator,
        refusal_handler: RefusalHandler,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.reranker = reranker
        self.context_builder = context_builder
        self.answer_generator = answer_generator
        self.citation_validator = citation_validator
        self.refusal_handler = refusal_handler

    def answer_question(self, question: str) -> dict[str, Any]:
        """Return a structured answer with evidence and measured timings."""

        processed = process_question(question)
        started = time.perf_counter()

        retrieval_started = time.perf_counter()
        hybrid = self.retrieval_service.hybrid_retrieve(processed.normalized)
        retrieval_time = time.perf_counter() - retrieval_started

        reranking_started = time.perf_counter()
        reranked = self.reranker.rerank(processed.normalized, hybrid)
        reranking_time = time.perf_counter() - reranking_started

        context = self.context_builder.build(processed.normalized, reranked)
        generation_started = time.perf_counter()
        generated = self.answer_generator.generate(context)
        generation_time = time.perf_counter() - generation_started

        validated = self.citation_validator.validate(generated.citations, context.passages)
        assessment = self.refusal_handler.assess(
            context.passages,
            validated,
            llm_insufficient_evidence=generated.insufficient_evidence,
            conflicting_evidence=generated.status == "conflicting_evidence",
        )

        status = assessment.status.value
        if status == EvidenceStatus.INSUFFICIENT.value:
            answer = (
                "The available research passages do not provide sufficient evidence "
                "to answer this question reliably."
            )
        else:
            answer = generated.answer

        metadata = ProcessingMetadata(
            retrieval_time=retrieval_time,
            reranking_time=reranking_time,
            generation_time=generation_time,
            total_time=time.perf_counter() - started,
        )
        return {
            "question": processed.original,
            "status": status,
            "answer": answer,
            "citations": [self._citation_dict(citation) for citation in validated],
            "evidence": [self._passage_dict(passage) for passage in context.passages],
            "retrieval_metadata": {
                "dense_candidates": self.retrieval_service.config.dense_k,
                "bm25_candidates": self.retrieval_service.config.bm25_k,
                "hybrid_candidates": len(hybrid),
                "reranked_candidates": len(reranked),
                "omitted_passages": list(context.omitted_passage_ids),
            },
            "processing_metadata": asdict(metadata),
            "reasoning_summary": generated.reasoning_summary,
            "evidence_reasons": list(assessment.reasons),
        }

    @staticmethod
    def _passage_dict(passage: RetrievedPassage) -> dict[str, Any]:
        return {
            "passage_id": passage.passage_id,
            "paper_id": passage.paper_id,
            "title": passage.title,
            "section_name": passage.section_name,
            "text": passage.text,
            "dense_rank": passage.dense_rank,
            "bm25_rank": passage.bm25_rank,
            "rrf_score": passage.rrf_score,
            "reranker_score": passage.reranker_score,
        }

    @staticmethod
    def _citation_dict(citation: ValidatedCitation) -> dict[str, Any]:
        return {
            "passage_id": citation.passage_id,
            "paper_title": citation.paper_title,
            "section_name": citation.section_name,
            "supporting_text": citation.supporting_text,
            "claim": citation.claim,
            "citation_valid": citation.citation_valid,
            "structural_valid": citation.structural_valid,
            "semantic_support": citation.semantic_support,
            "validation_error": citation.validation_error,
        }
