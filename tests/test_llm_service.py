import json

import pytest

from app.services.llm_service import (
    LLMConfig,
    LLMConfigurationError,
    LLMProviderError,
    LLMService,
)


def config(**overrides: object) -> LLMConfig:
    values = {
        "base_url": "https://example.test/v1",
        "api_key": "secret",
        "model": "test-model",
        "max_retries": 2,
        "retry_backoff": 0.1,
    }
    values.update(overrides)
    return LLMConfig(**values)


def test_complete_sends_openai_compatible_payload_without_logging_secret() -> None:
    calls = []

    def transport(endpoint, headers, body, timeout):
        calls.append((endpoint, headers, json.loads(body), timeout))
        return 200, b'{"choices":[{"message":{"content":"grounded answer"}}]}'

    result = LLMService(config(), transport=transport).complete("system", "user")

    assert result == "grounded answer"
    assert calls[0][0] == "https://example.test/v1/chat/completions"
    assert calls[0][2]["model"] == "test-model"
    assert calls[0][2]["messages"][0]["role"] == "system"
    assert calls[0][1]["Authorization"] == "Bearer secret"


def test_complete_retries_transient_status_with_exponential_backoff() -> None:
    statuses = iter([429, 503, 200])
    delays = []

    def transport(endpoint, headers, body, timeout):
        status = next(statuses)
        return status, b'{"choices":[{"message":{"content":"ok"}}]}'

    result = LLMService(config(), transport=transport, sleep=delays.append).complete(
        "system", "user"
    )

    assert result == "ok"
    assert delays == [0.1, 0.2]


def test_complete_sends_json_schema_and_disables_thinking_when_configured() -> None:
    calls = []
    response_format = {
        "type": "json_schema",
        "json_schema": {"name": "answer", "strict": True, "schema": {"type": "object"}},
    }

    def transport(endpoint, headers, body, timeout):
        calls.append(json.loads(body))
        return 200, b'{"choices":[{"message":{"content":"{}"}}]}'

    LLMService(config(disable_thinking=True), transport=transport).complete(
        "system",
        "user",
        response_format=response_format,
    )

    assert calls[0]["response_format"] == response_format
    assert calls[0]["chat_template_kwargs"] == {"enable_thinking": False}


def test_complete_reports_missing_configuration() -> None:
    service = LLMService(LLMConfig(model="model"))

    with pytest.raises(LLMConfigurationError, match="LLM_BASE_URL"):
        service.complete("system", "user")


def test_complete_rejects_malformed_provider_response() -> None:
    def transport(endpoint, headers, body, timeout):
        return 200, b'{"unexpected": []}'

    with pytest.raises(LLMProviderError, match="message content"):
        LLMService(config(), transport=transport).complete("system", "user")
