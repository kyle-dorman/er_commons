"""Shared synthetic corpus inputs for runtime and reference-equivalence tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from er_commons.artifact_io import write_json_atomic


def write_collection_spec(tmp_path: Path, data_root: Path) -> Path:
    """Write one explicit two-source fixture collection and sealed catalog."""
    manifest = json.loads((data_root / "release/records/source_manifest.json").read_bytes())
    records = {row["source_id"]: row for row in manifest["sources"]}
    catalog = {
        "schema_version": "er_commons.source_family_catalog.v1",
        "catalog_version": "fixture_source_family_v1",
        "source_family_id": "fixture_family",
        "sources": [
            {
                "source": {
                    "source_id": source_id,
                    "sha256": records[source_id]["sha256"],
                    "pdf_page_count": records[source_id]["pdf_page_count"],
                },
                "family_root_source_id": "alpha",
                "document_role": "root_report" if source_id == "alpha" else "top_level_appendix",
                "parent_source_id": None if source_id == "alpha" else "alpha",
                "reference_aliases": [f"report {source_id}"],
            }
            for source_id in ("alpha", "beta")
        ],
    }
    write_json_atomic(data_root / "catalog.json", catalog)
    path = tmp_path / "collection_spec.json"
    write_json_atomic(
        path,
        {
            "schema_version": "er_commons.collection_run_spec.v2",
            "document_run_spec": "run_spec.json",
            "source_ids": ["alpha", "beta"],
            "source_family_catalog_relative_path": "catalog.json",
            "blocking_policy": "all_sources_successful",
            "target_policy_sha256": "d" * 64,
            "resolution_policy_sha256": "e" * 64,
            "ordering_policy_version": "record_target_order_v2",
        },
    )
    return path


def write_cross_reference_inputs(root: Path, source_id: str) -> None:
    """Attach deterministic stage-one mention and alias streams to a fixture candidate."""
    canonical = root / "canonical"
    canonical.mkdir(parents=True, exist_ok=True)
    catalog_sha256 = hashlib.sha256((root.parent / "catalog.json").read_bytes()).hexdigest()
    mention_rows = (
        [
            {
                "id": "fixture-alpha-mention-1",
                "document_id": "fixture-alpha-document",
                "sequence": 1,
                "mention_class": "document",
                "lookup_key": "report beta",
                "resolution_status": "unresolved",
                "unresolved_reason": "deferred_cross_document",
                "cross_document_evidence": {
                    "catalog_sha256": catalog_sha256,
                    "source_family_id": "fixture_family",
                    "matched_alias": "report beta",
                    "traversal_rule": "reviewed_named_document_alias",
                    "intended_target_source_ids": ["beta"],
                },
            }
        ]
        if source_id == "alpha"
        else []
    )
    (canonical / "cross_references.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in mention_rows)
    )
    document_path = canonical / "documents.jsonl"
    document = json.loads(document_path.read_text().splitlines()[0])
    document["id"] = f"fixture-{source_id}-document"
    document_path.write_text(json.dumps(document) + "\n")
    target_rows = {
        "sections.jsonl": {"id": f"fixture-{source_id}-section"},
        "tables.jsonl": {"id": f"fixture-{source_id}-table"},
        "figures.jsonl": {"id": f"fixture-{source_id}-figure"},
        "pages.jsonl": {"id": f"fixture-{source_id}-page"},
    }
    for name, row in target_rows.items():
        (canonical / name).write_text(json.dumps(row) + "\n")
    aliases = (
        [
            {
                "id": "fixture-beta-alias-1",
                "normalized_alias": "official beta title",
                "targets": [{"target_id": "fixture-beta-document", "target_type": "document"}],
            },
            *[
                {
                    "id": f"fixture-beta-alias-{target_type}",
                    "normalized_alias": f"{target_type} beta",
                    "targets": [
                        {
                            "target_id": f"fixture-beta-{target_type}",
                            "target_type": target_type,
                        }
                    ],
                }
                for target_type in ("section", "table", "figure", "page")
            ],
        ]
        if source_id == "beta"
        else []
    )
    (canonical / "target_aliases.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in aliases)
    )
