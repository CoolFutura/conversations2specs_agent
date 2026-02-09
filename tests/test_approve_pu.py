import unittest

from src.domain.models import ProposedUpdate
from src.use_cases.approve_pu import ApprovePUUseCase


class FakePURepo:
    def __init__(self, updates):
        self._updates = {u.id: u for u in updates}
        self.saved = []

    def list_all(self):
        return list(self._updates.values())

    def get_by_id(self, pu_id: str):
        return self._updates.get(pu_id)

    def save(self, pu: ProposedUpdate):
        self._updates[pu.id] = pu
        self.saved.append(pu)

    def create_from_artifact(self, artifact):
        raise NotImplementedError("Not needed for this test")


class FakeSpecRepo:
    def __init__(self):
        self.saved = []

    def save(self, spec_update):
        self.saved.append(spec_update)


# Verifies that ApprovePUUseCase creates spec updates and tracks remaining drafts correctly.
class ApprovePUUseCaseTests(unittest.TestCase):
    # Verifies that approving a PU creates a spec update and marks the PU approved.
    def test_approves_pu_and_counts_remaining(self):
        pu_target = ProposedUpdate(
            id="pu_1",
            artifact_id="art_1",
            source_oq_id=None,
            rephrasing="Update content",
            context="ctx",
            decision="DECISION",
            rationale="why",
            status="DRAFT",
        )
        pu_other = ProposedUpdate(
            id="pu_2",
            artifact_id="art_2",
            source_oq_id=None,
            rephrasing="Another",
            context="ctx",
            decision="",
            rationale="",
            status="DRAFT",
        )

        pu_repo = FakePURepo([pu_target, pu_other])
        spec_repo = FakeSpecRepo()

        use_case = ApprovePUUseCase(pu_repo, spec_repo)
        result = use_case.execute("pu_1")

        self.assertIsNotNone(result.spec_update)
        self.assertEqual(pu_repo.get_by_id("pu_1").status, "APPROVED")
        self.assertEqual(result.spec_update.pu_id, "pu_1")
        self.assertEqual(result.spec_update.content, "Update content")
        self.assertEqual(result.spec_update.decision, "DECISION")
        self.assertEqual(result.spec_update.status, "ACTIVE")
        self.assertEqual(result.remaining_drafts, 1)
        self.assertEqual(len(spec_repo.saved), 1)

    def test_returns_none_when_pu_missing(self):
        pu_repo = FakePURepo([])
        spec_repo = FakeSpecRepo()
        use_case = ApprovePUUseCase(pu_repo, spec_repo)

        result = use_case.execute("missing")

        self.assertIsNone(result.spec_update)
        self.assertIsNone(result.remaining_drafts)
        self.assertEqual(len(spec_repo.saved), 0)

    def test_remaining_drafts_zero_when_last_draft_approved(self):
        pu_target = ProposedUpdate(
            id="pu_last",
            artifact_id="art_last",
            source_oq_id=None,
            rephrasing="Final update",
            context="ctx",
            decision="DECISION",
            rationale="why",
            status="DRAFT",
        )

        pu_repo = FakePURepo([pu_target])
        spec_repo = FakeSpecRepo()

        use_case = ApprovePUUseCase(pu_repo, spec_repo)
        result = use_case.execute("pu_last")

        self.assertIsNotNone(result.spec_update)
        self.assertEqual(result.remaining_drafts, 0)


if __name__ == "__main__":
    unittest.main()
