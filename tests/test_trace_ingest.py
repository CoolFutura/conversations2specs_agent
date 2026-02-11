import unittest

from src.use_cases.trace_ingest import TraceIngestUseCase


class FakeTracePort:
    def __init__(self):
        self.threads = None
        self.conversations = None

    def save_threads(self, threads):
        self.threads = threads

    def save_conversations(self, conversations):
        self.conversations = conversations


class TraceIngestUseCaseTests(unittest.TestCase):
    # Verifies that trace ingest saves threads and conversations.
    def test_saves_threads_and_conversations(self):
        trace_port = FakeTracePort()
        use_case = TraceIngestUseCase(trace_port)

        threads = [{"ts": "1"}]
        conversations = [{"ts": "1", "text": "U: hi"}]

        result = use_case.execute(threads, conversations)

        self.assertTrue(result.threads_saved)
        self.assertTrue(result.conversations_saved)
        self.assertEqual(trace_port.threads, threads)
        self.assertEqual(trace_port.conversations, conversations)


if __name__ == "__main__":
    unittest.main()
