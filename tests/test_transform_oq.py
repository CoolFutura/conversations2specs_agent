import unittest

from src.domain.models import OpenQuestion, ProposedUpdate
from src.use_cases.transform_oq import TransformOQUseCase


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


class FakePURepo:
    def __init__(self):
        self.saved = []

    def save(self, pu: ProposedUpdate):
        self.saved.append(pu)

    def create_from_artifact(self, artifact):
        raise NotImplementedError("Not needed for this test")


# Verifies that TransformOQUseCase creates a PU and updates OQ status correctly.
class TransformOQUseCaseTests(unittest.TestCase):
    def test_transforms_only_decided_oqs_and_counts_remaining(self):
        oq_decided = OpenQuestion(
            id="oq_1",
            artifact_id="art_1",
            question="Q1",
            context="ctx",
            status="DECIDED",
            slack_ts=None,
            decision="DECISION",
            decision_rationale="WHY",
        )
        oq_undecided = OpenQuestion(
            id="oq_2",
            artifact_id="art_2",
            question="Q2",
            context="ctx",
            status="OPEN",
            slack_ts=None,
            decision=None,
            decision_rationale=None,
        )

        oq_repo = FakeOQRepo([oq_decided, oq_undecided])
        pu_repo = FakePURepo()
        use_case = TransformOQUseCase(oq_repo, pu_repo)

        result = use_case.execute()

        self.assertEqual(result.transformed_count, 1)
        self.assertEqual(result.open_questions_remaining, 1)
        self.assertEqual(len(pu_repo.saved), 1)
        self.assertEqual(oq_repo.get_by_id("oq_1").status, "TRANSFORMED")
        self.assertEqual(oq_repo.get_by_id("oq_2").status, "OPEN")

        created_pu = pu_repo.saved[0]
        self.assertEqual(created_pu.source_oq_id, "oq_1")
        self.assertEqual(created_pu.decision, "DECISION")
        self.assertEqual(created_pu.rephrasing, "Q1")
        self.assertEqual(created_pu.context, "ctx")
        self.assertEqual(created_pu.rationale, "WHY")

    def test_no_decided_oqs_creates_nothing(self):
        oq_undecided = OpenQuestion(
            id="oq_3",
            artifact_id="art_3",
            question="Q3",
            context="ctx",
            status="OPEN",
            slack_ts=None,
            decision="",
            decision_rationale="",
        )

        oq_repo = FakeOQRepo([oq_undecided])
        pu_repo = FakePURepo()
        use_case = TransformOQUseCase(oq_repo, pu_repo)

        result = use_case.execute()

        self.assertEqual(result.transformed_count, 0)
        self.assertEqual(result.open_questions_remaining, 1)
        self.assertEqual(len(pu_repo.saved), 0)

    def test_missing_rationale_prevents_transformation(self):
        oq_missing_rationale = OpenQuestion(
            id="oq_4",
            artifact_id="art_4",
            question="Q4",
            context="ctx",
            status="OPEN",
            slack_ts=None,
            decision="DECISION",
            decision_rationale="  ",
        )

        oq_repo = FakeOQRepo([oq_missing_rationale])
        pu_repo = FakePURepo()
        use_case = TransformOQUseCase(oq_repo, pu_repo)

        result = use_case.execute()

        self.assertEqual(result.transformed_count, 0)
        self.assertEqual(result.open_questions_remaining, 1)
        self.assertEqual(len(pu_repo.saved), 0)


if __name__ == "__main__":
    unittest.main()
