"""Operational attempt history for restartable collection-stage publication."""

from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from er_commons.collection_processing.attempt_storage import (
    read_attempt_events,
    remove_partial_writes,
    validate_attempt,
    write_attempt_event,
    write_attempt_record,
)
from er_commons.collection_processing.contract import JsonObject
from er_commons.collection_processing.domain import StageHooks, StageName
from er_commons.collection_processing.storage import file_ref


@dataclass(frozen=True)
class OpenAttempt:
    """Paths and ordinal for one newly reserved publication attempt."""

    number: int
    root: Path
    events_root: Path
    staging_root: Path
    started_monotonic: float


class AttemptJournal:
    """Own attempt reservation, state transitions, recovery, and projection."""

    def __init__(self, extraction_root: Path, scope_root: Path) -> None:
        self._extraction_root = extraction_root
        self._scope_root = scope_root

    def reserve(self, stage: StageName, stage_id: str) -> OpenAttempt:
        """Close abandoned staging and reserve the next attempt ordinal."""
        parent = self.parent(stage, stage_id)
        parent.mkdir(parents=True, exist_ok=True)
        self._recover_interrupted(parent, stage=stage, stage_id=stage_id)
        number = len(list(parent.glob("attempt_*"))) + 1
        root = parent / f"attempt_{number:04d}"
        root.mkdir()
        events = root / "state_events"
        events.mkdir()
        write_attempt_event(events, 1, None, "selected")
        write_attempt_event(events, 2, "selected", "running")
        staging = root / "staging"
        staging.mkdir()
        return OpenAttempt(number, root, events, staging, time.monotonic())

    def complete(
        self,
        attempt: OpenAttempt,
        stage: StageName,
        stage_id: str,
        completion_path: Path,
        hooks: StageHooks,
    ) -> None:
        """Close a successful attempt after its final directory is durable."""
        write_attempt_event(attempt.events_root, 3, "running", "complete")
        hooks.before_attempt_record("complete")
        write_attempt_record(
            attempt.root,
            stage=stage,
            stage_id=stage_id,
            attempt=attempt.number,
            disposition="complete",
            failure_class=None,
            completion_path=completion_path,
            wall_seconds=time.monotonic() - attempt.started_monotonic,
        )

    def reconcile_published(
        self,
        stage: StageName,
        stage_id: str,
        completion_path: Path,
        hooks: StageHooks,
    ) -> None:
        """Finish the accepted rename-before-attempt-record crash window."""
        attempts = sorted(self.parent(stage, stage_id).glob("attempt_*"))
        if not attempts:
            raise ValueError("published stage lacks retained attempt evidence")
        latest = attempts[-1]
        attempt_number = int(latest.name.removeprefix("attempt_"))
        record_path = latest / "attempt_record.json"
        if record_path.is_file():
            record, _events = validate_attempt(
                latest,
                stage=stage,
                stage_id=stage_id,
                attempt=attempt_number,
                completion_path=completion_path,
            )
            if record.disposition != "complete":
                raise ValueError(f"published stage attempt is not complete: {record_path}")
            return
        events = read_attempt_events(latest / "state_events")
        if not events:
            raise ValueError(f"published stage has no journal events: {latest}")
        if events[-1].to_state == "running":
            write_attempt_event(latest / "state_events", len(events) + 1, "running", "complete")
        elif events[-1].to_state != "complete":
            raise ValueError(
                "published stage journal has an incompatible terminal state: "
                f"path={latest}, state={events[-1].to_state}"
            )
        hooks.before_attempt_record("complete")
        write_attempt_record(
            latest,
            stage=stage,
            stage_id=stage_id,
            attempt=attempt_number,
            disposition="complete",
            failure_class=None,
            completion_path=completion_path,
            wall_seconds=None,
        )

    def records(self, stage: StageName, stage_id: str) -> tuple[JsonObject, ...]:
        """Project retained filesystem evidence into public attempt records."""
        rows: list[JsonObject] = []
        for root in sorted(self.parent(stage, stage_id).glob("attempt_*")):
            attempt_number = int(root.name.removeprefix("attempt_"))
            record, _events = validate_attempt(
                root,
                stage=stage,
                stage_id=stage_id,
                attempt=attempt_number,
            )
            completion_path = record.completion_path
            rows.append(
                {
                    "schema_version": "er_commons.collection_stage_attempt.v2",
                    "stage_type": record.stage_type.value,
                    "stage_id": record.stage_id,
                    "attempt": record.attempt,
                    "disposition": record.disposition,
                    "failure_class": record.failure_class,
                    "state_event_refs": [
                        file_ref(path, self._extraction_root)
                        for path in sorted((root / "state_events").glob("*.json"))
                    ],
                    "completion_ref": (
                        file_ref(completion_path, self._extraction_root)
                        if completion_path is not None
                        else None
                    ),
                }
            )
        return tuple(rows)

    def parent(self, stage: StageName, stage_id: str) -> Path:
        """Return the retained-attempt directory for one stage identity."""
        return self._scope_root / "attempts" / stage.value / stage_id

    def _recover_interrupted(
        self,
        parent: Path,
        *,
        stage: StageName,
        stage_id: str,
    ) -> None:
        for root in sorted(parent.glob("attempt_*")):
            remove_partial_writes(root)
            record_path = root / "attempt_record.json"
            if record_path.is_file():
                validate_attempt(
                    root,
                    stage=stage,
                    stage_id=stage_id,
                    attempt=int(root.name.removeprefix("attempt_")),
                )
                continue
            events_root = root / "state_events"
            events = read_attempt_events(events_root)
            if not events:
                events_root.mkdir(exist_ok=True)
                write_attempt_event(events_root, 1, None, "selected")
                write_attempt_event(events_root, 2, "selected", "running")
                events = read_attempt_events(events_root)
            if events[-1].to_state == "selected":
                write_attempt_event(events_root, len(events) + 1, "selected", "running")
                events = read_attempt_events(events_root)
            if events[-1].to_state == "running":
                write_attempt_event(events_root, len(events) + 1, "running", "cancelled")
            elif events[-1].to_state != "cancelled":
                raise ValueError(
                    "unpublished stage journal has an incompatible terminal state: "
                    f"path={root}, state={events[-1].to_state}"
                )
            shutil.rmtree(root / "staging", ignore_errors=True)
            write_attempt_record(
                root,
                stage=stage,
                stage_id=stage_id,
                attempt=int(root.name.removeprefix("attempt_")),
                disposition="cancelled",
                failure_class="InterruptedPublication",
                completion_path=None,
                wall_seconds=None,
            )
