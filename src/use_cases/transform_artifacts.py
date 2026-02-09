from __future__ import annotations

from src.domain.models import ArtifactType
from src.ports.repositories import ArtifactRepository, OpenQuestionRepository, ProposedUpdateRepository


class TransformArtifactsUseCase:
    # Orchestrates the conversion of pending artifacts into OQs/PUs via repositories.
    def __init__(
        self,
        artifact_repo: ArtifactRepository,
        oq_repo: OpenQuestionRepository,
        pu_repo: ProposedUpdateRepository,
    ) -> None:
        self.artifact_repo = artifact_repo
        self.oq_repo = oq_repo
        self.pu_repo = pu_repo

    def execute(self) -> tuple[int, int]:
        oq_count = 0
        pu_count = 0

        for artifact in self.artifact_repo.list_all():
            if artifact.status != "PENDING":
                continue

            if artifact.type == ArtifactType.OQ:
                self.oq_repo.create_from_artifact(artifact)
                artifact.status = "OQ"
                oq_count += 1
            elif artifact.type == ArtifactType.PU:
                self.pu_repo.create_from_artifact(artifact)
                artifact.status = "PU"
                pu_count += 1

            self.artifact_repo.save(artifact)

        return oq_count, pu_count
