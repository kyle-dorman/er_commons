#!/usr/bin/env python3
"""Build one deterministic, checksummed first-pass Task 04 review bundle."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from er_commons.human_review_support.task04 import BuildRequest, build_review_bundle


def main() -> None:
    """Parse filesystem inputs and invoke the typed Task 04 application seam."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retained-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    root = build_review_bundle(BuildRequest(args.retained_root, args.data_root, args.output_root))
    logging.getLogger(__name__).info("Task 04 review bundle ready: %s", root)


if __name__ == "__main__":
    main()
