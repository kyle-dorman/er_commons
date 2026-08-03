"""Append-only state histories and deterministic failure classification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, cast

from er_commons.corpus_extraction.records import StateEvent
from er_commons.source_freeze import write_json_atomic

State = Literal[
    "selected",
    "running",
    "complete",
    "complete_with_warnings",
    "failed_retryable",
    "failed_terminal",
    "cancelled",
]
PreviousState = Literal["selected", "running"]
RawStatus = Literal["PENDING", "STARTED", "SUCCESS", "PARTIAL_SUCCESS", "FAILURE", "SKIPPED"]
Disposition = Literal[
    "complete",
    "complete_with_warnings",
    "failed_retryable",
    "failed_terminal",
    "cancelled",
]

ALLOWED = {
    (None, "selected"),
    ("selected", "running"),
    ("running", "complete"),
    ("running", "complete_with_warnings"),
    ("running", "failed_retryable"),
    ("running", "failed_terminal"),
    ("running", "cancelled"),
}
STATUS_BY_STATE: dict[State, frozenset[RawStatus | None]] = {
    "selected": frozenset({"PENDING"}),
    "running": frozenset({"STARTED"}),
    "complete": frozenset({"SUCCESS"}),
    "complete_with_warnings": frozenset({"SUCCESS"}),
    # A producer-level SUCCESS may still fail a project publication gate.
    "failed_retryable": frozenset({"SUCCESS", "PARTIAL_SUCCESS", "FAILURE", "SKIPPED", None}),
    "failed_terminal": frozenset({"SUCCESS", "PARTIAL_SUCCESS", "FAILURE", "SKIPPED", None}),
    "cancelled": frozenset({"PARTIAL_SUCCESS", None}),
}

TERMINAL_ERROR_TYPES = {
    "FileNotFoundError",
    "PermissionError",
    "ValidationError",
    "HierarchyAuthorizationError",
    "SourceIdentityError",
}


class EventWriter:
    """Write one immutable JSON file per contiguous transition."""

    def __init__(self, root: Path, *, transaction_id: str, source_id: str, attempt: int) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=False)
        self.transaction_id = transaction_id
        self.source_id = source_id
        self.attempt = attempt
        self.previous: State | None = None
        self.paths: list[Path] = []

    def transition(self, state: State, raw_status: RawStatus | None) -> StateEvent:
        """Validate and persist the next transition."""
        if (self.previous, state) not in ALLOWED:
            raise ValueError(f"illegal state transition: {self.previous!r} -> {state!r}")
        if raw_status not in STATUS_BY_STATE[state]:
            raise ValueError(f"raw Docling status {raw_status!r} is invalid for state {state!r}")
        event = StateEvent(
            transaction_id=self.transaction_id,
            source_id=self.source_id,
            attempt=self.attempt,
            sequence=len(self.paths) + 1,
            from_state=cast(PreviousState | None, self.previous),
            to_state=state,
            raw_docling_status=raw_status,
        )
        path = self.root / f"{event.sequence:04d}.json"
        write_json_atomic(path, event.model_dump(mode="json"))
        self.paths.append(path)
        self.previous = state
        return event


def read_events(root: Path) -> list[dict[str, object]]:
    """Read an attempt's ordered state-event files."""
    return [json.loads(path.read_text()) for path in sorted(root.glob("*.json"))]


def classify_failure(error_type: str, *, timed_out: bool = False) -> Disposition:
    """Return stable retry/cancellation/terminal disposition from typed evidence."""
    if timed_out:
        return "cancelled"
    if error_type in TERMINAL_ERROR_TYPES:
        return "failed_terminal"
    return "failed_retryable"
