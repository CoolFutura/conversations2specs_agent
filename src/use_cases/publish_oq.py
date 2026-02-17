from __future__ import annotations

import datetime
from dataclasses import dataclass

from src.domain.models import OpenQuestion
from src.ports.repositories import OpenQuestionRepository
from src.ports.slack_publish import SlackPublishPort


@dataclass
class PublishOQsResult:
    published_ids: list[str]
    updated_ids: list[str]
    skipped_ids: list[str]
    missing_ids: list[str]
    failed_ids: list[str]


class PublishOQsUseCase:
    # Publishes OQs to Slack; republishes only if modified since last publish.
    def __init__(self, oq_repo: OpenQuestionRepository, slack_publish: SlackPublishPort) -> None:
        self.oq_repo = oq_repo
        self.slack_publish = slack_publish

    def execute(self, oq_ids: list[str], channel_id: str) -> PublishOQsResult:
        published_ids: list[str] = []
        updated_ids: list[str] = []
        skipped_ids: list[str] = []
        missing_ids: list[str] = []
        failed_ids: list[str] = []

        for oq_id in oq_ids:
            oq = self.oq_repo.get_by_id(oq_id)
            if not oq:
                missing_ids.append(oq_id)
                continue

            message = self._build_message(oq)
            try:
                if oq.published_at:
                    if self._should_republish(oq):
                        if oq.published_message_ts:
                            ts = self.slack_publish.update_message(channel_id, oq.published_message_ts, message)
                            self._mark_published(oq, channel_id, ts)
                            updated_ids.append(oq_id)
                        else:
                            ts = self.slack_publish.post_message(channel_id, message)
                            self._mark_published(oq, channel_id, ts)
                            published_ids.append(oq_id)
                    else:
                        skipped_ids.append(oq_id)
                else:
                    ts = self.slack_publish.post_message(channel_id, message)
                    self._mark_published(oq, channel_id, ts)
                    published_ids.append(oq_id)
            except Exception:
                failed_ids.append(oq_id)
                continue

        return PublishOQsResult(
            published_ids=published_ids,
            updated_ids=updated_ids,
            skipped_ids=skipped_ids,
            missing_ids=missing_ids,
            failed_ids=failed_ids,
        )

    def _build_message(self, oq: OpenQuestion) -> str:
        return (
            f"Open Question:\n{oq.question}\n\n"
            f"Context:\n{oq.context}\n\n"
            "Please reply in this thread."
        )

    def _mark_published(self, oq: OpenQuestion, channel_id: str, message_ts: str) -> None:
        oq.status = "PUBLISHED"
        oq.published_at = datetime.datetime.now().isoformat()
        oq.published_message_ts = message_ts
        oq.published_channel_id = channel_id
        self.oq_repo.save(oq)

    def _should_republish(self, oq: OpenQuestion) -> bool:
        if not oq.last_modified_at or not oq.published_at:
            return False
        try:
            modified = datetime.datetime.fromisoformat(oq.last_modified_at)
            published = datetime.datetime.fromisoformat(oq.published_at)
        except Exception:
            return True
        return modified > published
