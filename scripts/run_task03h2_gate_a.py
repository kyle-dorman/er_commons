#!/usr/bin/env python3
"""Run Task 03H.2 Gate A from sealed, already-materialized G1 evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from er_commons.chunked_conversion.qualification.gate_a_application import (
    GateARequest,
    run_gate_a,
)


def main() -> None:
    """Parse paths and delegate the source-free proof to its application service."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    completion = run_gate_a(
        GateARequest(
            source_root=args.source_root,
            output_root=args.output_root,
            project_root=Path(__file__).resolve().parents[1],
        )
    )
    print(completion)


if __name__ == "__main__":
    main()
