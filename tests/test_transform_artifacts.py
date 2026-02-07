import unittest

from src.domain.models import Artifact, ArtifactType
from src.use_cases.transform_artifacts import TransformArtifactsUseCase


class FakeArtifactRepo:
    def __init__(self, artifacts, call_log=None):
        self._artifacts = {a.id: a for a in artifacts}
        self.save_calls = 0
        self.saved_ids = []
        self.call_log = call_log if call_log is not None else []

    def list_all(self):
        self.call_log.append("artifacts.list_all")
        return list(self._artifacts.values())

    def save(self, artifact):
        self.save_calls += 1
        self.saved_ids.append(artifact.id)
        self._artifacts[artifact.id] = artifact
        self.call_log.append(f"artifacts.save:{artifact.id}")


class FakeOQRepo:
    def __init__(self, call_log=None):
        self.created = []
        self.call_log = call_log if call_log is not None else []

    def create_from_artifact(self, artifact):
        self.created.append(artifact)
        self.call_log.append(f"oq.create_from_artifact:{artifact.id}")
        return artifact


class FakePURepo:
    def __init__(self, call_log=None):
        self.created = []
        self.call_log = call_log if call_log is not None else []

    def create_from_artifact(self, artifact):
        self.created.append(artifact)
        self.call_log.append(f"pu.create_from_artifact:{artifact.id}")
        return artifact


class TransformArtifactsUseCaseTests(unittest.TestCase):
    def test_creates_oq_and_pu_and_updates_status_and_saves(self):
        artifacts = [
            Artifact(
                id="art_1",
                conversation_id="c1",
                type=ArtifactType.OQ,
                status="PENDING",
                rephrasing="question",
                rationale="",
                summary_of_context="ctx",
            ),
            Artifact(
                id="art_2",
                conversation_id="c2",
                type=ArtifactType.PU,
                status="PENDING",
                rephrasing="update",
                rationale="",
                summary_of_context="ctx",
            ),
            Artifact(
                id="art_3",
                conversation_id="c3",
                type=ArtifactType.OQ,
                status="OQ",
                rephrasing="already done",
                rationale="",
                summary_of_context="ctx",
            ),
        ]

        shared_log = []
        artifact_repo = FakeArtifactRepo(artifacts, shared_log)
        oq_repo = FakeOQRepo(shared_log)
        pu_repo = FakePURepo(shared_log)

        use_case = TransformArtifactsUseCase(artifact_repo, oq_repo, pu_repo)
        oq_count, pu_count = use_case.execute()

        self.assertEqual(oq_count, 1)
        self.assertEqual(pu_count, 1)
        self.assertEqual(len(oq_repo.created), 1)
        self.assertEqual(len(pu_repo.created), 1)
        self.assertEqual(artifact_repo._artifacts["art_1"].status, "OQ")
        self.assertEqual(artifact_repo._artifacts["art_2"].status, "PU")
        # art_3 was not pending, should be unchanged
        self.assertEqual(artifact_repo._artifacts["art_3"].status, "OQ")

        # verify saves: only pending artifacts should be saved (art_1, art_2)
        self.assertEqual(artifact_repo.save_calls, 2)
        self.assertEqual(set(artifact_repo.saved_ids), {"art_1", "art_2"})

    def test_no_pending_artifacts_creates_nothing_and_saves_nothing(self):
        artifacts = [
            Artifact(
                id="art_10",
                conversation_id="c10",
                type=ArtifactType.OQ,
                status="OQ",
                rephrasing="already oq",
                rationale="",
                summary_of_context="ctx",
            ),
            Artifact(
                id="art_11",
                conversation_id="c11",
                type=ArtifactType.PU,
                status="PU",
                rephrasing="already pu",
                rationale="",
                summary_of_context="ctx",
            ),
        ]

        shared_log = []
        artifact_repo = FakeArtifactRepo(artifacts, shared_log)
        oq_repo = FakeOQRepo(shared_log)
        pu_repo = FakePURepo(shared_log)

        use_case = TransformArtifactsUseCase(artifact_repo, oq_repo, pu_repo)
        oq_count, pu_count = use_case.execute()

        self.assertEqual(oq_count, 0)
        self.assertEqual(pu_count, 0)
        self.assertEqual(len(oq_repo.created), 0)
        self.assertEqual(len(pu_repo.created), 0)
        self.assertEqual(artifact_repo.save_calls, 0)
        self.assertEqual(artifact_repo.saved_ids, [])

    def test_call_order_for_pending_artifacts(self):
        artifacts = [
            Artifact(
                id="art_a",
                conversation_id="c_a",
                type=ArtifactType.OQ,
                status="PENDING",
                rephrasing="question",
                rationale="",
                summary_of_context="ctx",
            ),
            Artifact(
                id="art_b",
                conversation_id="c_b",
                type=ArtifactType.PU,
                status="PENDING",
                rephrasing="update",
                rationale="",
                summary_of_context="ctx",
            ),
        ]

        shared_log = []
        artifact_repo = FakeArtifactRepo(artifacts, shared_log)
        oq_repo = FakeOQRepo(shared_log)
        pu_repo = FakePURepo(shared_log)

        use_case = TransformArtifactsUseCase(artifact_repo, oq_repo, pu_repo)
        use_case.execute()

        # We verify the overall order across repos by merging logs
        combined_log = shared_log

        # Expected sequence:
        # 1) list_all
        # 2) create OQ for art_a
        # 3) save art_a
        # 4) create PU for art_b
        # 5) save art_b
        expected = [
            "artifacts.list_all",
            "oq.create_from_artifact:art_a",
            "artifacts.save:art_a",
            "pu.create_from_artifact:art_b",
            "artifacts.save:art_b",
        ]

        self.assertEqual(combined_log, expected)


if __name__ == "__main__":
    unittest.main()
