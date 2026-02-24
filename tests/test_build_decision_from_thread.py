import unittest

from src.domain.models import OpenQuestion
from src.use_cases.build_decision_from_thread import BuildDecisionFromThreadUseCase


class FakeOQRepo:
    def __init__(self, questions):
        self._questions = {q.id: q for q in questions}
        self.saved = []

    def list_all(self):
        return list(self._questions.values())

    def get_by_id(self, oq_id: str):
        return self._questions.get(oq_id)

    def save(self, oq: OpenQuestion):
        self._questions[oq.id] = oq
        self.saved.append(oq)

    def create_from_artifact(self, artifact):
        raise NotImplementedError("Not needed for this test")


class FakeSlackPort:
    def __init__(self, thread):
        self.thread = thread
        self.calls = []

    def fetch_thread(self, channel_id: str, thread_ts: str):
        self.calls.append((channel_id, thread_ts))
        return self.thread

    def fetch_threads(self, channel_id: str):
        raise NotImplementedError("Not needed for this test")


class FakeLLMDecision:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def decide(self, question: str, context: str, thread_text: str):
        self.calls.append((question, context, thread_text))
        return self.payload


class RecordingNormalizer:
    def __init__(self, text="normalized"):
        self.text = text
        self.calls = []

    def __call__(self, thread: dict) -> str:
        self.calls.append(thread)
        return self.text


class BuildDecisionFromThreadUseCaseTests(unittest.TestCase):
    def test_missing_oq_returns_reason(self):
        repo = FakeOQRepo([])
        use_case = BuildDecisionFromThreadUseCase(
            repo,
            FakeSlackPort(thread=None),
            FakeLLMDecision(payload={"decision": "X", "decision_rationale": "Y"}),
            RecordingNormalizer(),
        )

        result = use_case.execute("missing")

        self.assertFalse(result.updated)
        self.assertEqual(result.reason, "missing_oq")

    def test_not_published_returns_reason(self):
        oq = OpenQuestion(
            id="oq_1",
            artifact_id="art_1",
            question="Q1",
            context="ctx",
            status="OPEN",
            slack_ts=None,
            decision=None,
            decision_rationale=None,
            published_channel_id=None,
            published_message_ts=None,
        )

        repo = FakeOQRepo([oq])
        use_case = BuildDecisionFromThreadUseCase(
            repo,
            FakeSlackPort(thread=None),
            FakeLLMDecision(payload={"decision": "X", "decision_rationale": "Y"}),
            RecordingNormalizer(),
        )

        result = use_case.execute("oq_1")

        self.assertFalse(result.updated)
        self.assertEqual(result.reason, "not_published")

    def test_thread_missing_returns_reason(self):
        oq = OpenQuestion(
            id="oq_2",
            artifact_id="art_2",
            question="Q2",
            context="ctx",
            status="OPEN",
            slack_ts=None,
            decision=None,
            decision_rationale=None,
            published_channel_id="C1",
            published_message_ts="123.45",
        )

        repo = FakeOQRepo([oq])
        use_case = BuildDecisionFromThreadUseCase(
            repo,
            FakeSlackPort(thread=None),
            FakeLLMDecision(payload={"decision": "X", "decision_rationale": "Y"}),
            RecordingNormalizer(),
        )

        result = use_case.execute("oq_2")

        self.assertFalse(result.updated)
        self.assertEqual(result.reason, "thread_missing")

    def test_no_tech_messages_returns_reason(self):
        thread_ts = "1700000000.0001"
        thread = {
            "ts": thread_ts,
            "messages": [
                {"ts": thread_ts, "user": "U1", "text": "Root message"},
                {"ts": "1700000000.0002", "user": "U2", "text": "Reply"},
            ],
        }

        oq = OpenQuestion(
            id="oq_3",
            artifact_id="art_3",
            question="Q3",
            context="ctx",
            status="OPEN",
            slack_ts=None,
            decision=None,
            decision_rationale=None,
            published_channel_id="C1",
            published_message_ts=thread_ts,
        )

        repo = FakeOQRepo([oq])
        use_case = BuildDecisionFromThreadUseCase(
            repo,
            FakeSlackPort(thread=thread),
            FakeLLMDecision(payload={"decision": "X", "decision_rationale": "Y"}),
            RecordingNormalizer(),
            tech_team_user_ids={"U1"},
        )

        result = use_case.execute("oq_3")

        self.assertFalse(result.updated)
        self.assertEqual(result.reason, "no_tech_messages")

    def test_llm_failed_returns_reason(self):
        thread_ts = "1700000000.0001"
        thread = {
            "ts": thread_ts,
            "messages": [
                {"ts": thread_ts, "user": "U1", "text": "Root message"},
                {"ts": "1700000000.0002", "user": "U1", "text": "Reply"},
            ],
        }

        oq = OpenQuestion(
            id="oq_4",
            artifact_id="art_4",
            question="Q4",
            context="ctx",
            status="OPEN",
            slack_ts=None,
            decision=None,
            decision_rationale=None,
            published_channel_id="C1",
            published_message_ts=thread_ts,
        )

        repo = FakeOQRepo([oq])
        use_case = BuildDecisionFromThreadUseCase(
            repo,
            FakeSlackPort(thread=thread),
            FakeLLMDecision(payload=None),
            RecordingNormalizer(),
        )

        result = use_case.execute("oq_4")

        self.assertFalse(result.updated)
        self.assertEqual(result.reason, "llm_failed")

    def test_empty_decision_returns_reason(self):
        thread_ts = "1700000000.0001"
        thread = {
            "ts": thread_ts,
            "messages": [
                {"ts": thread_ts, "user": "U1", "text": "Root message"},
                {"ts": "1700000000.0002", "user": "U1", "text": "Reply"},
            ],
        }

        oq = OpenQuestion(
            id="oq_5",
            artifact_id="art_5",
            question="Q5",
            context="ctx",
            status="OPEN",
            slack_ts=None,
            decision=None,
            decision_rationale=None,
            published_channel_id="C1",
            published_message_ts=thread_ts,
        )

        repo = FakeOQRepo([oq])
        use_case = BuildDecisionFromThreadUseCase(
            repo,
            FakeSlackPort(thread=thread),
            FakeLLMDecision(payload={"decision": " ", "decision_rationale": "Rationale"}),
            RecordingNormalizer(),
        )

        result = use_case.execute("oq_5")

        self.assertFalse(result.updated)
        self.assertEqual(result.reason, "empty_decision")

    def test_success_updates_oq_and_filters_messages(self):
        thread_ts = "1700000000.0001"
        messages = [
            {"ts": thread_ts, "user": "U1", "text": "Root message"},
            {"ts": "1700000000.0002", "user": "U1", "text": "We should do X"},
            {"ts": "1700000000.0003", "user": "U2", "text": "Agree"},
            {"ts": "1700000000.0004", "user": "U3", "text": ""},
        ]
        thread = {"ts": thread_ts, "messages": messages}

        oq = OpenQuestion(
            id="oq_6",
            artifact_id="art_6",
            question="Q6",
            context="ctx",
            status="PUBLISHED",
            slack_ts=None,
            decision=None,
            decision_rationale=None,
            published_channel_id="C1",
            published_message_ts=thread_ts,
        )

        normalizer = RecordingNormalizer(text="normalized thread")
        repo = FakeOQRepo([oq])
        use_case = BuildDecisionFromThreadUseCase(
            repo,
            FakeSlackPort(thread=thread),
            FakeLLMDecision(payload={"decision": "Do X", "decision_rationale": "Team agreed"}),
            normalizer,
            tech_team_user_ids={"U1", "U2"},
        )

        result = use_case.execute("oq_6")

        self.assertTrue(result.updated)
        self.assertIsNone(result.reason)
        self.assertEqual(result.decision, "Do X")
        self.assertEqual(result.decision_rationale, "Team agreed")
        self.assertEqual(result.messages_used, 2)
        self.assertEqual(repo.get_by_id("oq_6").decision, "Do X")
        self.assertEqual(repo.get_by_id("oq_6").decision_rationale, "Team agreed")
        self.assertEqual(repo.get_by_id("oq_6").status, "READY_TO_TRANSFORM")
        self.assertEqual(len(normalizer.calls), 1)
        self.assertEqual(
            normalizer.calls[0]["messages"],
            [
                {"ts": "1700000000.0002", "user": "U1", "text": "We should do X"},
                {"ts": "1700000000.0003", "user": "U2", "text": "Agree"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
