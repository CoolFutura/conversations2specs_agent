from __future__ import annotations

from src.domain.models import Artifact
from src.ports.repositories import ArtifactRepository


class ListArtifactsUseCase:
    # Returns all artifacts from the repository.
    def __init__(self, artifact_repo: ArtifactRepository) -> None:
        self.artifact_repo = artifact_repo

    def execute(self) -> list[Artifact]:
        return list(self.artifact_repo.list_all())
