"""Typed outputs and lifecycle states for Task 04 register publication."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class FindingRegisterStatus(StrEnum):
    """Human approval states supported after item-level review is complete."""

    APPROVED = "approved"
    CLOSED = "closed"


@dataclass(frozen=True)
class RegisterStatusResult:
    """Paths and overall status produced by a successful register transition."""

    status: FindingRegisterStatus
    finding_register: Path
    task03i_handoff: Path


__all__ = ["FindingRegisterStatus", "RegisterStatusResult"]
