"""Prepare Task 04A Gate A from Task 03J machine artifacts only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from er_commons.human_review_support.task04 import (
    prepare_task03j_final,
    publish_gate_a_preparation,
)
from er_commons.human_review_support.task04.records import RecordValidator
from er_commons.settings import load_settings


def main() -> None:
    """Prepare and publish the source-free MVP Gate A record."""
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=load_settings().data_root)
    parser.add_argument(
        "--task-root-relative", default="pipelines/brisbane_baylands/task_03h_clean_full_v4"
    )
    parser.add_argument("--task03i-root", type=Path)
    parser.add_argument("--no-upstream-validator", action="store_true")
    parser.add_argument("--no-raw-docling-scan", action="store_true")
    parser.add_argument(
        "--build-census",
        action="store_true",
        help="Opt in to the large per-source machine-artifact census for Gate B.",
    )
    args = parser.parse_args()
    record = prepare_task03j_final(
        args.data_root.resolve(),
        repo_root=repo_root,
        task_root_relative=args.task_root_relative,
        task03i_root=args.task03i_root.resolve() if args.task03i_root else None,
        validate_upstream=not args.no_upstream_validator,
        raw_docling_scan=not args.no_raw_docling_scan,
        build_census=args.build_census,
    )
    RecordValidator(repo_root / "benchmarks/er_bench/schemas/task04a_review/v1").validate(
        "gate_a_preparation", record
    )
    output = publish_gate_a_preparation(record, args.data_root.resolve())
    print(output)
    print(json.dumps(record["expected_review_workload"], sort_keys=True))


if __name__ == "__main__":
    main()
