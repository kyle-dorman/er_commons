"""Completion-last serialization, verification, reuse, and failure retention."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from er_commons.canonical_extraction.publication import (
    build_inventory,
    sha256_file,
    write_inventory,
)
from er_commons.cross_reference_materialization.construction import CrossReferenceBuild
from er_commons.cross_reference_materialization.errors import CrossReferenceMaterializationError
from er_commons.cross_reference_materialization.io import write_json, write_jsonl

JsonObject = dict[str, Any]
NEW_SUPPORT_PATHS = {
    "cross_reference_target_index": "support/cross_reference_target_index.json",
    "cross_reference_summary": "support/cross_reference_summary.json",
    "cross_reference_preservation": "support/cross_reference_preservation.json",
}


def serialize_candidate(
    *,
    root: Path,
    upstream_root: Path,
    build: CrossReferenceBuild,
    identity: JsonObject,
) -> None:
    """Write deterministic records and completion only after all other artifacts."""
    candidate_id = identity["extraction_id"]
    upstream_manifest = json.loads((upstream_root / "records" / "manifest.json").read_bytes())
    write_json(root / "records" / "extraction_identity.json", identity)

    record_files: list[JsonObject] = []
    for item in upstream_manifest["record_files"]:
        path = item["path"]
        if path == "canonical/target_aliases.jsonl":
            records = build.target_aliases
        elif path == "canonical/cross_references.jsonl":
            records = build.cross_references
        else:
            records = build.record_files[path]
        write_jsonl(root / path, records)
        record_files.append(
            {
                "record_type": item["record_type"],
                "path": path,
                "sha256": sha256_file(root / path),
                "record_count": len(records),
            }
        )

    inherited_support = []
    for item in upstream_manifest["support_files"]:
        source = upstream_root / item["path"]
        destination = root / item["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        inherited_support.append(
            {**item, "upstream_candidate_id": identity["upstream_candidate_id"]}
        )
    new_support = []
    for role, path in NEW_SUPPORT_PATHS.items():
        write_json(root / path, build.support[role])
        new_support.append(
            {
                "role": role,
                "path": path,
                "sha256": sha256_file(root / path),
                "schema_version": "3.0.0",
            }
        )
    extension = {
        "schema_version": "er_commons.canonical_extraction_manifest.v3",
        "cross_reference_count": len(build.cross_references),
        "preserved_alias_count": build.support["cross_reference_preservation"][
            "upstream_alias_count"
        ],
        "derived_table_alias_count": build.support["cross_reference_preservation"][
            "derived_table_alias_count"
        ],
        "derived_figure_alias_count": 0,
        "support_files": new_support,
    }
    manifest = {
        **upstream_manifest,
        "schema_version": "er_commons.canonical_extraction_manifest.v3",
        "extraction_id": candidate_id,
        "identity_sha256": identity["identity_sha256"],
        "ordered_document_ids": [build.record_files["canonical/documents.jsonl"][0]["id"]],
        "record_files": record_files,
        "target_alias_count": len(build.target_aliases),
        "cross_reference_count": len(build.cross_references),
        "support_files": [*inherited_support, *new_support],
        "cross_reference_extension": extension,
    }
    write_json(root / "records" / "manifest.json", manifest)
    upstream_summary = json.loads(
        (upstream_root / "records" / "canonicalization_summary.json").read_bytes()
    )
    write_json(
        root / "records" / "canonicalization_summary.json",
        {
            **upstream_summary,
            "schema_version": "er_commons.cross_reference_materialization_summary.v3",
            "candidate_id": candidate_id,
            "counts": {
                **upstream_summary["counts"],
                "target_aliases": len(build.target_aliases),
                "cross_references": len(build.cross_references),
            },
            "cross_reference_summary": build.support["cross_reference_summary"],
        },
    )
    inventory_path = write_inventory(root)
    write_json(
        root / "records" / "completion_record.json",
        {
            "schema_version": "er_commons.canonical_extraction_completion.v3",
            "extraction_id": candidate_id,
            "status": "complete_with_warnings",
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "support_files_verified": True,
            "preservation_status": "passed",
            "undeclared_difference_count": 0,
        },
    )


def verify_completed_candidate(root: Path, candidate_id: str) -> Path:
    """Fail closed unless identity, inventory, completion, and support are exact."""
    completion_path = root / "records" / "completion_record.json"
    inventory_path = root / "records" / "artifact_inventory.json"
    manifest_path = root / "records" / "manifest.json"
    if not all(path.is_file() for path in (completion_path, inventory_path, manifest_path)):
        raise CrossReferenceMaterializationError("candidate terminal records are incomplete")
    completion = json.loads(completion_path.read_bytes())
    manifest = json.loads(manifest_path.read_bytes())
    inventory = json.loads(inventory_path.read_bytes())
    expected = {
        "schema_version": "er_commons.canonical_extraction_completion.v3",
        "extraction_id": candidate_id,
        "status": "complete_with_warnings",
        "support_files_verified": True,
        "preservation_status": "passed",
        "undeclared_difference_count": 0,
    }
    if any(completion.get(key) != value for key, value in expected.items()):
        raise CrossReferenceMaterializationError("completion fields differ")
    if completion.get("artifact_inventory_sha256") != sha256_file(inventory_path):
        raise CrossReferenceMaterializationError("completion does not seal inventory")
    if inventory != build_inventory(root):
        raise CrossReferenceMaterializationError("managed file inventory differs")
    support = {item["role"]: item for item in manifest["support_files"]}
    for role, path in NEW_SUPPORT_PATHS.items():
        item = support.get(role)
        if item is None or item["path"] != path or item["sha256"] != sha256_file(root / path):
            raise CrossReferenceMaterializationError(f"support role differs: {role}")
    return completion_path


def preserve_failed_attempt(task_root: Path, staging_root: Path) -> Path:
    """Retain a failed workspace without a misleading completion record."""
    failed = task_root / "attempts" / staging_root.name
    failed.parent.mkdir(parents=True, exist_ok=True)
    staging_root.rename(failed)
    (failed / "records" / "completion_record.json").unlink(missing_ok=True)
    return failed
