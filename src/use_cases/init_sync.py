from __future__ import annotations

from dataclasses import dataclass

from src.ports.sources_state import SourcesStatePort


@dataclass
class InitSyncResult:
    channel_id: str
    last_ts: str


class InitSyncUseCase:
    # Initializes sync point for a channel by setting last_ts.
    def __init__(self, sources_state: SourcesStatePort) -> None:
        self.sources_state = sources_state

    def execute(self, channel_id: str, last_ts: str) -> InitSyncResult:
        self.sources_state.set_last_ts(channel_id, last_ts)
        return InitSyncResult(channel_id=channel_id, last_ts=last_ts)
