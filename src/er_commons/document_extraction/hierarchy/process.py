"""Independent producer-process execution for hierarchy repeatability gates."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def completed_run_root(completion_path: Path) -> Path:
    """Resolve the producer root from its required terminal record path."""
    if completion_path.name != "completion_record.json":
        raise ValueError(
            "producer runner returned an unexpected completion path: "
            f"expected=completion_record.json actual={completion_path.name}"
        )
    return completion_path.parents[1]


def run_producer_subprocess(
    data_root: Path,
    config_path: Path,
    *,
    artifact_root_override: Path | None = None,
) -> Path:
    """Run one producer invocation in a separate Python interpreter."""
    script = (
        "from pathlib import Path;"
        "from er_commons.document_extraction.complete_document import "
        "run_complete_document_producer;"
        "import sys;"
        "result=run_complete_document_producer("
        "Path(sys.argv[1]),Path(sys.argv[2]),"
        "artifact_root_override=None if sys.argv[3]=='-' else Path(sys.argv[3]));"
        "print(result)"
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            data_root.as_posix(),
            config_path.as_posix(),
            artifact_root_override.as_posix() if artifact_root_override else "-",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    output_lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if len(output_lines) != 1:
        raise ValueError(
            "independent producer process returned unexpected output: "
            f"nonempty_line_count={len(output_lines)} stderr={completed.stderr.strip()!r}"
        )
    return Path(output_lines[0])
