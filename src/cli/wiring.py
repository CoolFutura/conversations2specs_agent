from __future__ import annotations

from src.adapters.slack_reader import normalize_thread

from src.adapters.openai import OpenAILLMClassifier
from src.adapters.repo_json import (
    JsonArtifactRepository,
    JsonOpenQuestionRepository,
    JsonProposedUpdateRepository,
    JsonSpecUpdateRepository,
)
from src.adapters.slack_sdk import SlackSDKThreadsAdapter
from src.adapters.trace_json import JsonTraceabilityAdapter
from src.adapters.sources_state_json import JsonSourcesStateAdapter
from src.use_cases.ingest import IngestUseCase
from src.use_cases.transform_artifacts import TransformArtifactsUseCase
from src.use_cases.transform_oq import TransformOQUseCase
from src.use_cases.approve_pu import ApprovePUUseCase
from src.use_cases.add_decision import AddDecisionUseCase
from src.use_cases.modify_oq import ModifyOQUseCase
from src.use_cases.change_artifact_status import (
    ChangeArtifactStatusUseCase,
    ChangeArtifactStatusBatchUseCase,
)
from src.use_cases.list_artifacts import ListArtifactsUseCase
from src.use_cases.list_open_questions import ListOpenQuestionsUseCase
from src.use_cases.list_proposed_updates import ListProposedUpdatesUseCase
from src.use_cases.init_sync import InitSyncUseCase


def build_ingest_use_case() -> IngestUseCase:
    slack_adapter = SlackSDKThreadsAdapter()
    llm_classifier = OpenAILLMClassifier()
    artifact_repo = JsonArtifactRepository()
    trace_adapter = JsonTraceabilityAdapter()
    return IngestUseCase(slack_adapter, llm_classifier, artifact_repo, trace_adapter, normalize_thread)


def build_transform_artifacts_use_case() -> TransformArtifactsUseCase:
    artifact_repo = JsonArtifactRepository()
    oq_repo = JsonOpenQuestionRepository()
    pu_repo = JsonProposedUpdateRepository()
    return TransformArtifactsUseCase(artifact_repo, oq_repo, pu_repo)


def build_transform_oq_use_case() -> TransformOQUseCase:
    oq_repo = JsonOpenQuestionRepository()
    pu_repo = JsonProposedUpdateRepository()
    return TransformOQUseCase(oq_repo, pu_repo)


def build_approve_pu_use_case() -> ApprovePUUseCase:
    pu_repo = JsonProposedUpdateRepository()
    spec_repo = JsonSpecUpdateRepository()
    return ApprovePUUseCase(pu_repo, spec_repo)


def build_add_decision_use_case() -> AddDecisionUseCase:
    oq_repo = JsonOpenQuestionRepository()
    return AddDecisionUseCase(oq_repo)


def build_modify_oq_use_case() -> ModifyOQUseCase:
    oq_repo = JsonOpenQuestionRepository()
    pu_repo = JsonProposedUpdateRepository()
    return ModifyOQUseCase(oq_repo, pu_repo)


def build_change_artifact_status_use_case() -> ChangeArtifactStatusUseCase:
    artifact_repo = JsonArtifactRepository()
    return ChangeArtifactStatusUseCase(artifact_repo)


def build_change_artifact_status_batch_use_case() -> ChangeArtifactStatusBatchUseCase:
    artifact_repo = JsonArtifactRepository()
    return ChangeArtifactStatusBatchUseCase(artifact_repo)


def build_list_artifacts_use_case() -> ListArtifactsUseCase:
    artifact_repo = JsonArtifactRepository()
    return ListArtifactsUseCase(artifact_repo)


def build_list_open_questions_use_case() -> ListOpenQuestionsUseCase:
    oq_repo = JsonOpenQuestionRepository()
    return ListOpenQuestionsUseCase(oq_repo)


def build_list_proposed_updates_use_case() -> ListProposedUpdatesUseCase:
    pu_repo = JsonProposedUpdateRepository()
    return ListProposedUpdatesUseCase(pu_repo)


def build_init_sync_use_case() -> InitSyncUseCase:
    sources_state = JsonSourcesStateAdapter()
    return InitSyncUseCase(sources_state)
