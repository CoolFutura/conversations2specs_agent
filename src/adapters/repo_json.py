from __future__ import annotations

import uuid
from typing import Iterable

from src.domain.models import Artifact, ArtifactType, OpenQuestion, ProposedUpdate
from storage_utils import load_json, save_json


class JsonArtifactRepository:
    def list_all(self) -> Iterable[Artifact]:
        data = load_json("artifacts.json")
        artifacts = data.get("artifacts", [])
        return [self._from_dict(item) for item in artifacts]

    def save(self, artifact: Artifact) -> None:
        data = load_json("artifacts.json")
        artifacts = data.get("artifacts", [])

        updated = False
        for idx, item in enumerate(artifacts):
            if item.get("id") == artifact.id:
                artifacts[idx] = self._to_dict(artifact)
                updated = True
                break

        if not updated:
            artifacts.append(self._to_dict(artifact))

        data["artifacts"] = artifacts
        save_json("artifacts.json", data)

    def _from_dict(self, item: dict) -> Artifact:
        return Artifact(
            id=item["id"],
            conversation_id=item.get("conversation_id", ""),
            type=ArtifactType(item.get("type", "IRRELEVANT")),
            status=item.get("status", "PENDING"),
            rephrasing=item.get("rephrasing", ""),
            rationale=item.get("rationale", ""),
            summary_of_context=item.get("summary_of_context", ""),
        )

    def _to_dict(self, artifact: Artifact) -> dict:
        return {
            "id": artifact.id,
            "conversation_id": artifact.conversation_id,
            "type": artifact.type.value,
            "status": artifact.status,
            "rephrasing": artifact.rephrasing,
            "rationale": artifact.rationale,
            "summary_of_context": artifact.summary_of_context,
        }


class JsonOpenQuestionRepository:
    def create_from_artifact(self, artifact: Artifact) -> OpenQuestion:
        oq = OpenQuestion(
            id=f"oq_{uuid.uuid4().hex[:8]}",
            artifact_id=artifact.id,
            question=artifact.rephrasing,
            context=artifact.summary_of_context,
            status="OPEN",
            slack_ts=None,
        )

        data = load_json("open_questions.json")
        questions = data.get("questions", [])
        questions.append(self._to_dict(oq))
        data["questions"] = questions
        save_json("open_questions.json", data)
        return oq

    def _to_dict(self, oq: OpenQuestion) -> dict:
        return {
            "id": oq.id,
            "artifact_id": oq.artifact_id,
            "question": oq.question,
            "context": oq.context,
            "status": oq.status,
            "slack_ts": oq.slack_ts,
        }


class JsonProposedUpdateRepository:
    def create_from_artifact(self, artifact: Artifact) -> ProposedUpdate:
        pu = ProposedUpdate(
            id=f"pu_{uuid.uuid4().hex[:8]}",
            artifact_id=artifact.id,
            source_oq_id=None,
            rephrasing=artifact.rephrasing,
            context=artifact.summary_of_context,
            decision="",
            rationale=artifact.rationale,
            status="DRAFT",
        )

        data = load_json("proposed_updates.json")
        updates = data.get("updates", [])
        updates.append(self._to_dict(pu))
        data["updates"] = updates
        save_json("proposed_updates.json", data)
        return pu

    def _to_dict(self, pu: ProposedUpdate) -> dict:
        return {
            "id": pu.id,
            "artifact_id": pu.artifact_id,
            "source_oq_id": pu.source_oq_id,
            "rephrasing": pu.rephrasing,
            "context": pu.context,
            "decision": pu.decision,
            "rationale": pu.rationale,
            "status": pu.status,
        }
