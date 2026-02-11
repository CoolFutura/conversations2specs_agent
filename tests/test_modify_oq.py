import unittest

from src.domain.models import OpenQuestion, ProposedUpdate
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


class FakePURepo:
    def __init__(self, updates=None):
        self._updates = list(updates or [])
        self.saved = []
        self.deleted_source_ids = []

    def list_all(self):
        return list(self._updates)

    def get_by_id(self, pu_id: str):
        for pu in self._updates:
            if pu.id == pu_id:
                return pu
        return None

    def save(self, pu: ProposedUpdate):
        self._updates.append(pu)
        self.saved.append(pu)

    def create_from_artifact(self, artifact):
        raise NotImplementedError("Not needed for this test")

    def delete_by_source_oq_id(self, oq_id: str):
        self.deleted_source_ids.append(oq_id)
        self._updates = [pu for pu in self._updates if pu.source_oq_id != oq_id]


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
        pu_repo = FakePURepo()
        use_case = ModifyOQUseCase(oq_repo, pu_repo)

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
        pu_repo = FakePURepo()
        use_case = ModifyOQUseCase(oq_repo, pu_repo)

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
        pu_repo = FakePURepo()
        use_case = ModifyOQUseCase(oq_repo, pu_repo)

        result = use_case.execute("missing", question="X")

        self.assertFalse(result.updated)
        self.assertIsNone(result.oq)

    def test_decided_oq_deletes_old_pu_and_recreates_new_one(self):
        oq = OpenQuestion(
            id="oq_3",
            artifact_id="art_3",
            question="Q3",
            context="ctx",
            status="DECIDED",
            slack_ts=None,
            decision="DECISION",
            decision_rationale="WHY",
        )
        existing_pu = ProposedUpdate(
            id="pu_old",
            artifact_id="art_3",
            source_oq_id="oq_3",
            rephrasing="Old rephrasing",
            context="old ctx",
            decision="DECISION",
            rationale="WHY",
            status="DRAFT",
        )

        oq_repo = FakeOQRepo([oq])
        pu_repo = FakePURepo([existing_pu])
        use_case = ModifyOQUseCase(oq_repo, pu_repo)

        result = use_case.execute("oq_3", context="new ctx")

        self.assertTrue(result.updated)
        self.assertIn("oq_3", pu_repo.deleted_source_ids)
        self.assertEqual(len(pu_repo.saved), 1)
        new_pu = pu_repo.saved[0]
        self.assertEqual(new_pu.source_oq_id, "oq_3")
        self.assertEqual(new_pu.context, "new ctx")

    def test_open_oq_becomes_decided_and_creates_pu(self):
        oq = OpenQuestion(
            id="oq_4",
            artifact_id="art_4",
            question="Q4",
            context="ctx",
            status="OPEN",
            slack_ts=None,
            decision=None,
            decision_rationale=None,
        )

        oq_repo = FakeOQRepo([oq])
        pu_repo = FakePURepo()
        use_case = ModifyOQUseCase(oq_repo, pu_repo)

        result = use_case.execute(
            "oq_4",
            decision="DECISION",
            decision_rationale="WHY",
        )

        self.assertTrue(result.updated)
        self.assertEqual(result.oq.status, "DECIDED")
        self.assertEqual(len(pu_repo.saved), 1)
        new_pu = pu_repo.saved[0]
        self.assertEqual(new_pu.source_oq_id, "oq_4")


if __name__ == "__main__":
    unittest.main()
