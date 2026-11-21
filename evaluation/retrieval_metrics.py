"""Standard retrieval metrics used by the QASPER evaluation scripts."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence


@dataclass(frozen=True)
class RetrievalMetrics:
    """Aggregated metrics for one evaluation collection."""

    recall_at_5: float
    recall_at_10: float
    mrr_at_10: float
    ndcg_at_10: float
    candidate_recall_at_50: float
    evaluated_queries: int

    def as_dict(self) -> dict[str, float | int]:
        return {
            "recall_at_5": self.recall_at_5,
            "recall_at_10": self.recall_at_10,
            "mrr_at_10": self.mrr_at_10,
            "ndcg_at_10": self.ndcg_at_10,
            "candidate_recall_at_50": self.candidate_recall_at_50,
            "evaluated_queries": self.evaluated_queries,
        }


def evaluate_retrieval(
    ranked_results: Mapping[str, Sequence[str]],
    qrels: Mapping[str, Mapping[str, float]],
    *,
    candidate_results: Mapping[str, Sequence[str]] | None = None,
) -> RetrievalMetrics:
    """Evaluate only queries with at least one positive relevance judgment."""

    recall_5: list[float] = []
    recall_10: list[float] = []
    reciprocal_ranks: list[float] = []
    ndcgs: list[float] = []
    candidate_recalls: list[float] = []

    for query_id, relevance in qrels.items():
        relevant = {doc_id: score for doc_id, score in relevance.items() if score > 0}
        if not relevant:
            continue
        ranked = list(ranked_results.get(query_id, ()))
        evaluated_retrieved = ranked[:10]

        recall_5.append(_recall(ranked[:5], relevant))
        recall_10.append(_recall(evaluated_retrieved, relevant))
        reciprocal_ranks.append(_reciprocal_rank(evaluated_retrieved, relevant))
        ndcgs.append(_ndcg(evaluated_retrieved, relevant))

        if candidate_results is not None:
            candidate_recalls.append(
                _recall(list(candidate_results.get(query_id, ()))[:50], relevant)
            )

    count = len(recall_5)
    if count == 0:
        raise ValueError("no queries with positive relevance judgments were evaluated")

    return RetrievalMetrics(
        recall_at_5=sum(recall_5) / count,
        recall_at_10=sum(recall_10) / count,
        mrr_at_10=sum(reciprocal_ranks) / count,
        ndcg_at_10=sum(ndcgs) / count,
        candidate_recall_at_50=(
            sum(candidate_recalls) / len(candidate_recalls)
            if candidate_recalls
            else 0.0
        ),
        evaluated_queries=count,
    )


def _recall(ranked: Sequence[str], relevant: Mapping[str, float]) -> float:
    return len(set(ranked) & relevant.keys()) / len(relevant)


def _reciprocal_rank(ranked: Sequence[str], relevant: Mapping[str, float]) -> float:
    for rank, doc_id in enumerate(ranked, start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def _ndcg(ranked: Sequence[str], relevant: Mapping[str, float]) -> float:
    dcg = sum(
        (2**relevant[doc_id] - 1) / math.log2(rank + 1)
        for rank, doc_id in enumerate(ranked, start=1)
        if doc_id in relevant
    )
    ideal_scores = sorted(relevant.values(), reverse=True)[:10]
    idcg = sum(
        (2**score - 1) / math.log2(rank + 1)
        for rank, score in enumerate(ideal_scores, start=1)
    )
    return dcg / idcg if idcg else 0.0
