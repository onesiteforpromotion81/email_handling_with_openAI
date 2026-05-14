from __future__ import annotations

import json
import re
from typing import Any

from strata_triage.errors import LLMProviderError
from strata_triage.models import Classification, EnquiryTriageResult, Urgency
from strata_triage.ports import LLMClient
from strata_triage.prompts import REPAIR_SYSTEM_PROMPT, SYSTEM_PROMPT, build_user_prompt

_VALID_CLASSIFICATIONS = frozenset(c.value for c in Classification)
_VALID_URGENCY = frozenset(u.value for u in Urgency)
_REQUIRED_KEYS = frozenset(
    {
        "classification",
        "confidence",
        "confidence_rationale",
        "client_intent_summary",
        "suggested_staff_reply",
        "recommended_actions",
        "urgency",
        "flags",
    }
)


def _extract_json_object(text: str) -> str:
    t = text.strip()
    fence = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", t, re.DOTALL | re.IGNORECASE)
    if fence:
        return fence.group(1).strip()
    return t


def _coerce_raw(data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    for k in _REQUIRED_KEYS:
        if k not in out:
            if k in ("recommended_actions", "flags"):
                out[k] = []
            elif k == "confidence":
                out[k] = 0.5
            else:
                out[k] = ""
    cls = out.get("classification")
    if cls not in _VALID_CLASSIFICATIONS:
        out["classification"] = Classification.UNCLEAR.value
    try:
        c = float(out.get("confidence", 0))
        out["confidence"] = max(0.0, min(1.0, c))
    except (TypeError, ValueError):
        out["confidence"] = 0.5
    if not isinstance(out.get("recommended_actions"), list):
        out["recommended_actions"] = (
            [str(out["recommended_actions"])] if out.get("recommended_actions") else []
        )
    if not isinstance(out.get("flags"), list):
        out["flags"] = [str(out["flags"])] if out.get("flags") else []
    urg = out.get("urgency")
    if urg not in _VALID_URGENCY:
        out["urgency"] = Urgency.MEDIUM.value
    return out


def _parse_json(content: str) -> dict[str, Any]:
    return json.loads(_extract_json_object(content))


def _result_from_raw(raw: dict[str, Any]) -> EnquiryTriageResult:
    return EnquiryTriageResult.model_validate(_coerce_raw(raw))


def empty_enquiry_result() -> EnquiryTriageResult:
    return _result_from_raw(
        {
            "classification": Classification.UNCLEAR.value,
            "confidence": 0.0,
            "confidence_rationale": "No text was provided.",
            "client_intent_summary": "The enquiry field was empty.",
            "suggested_staff_reply": (
                "Thank you for contacting Strata Management Consultants. "
                "We did not receive any message text. Could you please resend your enquiry "
                "with your property address and a brief description of how we can help?"
            ),
            "recommended_actions": ["Wait for client to resubmit with details"],
            "urgency": Urgency.LOW.value,
            "flags": [],
        }
    )


class EnquiryTriageService:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def triage(self, enquiry_text: str) -> EnquiryTriageResult:
        text = (enquiry_text or "").strip()
        if not text:
            return empty_enquiry_result()

        user_prompt = build_user_prompt(text)
        raw_content: str | None = None

        try:
            raw_content = self._llm.complete_json(system=SYSTEM_PROMPT, user=user_prompt)
            data = _parse_json(raw_content)
            return _result_from_raw(data)
        except LLMProviderError:
            raise
        except json.JSONDecodeError:
            pass

        repair_user = f"Broken JSON to fix:\n{raw_content or ''}\n\nOriginal enquiry:\n{text}"
        try:
            repaired = self._llm.complete_json(system=REPAIR_SYSTEM_PROMPT, user=repair_user)
            data = _parse_json(repaired)
            return _result_from_raw(data)
        except LLMProviderError:
            raise
        except json.JSONDecodeError:
            pass

        return _result_from_raw(
            {
                "classification": Classification.UNCLEAR.value,
                "confidence": 0.2,
                "confidence_rationale": "Could not parse model output as JSON after retry.",
                "client_intent_summary": (
                    "Automated parsing failed; please read the original enquiry manually."
                ),
                "suggested_staff_reply": (
                    "Thank you for contacting us. A team member will review your message and respond shortly."
                ),
                "recommended_actions": [
                    "Review raw enquiry manually",
                    "Check API logs if this persists",
                ],
                "urgency": Urgency.MEDIUM.value,
                "flags": ["parse_error"],
            }
        )
