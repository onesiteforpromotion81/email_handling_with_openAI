"""Thin entrypoint for scripts — wires settings, adapter, and service."""

from __future__ import annotations

from typing import Any

from strata_triage.adapters.openai_llm import OpenAIChatClient
from strata_triage.config import Settings
from strata_triage.errors import MissingApiKeyError
from strata_triage.services.triage import EnquiryTriageService, empty_enquiry_result


def process_enquiry(enquiry_text: str) -> dict[str, Any]:
    """
    Analyse enquiry text. Returns a plain dict for JSON serialization / templates.
    Raises TriageError subclasses on configuration or provider failures.
    """
    settings = Settings()
    text = (enquiry_text or "").strip()

    if not text:
        return empty_enquiry_result().model_dump(mode="json")

    if not settings.openai_api_key:
        raise MissingApiKeyError()

    llm = OpenAIChatClient(settings)
    service = EnquiryTriageService(llm)
    return service.triage(enquiry_text).model_dump(mode="json")
