"""Deep-audit one existing hierarchy candidate without running hierarchy or a PDF."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from er_commons.hierarchy_inference import (
    deep_audit_completed_candidate,
)
from er_commons.hierarchy_inference.progress import CandidateAssemblyProgress

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = (
    PROJECT_ROOT / "benchmarks/er_bench/schemas/hierarchy_correction/v1/records.schema.json"
)


def main() -> None:
    """Require an existing candidate and stream-verify every managed byte."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA_PATH)
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    candidate_root = arguments.candidate_root.resolve()
    if not candidate_root.is_dir() or candidate_root.name != arguments.candidate_id:
        parser.error("deep audit requires the exact existing candidate root and ID")
    progress = CandidateAssemblyProgress(logging.getLogger(__name__), arguments.candidate_id)
    try:
        result = deep_audit_completed_candidate(
            candidate_root,
            arguments.candidate_id,
            arguments.schema.resolve(),
            progress=progress.report,
        )
    except (OSError, ValueError) as error:
        parser.exit(2, f"deep audit failed: {error}\n")
    print(f"candidate_id={result.candidate_id}")
    print(f"verified_files={result.verified_file_count}")
    print(f"verified_bytes={result.verified_bytes}")
    print(f"candidate_semantic_sha256={result.candidate_semantic_sha256}")
    print(f"artifact_inventory_sha256={result.artifact_inventory_sha256}")
    print(f"elapsed_seconds={result.elapsed_seconds:.3f}")
    print(f"completion={result.completion_path}")


if __name__ == "__main__":
    main()
