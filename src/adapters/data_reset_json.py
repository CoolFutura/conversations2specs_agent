from __future__ import annotations

from src.adapters.storage_utils import save_json


class JsonDataResetAdapter:
    def reset_all(self) -> None:
        save_json("conversations.json", {"conversations": []})
        save_json("artifacts.json", {"artifacts": []})
        save_json("open_questions.json", {"questions": []})
        save_json("proposed_updates.json", {"updates": []})
        save_json("slack_threads.json", {"threads": []})
