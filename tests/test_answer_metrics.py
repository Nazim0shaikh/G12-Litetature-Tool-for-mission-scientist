from evaluation.answer_metrics import (
    evaluate_answers,
    evaluate_citations,
    evaluate_refusals,
)


def test_answer_metrics_report_answerability_and_relevance() -> None:
    result = evaluate_answers(
        [
            {
                "reference_answer": "neural retrieval improves accuracy",
                "answer": "neural retrieval improves accuracy",
                "reference_answerable": True,
                "predicted_status": "answered",
            },
            {
                "reference_answer": "",
                "answer": "I do not know",
                "reference_answerable": False,
                "predicted_status": "insufficient_evidence",
            },
        ]
    )

    assert result.answerability_accuracy == 1.0
    assert result.answer_relevance == 1.0
    assert result.unsupported_claim_rate == 0.0


def test_citation_metrics_use_available_and_reference_id_sets() -> None:
    result = evaluate_citations(
        [
            {
                "predicted_citations": ["p1", "fake"],
                "available_evidence": ["p1"],
                "reference_citations": ["p1"],
            }
        ]
    )

    assert result.citation_existence_rate == 0.5
    assert result.citation_precision == 0.5
    assert result.citation_recall == 1.0


def test_refusal_metrics_distinguish_false_refusals_and_wrong_answers() -> None:
    result = evaluate_refusals(
        [True, False, False],
        ["answered", "insufficient_evidence", "answered"],
    )

    assert result.correct_refusal_rate == 0.5
    assert result.false_refusal_rate == 0.0
    assert result.incorrect_answering_rate == 0.5
