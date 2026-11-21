import json

import pytest

from app.services.answer_generator import AnswerGenerationError, AnswerGenerator
from app.services.context_builder import ContextResult
from app.services.retrieval_service import RetrievedPassage


def context() -> ContextResult:
    passage = RetrievedPassage(
        passage_id="paper_00001",
        paper_id="paper",
        title="Paper",
        section_name="Abstract",
        text="The evidence.",
    )
    return ContextResult(
        question="What is the answer?",
        passages=(passage,),
        context="RESEARCH QUESTION:\nWhat is the answer?\n\nAVAILABLE EVIDENCE:",
        omitted_passage_ids=(),
    )


def response(**overrides: object) -> str:
    value = {
        "status": "answered",
        "answer": "The evidence supports this.",
        "citations": [{"passage_id": "paper_00001", "claim": "Evidence supports it."}],
        "reasoning_summary": "The passage directly supports the claim.",
        "insufficient_evidence": False,
    }
    value.update(overrides)
    return json.dumps(value)


class FakeLLM:
    def __init__(self, output: str):
        self.output = output

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        assert "only the supplied research passages" in system_prompt
        return self.output


def test_generator_validates_answer_and_evidence_citations() -> None:
    result = AnswerGenerator(FakeLLM(response())).generate(context())

    assert result.status == "answered"
    assert result.citations[0].passage_id == "paper_00001"


def test_generator_accepts_fenced_json() -> None:
    result = AnswerGenerator(FakeLLM("```json\n" + response() + "\n```")).generate(context())

    assert result.answer == "The evidence supports this."


def test_generator_rejects_citation_outside_selected_evidence() -> None:
    with pytest.raises(AnswerGenerationError, match="outside supplied evidence"):
        AnswerGenerator(
            FakeLLM(response(citations=[{"passage_id": "fake", "claim": "unsupported"}]))
        ).generate(context())


def test_generator_rejects_invalid_json() -> None:
    with pytest.raises(AnswerGenerationError, match="valid JSON"):
        AnswerGenerator(FakeLLM("not json")).generate(context())


def test_generator_returns_explicit_refusal_without_calling_llm() -> None:
    result = AnswerGenerator(FakeLLM("unused")).generate(
        ContextResult("Question", (), "", ())
    )

    assert result.status == "insufficient_evidence"
    assert result.insufficient_evidence is True
    assert result.citations == ()
