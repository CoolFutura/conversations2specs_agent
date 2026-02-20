from __future__ import annotations

from src.adapters.slack_reader import fetch_slack_thread, fetch_slack_threads


class SlackSDKThreadsAdapter:
    def fetch_threads(self, channel_id: str) -> list[dict]:
        return fetch_slack_threads(channel_id)

    def fetch_thread(self, channel_id: str, thread_ts: str) -> dict | None:
        return fetch_slack_thread(channel_id, thread_ts)
