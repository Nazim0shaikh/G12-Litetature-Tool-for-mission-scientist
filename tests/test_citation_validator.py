from app.services.answer_generator import Citation
from app.services.citation_validator import CitationValidator
from app.services.retrieval_service import RetrievedPassage


def evidence() -> RetrievedPassage:
    return RetrievedPassage(
        passage_id="paper_00001",
        paper_id="paper",
        title="Research paper",
        section_name="Results",
        text="The treatment improved accuracy.",
    )


def test_validator_checks_membership_and_preserves_source_fields() -> None:
    result = CitationValidator().validate(
        [Citation("paper_00001", "The treatment improved accuracy.")],
        [evidence()],
    )[0]

    assert result.citation_valid is True
    assert result.structural_valid is True
    assert result.semantic_support is None
    assert result.paper_title == "Research paper"
    assert result.supporting_text == "The treatment improved accuracy."


def test_validator_rejects_citation_not_in_evidence() -> None:
    result = CitationValidator().validate(
        [Citation("fake", "Unsupported claim")], [evidence()]
    )[0]

    assert result.citation_valid is False
    assert result.structural_valid is False
    assert "not part of supplied evidence" in result.validation_error


def test_validator_separates_semantic_support_from_existence() -> None:
    result = CitationValidator(
        semantic_verifier=lambda claim, text: False
    ).validate([Citation("paper_00001", "The study used a placebo.")], [evidence()])[0]

    assert result.structural_valid is True
    assert result.semantic_support is False
    assert result.citation_valid is False
    assert "semantically support" in result.validation_error


def test_validator_can_verify_against_original_corpus() -> None:
    result = CitationValidator(
        corpus_lookup=lambda passage_id: None
    ).validate([Citation("paper_00001", "Claim")], [evidence()])[0]

    assert result.citation_valid is False
    assert result.structural_valid is False
    assert "original corpus" in result.validation_error
