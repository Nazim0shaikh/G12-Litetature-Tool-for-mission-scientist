"""Structural and semantic validation of generated passage citations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from app.services.answer_generator import Citation
from app.services.retrieval_service import RetrievedPassage


SemanticVerifier = Callable[[str, str], bool]


@dataclass(frozen=True)
class ValidatedCitation:
    """Validation result for one generated citation."""

    passage_id: str
    paper_title: str | None
    section_name: str | None
    supporting_text: str | None
    claim: str
    citation_valid: bool
    structural_valid: bool
    semantic_support: bool | None
    validation_error: str | None = None


class CitationValidator:
    """Validate citation membership and optionally claim support."""

    def __init__(
        self,
        *,
        corpus_lookup: Callable[[str], RetrievedPassage | None] | None = None,
        semantic_verifier: SemanticVerifier | None = None,
    ) -> None:
        self.corpus_lookup = corpus_lookup
        self.semantic_verifier = semantic_verifier

    def validate(
        self,
        citations: Sequence[Citation],
        evidence: Sequence[RetrievedPassage],
    ) -> list[ValidatedCitation]:
        """Validate citations against selected evidence and, if configured, corpus."""

        evidence_by_id = {passage.passage_id: passage for passage in evidence}
        validated: list[ValidatedCitation] = []
        for citation in citations:
            passage = evidence_by_id.get(citation.passage_id)
            if passage is None:
                validated.append(
                    ValidatedCitation(
                        passage_id=citation.passage_id,
                        paper_title=None,
                        section_name=None,
                        supporting_text=None,
                        claim=citation.claim,
                        citation_valid=False,
                        structural_valid=False,
                        semantic_support=None,
                        validation_error="citation is not part of supplied evidence",
                    )
                )
                continue

            source = self.corpus_lookup(citation.passage_id) if self.corpus_lookup else passage
            if source is None:
                validated.append(
                    ValidatedCitation(
                        passage_id=citation.passage_id,
                        paper_title=passage.title,
                        section_name=passage.section_name,
                        supporting_text=passage.text,
                        claim=citation.claim,
                        citation_valid=False,
                        structural_valid=False,
                        semantic_support=None,
                        validation_error="citation was not found in the original corpus",
                    )
                )
                continue

            semantic_support = (
                self.semantic_verifier(citation.claim, source.text)
                if self.semantic_verifier
                else None
            )
            citation_valid = semantic_support is not False
            validated.append(
                ValidatedCitation(
                    passage_id=citation.passage_id,
                    paper_title=source.title,
                    section_name=source.section_name,
                    supporting_text=source.text,
                    claim=citation.claim,
                    citation_valid=citation_valid,
                    structural_valid=True,
                    semantic_support=semantic_support,
                    validation_error=(
                        None
                        if citation_valid
                        else "passage does not semantically support the claim"
                    ),
                )
            )
        return validated
