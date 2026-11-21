import pytest

from app.services.query_processor import ProcessedQuestion, process_question


def test_process_question_preserves_original_and_normalizes_whitespace() -> None:
    question = "  What is   BERT?\nHow does it handle 2024 data?  "

    result = process_question(question)

    assert result == ProcessedQuestion(
        original=question,
        normalized="What is BERT? How does it handle 2024 data?",
    )


def test_process_question_preserves_technical_terms_and_punctuation() -> None:
    question = "Does QASPER-RAG improve BioBERT's F1-score by 3.14%?"

    result = process_question(question)

    assert result.normalized == question


@pytest.mark.parametrize("question", ["", "   ", "\n\t"])
def test_process_question_rejects_empty_input(question: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        process_question(question)


def test_process_question_rejects_non_string_input() -> None:
    with pytest.raises(TypeError, match="must be a string"):
        process_question(None)  # type: ignore[arg-type]
