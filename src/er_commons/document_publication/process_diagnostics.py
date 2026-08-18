"""Durable stage boundaries and failure-time timing recovery."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from pathlib import Path

from er_commons.artifact_io import sha256_file, write_json_atomic

LOGGER = logging.getLogger(__name__)


def run_process_stage(
    name: str,
    timings: dict[str, float],
    operation: Callable[[], Path],
    *,
    diagnostics_root: Path | None,
    ordinal: int,
    data_root: Path,
) -> Path:
    """Measure one process and durably record start, completion, or failure."""
    LOGGER.info("Starting document process %s", name)
    _write_stage_event(diagnostics_root, ordinal, name, "started")
    started = time.monotonic()
    try:
        result = operation()
    except Exception as error:
        elapsed = time.monotonic() - started
        _write_stage_event(
            diagnostics_root,
            ordinal,
            name,
            "failed",
            wall_seconds=elapsed,
            error_class=type(error).__name__,
            detail=str(error),
        )
        LOGGER.exception("Document process %s failed after %.3fs", name, elapsed)
        raise
    elapsed = time.monotonic() - started
    timings[name] = elapsed
    _write_stage_event(
        diagnostics_root,
        ordinal,
        name,
        "completed",
        wall_seconds=elapsed,
        completion_path=result.relative_to(data_root).as_posix(),
        completion_sha256=sha256_file(result),
    )
    LOGGER.info("Completed document process %s in %.3fs", name, elapsed)
    return result


def retained_stage_timings(attempt_root: Path) -> dict[str, float]:
    """Recover completed process timings even when the child has no final handoff."""
    timings: dict[str, float] = {}
    events_root = attempt_root / "document_process_events"
    if not events_root.is_dir():
        return timings
    for path in sorted(events_root.glob("*_completed.json")):
        event = json.loads(path.read_text())
        stage = event.get("stage")
        wall_seconds = event.get("wall_seconds")
        if isinstance(stage, str) and isinstance(wall_seconds, (int, float)):
            timings[stage] = float(wall_seconds)
    return timings


def _write_stage_event(
    diagnostics_root: Path | None,
    ordinal: int,
    stage: str,
    state: str,
    **details: object,
) -> None:
    if diagnostics_root is None:
        return
    path = diagnostics_root / "document_process_events" / f"{ordinal:02d}_{stage}_{state}.json"
    write_json_atomic(
        path,
        {
            "schema_version": "er_commons.document_process_event.v2",
            "stage": stage,
            "state": state,
            **details,
        },
    )
