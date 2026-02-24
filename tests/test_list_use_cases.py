import unittest

from src.domain.models import Artifact, ArtifactType, OpenQuestion, ProposedUpdate
from src.use_cases.list_artifacts import ListArtifactsUseCase
from src.use_cases.list_open_questions import ListOpenQuestionsUseCase
from src.use_cases.list_proposed_updates import ListProposedUpdatesUseCase


class FakeArtifactRepo:
    def __init__(self, artifacts):
        self._artifacts = artifacts

    def list_all(self):
        return list(self._artifacts)


class FakeOQRepo:
    def __init__(self, questions):
        self._questions = questions

    def list_all(self):
        return list(self._questions)


class FakePURepo:
    def __init__(self, updates):
        self._updates = updates

    def list_all(self):
        return list(self._updates)


class ListUseCasesTests(unittest.TestCase):
    # Verifies that list use cases return the expected items.
    def test_list_artifacts(self):
        artifacts = [
            Artifact(
                id="art_1",
                conversation_id="c1",
                type=ArtifactType.OQ,
                status="PENDING",
                rephrasing="",
                rationale="",
                summary_of_context="",
            )
        ]
        use_case = ListArtifactsUseCase(FakeArtifactRepo(artifacts))
        result = use_case.execute()
        self.assertEqual(result, artifacts)

    def test_list_open_questions(self):
        questions = [
            OpenQuestion(
                id="oq_1",
                artifact_id="art_1",
                question="Q1",
                context="ctx",
                status="OPEN",
                slack_ts=None,
                decision=None,
                decision_rationale=None,
            ),
            OpenQuestion(
                id="oq_2",
                artifact_id="art_2",
                question="Q2",
                context="ctx",
                status="TRANSFORMED",
                slack_ts=None,
                decision=None,
                decision_rationale=None,
            ),
        ]
        use_case = ListOpenQuestionsUseCase(FakeOQRepo(questions))
        result = use_case.execute()
        self.assertEqual(result, [questions[0]])

    def test_list_proposed_updates(self):
        updates = [
            ProposedUpdate(
                id="pu_1",
                artifact_id="art_1",
                source_oq_id=None,
                rephrasing="R",
                context="ctx",
                decision="",
                rationale="",
                status="DRAFT",
            )
        ]
        use_case = ListProposedUpdatesUseCase(FakePURepo(updates))
        result = use_case.execute()
        self.assertEqual(result, updates)


if __name__ == "__main__":
    unittest.main()
