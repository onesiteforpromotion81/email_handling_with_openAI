from __future__ import annotations

from typing import Any

from strata_triage.adapters.mock_llm import MockLLMClient
from strata_triage.adapters.openai_llm import OpenAIChatClient
from strata_triage.config import Settings
from strata_triage.errors import MissingApiKeyError
from strata_triage.services.triage import EnquiryTriageService, empty_enquiry_result


def process_enquiry(enquiry_text: str) -> dict[str, Any]:
    settings = Settings()
    text = (enquiry_text or "").strip()

    if not text:
        return empty_enquiry_result().model_dump(mode="json")

    if settings.triage_use_mock:
        llm = MockLLMClient()
    else:
        if not settings.openai_api_key:
            raise MissingApiKeyError()
        llm = OpenAIChatClient(settings)

    service = EnquiryTriageService(llm)
    return service.triage(enquiry_text).model_dump(mode="json")
