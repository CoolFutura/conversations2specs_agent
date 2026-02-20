from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from src.domain.models import OpenQuestion
from src.ports.llm import LLMDecisionPort
from src.ports.repositories import OpenQuestionRepository
from src.ports.slack import SlackThreadsPort

Normalizer = Callable[[dict], str]


@dataclass
class BuildDecisionFromThreadResult:
    updated: bool
    oq: OpenQuestion | None
    decision: str | None
    decision_rationale: str | None
    reason: str | None
    messages_used: int = 0


class BuildDecisionFromThreadUseCase:
    # Builds a decision from the published OQ's Slack thread replies.
    def __init__(
        self,
        oq_repo: OpenQuestionRepository,
        slack_port: SlackThreadsPort,
        llm_decider: LLMDecisionPort,
        normalizer: Normalizer,
        tech_team_user_ids: set[str] | None = None,
    ) -> None:
        self.oq_repo = oq_repo
        self.slack_port = slack_port
        self.llm_decider = llm_decider
        self.normalizer = normalizer
        self.tech_team_user_ids = tech_team_user_ids or set()

    def execute(self, oq_id: str) -> BuildDecisionFromThreadResult:
        oq = self.oq_repo.get_by_id(oq_id)
        if not oq:
            return BuildDecisionFromThreadResult(
                updated=False,
                oq=None,
                decision=None,
                decision_rationale=None,
                reason="missing_oq",
            )

        channel_id = oq.published_channel_id
        thread_ts = oq.published_message_ts
        if not channel_id or not thread_ts:
            return BuildDecisionFromThreadResult(
                updated=False,
                oq=oq,
                decision=None,
                decision_rationale=None,
                reason="not_published",
            )

        thread = self.slack_port.fetch_thread(channel_id, thread_ts)
        if not thread or not thread.get("messages"):
            return BuildDecisionFromThreadResult(
                updated=False,
                oq=oq,
                decision=None,
                decision_rationale=None,
                reason="thread_missing",
            )

        messages = thread.get("messages", [])
        tech_messages = [msg for msg in messages if self._is_tech_reply(msg, thread_ts)]
        if not tech_messages:
            return BuildDecisionFromThreadResult(
                updated=False,
                oq=oq,
                decision=None,
                decision_rationale=None,
                reason="no_tech_messages",
            )

        convo_text = self.normalizer({"messages": tech_messages})
        decision_payload = self.llm_decider.decide(oq.question, oq.context, convo_text)
        if not decision_payload:
            return BuildDecisionFromThreadResult(
                updated=False,
                oq=oq,
                decision=None,
                decision_rationale=None,
                reason="llm_failed",
            )

        decision = str(decision_payload.get("decision", "")).strip()
        rationale = str(
            decision_payload.get("decision_rationale", decision_payload.get("rationale", ""))
        ).strip()
        if not decision or not rationale:
            return BuildDecisionFromThreadResult(
                updated=False,
                oq=oq,
                decision=decision or None,
                decision_rationale=rationale or None,
                reason="empty_decision",
            )

        self._apply_decision(oq, decision, rationale)
        self.oq_repo.save(oq)

        return BuildDecisionFromThreadResult(
            updated=True,
            oq=oq,
            decision=decision,
            decision_rationale=rationale,
            reason=None,
            messages_used=len(tech_messages),
        )

    def _is_tech_reply(self, msg: dict, thread_ts: str) -> bool:
        if msg.get("ts") == thread_ts:
            return False
        if msg.get("bot_id") or msg.get("subtype") == "bot_message":
            return False
        user = msg.get("user")
        if not user:
            return False
        if self.tech_team_user_ids and user not in self.tech_team_user_ids:
            return False
        text = msg.get("text", "").strip()
        if not text:
            return False
        return True

    def _apply_decision(self, oq: OpenQuestion, decision: str, rationale: str) -> None:
        oq.decision = decision
        oq.decision_rationale = rationale
        if self._has_decision(oq):
            if oq.status == "PUBLISHED":
                oq.status = "READY_TO_TRANSFORM"
            elif oq.status in {"OPEN", "DECIDED"}:
                oq.status = "DECIDED"
        else:
            if oq.status == "DECIDED":
                oq.status = "OPEN"

    def _has_decision(self, oq: OpenQuestion) -> bool:
        if not oq.decision or not oq.decision_rationale:
            return False
        if str(oq.decision).strip() == "" or str(oq.decision_rationale).strip() == "":
            return False
        return True
