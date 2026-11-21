from app.services.reranker import PassageReranker, RerankerConfig
from app.services.retrieval_service import RetrievedPassage


def passage(passage_id: str, text: str) -> RetrievedPassage:
    return RetrievedPassage(
        passage_id=passage_id,
        paper_id="paper",
        title="Title",
        section_name="Abstract",
        text=text,
        dense_rank=1,
        rrf_score=0.1,
    )


def test_reranker_sorts_scores_and_preserves_metadata() -> None:
    class Model:
        def predict(self, pairs, *, batch_size, show_progress_bar):
            assert pairs == [["question", "low"], ["question", "high"]]
            return [0.1, 0.9]

    reranker = PassageReranker(Model(), RerankerConfig(top_k=1))
    result = reranker.rerank("question", [passage("low-id", "low"), passage("high-id", "high")])

    assert len(result) == 1
    assert result[0].passage_id == "high-id"
    assert result[0].title == "Title"
    assert result[0].dense_rank == 1
    assert result[0].reranker_score == 0.9


def test_reranker_handles_empty_input_without_model_call() -> None:
    class Model:
        def predict(self, *args, **kwargs):
            raise AssertionError("model should not be called")

    reranker = PassageReranker(Model())

    assert reranker.rerank(" ", [passage("id", "text")]) == []
    assert reranker.rerank("question", []) == []
