"""Attempt allocation, durable state, and interrupted-run recovery."""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from er_commons.corpus_extraction.identity import build_transaction_id
from er_commons.corpus_extraction.lifecycle import Disposition, EventWriter
from er_commons.corpus_extraction.preflight import DocumentRun
from er_commons.corpus_extraction.records import (
    AttemptRecord,
    ResourceRecord,
    SourceIdentity,
    StateEvent,
)
from er_commons.source_freeze import write_json_atomic

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class AttemptSession:
    """Paths and state writer for one retained document attempt."""

    number: int
    transaction_id: str
    root: Path
    events: EventWriter
    started_at: float

    @classmethod
    def start(cls, run: DocumentRun, number: int) -> AttemptSession:
        """Reserve an attempt directory and persist its initial state."""
        transaction_id = build_transaction_id(
            scope_id=run.scope_id,
            source_id=run.source.source_id,
            source_sha256=run.source.sha256,
            attempt=number,
        )
        root = run.extraction_root / "attempts" / f"{transaction_id}.{uuid.uuid4().hex}"
        root.mkdir(parents=True, exist_ok=False)
        events = EventWriter(
            root / "state_events",
            transaction_id=transaction_id,
            source_id=run.source.source_id,
            attempt=number,
        )
        events.transition("selected", "PENDING")
        events.transition("running", "STARTED")
        write_json_atomic(
            root / "resource_record.json",
            ResourceRecord(
                transaction_id=transaction_id,
                policy=run.spec.resource_policy.model_dump(mode="json"),
            ).model_dump(mode="json"),
        )
        return cls(number, transaction_id, root, events, time.monotonic())

    def wall_seconds(self) -> float:
        """Return elapsed monotonic time for observability records."""
        return time.monotonic() - self.started_at

    def record(
        self,
        *,
        source_id: str,
        disposition: Disposition,
        failure_class: str | None,
        message: str | None,
        completion_path: str | None = None,
    ) -> None:
        """Persist the terminal attempt record beside retained diagnostics."""
        record_attempt(
            self.root,
            transaction_id=self.transaction_id,
            source_id=source_id,
            attempt=self.number,
            disposition=disposition,
            failure_class=failure_class,
            message=message,
            event_paths=self.events.paths,
            completion_path=completion_path,
        )


def next_attempt_number(run: DocumentRun) -> int:
    """Continue contiguous attempt numbering across separate invocations."""
    attempts = _retained_attempts(run)
    if not attempts:
        return 1
    numbers = sorted(attempts)
    if numbers != list(range(1, numbers[-1] + 1)):
        raise ValueError("retained transaction attempts are not contiguous")
    latest = attempts[numbers[-1]]["disposition"]
    if latest in {"complete", "complete_with_warnings"}:
        raise ValueError("successful attempt exists without a reusable candidate")
    if latest == "failed_terminal":
        raise ValueError("document transaction already failed terminally for this scope")
    next_number = numbers[-1] + 1
    if next_number > run.maximum_attempts:
        raise ValueError("document retry limit is already exhausted")
    return next_number


def record_attempt(
    root: Path,
    *,
    transaction_id: str,
    source_id: str,
    attempt: int,
    disposition: Disposition,
    failure_class: str | None,
    message: str | None,
    event_paths: list[Path],
    completion_path: str | None = None,
) -> None:
    """Write one inspectable attempt record outside candidate completion."""
    record = AttemptRecord(
        transaction_id=transaction_id,
        source_id=source_id,
        attempt=attempt,
        disposition=disposition,
        failure_class=failure_class,
        message=message,
        state_event_paths=[str(path.relative_to(root)) for path in event_paths],
        completion_path=completion_path,
    )
    write_json_atomic(root / "attempt_record.json", record.model_dump(mode="json"))


def _retained_attempts(run: DocumentRun) -> dict[int, dict[str, object]]:
    """Load attempts belonging to this exact scope and source identity."""
    attempts: dict[int, dict[str, object]] = {}
    attempts_root = run.extraction_root / "attempts"
    if not attempts_root.is_dir():
        return attempts
    for root in sorted(path for path in attempts_root.iterdir() if path.is_dir()):
        record_path = root / "attempt_record.json"
        if not record_path.is_file():
            _recover_interrupted_attempt(root, run.scope_id, run.source)
        if not record_path.is_file():
            continue
        record = json.loads(record_path.read_text())
        if record.get("source_id") != run.source.source_id:
            continue
        number = int(record["attempt"])
        expected_id = build_transaction_id(
            scope_id=run.scope_id,
            source_id=run.source.source_id,
            source_sha256=run.source.sha256,
            attempt=number,
        )
        if record.get("transaction_id") != expected_id:
            continue
        if number in attempts:
            raise ValueError(f"duplicate retained transaction attempt: {number}")
        attempts[number] = record
    return attempts


def _recover_interrupted_attempt(root: Path, scope_id: str, source: SourceIdentity) -> None:
    """Close a retained running attempt before allocating its retry."""
    event_paths = sorted((root / "state_events").glob("*.json"))
    if not event_paths:
        return
    events = [json.loads(path.read_text()) for path in event_paths]
    last = events[-1]
    number = int(last["attempt"])
    transaction_id = build_transaction_id(
        scope_id=scope_id,
        source_id=source.source_id,
        source_sha256=source.sha256,
        attempt=number,
    )
    if last.get("transaction_id") != transaction_id or last.get("source_id") != source.source_id:
        return
    terminal = last.get("to_state")
    if terminal in _terminal_states():
        record_attempt(
            root,
            transaction_id=transaction_id,
            source_id=source.source_id,
            attempt=number,
            disposition=cast(Disposition, terminal),
            failure_class=(
                None if str(terminal).startswith("complete") else "RecoveredTerminalEvent"
            ),
            message="reconstructed from retained terminal state event",
            event_paths=event_paths,
        )
        LOGGER.info("Reconstructed terminal attempt %s from state events", transaction_id)
        return
    if terminal != "running":
        raise ValueError("interrupted attempt lacks a recoverable running state")
    cancelled_path = root / "state_events" / f"{len(events) + 1:04d}.json"
    event = StateEvent(
        transaction_id=transaction_id,
        source_id=source.source_id,
        attempt=number,
        sequence=len(events) + 1,
        from_state="running",
        to_state="cancelled",
        raw_docling_status=None,
    )
    write_json_atomic(cancelled_path, event.model_dump(mode="json"))
    record_attempt(
        root,
        transaction_id=transaction_id,
        source_id=source.source_id,
        attempt=number,
        disposition="cancelled",
        failure_class="InterruptedProcess",
        message="prior invocation ended without a terminal attempt record",
        event_paths=[*event_paths, cancelled_path],
    )
    LOGGER.warning("Recovered interrupted attempt %s as cancelled", transaction_id)


def _terminal_states() -> frozenset[str]:
    return frozenset(
        {
            "complete",
            "complete_with_warnings",
            "failed_retryable",
            "failed_terminal",
            "cancelled",
        }
    )
