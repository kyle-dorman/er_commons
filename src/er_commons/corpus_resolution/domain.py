"""Typed values shared by the human-owned corpus workflow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from er_commons.corpus_extraction_contract_v1_1.model import JsonObject


class StageName(StrEnum):
    """The four independently published stage-two products."""

    ACCOUNTING = "accounting"
    TARGET_INDEX = "target_index"
    RESOLUTION = "resolution"
    HANDOFF = "handoff"

    @property
    def directory(self) -> str:
        """Return the identity-owned directory for this stage."""
        return {
            StageName.ACCOUNTING: "accounting",
            StageName.TARGET_INDEX: "target_indexes",
            StageName.RESOLUTION: "resolutions",
            StageName.HANDOFF: "handoffs",
        }[self]


def _ignore_path(_path: Path) -> None:
    """Default no-op publication hook."""


def _ignore_disposition(_disposition: str) -> None:
    """Default no-op attempt hook."""


@dataclass(frozen=True)
class StageHooks:
    """Public durability seams for the two publication crash windows."""

    before_publish: Callable[[Path], None] = _ignore_path
    after_publish: Callable[[Path], None] = _ignore_path
    before_attempt_record: Callable[[str], None] = _ignore_disposition


@dataclass(frozen=True)
class StageBuild:
    """Complete deterministic bytes for one stage before publication."""

    name: StageName
    identity: str
    payloads: dict[str, bytes]
    completion: JsonObject


@dataclass(frozen=True)
class PublishedStage:
    """One verified semantic completion and its operational attempts."""

    completion_path: Path
    completion_ref: JsonObject
    attempts: tuple[JsonObject, ...]


@dataclass(frozen=True)
class ScopeHooks:
    """Stage-specific durability seams used by synthetic interruption tests."""

    accounting: StageHooks = field(default_factory=StageHooks)
    target_index: StageHooks = field(default_factory=StageHooks)
    resolution: StageHooks = field(default_factory=StageHooks)
    handoff: StageHooks = field(default_factory=StageHooks)
