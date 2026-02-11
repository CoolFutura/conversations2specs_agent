from __future__ import annotations

from typing import Iterable, Protocol

from src.domain.models import Artifact, OpenQuestion, ProposedUpdate, SpecUpdate


class ArtifactRepository(Protocol):
    def list_all(self) -> Iterable[Artifact]:
        ...

    def save(self, artifact: Artifact) -> None:
        ...


class OpenQuestionRepository(Protocol):
    def list_all(self) -> Iterable[OpenQuestion]:
        ...

    def get_by_id(self, oq_id: str) -> OpenQuestion | None:
        ...

    def save(self, oq: OpenQuestion) -> None:
        ...

    def create_from_artifact(self, artifact: Artifact) -> OpenQuestion:
        ...


class ProposedUpdateRepository(Protocol):
    def list_all(self) -> Iterable[ProposedUpdate]:
        ...

    def get_by_id(self, pu_id: str) -> ProposedUpdate | None:
        ...

    def save(self, pu: ProposedUpdate) -> None:
        ...

    def create_from_artifact(self, artifact: Artifact) -> ProposedUpdate:
        ...

    def delete_by_source_oq_id(self, oq_id: str) -> None:
        ...


class SpecUpdateRepository(Protocol):
    def save(self, spec_update: SpecUpdate) -> None:
        ...
