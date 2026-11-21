import sqlite3

from fastapi.testclient import TestClient

from app.config import AppConfig
from app.main import create_app
from app.services.corpus_service import CorpusService


def test_health_and_config_do_not_require_initialized_pipeline() -> None:
    app = create_app(config=AppConfig(cors_origins=("http://test",)))
    client = TestClient(app)

    health = client.get("/api/v1/health")
    config = client.get("/api/v1/config")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert config.status_code == 200
    assert "api_key" not in config.text


def test_ask_reports_unavailable_pipeline() -> None:
    client = TestClient(create_app())

    response = client.post("/api/v1/ask", json={"question": "What is retrieval?"})

    assert response.status_code == 503


def test_question_validation_rejects_empty_input() -> None:
    client = TestClient(create_app())

    response = client.post("/api/v1/ask", json={"question": ""})

    assert response.status_code == 422


def test_paper_endpoint_returns_lazy_corpus_result() -> None:
    corpus = CorpusService()

    class Dataset:
        def __iter__(self):
            return iter(
                [
                    {
                        "id": "paper_00001",
                        "title": "Paper",
                        "section_name": "Abstract",
                        "text": "Evidence",
                    }
                ]
            )

    corpus._dataset = Dataset()
    client = TestClient(create_app(corpus_service=corpus))

    response = client.get("/api/v1/paper/paper")

    assert response.status_code == 200
    assert response.json()["passages"][0]["passage_id"] == "paper_00001"


def test_paper_endpoint_returns_404_for_missing_paper() -> None:
    corpus = CorpusService()

    class Dataset:
        def __iter__(self):
            return iter([])

    corpus._dataset = Dataset()
    client = TestClient(create_app(corpus_service=corpus))

    assert client.get("/api/v1/paper/missing").status_code == 404
