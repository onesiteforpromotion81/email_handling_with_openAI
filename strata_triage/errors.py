class TriageError(Exception):
    def __init__(self, user_message: str) -> None:
        super().__init__(user_message)
        self.user_message = user_message


class MissingApiKeyError(TriageError):
    def __init__(self) -> None:
        super().__init__(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )


class LLMProviderError(TriageError):
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


class EnquiryProcessingError(TriageError):
    pass
