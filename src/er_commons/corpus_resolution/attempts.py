"""Operational attempt history for restartable corpus-stage publication."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from er_commons.corpus_extraction_contract_v1_1.model import JsonObject
from er_commons.corpus_resolution.domain import StageHooks, StageName
from er_commons.corpus_resolution.storage import file_ref, json_bytes


@dataclass(frozen=True)
class OpenAttempt:
    """Paths and ordinal for one newly reserved publication attempt."""

    number: int
    root: Path
    events_root: Path
    staging_root: Path


class AttemptJournal:
    """Own attempt reservation, state transitions, recovery, and projection."""

    def __init__(self, extraction_root: Path, scope_root: Path) -> None:
        self._extraction_root = extraction_root
        self._scope_root = scope_root

    def reserve(self, stage: StageName, stage_id: str) -> OpenAttempt:
        """Close abandoned staging and reserve the next attempt ordinal."""
        parent = self.parent(stage, stage_id)
        parent.mkdir(parents=True, exist_ok=True)
        self._cancel_interrupted(parent)
        number = len(list(parent.glob("attempt_*"))) + 1
        root = parent / f"attempt_{number:04d}"
        root.mkdir()
        events = root / "state_events"
        events.mkdir()
        self._write_event(events, 1, None, "selected")
        self._write_event(events, 2, "selected", "running")
        staging = root / "staging"
        staging.mkdir()
        return OpenAttempt(number, root, events, staging)

    def complete(
        self,
        attempt: OpenAttempt,
        stage: StageName,
        stage_id: str,
        completion_path: Path,
        hooks: StageHooks,
    ) -> None:
        """Close a successful attempt after its final directory is durable."""
        self._write_event(attempt.events_root, 3, "running", "complete")
        hooks.before_attempt_record("complete")
        self._write_record(
            attempt.root,
            stage=stage,
            stage_id=stage_id,
            attempt=attempt.number,
            disposition="complete",
            failure_class=None,
            completion_path=completion_path,
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
        if (latest / "attempt_record.json").is_file():
            return
        events = sorted((latest / "state_events").glob("*.json"))
        if json.loads(events[-1].read_bytes())["to_state"] == "running":
            self._write_event(latest / "state_events", len(events) + 1, "running", "complete")
        hooks.before_attempt_record("complete")
        self._write_record(
            latest,
            stage=stage,
            stage_id=stage_id,
            attempt=int(latest.name.removeprefix("attempt_")),
            disposition="complete",
            failure_class=None,
            completion_path=completion_path,
        )

    def records(self, stage: StageName, stage_id: str) -> tuple[JsonObject, ...]:
        """Project retained filesystem evidence into public attempt records."""
        rows: list[JsonObject] = []
        for root in sorted(self.parent(stage, stage_id).glob("attempt_*")):
            record = json.loads((root / "attempt_record.json").read_bytes())
            completion_path = record["completion_path"]
            rows.append(
                {
                    "schema_version": "er_commons.corpus_stage_attempt.v1",
                    "stage_type": record["stage_type"],
                    "stage_id": record["stage_id"],
                    "attempt": record["attempt"],
                    "disposition": record["disposition"],
                    "failure_class": record["failure_class"],
                    "state_event_refs": [
                        file_ref(path, self._extraction_root)
                        for path in sorted((root / "state_events").glob("*.json"))
                    ],
                    "completion_ref": (
                        file_ref(Path(completion_path), self._extraction_root)
                        if completion_path is not None
                        else None
                    ),
                }
            )
        return tuple(rows)

    def parent(self, stage: StageName, stage_id: str) -> Path:
        """Return the retained-attempt directory for one stage identity."""
        return self._scope_root / "attempts" / stage.value / stage_id

    def _cancel_interrupted(self, parent: Path) -> None:
        for root in sorted(parent.glob("attempt_*")):
            if (root / "attempt_record.json").is_file():
                continue
            events = sorted((root / "state_events").glob("*.json"))
            if not events:
                continue
            if json.loads(events[-1].read_bytes())["to_state"] == "running":
                self._write_event(root / "state_events", len(events) + 1, "running", "cancelled")
            shutil.rmtree(root / "staging", ignore_errors=True)
            self._write_record(
                root,
                stage=StageName(parent.parent.name),
                stage_id=parent.name,
                attempt=int(root.name.removeprefix("attempt_")),
                disposition="cancelled",
                failure_class="InterruptedPublication",
                completion_path=None,
            )

    @staticmethod
    def _write_event(root: Path, sequence: int, from_state: str | None, to_state: str) -> None:
        (root / f"{sequence:04d}.json").write_bytes(
            json_bytes(
                {
                    "schema_version": "er_commons.corpus_stage_event.v1",
                    "sequence": sequence,
                    "from_state": from_state,
                    "to_state": to_state,
                }
            )
        )

    @staticmethod
    def _write_record(
        root: Path,
        *,
        stage: StageName,
        stage_id: str,
        attempt: int,
        disposition: str,
        failure_class: str | None,
        completion_path: Path | None,
    ) -> None:
        (root / "attempt_record.json").write_bytes(
            json_bytes(
                {
                    "stage_type": stage.value,
                    "stage_id": stage_id,
                    "attempt": attempt,
                    "disposition": disposition,
                    "failure_class": failure_class,
                    "completion_path": str(completion_path) if completion_path else None,
                }
            )
        )
