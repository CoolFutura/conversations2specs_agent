import unittest

from src.domain.models import OpenQuestion
from src.use_cases.add_decision import AddDecisionUseCase


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


# Verifies that AddDecisionUseCase stores decision fields on an OQ.
class AddDecisionUseCaseTests(unittest.TestCase):
    def test_adds_decision_and_rationale(self):
        oq = OpenQuestion(
            id="oq_1",
            artifact_id="art_1",
            question="Q1",
            context="ctx",
            status="OPEN",
            slack_ts=None,
            decision=None,
            decision_rationale=None,
        )

        oq_repo = FakeOQRepo([oq])
        use_case = AddDecisionUseCase(oq_repo)

        result = use_case.execute("oq_1", decision="DECISION", rationale="WHY")

        self.assertTrue(result.updated)
        self.assertIsNotNone(result.oq)
        self.assertEqual(result.oq.decision, "DECISION")
        self.assertEqual(result.oq.decision_rationale, "WHY")
        self.assertEqual(result.oq.status, "DECIDED")
        self.assertEqual(oq_repo.get_by_id("oq_1").decision, "DECISION")

    def test_returns_false_when_oq_missing(self):
        oq_repo = FakeOQRepo([])
        use_case = AddDecisionUseCase(oq_repo)

        result = use_case.execute("missing", decision="X", rationale="Y")

        self.assertFalse(result.updated)
        self.assertIsNone(result.oq)

    def test_empty_decision_or_rationale_keeps_status_open(self):
        oq = OpenQuestion(
            id="oq_2",
            artifact_id="art_2",
            question="Q2",
            context="ctx",
            status="OPEN",
            slack_ts=None,
            decision=None,
            decision_rationale=None,
        )

        oq_repo = FakeOQRepo([oq])
        use_case = AddDecisionUseCase(oq_repo)

        result = use_case.execute("oq_2", decision="DECISION", rationale="  ")

        self.assertTrue(result.updated)
        self.assertIsNotNone(result.oq)
        self.assertEqual(result.oq.status, "OPEN")


if __name__ == "__main__":
    unittest.main()
