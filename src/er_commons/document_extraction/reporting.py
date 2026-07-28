"""Environment, summary, and manifest records for document extraction."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from er_commons.document_extraction.artifacts import artifact_inventory
from er_commons.document_extraction.config import PipelineConfig, SelectionSpec
from er_commons.source_freeze import sha256_file, write_json_atomic


def utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(UTC).isoformat()


def _run_command(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return (result.stdout or result.stderr).strip()


def environment_record(
    config_path: Path,
    selection_path: Path,
    model_inventory_path: Path,
) -> dict[str, Any]:
    """Record code and immutable inputs needed to interpret one run."""
    import psutil  # type: ignore[import-untyped]

    code_paths = sorted(Path("src/er_commons/document_extraction").glob("*.py"))
    tracked_inputs = [
        *code_paths,
        Path("src/er_commons/table_extraction/models.py"),
        Path("src/er_commons/table_extraction/pipeline.py"),
        Path("src/er_commons/cli.py"),
        Path("Makefile"),
        Path("pyproject.toml"),
        Path("uv.lock"),
        config_path,
        selection_path,
        model_inventory_path,
    ]
    return {
        "generated_at_utc": utc_now(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version,
        "physical_memory_bytes": psutil.virtual_memory().total,
        "cpu_count_logical": psutil.cpu_count(),
        "git_commit": _run_command(["git", "rev-parse", "HEAD"]),
        "git_dirty": bool(_run_command(["git", "status", "--porcelain"])),
        "input_sha256": {
            path.as_posix(): sha256_file(path) for path in tracked_inputs if path.is_file()
        },
        "offline_environment": {
            "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE"),
            "TRANSFORMERS_OFFLINE": os.environ.get("TRANSFORMERS_OFFLINE"),
        },
    }


def seal_run(
    root: Path,
    config: PipelineConfig,
    config_sha256: str,
    selection: SelectionSpec,
    selection_sha256: str,
    timings: list[dict[str, Any]],
    acceptance: dict[str, Any],
    timing_comparison: dict[str, Any],
    started: float,
) -> Path:
    """Write the terminal summary, inventory, and manifest."""
    accepted = bool(acceptance["accepted"])
    summary = {
        "pipeline_id": config.pipeline_id,
        "status": "complete" if accepted else "acceptance_failed",
        "configuration_id": config.configuration_id,
        "selected_page_count": selection.expected_selected_page_count,
        "range_count": len(timings),
        "all_ranges_success": all(record["status"] == "success" for record in timings),
        "error_count": sum(int(record["error_count"]) for record in timings),
        "accepted": accepted,
        "docling_wall_seconds": sum(float(record["wall_seconds"]) for record in timings),
        "pipeline_wall_seconds": time.perf_counter() - started,
        "max_peak_rss_bytes": max(int(record["peak_rss_bytes"]) for record in timings),
        "docling_output_bytes": sum(int(record["output_bytes"]) for record in timings),
        "timing_comparison": timing_comparison,
        "known_limitations": [
            "Docling labels and parent references remain observations, not canonical hierarchy.",
            "Baseline G3 page-1000 TableFormer cells remain unusable; "
            "clean-table output replaces them.",
            "Conversion success and table-stage success remain separate signals.",
        ],
    }
    write_json_atomic(root / "summary.json", summary)
    inventory_path = root / "artifact_inventory.json"
    manifest_path = root / "manifest.json"
    write_json_atomic(
        inventory_path,
        artifact_inventory(root, excluded={"artifact_inventory.json", "manifest.json"}),
    )
    inventory = json.loads(inventory_path.read_text())
    write_json_atomic(
        manifest_path,
        {
            "schema_version": "1.0.0",
            "pipeline_id": config.pipeline_id,
            "status": summary["status"],
            "generated_at_utc": utc_now(),
            "configuration_sha256": config_sha256,
            "selection_id": selection.pilot_id,
            "selection_sha256": selection_sha256,
            "baseline_run_relative_root": config.baseline_run_relative_root.as_posix(),
            "accepted": accepted,
            "timings": "timings.jsonl",
            "comparison": "comparison_to_task03a.json",
            "table_stage": "table_pipeline_summary.json",
            "summary": "summary.json",
            "environment": "environment.json",
            "artifact_inventory": "artifact_inventory.json",
            "relative_outputs": [record["path"] for record in inventory["files"]],
        },
    )
    return manifest_path
