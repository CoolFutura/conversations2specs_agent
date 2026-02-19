from __future__ import annotations

from src.domain.models import OpenQuestion
from src.ports.repositories import OpenQuestionRepository


class ListOpenQuestionsUseCase:
    # Returns only open questions from the repository.
    def __init__(self, oq_repo: OpenQuestionRepository) -> None:
        self.oq_repo = oq_repo

    def execute(self) -> list[OpenQuestion]:
        return [oq for oq in self.oq_repo.list_all() if oq.status == "OPEN"]
