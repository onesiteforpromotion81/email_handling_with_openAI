"""OpenAI adapter for `LLMClient` with explicit error mapping."""

from __future__ import annotations

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAIError,
    OpenAI,
    RateLimitError,
)

from strata_triage.config import Settings
from strata_triage.errors import LLMProviderError


def _nested_error_code(body: object | None) -> str | None:
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):
            code = err.get("code")
            if isinstance(code, str):
                return code
    return None


def _map_openai_exception(exc: OpenAIError) -> LLMProviderError:
    if isinstance(exc, AuthenticationError):
        return LLMProviderError(
            "OpenAI rejected the API key (authentication failed). Check OPENAI_API_KEY in .env.",
            http_status=401,
            provider_code="invalid_api_key",
        )
    if isinstance(exc, RateLimitError):
        code = _nested_error_code(exc.body)
        if code == "insufficient_quota":
            msg = (
                "OpenAI reported no quota left for this account (billing / credits). "
                "Check https://platform.openai.com/settings/organization/billing"
            )
        else:
            msg = "OpenAI rate limit reached. Wait briefly and try again."
        return LLMProviderError(msg, http_status=429, provider_code=code)
    if isinstance(exc, APIStatusError):
        code = _nested_error_code(exc.body)
        return LLMProviderError(
            f"OpenAI API error ({exc.status_code}): {exc.message}",
            http_status=exc.status_code,
            provider_code=code,
        )
    if isinstance(exc, (APIConnectionError, APITimeoutError)):
        return LLMProviderError(
            "Could not reach OpenAI (network error or timeout). Try again shortly.",
        )
    return LLMProviderError(f"OpenAI client error: {exc}")


class OpenAIChatClient:
    """Chat Completions with JSON object response format."""

    def __init__(self, settings: Settings) -> None:
        key = settings.openai_api_key
        if not key:
            raise ValueError("OpenAIChatClient requires settings.openai_api_key")
        self._client = OpenAI(api_key=key)
        self._model = settings.openai_model
        self._temperature = settings.llm_temperature

    def complete_json(self, *, system: str, user: str) -> str:
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                temperature=self._temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except OpenAIError as e:
            raise _map_openai_exception(e) from e

        choice = resp.choices[0].message
        if not choice or not choice.content:
            raise LLMProviderError("OpenAI returned an empty assistant message.")
        return choice.content
