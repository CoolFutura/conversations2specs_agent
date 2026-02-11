from __future__ import annotations

from src.domain.models import ProposedUpdate
from src.ports.repositories import ProposedUpdateRepository


class ListProposedUpdatesUseCase:
    # Returns all proposed updates from the repository.
    def __init__(self, pu_repo: ProposedUpdateRepository) -> None:
        self.pu_repo = pu_repo

    def execute(self) -> list[ProposedUpdate]:
        return list(self.pu_repo.list_all())
