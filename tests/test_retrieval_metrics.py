import pytest

from evaluation.retrieval_metrics import evaluate_retrieval


def test_retrieval_metrics_match_ranked_relevance() -> None:
    metrics = evaluate_retrieval(
        {"q1": ["wrong", "relevant", "other"]},
        {"q1": {"relevant": 1.0, "other": 2.0}},
        candidate_results={"q1": ["relevant", "other"]},
    )

    assert metrics.evaluated_queries == 1
    assert metrics.recall_at_5 == 1.0
    assert metrics.recall_at_10 == 1.0
    assert metrics.mrr_at_10 == 0.5
    assert metrics.candidate_recall_at_50 == 1.0
    assert 0.0 < metrics.ndcg_at_10 < 1.0


def test_retrieval_metrics_ignore_nonpositive_qrels() -> None:
    with pytest.raises(ValueError, match="positive relevance"):
        evaluate_retrieval({"q1": ["doc"]}, {"q1": {"doc": 0.0}})


def test_retrieval_metrics_use_zero_candidate_recall_when_not_supplied() -> None:
    metrics = evaluate_retrieval({"q1": ["doc"]}, {"q1": {"doc": 1.0}})

    assert metrics.candidate_recall_at_50 == 0.0
