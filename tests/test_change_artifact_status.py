import unittest

from src.domain.models import Artifact, ArtifactType
from src.use_cases.change_artifact_status import ChangeArtifactStatusUseCase
from src.use_cases.change_artifact_status import ChangeArtifactStatusBatchUseCase


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


class ChangeArtifactStatusUseCaseTests(unittest.TestCase):
    # Verifies that ChangeArtifactStatusUseCase updates status when artifact exists.
    def test_updates_status_when_artifact_exists(self):
        artifact = Artifact(
            id="art_1",
            conversation_id="c1",
            type=ArtifactType.OQ,
            status="PENDING",
            rephrasing="",
            rationale="",
            summary_of_context="",
        )

        repo = FakeArtifactRepo([artifact])
        use_case = ChangeArtifactStatusUseCase(repo)

        result = use_case.execute("art_1", "PU")

        self.assertTrue(result.updated)
        self.assertEqual(result.artifact.status, "PU")
        self.assertEqual(repo.get_by_id("art_1").status, "PU")
        self.assertEqual(len(repo.saved), 1)

    def test_returns_false_when_artifact_missing(self):
        repo = FakeArtifactRepo([])
        use_case = ChangeArtifactStatusUseCase(repo)

        result = use_case.execute("missing", "OQ")

        self.assertFalse(result.updated)
        self.assertIsNone(result.artifact)
        self.assertEqual(len(repo.saved), 0)


class ChangeArtifactStatusBatchUseCaseTests(unittest.TestCase):
    # Verifies that batch status update handles updated and missing IDs.
    def test_updates_multiple_and_reports_missing(self):
        artifacts = [
            Artifact(
                id="art_1",
                conversation_id="c1",
                type=ArtifactType.OQ,
                status="PENDING",
                rephrasing="",
                rationale="",
                summary_of_context="",
            ),
            Artifact(
                id="art_2",
                conversation_id="c2",
                type=ArtifactType.PU,
                status="PENDING",
                rephrasing="",
                rationale="",
                summary_of_context="",
            ),
        ]
        repo = FakeArtifactRepo(artifacts)
        use_case = ChangeArtifactStatusBatchUseCase(repo)

        result = use_case.execute(["art_1", "missing", "art_2"], "IRRELEVANT")

        self.assertEqual(set(result.updated_ids), {"art_1", "art_2"})
        self.assertEqual(result.missing_ids, ["missing"])


if __name__ == "__main__":
    unittest.main()
