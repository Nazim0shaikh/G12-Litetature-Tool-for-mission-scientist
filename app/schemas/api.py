"""Pydantic schemas for the public API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class CitationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    passage_id: str
    claim: str
    citation_valid: bool


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    passage_id: str
    paper_id: str
    title: str
    section_name: str
    text: str


class AskResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    question: str
    status: str
    answer: str
    citations: list[CitationResponse]
    evidence: list[EvidenceResponse]
    retrieval_metadata: dict[str, Any]
    processing_metadata: dict[str, float]


class HealthResponse(BaseModel):
    status: str
    llm_configured: bool


class ConfigResponse(BaseModel):
    provider: str
    model: str
    max_question_length: int
    cors_origins: list[str]
