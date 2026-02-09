from __future__ import annotations

from dataclasses import dataclass

from src.domain.models import OpenQuestion
from src.ports.repositories import OpenQuestionRepository


@dataclass
class ModifyOQResult:
    updated: bool
    oq: OpenQuestion | None


class ModifyOQUseCase:
    # Updates editable fields on an Open Question and normalizes status based on decision fields.
    def __init__(self, oq_repo: OpenQuestionRepository) -> None:
        self.oq_repo = oq_repo

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

        if question is not None:
            oq.question = question
        if context is not None:
            oq.context = context
        if decision is not None:
            oq.decision = decision
        if decision_rationale is not None:
            oq.decision_rationale = decision_rationale

        oq.status = "DECIDED" if self._has_decision(oq) else "OPEN"
        self.oq_repo.save(oq)
        return ModifyOQResult(updated=True, oq=oq)

    def _has_decision(self, oq: OpenQuestion) -> bool:
        if not oq.decision or not oq.decision_rationale:
            return False
        if str(oq.decision).strip() == "" or str(oq.decision_rationale).strip() == "":
            return False
        return True
