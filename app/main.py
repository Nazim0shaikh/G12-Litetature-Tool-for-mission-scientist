"""FastAPI application for the G12 research assistant."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import AppConfig
from app.schemas.api import (
    AskResponse,
    ConfigResponse,
    HealthResponse,
    QuestionRequest,
)
from app.services.llm_service import LLMConfig, LLMService
from app.services.rag_pipeline import RAGPipeline
from app.services.corpus_service import CorpusService


def create_app(
    pipeline: RAGPipeline | None = None,
    *,
    llm_service: LLMService | None = None,
    config: AppConfig | None = None,
    corpus_service: CorpusService | None = None,
    auto_initialize: bool = False,
) -> FastAPI:
    """Create the API without eagerly loading retrieval models."""

    app_config = config or AppConfig.from_env()
    app = FastAPI(title="G12 AI Research Assistant", version="1.0.0")
    allowed_origins = tuple(
        dict.fromkeys(
            (*app_config.cors_origins,
             "http://localhost:5173",
             "http://127.0.0.1:5173")
        )
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    configured_llm = llm_service or LLMService()
    app.state.pipeline = pipeline
    app.state.llm_service = configured_llm
    app.state.config = app_config
    app.state.corpus_service = corpus_service or CorpusService()

    @app.post("/api/v1/ask", response_model=AskResponse)
    def ask(request: QuestionRequest) -> dict[str, Any]:
        if app.state.pipeline is None:
            if not auto_initialize:
                raise HTTPException(status_code=503, detail="RAG pipeline is not initialized")
            try:
                from app.bootstrap import build_pipeline

                app.state.pipeline = build_pipeline()
            except (ImportError, OSError, RuntimeError, ValueError) as exc:
                raise HTTPException(status_code=503, detail="RAG pipeline is unavailable") from exc
        try:
            return app.state.pipeline.answer_question(request.question)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/v1/retrieve")
    def retrieve(request: QuestionRequest) -> dict[str, Any]:
        if app.state.pipeline is None:
            if not auto_initialize:
                raise HTTPException(status_code=503, detail="RAG pipeline is not initialized")
            try:
                from app.bootstrap import build_pipeline

                app.state.pipeline = build_pipeline()
            except (ImportError, OSError, RuntimeError, ValueError) as exc:
                raise HTTPException(status_code=503, detail="RAG pipeline is unavailable") from exc
        try:
            processed = app.state.pipeline.retrieval_service.hybrid_retrieve(request.question)
            reranked = app.state.pipeline.reranker.rerank(request.question, processed)
            return {
                "question": request.question,
                "evidence": [
                    app.state.pipeline._passage_dict(passage) for passage in reranked
                ],
            }
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/api/v1/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            llm_configured=app.state.llm_service.is_configured(),
        )

    @app.get("/api/v1/config", response_model=ConfigResponse)
    def safe_config() -> ConfigResponse:
        llm_config = app.state.llm_service.config
        return ConfigResponse(
            provider=llm_config.provider,
            model=llm_config.model,
            max_question_length=app_config.max_question_length,
            cors_origins=list(app_config.cors_origins),
        )

    @app.get("/api/v1/paper/{paper_id}")
    def paper(paper_id: str) -> dict[str, Any]:
        try:
            result = app.state.corpus_service.get_paper(paper_id)
        except (OSError, ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=503, detail="corpus is unavailable") from exc
        if result is None:
            raise HTTPException(status_code=404, detail="paper not found")
        return result

    return app


app = create_app(auto_initialize=True)
