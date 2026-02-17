from __future__ import annotations

import datetime
from dataclasses import dataclass

from src.domain.models import OpenQuestion
from src.ports.repositories import OpenQuestionRepository, ProposedUpdateRepository


@dataclass
class ModifyOQResult:
    updated: bool
    oq: OpenQuestion | None


class ModifyOQUseCase:
    # Updates editable fields on an Open Question, normalizes status, and refreshes linked PUs.
    def __init__(self, oq_repo: OpenQuestionRepository, pu_repo: ProposedUpdateRepository) -> None:
        self.oq_repo = oq_repo
        self.pu_repo = pu_repo

    def execute(
        self,
        oq_id: str,
        question: str | None = None,
        context: str | None = None,
        decision: str | None = None,
        decision_rationale: str | None = None,
    ) -> ModifyOQResult:
        oq = self.oq_repo.get_by_id(oq_id)
        if not oq:
            return ModifyOQResult(updated=False, oq=None)

        was_decided = oq.status == "DECIDED"

        if question is not None:
            oq.question = question
        if context is not None:
            oq.context = context
        if decision is not None:
            oq.decision = decision
        if decision_rationale is not None:
            oq.decision_rationale = decision_rationale

        oq.status = "OPEN"
        oq.last_modified_at = datetime.datetime.now().isoformat()
        self.oq_repo.save(oq)

        if was_decided:
            self.pu_repo.delete_by_source_oq_id(oq.id)

        return ModifyOQResult(updated=True, oq=oq)

    # No helper methods needed beyond modification logic.
