"""Run the Task 03J v4 source queue serially with durable progress evidence."""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from er_commons.settings import load_settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = load_settings().data_root.resolve()
SPEC = PROJECT_ROOT / "configs/brisbane_baylands_2025_deir_task03h_document_v4.json"
RUN_ROOT = DATA_ROOT / "pipelines/brisbane_baylands/task_03h_clean_full_v4"
LOG_ROOT = RUN_ROOT / "runner_logs"
PROGRESS = RUN_ROOT / "task03j_progress.jsonl"
FATAL_PATTERNS = (
    re.compile(r"resource (?:guard|limit|ceiling|budget)", re.IGNORECASE),
    re.compile(r"(?:identity|lineage) mismatch", re.IGNORECASE),
    re.compile(r"semantic loss", re.IGNORECASE),
    re.compile(r"checksum (?:failure|mismatch)", re.IGNORECASE),
    re.compile(r"invariant failed", re.IGNORECASE),
    re.compile(r"publication (?:failure|failed)", re.IGNORECASE),
)

LOGGER = logging.getLogger("task03j_v4")


def main() -> int:
    """Execute every configured source in frozen order and retain outcomes."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sources = _source_ids()
    production_extraction_id = _production_extraction_id()
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    completed = _successful_source_ids(production_extraction_id)
    _event(
        {
            "event": "runner_started",
            "source_count": len(sources),
            "source_ids": sources,
            "resumed_success_count": len(completed),
            "production_extraction_id": production_extraction_id,
        }
    )
    failures = 0
    for ordinal, source_id in enumerate(sources, start=1):
        if source_id in completed:
            LOGGER.info("retaining source %s/%s as already successful", ordinal, len(sources))
            continue
        result = _run_source(
            ordinal,
            len(sources),
            source_id,
            production_extraction_id=production_extraction_id,
        )
        if result["status"] != "success":
            failures += 1
        if result["hard_stop"]:
            _event(
                {
                    "event": "runner_stopped",
                    "reason": result["reason"],
                    "source_id": source_id,
                    "ordinal": ordinal,
                    "production_extraction_id": production_extraction_id,
                }
            )
            return 2
    _event(
        {
            "event": "runner_finished",
            "source_count": len(sources),
            "failure_count": failures,
            "collection_eligible": failures == 0,
            "production_extraction_id": production_extraction_id,
        }
    )
    return 1 if failures else 0


def _successful_source_ids(production_extraction_id: str) -> set[str]:
    """Return sources with successful terminal evidence in this v4 run root."""
    if not PROGRESS.exists():
        return set()
    completed: set[str] = set()
    for line in PROGRESS.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            event.get("event") == "source_finished"
            and event.get("status") == "success"
            and event.get("production_extraction_id") == production_extraction_id
        ):
            completed.add(event["source_id"])
    return completed


def _production_extraction_id() -> str:
    """Load the exact production identity owned by the active v4 spec."""
    value = json.loads(SPEC.read_bytes()).get("production_extraction_id")
    if not isinstance(value, str) or not re.fullmatch(r"exv1-[0-9a-f]{64}", value):
        raise ValueError("v4 document spec has an invalid production extraction ID")
    return value


def _source_ids() -> list[str]:
    """Load the already-validated v4 source order from the document spec."""
    value = json.loads(SPEC.read_bytes())
    sources = [item["source_id"] for item in value["document_processes"]]
    if len(sources) != 35 or len(sources) != len(set(sources)):
        raise ValueError("v4 document spec must contain 35 unique sources")
    return sources


def _run_source(
    ordinal: int,
    total: int,
    source_id: str,
    *,
    production_extraction_id: str,
) -> dict[str, Any]:
    """Run one source, continuing ordinary terminal failures."""
    started = time.monotonic()
    started_at = _now()
    log_path = LOG_ROOT / f"{ordinal:02d}_{source_id}.log"
    command = [
        str(PROJECT_ROOT / ".venv/bin/er-commons"),
        "documents",
        "publish",
        "--document-spec",
        str(SPEC),
        "--source-id",
        source_id,
    ]
    LOGGER.info("starting source %s/%s: %s", ordinal, total, source_id)
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            cwd=PROJECT_ROOT,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return_code = process.wait()
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
        "log_relative_path": log_path.relative_to(RUN_ROOT).as_posix(),
        "hard_stop": hard_stop,
        "reason": reason,
    }
    _event(result)
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


def _event(value: dict[str, Any]) -> None:
    """Append one progress event without treating it as candidate state."""
    with PROGRESS.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"timestamp": _now(), **value}, sort_keys=True) + "\n")


def _now() -> str:
    """Return an unambiguous UTC timestamp for progress evidence."""
    return datetime.now(UTC).isoformat()


if __name__ == "__main__":
    sys.exit(main())
