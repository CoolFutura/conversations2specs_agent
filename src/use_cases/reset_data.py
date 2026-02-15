from __future__ import annotations

from dataclasses import dataclass

from src.ports.data_reset import DataResetPort


@dataclass
class ResetDataResult:
    success: bool


class ResetDataUseCase:
    # Clears all stored JSON data (artifacts, OQs, PUs, threads, conversations).
    def __init__(self, reset_port: DataResetPort) -> None:
        self.reset_port = reset_port

    def execute(self) -> ResetDataResult:
        self.reset_port.reset_all()
        return ResetDataResult(success=True)
