from __future__ import annotations

from dataclasses import dataclass

from src.ports.traceability import TraceabilityPort


@dataclass
class TraceIngestResult:
    threads_saved: bool
    conversations_saved: bool


class TraceIngestUseCase:
    # Persists raw threads and normalized conversations for traceability.
    def __init__(self, trace_port: TraceabilityPort) -> None:
        self.trace_port = trace_port

    def execute(self, threads: list[dict], conversations: list[dict]) -> TraceIngestResult:
        self.trace_port.save_threads(threads)
        self.trace_port.save_conversations(conversations)
        return TraceIngestResult(threads_saved=True, conversations_saved=True)
