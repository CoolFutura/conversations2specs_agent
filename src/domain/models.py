from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ArtifactType(str, Enum):
    OQ = "OQ"
    PU = "PU"
    IRRELEVANT = "IRRELEVANT"


@dataclass
class Artifact:
    id: str
    conversation_id: str
    type: ArtifactType
    status: str
    rephrasing: str
    rationale: str
    summary_of_context: str


@dataclass
class OpenQuestion:
    id: str
    artifact_id: str
    question: str
    context: str
    status: str
    slack_ts: Optional[str] = None
    decision: Optional[str] = None
    decision_rationale: Optional[str] = None


@dataclass
class ProposedUpdate:
    id: str
    artifact_id: str
    source_oq_id: Optional[str]
    rephrasing: str
    context: str
    decision: str
    rationale: str
    status: str


@dataclass
class SpecUpdate:
    id: str
    pu_id: str
    content: str
    decision: str
    status: str
