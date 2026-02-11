from __future__ import annotations

from llm_pipeline.classify_points import classify_conversation


class OpenAILLMClassifier:
    def classify(self, conversation_text: str) -> dict | None:
        return classify_conversation(conversation_text)
