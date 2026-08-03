"""Narrow fault hooks for testing documented crash-recovery boundaries."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from er_commons.corpus_extraction.lifecycle import Disposition


def _after_publish(_completion: Path) -> None:
    return None


def _before_attempt_record(_disposition: Disposition) -> None:
    return None


@dataclass(frozen=True)
class WorkflowHooks:
    """Optional callbacks at the two durable publication/recovery gaps."""

    after_candidate_publish: Callable[[Path], None] = _after_publish
    before_attempt_record: Callable[[Disposition], None] = _before_attempt_record
