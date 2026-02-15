import unittest

from src.domain.models import Artifact, ArtifactType, OpenQuestion, ProposedUpdate
from src.use_cases.delete_oq import DeleteOQUseCase, DeleteOQBatchUseCase


class FakeArtifactRepo:
    def __init__(self, artifacts):
        self._artifacts = {a.id: a for a in artifacts}
        self.saved = []

    def list_all(self):
        return list(self._artifacts.values())

    def get_by_id(self, artifact_id: str):
        return self._artifacts.get(artifact_id)

    def save(self, artifact: Artifact):
        self._artifacts[artifact.id] = artifact
        self.saved.append(artifact)


class FakeOQRepo:
    def __init__(self, questions):
        self._questions = {q.id: q for q in questions}
        self.deleted_ids = []

    def list_all(self):
        return list(self._questions.values())

    def get_by_id(self, oq_id: str):
        return self._questions.get(oq_id)

    def save(self, oq: OpenQuestion):
        self._questions[oq.id] = oq

    def delete_by_id(self, oq_id: str) -> None:
        self.deleted_ids.append(oq_id)
        self._questions.pop(oq_id, None)

    def create_from_artifact(self, artifact):
        raise NotImplementedError("Not needed for this test")


class FakePURepo:
    def __init__(self, updates):
        self._updates = list(updates)
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

    def create_from_artifact(self, artifact):
        raise NotImplementedError("Not needed for this test")

    def delete_by_source_oq_id(self, oq_id: str):
        self.deleted_source_ids.append(oq_id)
        self._updates = [pu for pu in self._updates if pu.source_oq_id != oq_id]


class DeleteOQUseCaseTests(unittest.TestCase):
    # Verifies that deleting an OQ removes it, deletes related PUs, and marks artifact IRRELEVANT.
    def test_delete_oq_marks_artifact_and_deletes_pus(self):
        artifact = Artifact(
            id="art_1",
            conversation_id="c1",
            type=ArtifactType.OQ,
            status="PENDING",
            rephrasing="",
            rationale="",
            summary_of_context="",
        )
        oq = OpenQuestion(
            id="oq_1",
            artifact_id="art_1",
            question="Q",
            context="ctx",
            status="OPEN",
            slack_ts=None,
            decision=None,
            decision_rationale=None,
        )
        pu = ProposedUpdate(
            id="pu_1",
            artifact_id="art_1",
            source_oq_id="oq_1",
            rephrasing="R",
            context="ctx",
            decision="",
            rationale="",
            status="DRAFT",
        )

        oq_repo = FakeOQRepo([oq])
        artifact_repo = FakeArtifactRepo([artifact])
        pu_repo = FakePURepo([pu])

        use_case = DeleteOQUseCase(oq_repo, artifact_repo, pu_repo)
        result = use_case.execute("oq_1")

        self.assertTrue(result.deleted)
        self.assertEqual(result.artifact_id, "art_1")
        self.assertEqual(artifact_repo.get_by_id("art_1").status, "IRRELEVANT")
        self.assertIn("oq_1", oq_repo.deleted_ids)
        self.assertIn("oq_1", pu_repo.deleted_source_ids)

    def test_returns_false_when_oq_missing(self):
        oq_repo = FakeOQRepo([])
        artifact_repo = FakeArtifactRepo([])
        pu_repo = FakePURepo([])

        use_case = DeleteOQUseCase(oq_repo, artifact_repo, pu_repo)
        result = use_case.execute("missing")

        self.assertFalse(result.deleted)
        self.assertIsNone(result.artifact_id)


class DeleteOQBatchUseCaseTests(unittest.TestCase):
    # Verifies that batch delete handles deleted and missing IDs.
    def test_batch_delete(self):
        artifact1 = Artifact(
            id="art_1",
            conversation_id="c1",
            type=ArtifactType.OQ,
            status="PENDING",
            rephrasing="",
            rationale="",
            summary_of_context="",
        )
        artifact2 = Artifact(
            id="art_2",
            conversation_id="c2",
            type=ArtifactType.OQ,
            status="PENDING",
            rephrasing="",
            rationale="",
            summary_of_context="",
        )
        oq1 = OpenQuestion(
            id="oq_1",
            artifact_id="art_1",
            question="Q1",
            context="ctx",
            status="OPEN",
            slack_ts=None,
            decision=None,
            decision_rationale=None,
        )
        oq2 = OpenQuestion(
            id="oq_2",
            artifact_id="art_2",
            question="Q2",
            context="ctx",
            status="OPEN",
            slack_ts=None,
            decision=None,
            decision_rationale=None,
        )

        oq_repo = FakeOQRepo([oq1, oq2])
        artifact_repo = FakeArtifactRepo([artifact1, artifact2])
        pu_repo = FakePURepo([])

        use_case = DeleteOQBatchUseCase(oq_repo, artifact_repo, pu_repo)
        result = use_case.execute(["oq_1", "missing", "oq_2"])

        self.assertEqual(set(result.deleted_ids), {"oq_1", "oq_2"})
        self.assertEqual(result.missing_ids, ["missing"])
        self.assertEqual(artifact_repo.get_by_id("art_1").status, "IRRELEVANT")
        self.assertEqual(artifact_repo.get_by_id("art_2").status, "IRRELEVANT")


if __name__ == "__main__":
    unittest.main()
