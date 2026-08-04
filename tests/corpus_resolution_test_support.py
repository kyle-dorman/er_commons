"""Shared synthetic corpus inputs for runtime and reference-equivalence tests."""

from __future__ import annotations

import json
from pathlib import Path

from er_commons.source_freeze import write_json_atomic


def write_scope_spec(tmp_path: Path, data_root: Path) -> Path:
    """Write one explicit two-source fixture scope and sealed catalog."""
    manifest = json.loads((data_root / "release/records/source_manifest.json").read_bytes())
    records = {row["source_id"]: row for row in manifest["sources"]}
    catalog = {
        "documents": [
            {
                "source": {
                    "source_id": source_id,
                    "sha256": records[source_id]["sha256"],
                    "pdf_page_count": records[source_id]["pdf_page_count"],
                },
                "lookup_keys": [f"report {source_id}"],
            }
            for source_id in ("alpha", "beta")
        ]
    }
    write_json_atomic(data_root / "catalog.json", catalog)
    path = tmp_path / "scope_spec.json"
    write_json_atomic(
        path,
        {
            "schema_version": "er_commons.scope_run_spec.v1",
            "document_run_spec": "run_spec.json",
            "source_ids": ["alpha", "beta"],
            "corpus_catalog_relative_path": "catalog.json",
            "blocking_policy": "all_sources_successful",
            "target_policy_sha256": "d" * 64,
            "resolution_policy_sha256": "e" * 64,
            "ordering_policy_version": "corpus_target_order_v1",
        },
    )
    return path


def write_cross_reference_inputs(root: Path, source_id: str) -> None:
    """Attach deterministic stage-one mention and alias streams to a fixture candidate."""
    canonical = root / "canonical"
    canonical.mkdir(parents=True, exist_ok=True)
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
    aliases = (
        [
            {
                "id": "fixture-beta-alias-1",
                "normalized_alias": "report beta",
                "targets": [{"target_id": "fixture-beta-document", "target_type": "document"}],
            }
        ]
        if source_id == "beta"
        else []
    )
    (canonical / "target_aliases.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in aliases)
    )
