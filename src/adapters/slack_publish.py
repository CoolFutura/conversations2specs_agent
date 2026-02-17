from __future__ import annotations

import os

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv(override=True)


class SlackSDKPublishAdapter:
    def __init__(self) -> None:
        token = os.getenv("SLACK_BOT_TOKEN")
        self.client = WebClient(token=token)

    def post_message(self, channel_id: str, text: str) -> str:
        try:
            result = self.client.chat_postMessage(channel=channel_id, text=text)
            return result.get("ts")
        except SlackApiError as e:
            raise RuntimeError(f"Error posting message: {e.response['error']}")

    def update_message(self, channel_id: str, message_ts: str, text: str) -> str:
        try:
            result = self.client.chat_update(channel=channel_id, ts=message_ts, text=text)
            return result.get("ts")
        except SlackApiError as e:
            raise RuntimeError(f"Error updating message: {e.response['error']}")
