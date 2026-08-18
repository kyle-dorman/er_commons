"""Typed, contextual readers for retained publication recovery evidence."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ValidationError

from er_commons.document_publication.lifecycle import ALLOWED, STATUS_BY_STATE
from er_commons.document_publication.records import AttemptRecord, StateEvent


class RetainedEvidenceError(ValueError):
    """A retained recovery record is unreadable or violates its local contract."""

    def __init__(self, *, path: Path, subject: str, detail: str) -> None:
        self.path = path
        self.subject = subject
        self.detail = detail
        super().__init__(f"retained evidence invalid [{subject}] at {path}: {detail}")


def read_retained_record[RecordT: BaseModel](
    path: Path, record_type: type[RecordT], *, subject: str
) -> RecordT:
    """Read one strict record while preserving its path in every failure."""
    try:
        return record_type.model_validate_json(path.read_bytes())
    except OSError as error:
        raise RetainedEvidenceError(
            path=path,
            subject=subject,
            detail=f"cannot read {type(error).__name__}: {error}",
        ) from error
    except ValidationError as error:
        raise RetainedEvidenceError(
            path=path,
            subject=subject,
            detail=f"does not match {record_type.__name__}: {error.errors(include_url=False)}",
        ) from error


def require_retained_evidence(
    condition: bool,
    *,
    path: Path,
    subject: str,
    detail: str,
) -> None:
    """Raise a path-bearing error when cross-record recovery evidence differs."""
    if not condition:
        raise RetainedEvidenceError(path=path, subject=subject, detail=detail)


def read_attempt_record(path: Path) -> AttemptRecord:
    """Read one strict terminal attempt record with recovery context."""
    return read_retained_record(path, AttemptRecord, subject="attempt record")


def read_state_events(root: Path) -> list[StateEvent]:
    """Read and validate one contiguous, identity-consistent state history."""
    paths = sorted(root.glob("*.json"))
    events = [read_retained_record(path, StateEvent, subject="state event") for path in paths]
    for index, (path, event) in enumerate(zip(paths, events, strict=True), start=1):
        require_retained_evidence(
            event.sequence == index,
            path=path,
            subject="state event sequence",
            detail=f"expected sequence {index}, observed {event.sequence}",
        )
        if index == 1:
            require_retained_evidence(
                event.from_state is None and event.to_state == "selected",
                path=path,
                subject="state event history",
                detail="first event must transition from null to selected",
            )
            continue
        previous = events[index - 2]
        require_retained_evidence(
            (
                event.transaction_id == previous.transaction_id
                and event.source_id == previous.source_id
                and event.attempt == previous.attempt
                and event.from_state == previous.to_state
            ),
            path=path,
            subject="state event history",
            detail="identity or transition differs from the preceding event",
        )
        require_retained_evidence(
            (previous.to_state, event.to_state) in ALLOWED,
            path=path,
            subject="state event transition",
            detail=f"illegal transition {previous.to_state} -> {event.to_state}",
        )
    for path, event in zip(paths, events, strict=True):
        require_retained_evidence(
            event.raw_docling_status in STATUS_BY_STATE[event.to_state],
            path=path,
            subject="state event status",
            detail=(f"raw status {event.raw_docling_status!r} is invalid for {event.to_state}"),
        )
    return events
