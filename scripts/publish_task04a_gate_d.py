#!/usr/bin/env python3
"""Publish Task 04A Gate D from accepted compact c17 review records."""

from __future__ import annotations

import argparse
from pathlib import Path

from er_commons.human_review_support.task04.gate_d import GateDRequest, publish_gate_d
from er_commons.settings import load_settings


def parse_args() -> argparse.Namespace:
    """Parse explicit compact inputs without providing PDF or render options."""
    data_root = load_settings().data_root
    review_root = data_root / "pipelines/brisbane_baylands/task_04_review"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gate-a",
        type=Path,
        default=review_root
        / "reviewv1-task03j-final-b19a7a36b04bda89/records/gate_a_preparation.json",
    )
    parser.add_argument(
        "--gate-c-root",
        type=Path,
        default=review_root / "reviewv1-task03j-final-c17",
    )
    parser.add_argument(
        "--schema-root",
        type=Path,
        default=Path(__file__).parents[1] / "benchmarks/er_bench/schemas/task04a_review/v1",
    )
    return parser.parse_args()


def main() -> None:
    """Publish the additive closure package and print its path."""
    args = parse_args()
    output = publish_gate_d(
        GateDRequest(
            gate_a_path=args.gate_a.resolve(),
            gate_c_root=args.gate_c_root.resolve(),
            schema_root=args.schema_root.resolve(),
        )
    )
    print(output)


if __name__ == "__main__":
    main()
