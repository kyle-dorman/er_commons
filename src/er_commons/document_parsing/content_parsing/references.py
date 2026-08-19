"""Resolve closed references from derived stages to immutable owner bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from er_commons.artifact_io import assert_contained, iter_jsonl, read_json_object, sha256_file
from er_commons.document_parsing.content_parsing.evidence import (
    CompletedRunInvariantError,
    verify_inventory_metadata,
)
from er_commons.document_parsing.heading_evidence_parsing.heading_overlay import (
    apply_heading_overlay,
)


class ConversionInputReference(BaseModel):
    """Exact conversion owner and seal digests required by a derived producer."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["er_commons.conversion_input_reference.v1"]
    conversion_id: str
    path: str
    completion_path: str
    inventory_path: str
    completion_sha256: str
    inventory_sha256: str
    document_view: Literal["base", "heading"]


@dataclass(frozen=True)
class ResolvedConversionInput:
    """Contained owner root after small-seal verification."""

    reference: ConversionInputReference
    root: Path
    inventory: dict[str, Any]


def resolve_conversion_input(data_root: Path, reference_path: Path) -> ResolvedConversionInput:
    """Verify a closed conversion reference without hashing unused large payloads."""
    reference = ConversionInputReference.model_validate(read_json_object(reference_path))
    root = assert_contained(data_root, reference.path)
    completion_path = assert_contained(data_root, reference.completion_path)
    inventory_path = assert_contained(data_root, reference.inventory_path)
    expected_records = root / "records"
    if completion_path != expected_records / "completion_record.json":
        raise CompletedRunInvariantError("conversion_reference", "completion path differs")
    if inventory_path != expected_records / "artifact_inventory.json":
        raise CompletedRunInvariantError("conversion_reference", "inventory path differs")
    if sha256_file(completion_path) != reference.completion_sha256:
        raise CompletedRunInvariantError("conversion_reference", "completion digest differs")
    if sha256_file(inventory_path) != reference.inventory_sha256:
        raise CompletedRunInvariantError("conversion_reference", "inventory digest differs")
    completion = read_json_object(completion_path)
    if completion.get("conversion_id") != reference.conversion_id:
        raise CompletedRunInvariantError("conversion_reference", "conversion ID differs")
    inventory = read_json_object(inventory_path)
    verify_inventory_metadata(root, inventory)
    return ResolvedConversionInput(reference, root, inventory)


def inventory_file_record(
    resolved: ResolvedConversionInput,
    relative_path: str,
) -> dict[str, object]:
    """Return one sealed owner file record after path and size checks."""
    records = resolved.inventory.get("files")
    if not isinstance(records, list):
        raise CompletedRunInvariantError("conversion_inventory", "files list is invalid")
    matches = [
        record
        for record in records
        if isinstance(record, dict) and record.get("path") == relative_path
    ]
    if len(matches) != 1:
        raise CompletedRunInvariantError(
            "conversion_inventory", f"expected one managed file: {relative_path}"
        )
    record = matches[0]
    path = resolved.root / relative_path
    if not path.is_file() or path.stat().st_size != record.get("byte_size"):
        raise CompletedRunInvariantError(
            "conversion_inventory", f"managed file differs: {relative_path}"
        )
    return record


def load_conversion_document(
    resolved: ResolvedConversionInput,
    *,
    source_id: str,
) -> dict[str, Any]:
    """Load the configured base or heading view from one common document owner."""
    prefix = f"documents/{source_id}/producer/docling"
    document_relative = f"{prefix}/document.json"
    inventory_file_record(resolved, document_relative)
    document = read_json_object(resolved.root / document_relative)
    if resolved.reference.document_view == "base":
        return document
    overlay_relative = f"{prefix}/heading_overlay.jsonl"
    inventory_file_record(resolved, overlay_relative)
    overlay = list(iter_jsonl(resolved.root / overlay_relative))
    return apply_heading_overlay(document, overlay)


def load_document_views(
    baseline: ResolvedConversionInput,
    hierarchy: ResolvedConversionInput,
    *,
    source_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load one common base document and derive its detached heading view once."""
    references = (baseline.reference, hierarchy.reference)
    if (
        baseline.root != hierarchy.root
        or references[0].conversion_id != references[1].conversion_id
        or references[0].completion_sha256 != references[1].completion_sha256
        or references[0].inventory_sha256 != references[1].inventory_sha256
    ):
        raise CompletedRunInvariantError(
            "conversion_document_views",
            "baseline and hierarchy views must share one sealed conversion owner",
        )
    if {reference.document_view for reference in references} != {"base", "heading"}:
        raise CompletedRunInvariantError(
            "conversion_document_views",
            "one base and one heading view are required",
        )
    base = baseline if baseline.reference.document_view == "base" else hierarchy
    heading = hierarchy if hierarchy.reference.document_view == "heading" else baseline
    prefix = f"documents/{source_id}/producer/docling"
    document_relative = f"{prefix}/document.json"
    overlay_relative = f"{prefix}/heading_overlay.jsonl"
    inventory_file_record(base, document_relative)
    inventory_file_record(heading, overlay_relative)
    document = read_json_object(base.root / document_relative)
    overlay = list(iter_jsonl(heading.root / overlay_relative))
    heading_document = apply_heading_overlay(document, overlay)
    return (
        (document, heading_document)
        if baseline.reference.document_view == "base"
        else (heading_document, document)
    )


__all__ = [
    "ConversionInputReference",
    "ResolvedConversionInput",
    "inventory_file_record",
    "load_conversion_document",
    "load_document_views",
    "resolve_conversion_input",
]
