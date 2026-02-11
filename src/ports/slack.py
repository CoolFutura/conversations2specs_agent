from __future__ import annotations

from typing import Protocol


class SlackThreadsPort(Protocol):
    def fetch_threads(self, channel_id: str) -> list[dict]:
        ...
