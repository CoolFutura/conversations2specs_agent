from __future__ import annotations

from dataclasses import dataclass

from src.domain.models import OpenQuestion
from src.ports.repositories import OpenQuestionRepository


@dataclass
class AddDecisionResult:
    updated: bool
    oq: OpenQuestion | None


class AddDecisionUseCase:
    # Adds decision fields to an Open Question without transforming it.
    def __init__(self, oq_repo: OpenQuestionRepository) -> None:
        self.oq_repo = oq_repo

    def execute(self, oq_id: str, decision: str, rationale: str) -> AddDecisionResult:
        oq = self.oq_repo.get_by_id(oq_id)
        if not oq:
            return AddDecisionResult(updated=False, oq=None)

        oq.decision = decision
        oq.decision_rationale = rationale
        if self._has_decision(oq):
            oq.status = "DECIDED"
        self.oq_repo.save(oq)
        return AddDecisionResult(updated=True, oq=oq)

    def _has_decision(self, oq: OpenQuestion) -> bool:
        if not oq.decision or not oq.decision_rationale:
            return False
        if str(oq.decision).strip() == "" or str(oq.decision_rationale).strip() == "":
            return False
        return True
