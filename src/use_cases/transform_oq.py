from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.domain.models import OpenQuestion, ProposedUpdate
from src.ports.repositories import OpenQuestionRepository, ProposedUpdateRepository


@dataclass
class TransformOQResult:
    transformed_count: int
    open_questions_remaining: int


class TransformOQUseCase:
    # Converts all decided Open Questions into Proposed Updates and tracks remaining OQs.
    def __init__(
        self,
        oq_repo: OpenQuestionRepository,
        pu_repo: ProposedUpdateRepository,
    ) -> None:
        self.oq_repo = oq_repo
        self.pu_repo = pu_repo

    def execute(self) -> TransformOQResult:
        transformed = 0

        for oq in self.oq_repo.list_all():
            if oq.status not in {"OPEN", "DECIDED", "READY_TO_TRANSFORM"}:
                continue
            if not self._has_decision(oq):
                continue

            oq.status = "TRANSFORMED"
            self.oq_repo.save(oq)

            pu = self._create_pu_from_oq(oq)
            self.pu_repo.save(pu)
            transformed += 1

        remaining = sum(1 for item in self.oq_repo.list_all() if item.status == "OPEN")
        return TransformOQResult(transformed_count=transformed, open_questions_remaining=remaining)

    def _create_pu_from_oq(
        self,
        oq: OpenQuestion,
    ) -> ProposedUpdate:
        return ProposedUpdate(
            id=f"pu_from_oq_{uuid.uuid4().hex[:8]}",
            artifact_id=oq.artifact_id,
            source_oq_id=oq.id,
            rephrasing=oq.question,
            context=oq.context,
            decision=oq.decision or "",
            rationale=oq.decision_rationale or "Transformed from OQ",
            status="DRAFT",
            source_channel_id=oq.source_channel_id,
            source_thread_ts=oq.source_thread_ts,
            source_thread_url=oq.source_thread_url,
        )

    def _has_decision(self, oq: OpenQuestion) -> bool:
        if not oq.decision or not oq.decision_rationale:
            return False
        if str(oq.decision).strip() == "" or str(oq.decision_rationale).strip() == "":
            return False
        return True
