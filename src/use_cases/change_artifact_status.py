from __future__ import annotations

from dataclasses import dataclass

from src.domain.models import Artifact
from src.ports.repositories import ArtifactRepository


@dataclass
class ChangeArtifactStatusResult:
    updated: bool
    artifact: Artifact | None


class ChangeArtifactStatusUseCase:
    # Updates the status of a single artifact if it exists.
    def __init__(self, artifact_repo: ArtifactRepository) -> None:
        self.artifact_repo = artifact_repo

    def execute(self, artifact_id: str, status: str) -> ChangeArtifactStatusResult:
        artifact = self.artifact_repo.get_by_id(artifact_id)
        if not artifact:
            return ChangeArtifactStatusResult(updated=False, artifact=None)

        artifact.status = status
        self.artifact_repo.save(artifact)
        return ChangeArtifactStatusResult(updated=True, artifact=artifact)


@dataclass
class ChangeArtifactStatusBatchResult:
    updated_ids: list[str]
    missing_ids: list[str]


class ChangeArtifactStatusBatchUseCase:
    # Updates the status for multiple artifacts and reports missing IDs.
    def __init__(self, artifact_repo: ArtifactRepository) -> None:
        self.artifact_repo = artifact_repo

    def execute(self, artifact_ids: list[str], status: str) -> ChangeArtifactStatusBatchResult:
        updated_ids: list[str] = []
        missing_ids: list[str] = []

        for artifact_id in artifact_ids:
            artifact = self.artifact_repo.get_by_id(artifact_id)
            if not artifact:
                missing_ids.append(artifact_id)
                continue

            artifact.status = status
            self.artifact_repo.save(artifact)
            updated_ids.append(artifact_id)

        return ChangeArtifactStatusBatchResult(updated_ids=updated_ids, missing_ids=missing_ids)
