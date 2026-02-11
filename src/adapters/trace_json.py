from __future__ import annotations

from storage_utils import save_json


class JsonTraceabilityAdapter:
    def save_threads(self, threads: list[dict]) -> None:
        save_json("slack_threads.json", {"threads": threads})

    def save_conversations(self, conversations: list[dict]) -> None:
        save_json("conversations.json", {"conversations": conversations})
