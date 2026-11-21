import pytest

from app.services.context_builder import ContextBuilder, ContextConfig
from app.services.retrieval_service import RetrievedPassage


def make_passage(
    passage_id: str,
    text: str,
    paper_id: str = "paper",
) -> RetrievedPassage:
    return RetrievedPassage(
        passage_id=passage_id,
        paper_id=paper_id,
        title="Research paper",
        section_name="Results",
        text=text,
    )


def test_context_builder_deduplicates_and_limits_paper_repetition() -> None:
    passages = [
        make_passage("a", "first"),
        make_passage("a", "duplicate"),
        make_passage("b", "second"),
        make_passage("c", "third"),
        make_passage("d", "other paper", paper_id="other"),
    ]

    result = ContextBuilder(
        ContextConfig(max_context_chars=5000, max_passages=10, max_passages_per_paper=2)
    ).build("What is the result?", passages)

    assert [passage.passage_id for passage in result.passages] == ["a", "b", "d"]
    assert result.omitted_passage_ids == ("a", "c")
    assert result.context.count("Passage ID: a") == 1
    assert "[PASSAGE 1]" in result.context


def test_context_builder_omits_whole_passages_when_context_limit_is_reached() -> None:
    passages = [make_passage("a", "x" * 100), make_passage("b", "y" * 100)]

    result = ContextBuilder(ContextConfig(max_context_chars=180)).build(
        "Question", passages
    )

    assert len(result.passages) == 0
    assert result.omitted_passage_ids == ("a", "b")
    assert "x" not in result.context
    assert "y" not in result.context


def test_context_builder_rejects_empty_question() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        ContextBuilder().build(" ", [])
