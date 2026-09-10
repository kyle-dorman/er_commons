"""Deliberate byte audit of historical navigation seals, separate from compact reuse."""

from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import (
    artifact_inventory,
    canonical_json_sha256,
    read_json_object,
    sha256_file,
)


def deep_audit_navigation_root(root: Path) -> str:
    """Verify the exact completed Task 04C bundle before consuming its rows."""
    completion_path = root / "records/completion_record.json"
    inventory_path = root / "records/artifact_inventory.json"
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"role=navigation_audit path={path}: symlink is not managed evidence")
    completion = read_json_object(completion_path)
    if completion.get("status") != "complete" or completion.get("link_view_id") != root.name:
        raise ValueError(f"invalid Task 04C completion identity: {root}")
    preimage = read_json_object(root / "records/identity_preimage.json")
    if root.name != f"navlinkv1-{canonical_json_sha256(preimage)}":
        raise ValueError(f"Task 04C identity does not rederive from its preimage: {root}")
    if sha256_file(inventory_path) != completion.get("artifact_inventory_sha256"):
        raise ValueError(f"Task 04C inventory seal differs: {inventory_path}")
    required = {
        "toc_text_pages.jsonl",
        "toc_text_entries.jsonl",
        "toc_entry_reconciliations.jsonl",
        "link_overlay.jsonl",
        "records/identity_preimage.json",
    }
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"role=navigation_audit path={path}: symlink is not managed evidence")
    sealed = read_json_object(inventory_path)
    observed = artifact_inventory(
        root, {"records/artifact_inventory.json", "records/completion_record.json"}
    )
    if observed != sealed:
        expected_paths = {
            str(row.get("path")) for row in _object_rows(sealed.get("files"), inventory_path)
        }
        observed_paths = {str(row["path"]) for row in observed["files"]}
        raise ValueError(
            f"role=navigation_audit path={root}: exact inventory differs; "
            f"missing={sorted(expected_paths - observed_paths)[:8]} "
            f"extra={sorted(observed_paths - expected_paths)[:8]}"
        )
    observed_records = {str(row["path"]): row for row in observed["files"]}
    if not required.issubset(observed_records):
        raise ValueError(f"role=navigation_audit path={root}: required input rows absent")
    managed_files = _object_rows(completion.get("managed_files"), completion_path)
    expected_records = dict(observed_records)
    expected_records["records/artifact_inventory.json"] = {
        "path": "records/artifact_inventory.json",
        "byte_size": inventory_path.stat().st_size,
        "sha256": completion["artifact_inventory_sha256"],
    }
    if (
        len(managed_files) != len(expected_records)
        or {str(row.get("path")): row for row in managed_files} != expected_records
    ):
        raise ValueError(f"role=navigation_audit path={completion_path}: managed closure differs")
    return sha256_file(completion_path)


def _object_rows(value: object, path: Path) -> list[dict[str, Any]]:
    """Reject malformed inventory rows before inspecting their closed record values."""
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"role=navigation_audit path={path}: expected object rows")
    return cast(list[dict[str, Any]], value)
