"""Interpret retained Task 03H attempt histories for the failure queue."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from er_commons.human_review_support.task04.json_io import read_json_object
from er_commons.human_review_support.task04.models import AttemptEvidence, FailureHistory

_ARTIFACT_PATH = re.compile(r"/Volumes/x10pro/er_commons/[^\s'\",}]+")


def failure_histories(
    retained_root: Path,
    ordered_source_ids: tuple[str, ...],
    selected_candidate_ids: dict[str, str],
) -> tuple[tuple[FailureHistory, ...], int]:
    """Group every retained non-success attempt by source and current outcome."""
    attempts = _attempts(retained_root)
    by_source: dict[str, list[AttemptEvidence]] = defaultdict(list)
    for source_id, attempt in attempts:
        by_source[source_id].append(attempt)
    histories: list[FailureHistory] = []
    for source_id in ordered_source_ids:
        source_attempts = tuple(
            sorted(by_source.get(source_id, []), key=lambda item: item.attempt_id)
        )
        selected_id = selected_candidate_ids.get(source_id)
        if not source_attempts and selected_id is not None:
            continue
        histories.append(
            FailureHistory(
                source_id=source_id,
                current_status=(
                    "recovered_later" if selected_id else "unresolved_missing_publication"
                ),
                selected_candidate_id=selected_id,
                attempts=source_attempts,
            )
        )
    return tuple(histories), len(attempts)


def attempt_workspace_count(retained_root: Path) -> int:
    """Count retained attempt workspaces with a useful missing-root diagnostic."""
    root = retained_root / "document_publications" / "attempts"
    if not root.is_dir():
        raise ValueError(f"required document attempt root is missing: {root}")
    return sum(path.is_dir() for path in root.iterdir())


def _attempts(retained_root: Path) -> list[tuple[str, AttemptEvidence]]:
    """Read every retained non-success attempt and its terminal diagnostic."""
    root = retained_root / "document_publications" / "attempts"
    if not root.is_dir():
        raise ValueError(f"required document attempt root is missing: {root}")
    items: list[tuple[str, AttemptEvidence]] = []
    for directory in sorted(path for path in root.iterdir() if path.is_dir()):
        result = _attempt_from_directory(directory, retained_root)
        if result is not None:
            items.append(result)
    return items


def _attempt_from_directory(
    directory: Path, retained_root: Path
) -> tuple[str, AttemptEvidence] | None:
    """Build one non-success attempt or discard a successful historical attempt."""
    attempt_path = directory / "attempt_record.json"
    record = read_json_object(attempt_path) if attempt_path.is_file() else {}
    preflight_path = directory / "execution_preflight.json"
    preflight = read_json_object(preflight_path) if preflight_path.is_file() else {}
    disposition = str(record.get("disposition") or "incomplete")
    if disposition in {"complete", "complete_with_warnings"}:
        return None
    events = [
        read_json_object(path)
        for path in sorted((directory / "document_process_events").glob("*.json"))
    ]
    failed = [event for event in events if event.get("state") == "failed"]
    event = failed[-1] if failed else (events[-1] if events else {})
    source_id = str(record.get("source_id") or preflight.get("source_id") or "unknown")
    detail = event.get("detail") or record.get("message")
    if not detail and disposition == "incomplete":
        detail = "Invocation ended without a terminal attempt record."
    return source_id, AttemptEvidence(
        attempt_id=directory.name,
        disposition=disposition,
        failure_class=_optional_text(event.get("error_class") or record.get("failure_class")),
        stage=str(event.get("stage") or "unknown"),
        detail=_compact_detail(detail),
        relative_path=directory.relative_to(retained_root).as_posix(),
    )


def _compact_detail(value: object, *, limit: int = 900) -> str:
    """Retain actionable errors while removing repeated machine-specific roots."""
    text = _ARTIFACT_PATH.sub("<artifact-path>", str(value or "").strip())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _optional_text(value: object) -> str | None:
    """Narrow optional diagnostic text."""
    return str(value) if value is not None else None


__all__ = ["attempt_workspace_count", "failure_histories"]
