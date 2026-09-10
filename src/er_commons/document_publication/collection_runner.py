"""Run the explicit document collection source queue serially with durable progress evidence."""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from er_commons.document_publication.config import DocumentRunSpec, load_document_run_spec

FATAL_PATTERNS = (
    re.compile(r"resource (?:guard|limit|ceiling|budget)", re.IGNORECASE),
    re.compile(r"(?:identity|lineage) mismatch", re.IGNORECASE),
    re.compile(r"semantic loss", re.IGNORECASE),
    re.compile(r"checksum (?:failure|mismatch)", re.IGNORECASE),
    re.compile(r"invariant failed", re.IGNORECASE),
    re.compile(r"publication (?:failure|failed)", re.IGNORECASE),
)

LOGGER = logging.getLogger("er_commons.document_publication.collection_runner")


@dataclass(frozen=True)
class CollectionRunRequest:
    """Explicit execution selection and progress output; no import-time settings."""

    document_spec: Path
    progress_root: Path
    repository_root: Path
    data_root: Path
    source_ids: tuple[str, ...] = ()
    all_sources: bool = False

    @property
    def progress_path(self) -> Path:
        """Locate newly owned serial-run observations."""
        return self.progress_root / "document_progress.jsonl"

    @property
    def log_root(self) -> Path:
        """Keep source logs under the explicit progress root."""
        return self.progress_root / "runner_logs"


def run_document_collection(request: CollectionRunRequest) -> int:
    """Execute every configured source in frozen order and retain outcomes."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    spec, spec_digest = load_document_run_spec(request.document_spec)
    stamp = _spec_stamp(request.document_spec)
    sources = _source_ids(request, spec)
    production_extraction_id = spec.production_extraction_id
    request.log_root.mkdir(parents=True, exist_ok=True)
    completed = _successful_source_ids(request, production_extraction_id, spec_digest)
    _event(
        request,
        spec_digest,
        {
            "event": "runner_started",
            "source_count": len(sources),
            "source_ids": sources,
            "resumed_success_count": len(completed),
            "production_extraction_id": production_extraction_id,
        },
    )
    failures = 0
    for ordinal, source_id in enumerate(sources, start=1):
        if source_id in completed:
            LOGGER.info("retaining source %s/%s as already successful", ordinal, len(sources))
            continue
        if _spec_stamp(request.document_spec) != stamp:
            raise ValueError("document spec changed during collection invocation")
        result = _run_source(
            request,
            ordinal,
            len(sources),
            source_id,
            production_extraction_id=production_extraction_id,
            spec_digest=spec_digest,
            spec_stamp=stamp,
        )
        if _spec_stamp(request.document_spec) != stamp:
            raise ValueError("document spec changed during collection invocation")
        if result["status"] != "success":
            failures += 1
        if result["hard_stop"]:
            _event(
                request,
                spec_digest,
                {
                    "event": "runner_stopped",
                    "reason": result["reason"],
                    "source_id": source_id,
                    "ordinal": ordinal,
                    "production_extraction_id": production_extraction_id,
                },
            )
            return 2
    _event(
        request,
        spec_digest,
        {
            "event": "runner_finished",
            "source_count": len(sources),
            "failure_count": failures,
            "collection_eligible": failures == 0,
            "production_extraction_id": production_extraction_id,
        },
    )
    return 1 if failures else 0


def _successful_source_ids(
    request: CollectionRunRequest, production_extraction_id: str, spec_digest: str
) -> set[str]:
    """Return sources with successful terminal evidence in the selected progress root."""
    if not request.progress_path.exists():
        return set()
    completed: set[str] = set()
    for line in request.progress_path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            event.get("event") == "source_finished"
            and event.get("status") == "success"
            and event.get("production_extraction_id") == production_extraction_id
            and event.get("document_spec_sha256") == spec_digest
        ):
            completed.add(event["source_id"])
    return completed


def _source_ids(request: CollectionRunRequest, spec: DocumentRunSpec) -> list[str]:
    """Require an explicit full selection or unique ordered configured subset."""
    declared = [item.source_id for item in spec.document_processes]
    if request.all_sources == bool(request.source_ids):
        raise ValueError("select explicit source IDs or all sources, exclusively")
    selected = declared if request.all_sources else list(request.source_ids)
    if len(selected) != len(set(selected)) or any(source not in declared for source in selected):
        raise ValueError("runner selection must name unique configured sources")
    if [source for source in declared if source in selected] != selected:
        raise ValueError("runner sources must retain document-spec order")
    return selected


def _run_source(
    request: CollectionRunRequest,
    ordinal: int,
    total: int,
    source_id: str,
    *,
    production_extraction_id: str,
    spec_digest: str,
    spec_stamp: tuple[int, int, int, int],
) -> dict[str, Any]:
    """Run one source, continuing ordinary terminal failures."""
    started = time.monotonic()
    started_at = _now()
    log_path = request.log_root / f"{ordinal:02d}_{source_id}.log"
    command = [
        str(request.repository_root / ".venv/bin/er-commons"),
        "documents",
        "publish",
        "--document-spec",
        str(request.document_spec),
        "--source-id",
        source_id,
    ]
    LOGGER.info("starting source %s/%s: %s", ordinal, total, source_id)
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            cwd=request.repository_root,
            env={
                **os.environ,
                "PYTHONUNBUFFERED": "1",
                "ER_COMMONS_DATA_ROOT": str(request.data_root),
            },
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return_code = process.wait()
    if _spec_stamp(request.document_spec) != spec_stamp:
        raise ValueError("document spec changed during collection invocation")
    output = log_path.read_text(encoding="utf-8", errors="replace")
    hard_stop, reason = _hard_stop(output)
    status = "success" if return_code == 0 else "failed_terminal"
    result = {
        "event": "source_finished",
        "ordinal": ordinal,
        "source_id": source_id,
        "production_extraction_id": production_extraction_id,
        "status": status,
        "return_code": return_code,
        "started_at": started_at,
        "finished_at": _now(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "log_relative_path": log_path.relative_to(request.progress_root).as_posix(),
        "hard_stop": hard_stop,
        "reason": reason,
    }
    _event(request, spec_digest, result)
    if return_code == 0:
        LOGGER.info("finished source %s/%s successfully", ordinal, total)
    elif hard_stop:
        LOGGER.error("hard stop after source %s/%s: %s", ordinal, total, reason)
    else:
        LOGGER.error("retaining ordinary source failure and continuing: %s", source_id)
    return result


def _hard_stop(output: str) -> tuple[bool, str | None]:
    """Classify only contract-level safety and publication failures as stops."""
    for pattern in FATAL_PATTERNS:
        match = pattern.search(output)
        if match:
            return True, match.group(0)
    return False, None


def _event(request: CollectionRunRequest, spec_digest: str, value: dict[str, Any]) -> None:
    """Append one progress event without treating it as candidate state."""
    with request.progress_path.open("a", encoding="utf-8") as stream:
        stream.write(
            json.dumps(
                {
                    "timestamp": _now(),
                    "document_spec_sha256": spec_digest,
                    **value,
                },
                sort_keys=True,
            )
            + "\n"
        )


def _now() -> str:
    """Return an unambiguous UTC timestamp for progress evidence."""
    return datetime.now(UTC).isoformat()


def _spec_stamp(path: Path) -> tuple[int, int, int, int]:
    """Detect changed controls while allowing ordinary filesystem access-time updates."""
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino
