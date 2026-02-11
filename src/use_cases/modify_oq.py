from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.domain.models import OpenQuestion, ProposedUpdate
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

        oq.status = "DECIDED" if self._has_decision(oq) else "OPEN"
        self.oq_repo.save(oq)

        if oq.status == "DECIDED":
            self.pu_repo.delete_by_source_oq_id(oq.id)
            pu = self._create_pu_from_oq(oq)
            self.pu_repo.save(pu)
        elif was_decided:
            self.pu_repo.delete_by_source_oq_id(oq.id)

        return ModifyOQResult(updated=True, oq=oq)

    def _has_decision(self, oq: OpenQuestion) -> bool:
        if not oq.decision or not oq.decision_rationale:
            return False
        if str(oq.decision).strip() == "" or str(oq.decision_rationale).strip() == "":
            return False
        return True

    def _create_pu_from_oq(self, oq: OpenQuestion) -> ProposedUpdate:
        return ProposedUpdate(
            id=f"pu_from_oq_{uuid.uuid4().hex[:8]}",
            artifact_id=oq.artifact_id,
            source_oq_id=oq.id,
            rephrasing=oq.question,
            context=oq.context,
            decision=oq.decision or "",
            rationale=oq.decision_rationale or "Transformed from OQ",
            status="DRAFT",
        )
