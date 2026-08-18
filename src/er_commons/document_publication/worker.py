"""One-shot child process for a complete document transaction."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from er_commons.artifact_io import write_json_atomic
from er_commons.document_publication.config import load_document_run_spec
from er_commons.document_publication.document_processes import run_document_processes
from er_commons.document_publication.lineage_preflight import (
    ExecutionPreflight,
    verify_execution_preflight,
)


def main() -> None:
    """Run exactly one document and persist a minimal typed handoff."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--run-spec", type=Path, required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--preflight-sha256")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    spec, run_spec_digest = load_document_run_spec(args.run_spec)
    configs = None
    if spec.scope_kind != "fixture":
        if args.preflight_sha256 is None:
            raise ValueError("non-fixture worker lacks a parent preflight checksum")
        snapshot_path = args.result.parent / "execution_preflight.json"
        snapshot = ExecutionPreflight.model_validate_json(snapshot_path.read_bytes())
        configs = verify_execution_preflight(
            snapshot=snapshot,
            expected_digest=args.preflight_sha256,
            data_root=args.data_root,
            project_root=args.project_root,
            run_spec=spec,
            run_spec_sha256=run_spec_digest,
            source_id=args.source_id,
        )
    result = run_document_processes(
        data_root=args.data_root,
        project_root=args.project_root,
        run_spec=spec,
        source_id=args.source_id,
        configs=configs,
        diagnostics_root=args.result.parent,
    )
    write_json_atomic(args.result, result.model_dump(mode="json"))


if __name__ == "__main__":
    main()
