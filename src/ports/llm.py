from __future__ import annotations

from typing import Protocol


class LLMClassifierPort(Protocol):
    def classify(self, conversation_text: str) -> dict | None:
        ...
