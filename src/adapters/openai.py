from __future__ import annotations

import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)


def _load_prompt(name: str, **kwargs) -> str:
    base_dir = os.path.dirname(__file__)
    prompts_dir = os.path.abspath(os.path.join(base_dir, "..", "prompts"))
    path = os.path.join(prompts_dir, f"{name}.txt")
    with open(path, "r") as f:
        template = f.read()

    for key, value in kwargs.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))

    return template


def _parse_json(text: str) -> dict | None:
    import json

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("Error parsing LLM response.")
        return None


class OpenAILLMClassifier:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)

    def classify(self, conversation_text: str) -> dict | None:
        prompt = _load_prompt("classify_discussion", conversation=conversation_text)
        model = os.getenv("OPENAI_MODEL", "gpt-4o")

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content and _parse_json(response.choices[0].message.content)
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None


class OpenAILLMDecision:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)

    def decide(self, question: str, context: str, thread_text: str) -> dict | None:
        prompt = _load_prompt(
            "decision_from_thread",
            question=question,
            context=context,
            thread=thread_text,
        )
        model = os.getenv("OPENAI_DECISION_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o"))

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content and _parse_json(response.choices[0].message.content)
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None
