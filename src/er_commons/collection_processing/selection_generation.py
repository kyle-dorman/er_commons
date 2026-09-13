"""Generate an exact source-free selection of retained downstream candidates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

from er_commons.collection_processing.contract import JsonObject
from er_commons.collection_processing.selection_models import ImportedDocumentSelection
from er_commons.task06g.core import canonical_bytes

_PROHIBITED = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".webp",
    ".jp2",
    ".pt",
    ".pth",
    ".safetensors",
    ".onnx",
    ".gguf",
    ".bin",
}


def generate_imported_selection(
    *,
    data_root: Path,
    document_input_root: Path,
    retained_collection_spec: Path,
) -> bytes:
    """Return a deterministic 35-row manifest using compact v32 evidence only."""
    data = data_root.resolve()
    document_root = document_input_root.resolve()
    if not document_root.is_relative_to(data) or not document_root.is_dir():
        raise ValueError("document input root must be a retained data-root directory")
    root_relative = document_root.relative_to(data).as_posix()
    spec = _object(retained_collection_spec)
    membership = spec.get("source_membership")
    if not isinstance(membership, list) or len(membership) != 35:
        raise ValueError("retained collection spec must contain 35 ordered members")
    document_spec_path = document_root / "resolved_specs_v1/00_initial/task06g_document_v1.json"
    production_path = document_root / "resolved_specs_v1/00_initial/production_identity.json"
    candidates = [
        _candidate(
            data_root=data,
            document_root=document_root,
            root_relative=root_relative,
            member=cast(JsonObject, member),
            ordinal=ordinal,
        )
        for ordinal, member in enumerate(membership, start=1)
        if isinstance(member, dict)
    ]
    value: JsonObject = {
        "schema_version": "er_commons.imported_document_selection.v1",
        "document_input_root_relative_path": root_relative,
        "document_production_identity_ref": _ref(production_path, document_root),
        "document_run_spec_ref": _ref(document_spec_path, document_root),
        "source_count": len(candidates),
        "ordered_source_ids": [item["physical_source_id"] for item in candidates],
        "candidates": candidates,
    }
    ImportedDocumentSelection.model_validate(value)
    return canonical_bytes(value)


def write_imported_selection(
    *,
    data_root: Path,
    document_input_root: Path,
    retained_collection_spec: Path,
    output: Path,
    check: bool,
) -> None:
    """Write once or verify the exact deterministic selection bytes."""
    content = generate_imported_selection(
        data_root=data_root,
        document_input_root=document_input_root,
        retained_collection_spec=retained_collection_spec,
    )
    if check:
        if not output.is_file() or output.read_bytes() != content:
            raise ValueError("imported document selection differs from deterministic generation")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    output.write_bytes(content)


def _candidate(
    *,
    data_root: Path,
    document_root: Path,
    root_relative: str,
    member: JsonObject,
    ordinal: int,
) -> JsonObject:
    logical = member.get("logical_source_id")
    physical = member.get("physical_source_id")
    if not isinstance(logical, str) or not isinstance(physical, str):
        raise ValueError("retained collection membership is malformed")
    source_root = document_root / "document_publications/documents" / physical
    matches = sorted(source_root.glob("docv1-*/records/downstream_replay.json"))
    if len(matches) != 1:
        raise ValueError(f"expected one retained downstream candidate for {physical}")
    downstream_path = matches[0]
    candidate_root = downstream_path.parents[1]
    downstream = _object(downstream_path)
    identity_path = candidate_root / "records/document_identity.json"
    completion_path = candidate_root / "records/completion_record.json"
    inventory_path = candidate_root / "records/artifact_inventory.json"
    identity = _object(identity_path)
    linked = downstream.get("replacement_linked_document_completion_ref")
    if not isinstance(linked, dict) or not isinstance(linked.get("path"), str):
        raise ValueError("downstream candidate lacks a linked completion")
    linked_completion = data_root / str(linked["path"])
    linked_root = linked_completion.parents[1]
    if not linked_root.is_relative_to(document_root):
        raise ValueError("linked candidate is outside the retained v32 root")
    linked_completion_ref = _ref(linked_completion, document_root)
    if (
        linked.get("path") != f"{root_relative}/{linked_completion_ref['path']}"
        or linked.get("sha256") != linked_completion_ref["sha256"]
    ):
        raise ValueError("downstream linked completion binding is stale")
    source = identity.get("source")
    candidate_id = identity.get("candidate_id")
    if not isinstance(source, dict) or not isinstance(candidate_id, str):
        raise ValueError("downstream candidate identity is malformed")
    return {
        "source_ordinal": ordinal,
        "logical_source_id": logical,
        "physical_source_id": physical,
        "source_identity": source,
        "candidate_id": candidate_id,
        "candidate_root": candidate_root.relative_to(document_root).as_posix(),
        "document_identity_ref": _ref(identity_path, document_root),
        "document_completion_ref": _ref(completion_path, document_root),
        "candidate_inventory_ref": _ref(inventory_path, document_root),
        "downstream_replay_ref": _ref(downstream_path, document_root),
        "linked_candidate_id": linked_root.name,
        "linked_candidate_root": linked_root.relative_to(document_root).as_posix(),
        "linked_identity_ref": _ref(
            linked_root / "records/extraction_identity.json", document_root
        ),
        "linked_completion_ref": linked_completion_ref,
        "linked_inventory_ref": _ref(
            linked_root / "records/artifact_inventory.json", document_root
        ),
    }


def _ref(path: Path, root: Path) -> JsonObject:
    resolved = path.resolve()
    if (
        not resolved.is_relative_to(root)
        or not resolved.is_file()
        or resolved.is_symlink()
        or resolved.suffix.lower() in _PROHIBITED
    ):
        raise ValueError(f"selection reference is unsafe or absent: {path}")
    content = resolved.read_bytes()
    return {
        "authority": "document_input_root",
        "path": resolved.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "byte_size": len(content),
    }


def _object(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return cast(JsonObject, value)


__all__ = ["generate_imported_selection", "write_imported_selection"]
