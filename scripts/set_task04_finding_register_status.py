#!/usr/bin/env python3
"""Approve or close a validated Task 04 finding register."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from er_commons.human_review_support.task04 import (
    FindingRegisterStatus,
    default_schema_root,
    set_finding_register_status,
)


def parse_args() -> argparse.Namespace:
    """Parse the deliberately one-way register lifecycle command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-root", required=True, type=Path)
    parser.add_argument("--status", required=True, choices=FindingRegisterStatus)
    return parser.parse_args()


def main() -> None:
    """Validate and recoverably publish one overall register transition."""
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = set_finding_register_status(
        args.review_root,
        FindingRegisterStatus(args.status),
        schema_root=default_schema_root(),
    )
    logging.info("Task 04 finding register is %s: %s", result.status, result.finding_register)
    logging.info("Task 03I handoff refreshed: %s", result.task03i_handoff)


if __name__ == "__main__":
    main()
