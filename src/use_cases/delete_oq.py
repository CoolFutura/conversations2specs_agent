from __future__ import annotations

from dataclasses import dataclass

from src.ports.repositories import ArtifactRepository, OpenQuestionRepository, ProposedUpdateRepository


@dataclass
class DeleteOQResult:
    deleted: bool
    oq_id: str
    artifact_id: str | None


class DeleteOQUseCase:
    # Deletes an OQ, marks its artifact IRRELEVANT, and deletes linked PUs.
    def __init__(
        self,
        oq_repo: OpenQuestionRepository,
        artifact_repo: ArtifactRepository,
        pu_repo: ProposedUpdateRepository,
    ) -> None:
        self.oq_repo = oq_repo
        self.artifact_repo = artifact_repo
        self.pu_repo = pu_repo

    def execute(self, oq_id: str) -> DeleteOQResult:
        oq = self.oq_repo.get_by_id(oq_id)
        if not oq:
            return DeleteOQResult(deleted=False, oq_id=oq_id, artifact_id=None)

        self.oq_repo.delete_by_id(oq_id)
        self.pu_repo.delete_by_source_oq_id(oq_id)

        artifact = self.artifact_repo.get_by_id(oq.artifact_id)
        if artifact:
            artifact.status = "IRRELEVANT"
            self.artifact_repo.save(artifact)

        return DeleteOQResult(deleted=True, oq_id=oq_id, artifact_id=oq.artifact_id)


@dataclass
class DeleteOQBatchResult:
    deleted_ids: list[str]
    missing_ids: list[str]


class DeleteOQBatchUseCase:
    # Deletes multiple OQs, marks their artifacts IRRELEVANT, and deletes linked PUs.
    def __init__(
        self,
        oq_repo: OpenQuestionRepository,
        artifact_repo: ArtifactRepository,
        pu_repo: ProposedUpdateRepository,
    ) -> None:
        self.oq_repo = oq_repo
        self.artifact_repo = artifact_repo
        self.pu_repo = pu_repo

    def execute(self, oq_ids: list[str]) -> DeleteOQBatchResult:
        deleted_ids: list[str] = []
        missing_ids: list[str] = []

        for oq_id in oq_ids:
            oq = self.oq_repo.get_by_id(oq_id)
            if not oq:
                missing_ids.append(oq_id)
                continue

            self.oq_repo.delete_by_id(oq_id)
            self.pu_repo.delete_by_source_oq_id(oq_id)

            artifact = self.artifact_repo.get_by_id(oq.artifact_id)
            if artifact:
                artifact.status = "IRRELEVANT"
                self.artifact_repo.save(artifact)

            deleted_ids.append(oq_id)

        return DeleteOQBatchResult(deleted_ids=deleted_ids, missing_ids=missing_ids)
