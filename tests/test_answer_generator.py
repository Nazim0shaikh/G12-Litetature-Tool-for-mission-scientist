import json

import pytest

from app.services.answer_generator import AnswerGenerationError, AnswerGenerator
from app.services.context_builder import ContextResult
from app.services.llm_service import LLMInvalidResponseError
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
        self.response_formats = []

    def complete(self, system_prompt: str, user_prompt: str, *, response_format=None) -> str:
        assert "only the supplied research passages" in system_prompt
        self.response_formats.append(response_format)
        return self.output


def test_generator_validates_answer_and_evidence_citations() -> None:
    llm = FakeLLM(response())
    result = AnswerGenerator(llm).generate(context())

    assert result.status == "answered"
    assert result.citations[0].passage_id == "paper_00001"
    assert llm.response_formats[0]["type"] == "json_schema"
    assert llm.response_formats[0]["json_schema"]["strict"] is True


def test_generator_accepts_fenced_json() -> None:
    result = AnswerGenerator(FakeLLM("```json\n" + response() + "\n```")).generate(context())

    assert result.answer == "The evidence supports this."


def test_generator_rejects_citation_outside_selected_evidence() -> None:
    with pytest.raises(AnswerGenerationError, match="after retry"):
        AnswerGenerator(
            FakeLLM(response(citations=[{"passage_id": "fake", "claim": "unsupported"}]))
        ).generate(context())


def test_generator_rejects_invalid_json() -> None:
    with pytest.raises(AnswerGenerationError, match="after retry"):
        AnswerGenerator(FakeLLM("not json")).generate(context())


def test_generator_retries_invalid_json_once_and_accepts_repaired_answer() -> None:
    class RetryingLLM:
        def __init__(self):
            self.prompts = []

        def complete(self, system_prompt: str, user_prompt: str, *, response_format=None) -> str:
            self.prompts.append(system_prompt)
            return "not json" if len(self.prompts) == 1 else response()

    llm = RetryingLLM()
    result = AnswerGenerator(llm).generate(context())

    assert result.status == "answered"
    assert len(llm.prompts) == 2
    assert "previous response was invalid" in llm.prompts[1]


def test_generator_retries_empty_provider_content() -> None:
    class RetryingLLM:
        def __init__(self):
            self.calls = 0

        def complete(self, system_prompt: str, user_prompt: str, *, response_format=None) -> str:
            self.calls += 1
            if self.calls == 1:
                raise LLMInvalidResponseError("empty content")
            return response()

    llm = RetryingLLM()
    result = AnswerGenerator(llm).generate(context())

    assert result.status == "answered"
    assert llm.calls == 2


def test_generator_returns_explicit_refusal_without_calling_llm() -> None:
    result = AnswerGenerator(FakeLLM("unused")).generate(
        ContextResult("Question", (), "", ())
    )

    assert result.status == "insufficient_evidence"
    assert result.insufficient_evidence is True
    assert result.citations == ()
