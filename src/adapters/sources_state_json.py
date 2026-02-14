from __future__ import annotations

from src.adapters.storage_utils import load_json, save_json


class JsonSourcesStateAdapter:
    def set_last_ts(self, channel_id: str, last_ts: str) -> None:
        sources_state = load_json("sources_state.json")
        if "slack" not in sources_state:
            sources_state["slack"] = {}

        if channel_id not in sources_state["slack"]:
            sources_state["slack"][channel_id] = {}

        sources_state["slack"][channel_id]["last_ts"] = last_ts
        save_json("sources_state.json", sources_state)
