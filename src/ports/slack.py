from __future__ import annotations

from typing import Protocol


class SlackThreadsPort(Protocol):
    def fetch_threads(self, channel_id: str) -> list[dict]:
        ...

    def fetch_thread(self, channel_id: str, thread_ts: str) -> dict | None:
        ...
