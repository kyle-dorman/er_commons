"""Stable, context-rich failures for the Task 03G.2f replay."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReplayFailureDetail:
    """Machine-readable failure fields that are also useful to a human debugger."""

    code: str
    message: str
    context: dict[str, Any]


class ReplayValidationError(ValueError):
    """A replay invariant failed with a stable code and diagnostic context."""

    def __init__(self, code: str, message: str, **context: Any) -> None:
        self.detail = ReplayFailureDetail(code, message, context)
        suffix = f" context={context}" if context else ""
        super().__init__(f"{code}: {message}{suffix}")
