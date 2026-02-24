from __future__ import annotations

import time
from dataclasses import dataclass

from src.ports.sources_state import SourcesStatePort


@dataclass
class SetLastTsResult:
    channel_id: str
    last_ts: str


class SetLastTsUseCase:
    # Sets last_ts based on a number of days back from now.
    def __init__(self, sources_state: SourcesStatePort) -> None:
        self.sources_state = sources_state

    def execute(self, channel_id: str, days_back: float, now_ts: float | None = None) -> SetLastTsResult:
        if now_ts is None:
            now_ts = time.time()
        last_ts_value = now_ts - (days_back * 86400)
        last_ts = f"{last_ts_value:.6f}"
        self.sources_state.set_last_ts(channel_id, last_ts)
        return SetLastTsResult(channel_id=channel_id, last_ts=last_ts)
