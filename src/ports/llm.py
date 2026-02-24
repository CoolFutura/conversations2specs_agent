from __future__ import annotations

from typing import Protocol


class LLMClassifierPort(Protocol):
    def classify(self, conversation_text: str) -> dict | None:
        ...


class LLMDecisionPort(Protocol):
    def decide(self, question: str, context: str, thread_text: str) -> dict | None:
        ...
