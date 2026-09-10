"""Audit the implemented document no-page-section rules without publishing."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from er_commons.document_records.document_references.linking_policy import (
    load_document_linking_policy,
)
from er_commons.navigation_overlay.linking_reconciliation import (
    reconcile_no_page_sections,
)

LOGGER = logging.getLogger(__name__)


def main() -> int:
    """Print a complete JSON summary for the selected inspection path."""
    parser = argparse.ArgumentParser(
        description=(
            "Audit only the currently implemented Task 04D no-page section rules. "
            "This command does not run the full accepted policy or publish artifacts."
        )
    )
    parser.add_argument("--entries", type=Path, required=True)
    parser.add_argument("--document-publications-root", type=Path, required=True)
    parser.add_argument("--linking-policy", type=Path, required=True)
    parser.add_argument("--policy-schema", type=Path, required=True)
    parser.add_argument("--operation", choices=["no-page-sections"], required=True)
    args = parser.parse_args()
    entries = args.entries
    document_publications = args.document_publications_root
    if not entries.is_file():
        parser.error(f"accepted Task 04C TOC entries are missing: {entries}")
    if not document_publications.is_dir():
        parser.error(f"Task 03J document publications are missing: {document_publications}")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    LOGGER.info("auditing no-page sections from %s", entries)
    records, summary = reconcile_no_page_sections(
        entries_path=entries,
        document_publications_root=document_publications,
        policy=load_document_linking_policy(
            args.linking_policy,
            schema_path=args.policy_schema,
        ),
    )
    summary["audit_scope"] = "implemented_no_page_sections_only"
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
