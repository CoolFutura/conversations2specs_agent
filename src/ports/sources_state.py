from __future__ import annotations

from typing import Protocol


class SourcesStatePort(Protocol):
    def set_last_ts(self, channel_id: str, last_ts: str) -> None:
        ...
