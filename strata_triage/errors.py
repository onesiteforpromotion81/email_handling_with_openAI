"""Domain errors with messages safe to show operators in the UI."""


class TriageError(Exception):
    """Base class for failures the web/CLI layer should surface to the user."""

    def __init__(self, user_message: str) -> None:
        super().__init__(user_message)
        self.user_message = user_message


class MissingApiKeyError(TriageError):
    """No API key configured."""

    def __init__(self) -> None:
        super().__init__(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )


class LLMProviderError(TriageError):
    """Upstream LLM HTTP or transport failure."""

    def __init__(
        self,
        user_message: str,
        *,
        http_status: int | None = None,
        provider_code: str | None = None,
    ) -> None:
        super().__init__(user_message)
        self.http_status = http_status
        self.provider_code = provider_code


# Backwards-compatible name used by cli.py and earlier iterations
class EnquiryProcessingError(TriageError):
    """Raised when the enquiry cannot be processed (config, provider, or fatal parse)."""
