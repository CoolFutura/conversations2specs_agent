from __future__ import annotations

from typing import Protocol


class SlackPublishPort(Protocol):
    def post_message(self, channel_id: str, text: str) -> str:
        ...

    def update_message(self, channel_id: str, message_ts: str, text: str) -> str:
        ...
