from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.domain.models import ProposedUpdate, SpecUpdate
from src.ports.repositories import ProposedUpdateRepository, SpecUpdateRepository


@dataclass
class ApprovePUResult:
    spec_update: SpecUpdate | None
    remaining_drafts: int | None


class ApprovePUUseCase:
    # Approves a Proposed Update, creates a Spec Update, and counts remaining drafts.
    def __init__(
        self,
        pu_repo: ProposedUpdateRepository,
        spec_repo: SpecUpdateRepository,
    ) -> None:
        self.pu_repo = pu_repo
        self.spec_repo = spec_repo

    def execute(self, pu_id: str) -> ApprovePUResult:
        pu = self.pu_repo.get_by_id(pu_id)
        if not pu:
            return ApprovePUResult(spec_update=None, remaining_drafts=None)

        pu.status = "APPROVED"
        self.pu_repo.save(pu)

        spec_update = self._create_spec_update(pu)
        self.spec_repo.save(spec_update)

        remaining_drafts = sum(1 for item in self.pu_repo.list_all() if item.status == "DRAFT")
        return ApprovePUResult(spec_update=spec_update, remaining_drafts=remaining_drafts)

    def _create_spec_update(self, pu: ProposedUpdate) -> SpecUpdate:
        return SpecUpdate(
            id=f"su_{uuid.uuid4().hex[:8]}",
            pu_id=pu.id,
            content=pu.rephrasing,
            decision=pu.decision,
            status="ACTIVE",
        )
