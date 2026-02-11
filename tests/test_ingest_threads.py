import unittest

from src.domain.models import Artifact
from src.use_cases.ingest_threads import IngestThreadsUseCase


def normalize_thread(thread):
    lines = []
    for msg in thread.get("messages", []):
        user = msg.get("user", "System")
        text = msg.get("text", "")
        lines.append(f"{user}: {text}")
    return "\n".join(lines)


class FakeLLMClassifier:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def classify(self, conversation_text: str):
        self.calls.append(conversation_text)
        if self.responses:
            return self.responses.pop(0)
        return None


class FakeArtifactRepo:
    def __init__(self, artifacts=None):
        self._artifacts = list(artifacts or [])
        self.saved = []

    def list_all(self):
        return list(self._artifacts)

    def save(self, artifact: Artifact):
        self._artifacts.append(artifact)
        self.saved.append(artifact)


class IngestThreadsUseCaseTests(unittest.TestCase):
    # Verifies that ingesting threads creates artifacts and skips irrelevant/duplicates.
    def test_creates_artifacts_from_relevant_threads(self):
        threads = [
            {"ts": "1", "messages": [{"user": "U1", "text": "Hi"}]},
            {"ts": "2", "messages": [{"user": "U2", "text": "Yo"}]},
            {"ts": "3", "messages": [{"user": "U3", "text": "Dup"}]},
        ]

        existing = [
            Artifact(
                id="art_existing",
                conversation_id="3",
                type="OQ",
                status="PENDING",
                rephrasing="",
                rationale="",
                summary_of_context="",
            )
        ]

        llm = FakeLLMClassifier(
            [
                {"type": "OQ", "rephrasing": "Q?", "rationale": "", "summary_of_context": "ctx"},
                {"type": "IRRELEVANT"},
            ]
        )
        repo = FakeArtifactRepo(existing)
        use_case = IngestThreadsUseCase(llm, repo, normalize_thread)

        result = use_case.execute(threads)

        self.assertEqual(result.artifacts_created, 1)
        self.assertEqual(len(repo.saved), 1)
        self.assertEqual(len(result.conversations), 3)
        # only two threads classified (third is duplicate)
        self.assertEqual(len(llm.calls), 2)


if __name__ == "__main__":
    unittest.main()
