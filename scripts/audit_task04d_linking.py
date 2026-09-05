"""Audit the implemented Task 04D no-page-section rules without publishing."""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

from er_commons.document_records.document_references.linking_policy import (
    load_document_linking_policy,
)
from er_commons.navigation_overlay.task04d_reconciliation import (
    reconcile_task04d_no_page_sections,
)

ACCEPTED_TASK04C_LINK_VIEW = (
    "navlinkv1-978dbf3f3363eeb4265c75f60efd80bb3995234586e1821f060fe70a9c11bed4"
)
LOGGER = logging.getLogger(__name__)


def main() -> int:
    """Print a complete JSON summary for the bounded 87-entry inspection path."""
    parser = argparse.ArgumentParser(
        description=(
            "Audit only the currently implemented Task 04D no-page section rules. "
            "This command does not run the full accepted policy or publish artifacts."
        )
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        help="Artifact root; defaults to the required ER_COMMONS_DATA_ROOT setting.",
    )
    args = parser.parse_args()
    configured_root = os.environ.get("ER_COMMONS_DATA_ROOT")
    if args.data_root is None and not configured_root:
        parser.error("set ER_COMMONS_DATA_ROOT or pass --data-root")
    data_root = args.data_root or Path(configured_root or "")
    task03j = data_root / "pipelines/brisbane_baylands/task_03h_clean_full_v4"
    entries = (
        data_root
        / "pipelines/brisbane_baylands/task_04_navigation_overlay"
        / ACCEPTED_TASK04C_LINK_VIEW
        / "toc_text_entries.jsonl"
    )
    document_publications = task03j / "document_publications"
    if not entries.is_file():
        parser.error(f"accepted Task 04C TOC entries are missing: {entries}")
    if not document_publications.is_dir():
        parser.error(f"Task 03J document publications are missing: {document_publications}")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    LOGGER.info("auditing no-page sections from %s", entries)
    records, summary = reconcile_task04d_no_page_sections(
        entries_path=entries,
        document_publications_root=document_publications,
        policy=load_document_linking_policy(
            Path("configs/linking_policies/document_linking_v1.json"),
            schema_path=Path(
                "benchmarks/er_bench/schemas/document_linking/v1/linking_policy.schema.json"
            ),
        ),
    )
    summary["audit_scope"] = "implemented_no_page_sections_only"
    summary["accepted_task04c_link_view"] = ACCEPTED_TASK04C_LINK_VIEW
    summary["entries_path"] = str(entries)
    summary["document_publications_root"] = str(document_publications)
    summary["resolved_entries"] = [
        {
            "raw_entry_text": record["raw_entry_text"],
            "target_ids": record["target_ids"],
            "match_basis": record["match_basis"],
        }
        for record in records
        if record["outcome"] == "resolved_unique"
    ]
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
