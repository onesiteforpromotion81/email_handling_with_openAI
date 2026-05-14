from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    def complete_json(self, *, system: str, user: str) -> str:
        ...
