"""Evidence sufficiency and refusal classification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from app.services.citation_validator import ValidatedCitation
from app.services.retrieval_service import RetrievedPassage


class EvidenceStatus(str, Enum):
    ANSWERABLE = "answered"
    PARTIALLY_ANSWERABLE = "partially_answered"
    INSUFFICIENT = "insufficient_evidence"
    CONFLICTING = "conflicting_evidence"


@dataclass(frozen=True)
class SufficiencyConfig:
    """Conservative, configurable evidence sufficiency rules."""

    min_evidence_passages: int = 1
    min_supported_citations_for_answer: int = 1
    minimum_reranker_score: float | None = None

    def __post_init__(self) -> None:
        if self.min_evidence_passages <= 0:
            raise ValueError("min_evidence_passages must be positive")
        if self.min_supported_citations_for_answer <= 0:
            raise ValueError("minimum supported citations must be positive")


@dataclass(frozen=True)
class SufficiencyAssessment:
    """Classification and reasons used by the orchestrator and UI."""

    status: EvidenceStatus
    reasons: tuple[str, ...]
    evidence_count: int
    supported_citation_count: int


class RefusalHandler:
    """Classify whether generated evidence supports a reliable response."""

    def __init__(self, config: SufficiencyConfig | None = None) -> None:
        self.config = config or SufficiencyConfig()

    def assess(
        self,
        evidence: Sequence[RetrievedPassage],
        citations: Sequence[ValidatedCitation] = (),
        *,
        llm_insufficient_evidence: bool = False,
        conflicting_evidence: bool = False,
    ) -> SufficiencyAssessment:
        """Assess evidence without treating any raw score as calibrated confidence."""

        reasons: list[str] = []
        supported_count = sum(
            citation.citation_valid and citation.semantic_support is not False
            for citation in citations
        )

        if len(evidence) < self.config.min_evidence_passages:
            reasons.append("fewer than the minimum number of evidence passages were selected")
            return self._assessment(
                EvidenceStatus.INSUFFICIENT, reasons, evidence, supported_count
            )

        if self.config.minimum_reranker_score is not None:
            scored = [
                passage.reranker_score
                for passage in evidence
                if passage.reranker_score is not None
            ]
            if scored and max(scored) < self.config.minimum_reranker_score:
                reasons.append("retrieved evidence did not meet the configured ranking floor")
                return self._assessment(
                    EvidenceStatus.INSUFFICIENT, reasons, evidence, supported_count
                )

        if conflicting_evidence:
            reasons.append("evidence contains conflicting findings")
            return self._assessment(
                EvidenceStatus.CONFLICTING, reasons, evidence, supported_count
            )

        if llm_insufficient_evidence:
            reasons.append("the answer generator judged the evidence insufficient")
            return self._assessment(
                EvidenceStatus.INSUFFICIENT, reasons, evidence, supported_count
            )

        if supported_count == 0:
            reasons.append("no generated citation was validated as supporting the answer")
            return self._assessment(
                EvidenceStatus.INSUFFICIENT, reasons, evidence, supported_count
            )

        if supported_count < self.config.min_supported_citations_for_answer:
            reasons.append("only part of the generated answer has supported citations")
            return self._assessment(
                EvidenceStatus.PARTIALLY_ANSWERABLE, reasons, evidence, supported_count
            )

        reasons.append("selected evidence has validated support for the generated answer")
        return self._assessment(
            EvidenceStatus.ANSWERABLE, reasons, evidence, supported_count
        )

    @staticmethod
    def _assessment(
        status: EvidenceStatus,
        reasons: list[str],
        evidence: Sequence[RetrievedPassage],
        supported_count: int,
    ) -> SufficiencyAssessment:
        return SufficiencyAssessment(
            status=status,
            reasons=tuple(reasons),
            evidence_count=len(evidence),
            supported_citation_count=supported_count,
        )
