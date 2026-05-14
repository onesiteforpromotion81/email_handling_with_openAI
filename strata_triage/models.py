from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Classification(StrEnum):
    NEW_CLIENT = "new_client"
    SUPPORT_REQUEST = "support_request"
    COMPLAINT = "complaint"
    GENERAL_QUESTION = "general_question"
    UNCLEAR = "unclear"


class Urgency(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EnquiryTriageResult(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    classification: Classification
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_rationale: str
    client_intent_summary: str
    suggested_staff_reply: str
    recommended_actions: list[str]
    urgency: Urgency
    flags: list[str]
