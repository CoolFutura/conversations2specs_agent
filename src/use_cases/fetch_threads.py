from __future__ import annotations

from dataclasses import dataclass

from src.ports.slack import SlackThreadsPort


@dataclass
class FetchThreadsResult:
    threads: list[dict]


class FetchThreadsUseCase:
    # Fetches Slack threads using a Slack adapter.
    def __init__(self, slack_port: SlackThreadsPort) -> None:
        self.slack_port = slack_port

    def execute(self, channel_id: str) -> FetchThreadsResult:
        threads = self.slack_port.fetch_threads(channel_id)
        return FetchThreadsResult(threads=threads)
