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
