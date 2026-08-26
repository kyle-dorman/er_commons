#!/usr/bin/env python3
"""Record one validated Task 04 finding and refresh the Task 03I handoff."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from er_commons.human_review_support.task04 import (
    FindingClass,
    FindingDraft,
    FindingSelectors,
    FindingStatus,
    default_schema_root,
    record_finding,
)


def parse_args() -> argparse.Namespace:
    """Parse the deliberately narrow human finding-edit interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-root", required=True, type=Path)
    parser.add_argument("--review-item-id", required=True)
    parser.add_argument("--class", required=True, dest="finding_class", choices=FindingClass)
    parser.add_argument("--status", required=True, choices=FindingStatus)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--observed", required=True)
    parser.add_argument("--downstream-consequence", required=True)
    parser.add_argument("--table-id", action="append", default=[], help="Retained table ID.")
    parser.add_argument("--block-id", action="append", default=[], help="Retained block ID.")
    parser.add_argument("--observation-id", action="append", default=[])
    return parser.parse_args()


def main() -> None:
    """Apply one finding update through the typed Task 04 application seam."""
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = record_finding(
        args.review_root,
        FindingDraft(
            review_item_id=args.review_item_id,
            finding_class=FindingClass(args.finding_class),
            status=FindingStatus(args.status),
            expected_behavior=args.expected,
            observed_behavior=args.observed,
            downstream_consequence=args.downstream_consequence,
            selectors=FindingSelectors(
                tuple(args.table_id), tuple(args.block_id), tuple(args.observation_id)
            ),
        ),
        schema_root=default_schema_root(),
    )
    logging.info("recorded %s in %s", result.finding_id, result.finding_register)
    logging.info("refreshed Task 03I handoff at %s", result.task03i_handoff)


if __name__ == "__main__":
    main()
