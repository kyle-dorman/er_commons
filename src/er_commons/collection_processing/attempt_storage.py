"""Atomic persistence and validation for collection attempt journals."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.artifact_io import read_json_object, write_json_atomic
from er_commons.collection_processing.domain import StageName

type AttemptState = Literal["selected", "running", "complete", "cancelled"]
type PreviousAttemptState = Literal["selected", "running"]
type AttemptDisposition = Literal["complete", "cancelled"]


class AttemptEvent(BaseModel):
    """One strict internal transition in a collection-stage attempt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["er_commons.collection_stage_event.v2"]
    sequence: int = Field(ge=1)
    from_state: PreviousAttemptState | None
    to_state: AttemptState
    observed_at_utc: datetime


class AttemptRecord(BaseModel):
    """Strict internal terminal record for one collection-stage attempt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["er_commons.collection_stage_attempt_record.v2"]
    stage_type: StageName
    stage_id: str = Field(min_length=1)
    attempt: int = Field(ge=1)
    disposition: AttemptDisposition
    failure_class: str | None = Field(min_length=1)
    completion_path: Path | None
    recorded_at_utc: datetime
    wall_seconds: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_terminal_shape(self) -> AttemptRecord:
        """Keep success and cancellation evidence mutually exclusive."""
        if self.disposition == "complete":
            if self.failure_class is not None or self.completion_path is None:
                raise ValueError("complete attempt requires completion and no failure")
        elif self.failure_class is None or self.completion_path is not None:
            raise ValueError("cancelled attempt requires failure and no completion")
        return self


def write_attempt_event(
    root: Path,
    sequence: int,
    from_state: PreviousAttemptState | None,
    to_state: AttemptState,
) -> None:
    """Atomically append one explicitly sequenced attempt transition."""
    write_json_atomic(
        root / f"{sequence:04d}.json",
        AttemptEvent(
            schema_version="er_commons.collection_stage_event.v2",
            sequence=sequence,
            from_state=from_state,
            to_state=to_state,
            observed_at_utc=datetime.now(UTC),
        ),
    )


def write_attempt_record(
    root: Path,
    *,
    stage: StageName,
    stage_id: str,
    attempt: int,
    disposition: AttemptDisposition,
    failure_class: str | None,
    completion_path: Path | None,
    wall_seconds: float | None,
) -> None:
    """Atomically publish one terminal operational attempt record."""
    write_json_atomic(
        root / "attempt_record.json",
        AttemptRecord(
            schema_version="er_commons.collection_stage_attempt_record.v2",
            stage_type=stage,
            stage_id=stage_id,
            attempt=attempt,
            disposition=disposition,
            failure_class=failure_class,
            completion_path=completion_path,
            recorded_at_utc=datetime.now(UTC),
            wall_seconds=wall_seconds,
        ),
    )


def read_attempt_events(root: Path) -> tuple[AttemptEvent, ...]:
    """Read and verify a contiguous attempt transition history."""
    paths = sorted(root.glob("*.json"))
    events = tuple(_read_model(path, AttemptEvent, "collection stage event") for path in paths)
    previous: str | None = None
    for sequence, (path, event) in enumerate(zip(paths, events, strict=True), start=1):
        if event.sequence != sequence or event.from_state != previous:
            raise ValueError(
                "collection stage event history is not contiguous: "
                f"path={path}, sequence={sequence}"
            )
        expected = "selected" if previous is None else "running" if previous == "selected" else None
        if expected is not None and event.to_state != expected:
            raise ValueError(
                f"collection stage event transition is invalid: path={path}, "
                f"expected={expected}, observed={event.to_state}"
            )
        if previous == "running" and event.to_state not in {"complete", "cancelled"}:
            raise ValueError(f"collection stage event terminal state is invalid: {path}")
        if previous in {"complete", "cancelled"}:
            raise ValueError(f"collection stage event follows a terminal state: {path}")
        previous = event.to_state
    return events


def read_attempt_record(path: Path) -> AttemptRecord:
    """Read one typed terminal record with artifact-path context."""
    return _read_model(path, AttemptRecord, "collection attempt record")


def validate_attempt(
    root: Path,
    *,
    stage: StageName,
    stage_id: str,
    attempt: int,
    completion_path: Path | None = None,
) -> tuple[AttemptRecord, tuple[AttemptEvent, ...]]:
    """Validate record identity, terminal history, and optional completion path."""
    record_path = root / "attempt_record.json"
    record = read_attempt_record(record_path)
    events = read_attempt_events(root / "state_events")
    if (record.stage_type, record.stage_id, record.attempt) != (stage, stage_id, attempt):
        raise ValueError(f"collection attempt record identity differs: {record_path}")
    if not events or events[-1].to_state != record.disposition:
        raise ValueError(f"collection attempt record differs from terminal event: {record_path}")
    if completion_path is not None and record.completion_path != completion_path:
        raise ValueError(f"collection attempt completion path differs: {record_path}")
    return record, events


def _read_model[Model: BaseModel](path: Path, model: type[Model], label: str) -> Model:
    """Parse one strict internal model with the source artifact in errors."""
    try:
        return model.model_validate(read_json_object(path))
    except ValueError as error:
        raise ValueError(f"{label} is invalid: {path}: {error}") from error


def remove_partial_writes(root: Path) -> None:
    """Remove abandoned atomic-write temporaries before journal recovery."""
    for path in root.rglob("*.part"):
        path.unlink(missing_ok=True)
