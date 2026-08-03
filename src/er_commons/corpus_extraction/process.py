"""Outer one-document process deadline and structured result handling."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from er_commons.corpus_extraction.config import ResourcePolicy
from er_commons.corpus_extraction.records import PipelineResult


@dataclass(frozen=True)
class ProcessOutcome:
    """Typed child outcome without parsing exception prose for success."""

    result: PipelineResult | None
    timed_out: bool
    return_code: int | None
    stderr: str


def run_isolated_document(
    *,
    data_root: Path,
    project_root: Path,
    run_spec_path: Path,
    source_id: str,
    attempt_root: Path,
    resources: ResourcePolicy,
) -> ProcessOutcome:
    """Run one child; terminate then kill if it exceeds the hard deadline."""
    result_path = attempt_root / "pipeline_result.json"
    command = [
        sys.executable,
        "-m",
        "er_commons.corpus_extraction.worker",
        "--data-root",
        str(data_root),
        "--project-root",
        str(project_root),
        "--run-spec",
        str(run_spec_path),
        "--source-id",
        source_id,
        "--result",
        str(result_path),
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        _stdout, stderr = process.communicate(timeout=resources.outer_process_deadline_seconds)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            _stdout, stderr = process.communicate(timeout=resources.cancellation_grace_seconds)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            _stdout, stderr = process.communicate()
        return ProcessOutcome(result=None, timed_out=True, return_code=None, stderr=stderr)
    result = (
        PipelineResult.model_validate_json(result_path.read_bytes())
        if process.returncode == 0 and result_path.is_file()
        else None
    )
    return ProcessOutcome(
        result=result,
        timed_out=False,
        return_code=process.returncode,
        stderr=stderr,
    )
