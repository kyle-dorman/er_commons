#!/usr/bin/env python3
"""Build the Task 03J final-pass Gate C review package."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from er_commons.human_review_support.task04.final_review import build_task03j_final_review


def parse_args() -> argparse.Namespace:
    """Parse the explicit Gate C input and output paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--gate-a", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument(
        "--toc-decisions",
        type=Path,
        help="Exported TOC decisions; later c-runs automatically reuse the newest import",
    )
    return parser.parse_args()


def main() -> None:
    """Run one immutable Task 03J final-pass package build."""
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    output = build_task03j_final_review(
        args.data_root,
        args.gate_a,
        args.output_root,
        toc_decisions_path=args.toc_decisions,
    )
    logging.info("published Gate C review package at %s", output)


if __name__ == "__main__":
    main()
