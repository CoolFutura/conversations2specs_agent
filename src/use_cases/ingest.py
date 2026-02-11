from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from src.ports.llm import LLMClassifierPort
from src.ports.repositories import ArtifactRepository
from src.ports.slack import SlackThreadsPort
from src.ports.traceability import TraceabilityPort
from src.use_cases.ingest_threads import IngestThreadsUseCase

Normalizer = Callable[[dict], str]


@dataclass
class IngestResult:
    threads_fetched: int
    artifacts_created: int


class IngestUseCase:
    # Orchestrates Slack fetch, LLM classification, and traceability persistence.
    def __init__(
        self,
        slack_port: SlackThreadsPort,
        llm_classifier: LLMClassifierPort,
        artifact_repo: ArtifactRepository,
        trace_port: TraceabilityPort,
        normalizer: Normalizer,
    ) -> None:
        self.slack_port = slack_port
        self.llm_classifier = llm_classifier
        self.artifact_repo = artifact_repo
        self.trace_port = trace_port
        self.normalizer = normalizer

    def execute(
        self,
        channel_id: str,
        on_start_run: Optional[Callable[[], None]] = None,
    ) -> IngestResult:
        threads = self.slack_port.fetch_threads(channel_id)
        if not threads:
            return IngestResult(threads_fetched=0, artifacts_created=0)

        if on_start_run:
            on_start_run()

        self.trace_port.save_threads(threads)

        ingest_threads = IngestThreadsUseCase(
            self.llm_classifier,
            self.artifact_repo,
            self.normalizer,
        )
        result = ingest_threads.execute(threads)

        self.trace_port.save_conversations(result.conversations)

        return IngestResult(
            threads_fetched=len(threads),
            artifacts_created=result.artifacts_created,
        )
