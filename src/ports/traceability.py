from __future__ import annotations

from typing import Protocol


class TraceabilityPort(Protocol):
    def save_threads(self, threads: list[dict]) -> None:
        ...

    def save_conversations(self, conversations: list[dict]) -> None:
        ...
