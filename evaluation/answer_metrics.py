"""Deterministic answer, citation, and refusal evaluation metrics."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Sequence


_TOKEN = re.compile(r"\w+")


@dataclass(frozen=True)
class AnswerMetrics:
    """Aggregate lexical diagnostics; these are not a substitute for expert review."""

    answerability_accuracy: float
    answer_relevance: float
    unsupported_claim_rate: float
    evaluated_answers: int


@dataclass(frozen=True)
class CitationMetrics:
    citation_existence_rate: float
    citation_precision: float
    citation_recall: float
    evaluated_citations: int


@dataclass(frozen=True)
class RefusalMetrics:
    correct_refusal_rate: float
    false_refusal_rate: float
    incorrect_answering_rate: float
    evaluated_questions: int


def answer_relevance(reference: str, generated: str) -> float:
    """Return token-set overlap, useful as a transparent diagnostic."""

    reference_tokens = set(_TOKEN.findall(reference.lower()))
    generated_tokens = set(_TOKEN.findall(generated.lower()))
    if not reference_tokens:
        return 0.0
    return len(reference_tokens & generated_tokens) / len(reference_tokens)


def evaluate_answers(
    predictions: Sequence[dict[str, object]],
) -> AnswerMetrics:
    """Evaluate answerability and lexical relevance from recorded predictions.

    Each item must contain ``reference_answer``, ``answer``,
    ``reference_answerable``, and ``predicted_status``. Optional
    ``unsupported_claim`` defaults to false.
    """

    if not predictions:
        raise ValueError("predictions must not be empty")
    answerability_hits = 0
    relevance_scores: list[float] = []
    unsupported = 0
    for prediction in predictions:
        reference_answerable = bool(prediction["reference_answerable"])
        predicted_answerable = prediction["predicted_status"] != "insufficient_evidence"
        answerability_hits += reference_answerable == predicted_answerable
        if reference_answerable:
            relevance_scores.append(
                answer_relevance(
                    str(prediction["reference_answer"]),
                    str(prediction["answer"]),
                )
            )
        unsupported += bool(prediction.get("unsupported_claim", False))
    count = len(predictions)
    return AnswerMetrics(
        answerability_accuracy=answerability_hits / count,
        answer_relevance=(
            sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
        ),
        unsupported_claim_rate=unsupported / count,
        evaluated_answers=count,
    )


def evaluate_citations(
    predictions: Sequence[dict[str, object]],
) -> CitationMetrics:
    """Evaluate citation existence, precision, and recall from ID sets."""

    if not predictions:
        raise ValueError("predictions must not be empty")
    existing = 0
    predicted_total = 0
    relevant_predicted = 0
    relevant_total = 0
    for prediction in predictions:
        predicted = set(prediction.get("predicted_citations", ()))
        available = set(prediction.get("available_evidence", ()))
        reference = set(prediction.get("reference_citations", ()))
        existing += len(predicted & available)
        predicted_total += len(predicted)
        relevant_predicted += len(predicted & reference)
        relevant_total += len(reference)
    return CitationMetrics(
        citation_existence_rate=existing / predicted_total if predicted_total else 0.0,
        citation_precision=relevant_predicted / predicted_total if predicted_total else 0.0,
        citation_recall=relevant_predicted / relevant_total if relevant_total else 0.0,
        evaluated_citations=predicted_total,
    )


def evaluate_refusals(
    reference_answerable: Sequence[bool],
    predicted_status: Sequence[str],
) -> RefusalMetrics:
    """Measure refusal behaviour with explicit answerable/unanswerable labels."""

    if not reference_answerable or len(reference_answerable) != len(predicted_status):
        raise ValueError("reference and prediction sequences must have equal non-zero length")
    correct_refusals = false_refusals = incorrect_answers = 0
    unanswerable = 0
    answerable = 0
    for expected_answerable, status in zip(reference_answerable, predicted_status):
        refused = status == "insufficient_evidence"
        if expected_answerable:
            answerable += 1
            false_refusals += refused
        else:
            unanswerable += 1
            correct_refusals += refused
            incorrect_answers += not refused
    count = len(reference_answerable)
    return RefusalMetrics(
        correct_refusal_rate=correct_refusals / unanswerable if unanswerable else 0.0,
        false_refusal_rate=false_refusals / answerable if answerable else 0.0,
        incorrect_answering_rate=incorrect_answers / unanswerable if unanswerable else 0.0,
        evaluated_questions=count,
    )
