import unittest

from src.domain.models import OpenQuestion
from src.use_cases.publish_oq import PublishOQsUseCase


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


class FakeSlackPublish:
    def __init__(self):
        self.posts = []
        self.updates = []

    def post_message(self, channel_id: str, text: str) -> str:
        self.posts.append((channel_id, text))
        return "123.456"

    def update_message(self, channel_id: str, message_ts: str, text: str) -> str:
        self.updates.append((channel_id, message_ts, text))
        return message_ts


class PublishOQsUseCaseTests(unittest.TestCase):
    # Verifies publish/republish/skip behavior based on status and last_modified_at.
    def test_publish_new_and_skip_unmodified(self):
        oq_new = OpenQuestion(
            id="oq_1",
            artifact_id="art_1",
            question="Q1",
            context="ctx",
            status="OPEN",
            slack_ts=None,
        )
        oq_published = OpenQuestion(
            id="oq_2",
            artifact_id="art_2",
            question="Q2",
            context="ctx",
            status="PUBLISHED",
            slack_ts=None,
            published_at="2025-01-01T00:00:00",
            published_message_ts="111.222",
            published_channel_id="C1",
            last_modified_at="2025-01-01T00:00:00",
        )

        repo = FakeOQRepo([oq_new, oq_published])
        slack = FakeSlackPublish()
        use_case = PublishOQsUseCase(repo, slack)

        result = use_case.execute(["oq_1", "oq_2"], "C1")

        self.assertIn("oq_1", result.published_ids)
        self.assertIn("oq_2", result.skipped_ids)
        self.assertEqual(len(slack.posts), 1)
        self.assertEqual(len(slack.updates), 0)

    def test_republish_when_modified(self):
        oq_modified = OpenQuestion(
            id="oq_3",
            artifact_id="art_3",
            question="Q3",
            context="ctx",
            status="OPEN",
            slack_ts=None,
            published_at="2025-01-01T00:00:00",
            published_message_ts="333.444",
            published_channel_id="C1",
            last_modified_at="2025-01-02T00:00:00",
        )

        repo = FakeOQRepo([oq_modified])
        slack = FakeSlackPublish()
        use_case = PublishOQsUseCase(repo, slack)

        result = use_case.execute(["oq_3"], "C1")

        self.assertIn("oq_3", result.updated_ids)
        self.assertEqual(len(slack.updates), 1)
        self.assertEqual(slack.updates[0][1], "333.444")

    # Ensures non-OPEN OQs are skipped.
    def test_skip_when_status_not_open(self):
        oq_transformed = OpenQuestion(
            id="oq_4",
            artifact_id="art_4",
            question="Q4",
            context="ctx",
            status="TRANSFORMED",
            slack_ts=None,
        )

        repo = FakeOQRepo([oq_transformed])
        slack = FakeSlackPublish()
        use_case = PublishOQsUseCase(repo, slack)

        result = use_case.execute(["oq_4"], "C1")

        self.assertIn("oq_4", result.skipped_ids)
        self.assertEqual(len(slack.posts), 0)
        self.assertEqual(len(slack.updates), 0)


if __name__ == "__main__":
    unittest.main()
