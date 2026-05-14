"""Ports (interfaces) — keeps the domain testable and swappable."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    """Minimal contract for chat-style JSON completion."""

    def complete_json(self, *, system: str, user: str) -> str:
        """Return assistant message content (expected JSON object as string)."""
        ...
