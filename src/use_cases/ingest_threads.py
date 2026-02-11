from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Callable

from src.domain.models import Artifact, ArtifactType
from src.ports.llm import LLMClassifierPort
from src.ports.repositories import ArtifactRepository

Normalizer = Callable[[dict], str]


@dataclass
class IngestThreadsResult:
    conversations: list[dict]
    artifacts_created: int


class IngestThreadsUseCase:
    # Classifies provided threads and stores artifacts for non-duplicate, relevant conversations.
    def __init__(
        self,
        llm_classifier: LLMClassifierPort,
        artifact_repo: ArtifactRepository,
        normalizer: Normalizer,
    ) -> None:
        self.llm_classifier = llm_classifier
        self.artifact_repo = artifact_repo
        self.normalizer = normalizer

    def execute(self, threads: list[dict]) -> IngestThreadsResult:
        existing_artifacts = self.artifact_repo.list_all()
        existing_conv_ids = {art.conversation_id for art in existing_artifacts}

        conversations: list[dict] = []
        artifacts_created = 0

        for thread in threads:
            ts = thread.get("ts")
            if not ts:
                continue

            conv_text = self.normalizer(thread)
            conversations.append({"ts": ts, "text": conv_text})

            if ts in existing_conv_ids:
                continue

            classification = self.llm_classifier.classify(conv_text)
            if not classification:
                continue

            artifact_type = self._parse_artifact_type(classification.get("type"))
            if artifact_type == ArtifactType.IRRELEVANT:
                continue

            artifact = self._artifact_from_classification(ts, artifact_type, classification)
            self.artifact_repo.save(artifact)
            artifacts_created += 1

        return IngestThreadsResult(
            conversations=conversations,
            artifacts_created=artifacts_created,
        )

    def _parse_artifact_type(self, raw_type: object) -> ArtifactType:
        if isinstance(raw_type, ArtifactType):
            return raw_type
        try:
            return ArtifactType(str(raw_type))
        except Exception:
            return ArtifactType.IRRELEVANT

    def _artifact_from_classification(
        self,
        conversation_id: str,
        artifact_type: ArtifactType,
        classification: dict,
    ) -> Artifact:
        return Artifact(
            id=f"art_{uuid.uuid4().hex[:8]}",
            conversation_id=conversation_id,
            type=artifact_type,
            status="PENDING",
            rephrasing=classification.get("rephrasing", ""),
            rationale=classification.get("rationale", ""),
            summary_of_context=classification.get("summary_of_context", ""),
        )
