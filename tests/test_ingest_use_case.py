import unittest

from src.use_cases.ingest import IngestUseCase


def normalize_thread(thread):
    lines = []
    for msg in thread.get("messages", []):
        user = msg.get("user", "System")
        text = msg.get("text", "")
        lines.append(f"{user}: {text}")
    return "\n".join(lines)


class FakeSlackPort:
    def __init__(self, threads):
        self.threads = threads
        self.calls = []

    def fetch_threads(self, channel_id: str):
        self.calls.append(channel_id)
        return self.threads


class FakeLLMClassifier:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def classify(self, conversation_text: str):
        self.calls.append(conversation_text)
        return self.response


class FakeArtifactRepo:
    def __init__(self, artifacts=None):
        self._artifacts = list(artifacts or [])
        self.saved = []

    def list_all(self):
        return list(self._artifacts)

    def save(self, artifact):
        self._artifacts.append(artifact)
        self.saved.append(artifact)


class FakeTracePort:
    def __init__(self):
        self.threads = None
        self.conversations = None
        self.call_log = []

    def save_threads(self, threads):
        self.threads = threads
        self.call_log.append("threads")

    def save_conversations(self, conversations):
        self.conversations = conversations
        self.call_log.append("conversations")


class IngestUseCaseTests(unittest.TestCase):
    # Verifies that IngestUseCase orchestrates fetch, ingest, and trace.
    def test_ingest_orchestrates_all_steps(self):
        threads = [
            {"ts": "1", "messages": [{"user": "U1", "text": "Hi"}]},
            {"ts": "2", "messages": [{"user": "U2", "text": "Yo"}]},
        ]

        slack = FakeSlackPort(threads)
        llm = FakeLLMClassifier(
            {
                "type": "OQ",
                "rephrasing": "Q?",
                "rationale": "",
                "summary_of_context": "ctx",
            }
        )
        repo = FakeArtifactRepo()
        trace = FakeTracePort()

        started = {"count": 0}

        def on_start():
            started["count"] += 1

        use_case = IngestUseCase(slack, llm, repo, trace, normalize_thread)
        result = use_case.execute("C1", on_start_run=on_start)

        self.assertEqual(result.threads_fetched, 2)
        self.assertEqual(result.artifacts_created, 2)
        self.assertEqual(result.oq_count, 2)
        self.assertEqual(result.pu_count, 0)
        self.assertEqual(result.irrelevant_count, 0)
        self.assertEqual(started["count"], 1)
        self.assertEqual(trace.threads, threads)
        self.assertEqual(len(trace.conversations), 2)
        self.assertEqual(len(repo.saved), 2)

    def test_no_threads_skips_start_and_trace(self):
        slack = FakeSlackPort([])
        llm = FakeLLMClassifier({"type": "OQ"})
        repo = FakeArtifactRepo()
        trace = FakeTracePort()

        started = {"count": 0}

        def on_start():
            started["count"] += 1

        use_case = IngestUseCase(slack, llm, repo, trace, normalize_thread)
        result = use_case.execute("C_EMPTY", on_start_run=on_start)

        self.assertEqual(result.threads_fetched, 0)
        self.assertEqual(result.artifacts_created, 0)
        self.assertEqual(result.oq_count, 0)
        self.assertEqual(result.pu_count, 0)
        self.assertEqual(result.irrelevant_count, 0)
        self.assertEqual(started["count"], 0)
        self.assertEqual(slack.calls, ["C_EMPTY"])
        self.assertEqual(len(llm.calls), 0)
        self.assertEqual(len(repo.saved), 0)
        self.assertIsNone(trace.threads)
        self.assertIsNone(trace.conversations)
        self.assertEqual(trace.call_log, [])

    def test_trace_order_and_conversations_count(self):
        threads = [
            {"ts": "1", "messages": [{"user": "U1", "text": "Hi"}]},
            {"messages": [{"user": "U2", "text": "Missing ts"}]},
        ]

        slack = FakeSlackPort(threads)
        llm = FakeLLMClassifier(
            {"type": "OQ", "rephrasing": "Q?", "rationale": "", "summary_of_context": "ctx"}
        )
        repo = FakeArtifactRepo()
        trace = FakeTracePort()

        use_case = IngestUseCase(slack, llm, repo, trace, normalize_thread)
        result = use_case.execute("C1")

        self.assertEqual(result.threads_fetched, 2)
        self.assertEqual(trace.call_log, ["threads", "conversations"])
        self.assertIsNotNone(trace.conversations)
        self.assertEqual(len(trace.conversations), 1)


if __name__ == "__main__":
    unittest.main()
