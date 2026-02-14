import unittest

from src.adapters.openai import _load_prompt


class LLMUtilsTests(unittest.TestCase):
    # Verifies that prompt loader replaces variables.
    def test_load_prompt_replaces_conversation(self):
        prompt = _load_prompt("classify_discussion", conversation="Hello world")
        self.assertIsInstance(prompt, str)
        self.assertIn("Hello world", prompt)
        self.assertNotIn("{{conversation}}", prompt)


if __name__ == "__main__":
    unittest.main()
