import unittest

from src.domain.models import OpenQuestion
from src.use_cases.modify_oq import ModifyOQUseCase


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


# Verifies that ModifyOQUseCase updates fields and normalizes status.
class ModifyOQUseCaseTests(unittest.TestCase):
    def test_updates_fields_and_sets_decided_when_complete(self):
        oq = OpenQuestion(
            id="oq_1",
            artifact_id="art_1",
            question="Old question",
            context="Old context",
            status="OPEN",
            slack_ts=None,
            decision=None,
            decision_rationale=None,
        )

        oq_repo = FakeOQRepo([oq])
        use_case = ModifyOQUseCase(oq_repo)

        result = use_case.execute(
            "oq_1",
            question="New question",
            context="New context",
            decision="DECISION",
            decision_rationale="WHY",
        )

        self.assertTrue(result.updated)
        self.assertIsNotNone(result.oq)
        self.assertEqual(result.oq.question, "New question")
        self.assertEqual(result.oq.context, "New context")
        self.assertEqual(result.oq.decision, "DECISION")
        self.assertEqual(result.oq.decision_rationale, "WHY")
        self.assertEqual(result.oq.status, "DECIDED")

    def test_sets_open_when_decision_incomplete(self):
        oq = OpenQuestion(
            id="oq_2",
            artifact_id="art_2",
            question="Q2",
            context="ctx",
            status="DECIDED",
            slack_ts=None,
            decision="DECISION",
            decision_rationale="WHY",
        )

        oq_repo = FakeOQRepo([oq])
        use_case = ModifyOQUseCase(oq_repo)

        result = use_case.execute(
            "oq_2",
            decision="",
            decision_rationale="",
        )

        self.assertTrue(result.updated)
        self.assertIsNotNone(result.oq)
        self.assertEqual(result.oq.status, "OPEN")

    def test_returns_false_when_oq_missing(self):
        oq_repo = FakeOQRepo([])
        use_case = ModifyOQUseCase(oq_repo)

        result = use_case.execute("missing", question="X")

        self.assertFalse(result.updated)
        self.assertIsNone(result.oq)


if __name__ == "__main__":
    unittest.main()
