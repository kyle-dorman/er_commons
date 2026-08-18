"""Outer one-document process deadline and structured result handling."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from er_commons.document_publication.config import ResourcePolicy
from er_commons.document_publication.records import PipelineResult

MAX_RETAINED_OUTPUT_CHARS = 16_000


def _bounded_output(value: str) -> str:
    """Keep the tail of child output while making retained evidence predictable."""
    if len(value) <= MAX_RETAINED_OUTPUT_CHARS:
        return value
    omitted = len(value) - MAX_RETAINED_OUTPUT_CHARS
    return f"[... {omitted} earlier characters omitted ...]\n{value[-MAX_RETAINED_OUTPUT_CHARS:]}"


@dataclass(frozen=True)
class ProcessOutcome:
    """Result and bounded diagnostics from one isolated document process."""

    result: PipelineResult | None
    timed_out: bool
    return_code: int | None
    stderr: str
    stdout: str = ""

    @property
    def diagnostic_text(self) -> str:
        """Return the child output that is useful in retained failure evidence."""
        parts = []
        if self.return_code is not None:
            parts.append(f"return_code={self.return_code}")
        if self.stderr.strip():
            parts.append(f"stderr:\n{self.stderr.strip()}")
        if self.stdout.strip():
            parts.append(f"stdout:\n{self.stdout.strip()}")
        return "\n".join(parts)


def run_isolated_document(
    *,
    data_root: Path,
    project_root: Path,
    run_spec_path: Path,
    source_id: str,
    attempt_root: Path,
    resources: ResourcePolicy,
    preflight_digest: str | None = None,
) -> ProcessOutcome:
    """Run one child; terminate then kill if it exceeds the hard deadline."""
    result_path = attempt_root / "pipeline_result.json"
    command = [
        sys.executable,
        "-m",
        "er_commons.document_publication.worker",
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
    if preflight_digest is not None:
        command.extend(["--preflight-sha256", preflight_digest])
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=resources.outer_process_deadline_seconds)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=resources.cancellation_grace_seconds)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        return ProcessOutcome(
            result=None,
            timed_out=True,
            return_code=process.returncode,
            stderr=_bounded_output(stderr),
            stdout=_bounded_output(stdout),
        )
    result = (
        PipelineResult.model_validate_json(result_path.read_bytes())
        if process.returncode == 0 and result_path.is_file()
        else None
    )
    return ProcessOutcome(
        result=result,
        timed_out=False,
        return_code=process.returncode,
        stderr=_bounded_output(stderr),
        stdout=_bounded_output(stdout),
    )
