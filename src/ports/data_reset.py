from __future__ import annotations

from typing import Protocol


class DataResetPort(Protocol):
    def reset_all(self) -> None:
        ...
