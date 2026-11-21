from app.services.corpus_service import CorpusService


def test_corpus_service_returns_passages_for_a_paper_without_loading_until_lookup() -> None:
    service = CorpusService()
    assert service._dataset is None

    class Dataset:
        def __iter__(self):
            return iter(
                [
                    {
                        "id": "paper_00001",
                        "title": "Paper",
                        "section_name": "Abstract",
                        "text": "Evidence",
                    },
                    {
                        "id": "other_00001",
                        "title": "Other",
                        "section_name": "Results",
                        "text": "Other evidence",
                    },
                ]
            )

    service._dataset = Dataset()
    result = service.get_paper("paper")

    assert result is not None
    assert result["title"] == "Paper"
    assert result["passages"][0]["passage_id"] == "paper_00001"


def test_corpus_service_returns_none_for_unknown_paper() -> None:
    service = CorpusService()

    class Dataset:
        def __iter__(self):
            return iter([])

    service._dataset = Dataset()

    assert service.get_paper("missing") is None
