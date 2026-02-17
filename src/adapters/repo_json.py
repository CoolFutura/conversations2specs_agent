from __future__ import annotations

import uuid
from typing import Iterable

from src.domain.models import Artifact, ArtifactType, OpenQuestion, ProposedUpdate, SpecUpdate
from src.adapters.storage_utils import load_json, save_json


class JsonArtifactRepository:
    def list_all(self) -> Iterable[Artifact]:
        data = load_json("artifacts.json")
        artifacts = data.get("artifacts", [])
        return [self._from_dict(item) for item in artifacts]

    def get_by_id(self, artifact_id: str) -> Artifact | None:
        for artifact in self.list_all():
            if artifact.id == artifact_id:
                return artifact
        return None

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
    def list_all(self) -> Iterable[OpenQuestion]:
        data = load_json("open_questions.json")
        questions = data.get("questions", [])
        return [self._from_dict(item) for item in questions]

    def get_by_id(self, oq_id: str) -> OpenQuestion | None:
        for oq in self.list_all():
            if oq.id == oq_id:
                return oq
        return None

    def save(self, oq: OpenQuestion) -> None:
        data = load_json("open_questions.json")
        questions = data.get("questions", [])

        updated = False
        for idx, item in enumerate(questions):
            if item.get("id") == oq.id:
                questions[idx] = self._to_dict(oq)
                updated = True
                break

        if not updated:
            questions.append(self._to_dict(oq))

        data["questions"] = questions
        save_json("open_questions.json", data)

    def delete_by_id(self, oq_id: str) -> None:
        data = load_json("open_questions.json")
        questions = data.get("questions", [])
        questions = [item for item in questions if item.get("id") != oq_id]
        data["questions"] = questions
        save_json("open_questions.json", data)

    def create_from_artifact(self, artifact: Artifact) -> OpenQuestion:
        oq = OpenQuestion(
            id=f"oq_{uuid.uuid4().hex[:8]}",
            artifact_id=artifact.id,
            question=artifact.rephrasing,
            context=artifact.summary_of_context,
            status="OPEN",
            slack_ts=None,
            decision=None,
            decision_rationale=None,
            published_at=None,
            published_message_ts=None,
            published_channel_id=None,
            last_modified_at=None,
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
            "decision": oq.decision,
            "decision_rationale": oq.decision_rationale,
            "published_at": oq.published_at,
            "published_message_ts": oq.published_message_ts,
            "published_channel_id": oq.published_channel_id,
            "last_modified_at": oq.last_modified_at,
        }

    def _from_dict(self, item: dict) -> OpenQuestion:
        return OpenQuestion(
            id=item["id"],
            artifact_id=item.get("artifact_id", ""),
            question=item.get("question", ""),
            context=item.get("context", ""),
            status=item.get("status", "OPEN"),
            slack_ts=item.get("slack_ts"),
            decision=item.get("decision"),
            decision_rationale=item.get("decision_rationale"),
            published_at=item.get("published_at"),
            published_message_ts=item.get("published_message_ts"),
            published_channel_id=item.get("published_channel_id"),
            last_modified_at=item.get("last_modified_at"),
        )


class JsonProposedUpdateRepository:
    def list_all(self) -> Iterable[ProposedUpdate]:
        data = load_json("proposed_updates.json")
        updates = data.get("updates", [])
        return [self._from_dict(item) for item in updates]

    def get_by_id(self, pu_id: str) -> ProposedUpdate | None:
        for pu in self.list_all():
            if pu.id == pu_id:
                return pu
        return None

    def save(self, pu: ProposedUpdate) -> None:
        data = load_json("proposed_updates.json")
        updates = data.get("updates", [])

        updated = False
        for idx, item in enumerate(updates):
            if item.get("id") == pu.id:
                updates[idx] = self._to_dict(pu)
                updated = True
                break

        if not updated:
            updates.append(self._to_dict(pu))

        data["updates"] = updates
        save_json("proposed_updates.json", data)

    def delete_by_source_oq_id(self, oq_id: str) -> None:
        data = load_json("proposed_updates.json")
        updates = data.get("updates", [])
        updates = [item for item in updates if item.get("source_oq_id") != oq_id]
        data["updates"] = updates
        save_json("proposed_updates.json", data)

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

    def _from_dict(self, item: dict) -> ProposedUpdate:
        return ProposedUpdate(
            id=item["id"],
            artifact_id=item.get("artifact_id", ""),
            source_oq_id=item.get("source_oq_id"),
            rephrasing=item.get("rephrasing", ""),
            context=item.get("context", ""),
            decision=item.get("decision", ""),
            rationale=item.get("rationale", ""),
            status=item.get("status", "DRAFT"),
        )


class JsonSpecUpdateRepository:
    def save(self, spec_update: SpecUpdate) -> None:
        data = load_json("specs_updates.json")
        updates = data.get("updates", [])

        updated = False
        for idx, item in enumerate(updates):
            if item.get("id") == spec_update.id:
                updates[idx] = self._to_dict(spec_update)
                updated = True
                break

        if not updated:
            updates.append(self._to_dict(spec_update))

        data["updates"] = updates
        save_json("specs_updates.json", data)

    def _to_dict(self, spec_update: SpecUpdate) -> dict:
        return {
            "id": spec_update.id,
            "pu_id": spec_update.pu_id,
            "content": spec_update.content,
            "decision": spec_update.decision,
            "status": spec_update.status,
        }
