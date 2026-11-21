"""Provider-independent client for OpenAI-compatible chat-completion APIs."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import time
from typing import Any, Callable
from urllib import error, request


class LLMServiceError(RuntimeError):
    """Base error for configuration, transport, and provider failures."""


class LLMConfigurationError(LLMServiceError):
    """Raised when required provider configuration is missing."""


class LLMProviderError(LLMServiceError):
    """Raised when the provider rejects or cannot process a request."""


@dataclass(frozen=True)
class LLMConfig:
    """Runtime configuration loaded from environment variables."""

    provider: str = "openai_compatible"
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    temperature: float = 0.0
    max_tokens: int = 1500
    timeout: float = 60.0
    max_retries: int = 2
    retry_backoff: float = 0.5

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            provider=os.getenv("LLM_PROVIDER", "openai_compatible"),
            base_url=os.getenv("LLM_BASE_URL", ""),
            api_key=os.getenv("LLM_API_KEY", ""),
            model=os.getenv("LLM_MODEL", ""),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1500")),
            timeout=float(os.getenv("LLM_TIMEOUT", "60")),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "2")),
            retry_backoff=float(os.getenv("LLM_RETRY_BACKOFF", "0.5")),
        )

    def validate(self) -> None:
        if self.provider != "openai_compatible":
            raise LLMConfigurationError(f"unsupported LLM provider: {self.provider}")
        if not self.base_url or not self.model:
            raise LLMConfigurationError(
                "LLM_BASE_URL and LLM_MODEL are required for generation"
            )
        if self.temperature < 0 or self.max_tokens <= 0:
            raise LLMConfigurationError("invalid generation parameters")
        if self.timeout <= 0 or self.max_retries < 0 or self.retry_backoff < 0:
            raise LLMConfigurationError("invalid timeout or retry parameters")


Transport = Callable[[str, dict[str, str], bytes, float], tuple[int, bytes]]


class LLMService:
    """Small, testable adapter for the chat-completions endpoint."""

    def __init__(
        self,
        config: LLMConfig | None = None,
        *,
        transport: Transport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config or LLMConfig.from_env()
        self._transport = transport or self._urlopen_transport
        self._sleep = sleep

    def is_configured(self) -> bool:
        """Return whether required non-secret settings are available."""

        try:
            self.config.validate()
        except LLMConfigurationError:
            return False
        return bool(self.config.api_key)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Generate one response and return the provider's text content."""

        self.config.validate()
        if not self.config.api_key:
            raise LLMConfigurationError("LLM_API_KEY is required for generation")
        if not system_prompt.strip() or not user_prompt.strip():
            raise ValueError("system_prompt and user_prompt must not be empty")

        endpoint = self.config.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(self.config.max_retries + 1):
            try:
                status, response_body = self._transport(
                    endpoint, headers, body, self.config.timeout
                )
                if 200 <= status < 300:
                    return self._extract_content(response_body)
                if status not in {408, 409, 429} and status < 500:
                    raise LLMProviderError(f"LLM request rejected with status {status}")
                if attempt == self.config.max_retries:
                    raise LLMProviderError(
                        f"LLM request failed after retries with status {status}"
                    )
            except (TimeoutError, error.URLError) as exc:
                if attempt == self.config.max_retries:
                    raise LLMProviderError("LLM request timed out or failed") from exc
            if attempt < self.config.max_retries:
                self._sleep(self.config.retry_backoff * (2**attempt))

        raise LLMProviderError("LLM request failed")

    @staticmethod
    def _extract_content(response_body: bytes) -> str:
        try:
            payload: Any = json.loads(response_body)
            content = payload["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("LLM response did not contain message content") from exc
        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("LLM response contained empty message content")
        return content

    @staticmethod
    def _urlopen_transport(
        endpoint: str,
        headers: dict[str, str],
        body: bytes,
        timeout: float,
    ) -> tuple[int, bytes]:
        req = request.Request(endpoint, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=timeout) as response:
                return response.status, response.read()
        except error.HTTPError as exc:
            return exc.code, exc.read()
