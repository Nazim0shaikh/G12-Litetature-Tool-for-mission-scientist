from app.services.citation_validator import ValidatedCitation
from app.services.refusal_handler import EvidenceStatus, RefusalHandler, SufficiencyConfig
from app.services.retrieval_service import RetrievedPassage


def passage() -> RetrievedPassage:
    return RetrievedPassage(
        passage_id="p1",
        paper_id="paper",
        title="Paper",
        section_name="Results",
        text="Evidence",
    )


def citation(*, valid: bool, semantic: bool | None) -> ValidatedCitation:
    return ValidatedCitation(
        passage_id="p1",
        paper_title="Paper",
        section_name="Results",
        supporting_text="Evidence",
        claim="Claim",
        citation_valid=valid,
        structural_valid=valid,
        semantic_support=semantic,
    )


def test_refuses_when_no_evidence_is_selected() -> None:
    result = RefusalHandler().assess([])

    assert result.status is EvidenceStatus.INSUFFICIENT
    assert result.evidence_count == 0


def test_accepts_answer_with_structurally_valid_unassessed_citation() -> None:
    result = RefusalHandler().assess([passage()], [citation(valid=True, semantic=None)])

    assert result.status is EvidenceStatus.ANSWERABLE
    assert result.supported_citation_count == 1


def test_marks_conflicting_evidence_explicitly() -> None:
    result = RefusalHandler().assess(
        [passage()], [citation(valid=True, semantic=True)], conflicting_evidence=True
    )

    assert result.status is EvidenceStatus.CONFLICTING


def test_refuses_when_llm_reports_insufficient_evidence() -> None:
    result = RefusalHandler().assess(
        [passage()], [citation(valid=True, semantic=True)], llm_insufficient_evidence=True
    )

    assert result.status is EvidenceStatus.INSUFFICIENT


def test_can_apply_ranking_floor_when_scores_are_available() -> None:
    low = passage()
    low.reranker_score = -1.0
    result = RefusalHandler(SufficiencyConfig(minimum_reranker_score=0.0)).assess(
        [low], [citation(valid=True, semantic=True)]
    )

    assert result.status is EvidenceStatus.INSUFFICIENT
