"""Cross-encoder reranking for hybrid retrieval candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence

from app.services.retrieval_service import RetrievedPassage


class CrossEncoderModel(Protocol):
    def predict(
        self,
        sentences: Sequence[Sequence[str]],
        *,
        batch_size: int,
        show_progress_bar: bool,
    ) -> Any:
        ...


@dataclass(frozen=True)
class RerankerConfig:
    """Configuration for cross-encoder inference."""

    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    batch_size: int = 32
    top_k: int = 10

    def __post_init__(self) -> None:
        if self.batch_size <= 0 or self.top_k <= 0:
            raise ValueError("batch_size and top_k must be positive")


class PassageReranker:
    """Score and sort passages without changing their source metadata."""

    def __init__(
        self,
        model: CrossEncoderModel,
        config: RerankerConfig | None = None,
    ) -> None:
        self.model = model
        self.config = config or RerankerConfig()

    @classmethod
    def from_model_name(
        cls, config: RerankerConfig | None = None
    ) -> "PassageReranker":
        from sentence_transformers import CrossEncoder

        selected = config or RerankerConfig()
        return cls(CrossEncoder(selected.model_name), selected)

    def rerank(
        self,
        question: str,
        passages: Sequence[RetrievedPassage],
    ) -> list[RetrievedPassage]:
        """Return the highest-scoring passages with score metadata attached."""

        if not question.strip() or not passages:
            return []

        pairs = [[question, passage.text] for passage in passages]
        scores = self.model.predict(
            pairs,
            batch_size=self.config.batch_size,
            show_progress_bar=False,
        )
        scored = [
            (float(score), index, passage)
            for index, (score, passage) in enumerate(zip(scores, passages))
        ]
        scored.sort(key=lambda item: (-item[0], item[1]))
        reranked: list[RetrievedPassage] = []
        for score, _, passage in scored[: self.config.top_k]:
            result = RetrievedPassage(
                passage_id=passage.passage_id,
                paper_id=passage.paper_id,
                title=passage.title,
                section_name=passage.section_name,
                text=passage.text,
                dense_rank=passage.dense_rank,
                bm25_rank=passage.bm25_rank,
                rrf_score=passage.rrf_score,
                reranker_score=score,
            )
            reranked.append(result)
        return reranked
