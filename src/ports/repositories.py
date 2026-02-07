from __future__ import annotations

from typing import Iterable, Protocol

from src.domain.models import Artifact, OpenQuestion, ProposedUpdate


class ArtifactRepository(Protocol):
    def list_all(self) -> Iterable[Artifact]:
        ...

    def save(self, artifact: Artifact) -> None:
        ...


class OpenQuestionRepository(Protocol):
    def create_from_artifact(self, artifact: Artifact) -> OpenQuestion:
        ...


class ProposedUpdateRepository(Protocol):
    def create_from_artifact(self, artifact: Artifact) -> ProposedUpdate:
        ...
