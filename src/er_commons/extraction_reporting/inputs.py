"""Typed access and checksum verification for extraction-report inputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from er_commons.artifact_io import canonical_json_sha256, sha256_file
from er_commons.extraction_reporting.compatibility_v1 import legacy_product_completion

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class VerifiedCollectionEvidence:
    """Validated top-level views needed to summarize one collection bundle."""

    production_extraction_id: str
    document_completions: tuple[JsonObject, ...]
    accounting: JsonObject
    target_index: JsonObject
    resolution: JsonObject
    handoff: JsonObject

    @classmethod
    def from_bundle(cls, bundle: JsonObject) -> VerifiedCollectionEvidence:
        """Validate report-required bundle structure at one explicit boundary."""
        production_id = bundle.get("production_extraction_id")
        if not isinstance(production_id, str) or not production_id:
            raise ValueError("collection bundle lacks production_extraction_id")
        completions = _object_list(bundle, "document_completions", context="collection bundle")
        accounting = _object(bundle, "accounting", context="collection bundle")
        _object_list(accounting, "rows", context="collection accounting")
        resolution = _object(bundle, "resolution_completion", context="collection bundle")
        _object_list(resolution, "resolutions", context="resolution completion")
        return cls(
            production_extraction_id=production_id,
            document_completions=tuple(completions),
            accounting=accounting,
            target_index=_object(bundle, "target_index", context="collection bundle"),
            resolution=resolution,
            handoff=_object(bundle, "handoff", context="collection bundle"),
        )

    @property
    def accounting_rows(self) -> tuple[JsonObject, ...]:
        """Return the validated ordered accounting rows."""
        return tuple(_object_list(self.accounting, "rows", context="collection accounting"))


def read_json_object(path: Path) -> JsonObject:
    """Read one JSON object and report parsing failures with its path."""
    try:
        value = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON object {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def read_jsonl_objects(path: Path) -> list[JsonObject]:
    """Read ordered JSONL objects and identify the failing file and line."""
    try:
        lines = path.read_text().splitlines()
    except OSError as error:
        raise ValueError(f"cannot read JSONL input {path}: {error}") from error
    rows: list[JsonObject] = []
    for number, line in enumerate(lines, start=1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSONL record {path}:{number}: {error.msg}") from error
        if not isinstance(value, dict):
            raise ValueError(f"expected JSON object: {path}:{number}")
        rows.append(value)
    return rows


def product_completion(
    identity: JsonObject,
    product: Literal["stable_content_evidence", "hierarchy_decisions"],
) -> JsonObject:
    """Select a v2 product role or route immutable v1 evidence explicitly."""
    stages = identity.get("stage_completions")
    if not isinstance(stages, dict):
        raise ValueError("document identity has no stage completions")
    if identity.get("schema_version") == "er_commons.document_candidate_identity.v2":
        value = stages.get(product)
        if not isinstance(value, dict):
            raise ValueError(f"v2 document identity lacks {product}")
        return cast(JsonObject, value)
    return legacy_product_completion(identity, product)


def verified_reference(data_root: Path, reference: JsonObject, *, role: str) -> Path:
    """Resolve and verify one checksum-bound input reference."""
    relative = reference.get("path")
    expected = reference.get("sha256")
    root = data_root.resolve()
    path = (root / str(relative)).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"{role} reference escapes data root: {relative}")
    if not path.is_file():
        raise ValueError(f"{role} reference is absent: {relative}")
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(
            f"{role} checksum differs: path={relative}, expected={expected}, observed={observed}"
        )
    return path


def verified_inventory(root: Path, *, completion: Path, role: str) -> JsonObject:
    """Verify one process inventory against its completion seal."""
    completion_record = read_json_object(completion)
    inventory_path = root / "records" / "artifact_inventory.json"
    if not inventory_path.is_file():
        raise ValueError(f"{role} inventory is absent: {inventory_path}")
    inventory = read_json_object(inventory_path)
    accepted_seals = {sha256_file(inventory_path), canonical_json_sha256(inventory)}
    observed = completion_record.get("artifact_inventory_sha256")
    if observed not in accepted_seals:
        raise ValueError(
            f"{role} inventory seal differs: root={root}, observed={observed}, "
            f"accepted={sorted(accepted_seals)}"
        )
    return inventory


def verified_inventory_path(
    root: Path,
    inventory: JsonObject,
    relative: str,
    *,
    role: str,
) -> Path:
    """Verify one inventoried artifact with explicit absence/size/hash errors."""
    entries = {str(item["path"]): item for item in inventory.get("files", [])}
    item = entries.get(relative)
    if item is None:
        raise ValueError(f"{role} artifact is absent from inventory: {relative}")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"{role} artifact escapes process root: {relative}")
    if not path.is_file():
        raise ValueError(f"{role} artifact file is absent: {relative}")
    observed_size = path.stat().st_size
    if observed_size != item.get("byte_size"):
        raise ValueError(
            f"{role} artifact size differs: path={relative}, "
            f"expected={item.get('byte_size')}, observed={observed_size}"
        )
    observed_sha = sha256_file(path)
    if observed_sha != item.get("sha256"):
        raise ValueError(
            f"{role} artifact checksum differs: path={relative}, "
            f"expected={item.get('sha256')}, observed={observed_sha}"
        )
    return path


def _object(value: JsonObject, field: str, *, context: str) -> JsonObject:
    observed = value.get(field)
    if not isinstance(observed, dict):
        raise ValueError(f"{context} field must be an object: {field}")
    return observed


def _object_list(value: JsonObject, field: str, *, context: str) -> list[JsonObject]:
    observed = value.get(field)
    if not isinstance(observed, list) or any(not isinstance(item, dict) for item in observed):
        raise ValueError(f"{context} field must be a list of objects: {field}")
    return cast(list[JsonObject], observed)


__all__ = [
    "JsonObject",
    "VerifiedCollectionEvidence",
    "product_completion",
    "read_json_object",
    "read_jsonl_objects",
    "verified_inventory",
    "verified_inventory_path",
    "verified_reference",
]
