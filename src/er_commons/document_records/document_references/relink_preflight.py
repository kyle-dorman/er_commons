"""Metadata-only provenance checks for a prepared document-relink run."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from er_commons.collection_processing.contract import build_collection_handoff_id
from er_commons.document_publication.records import DocumentCompletion
from er_commons.document_records.document_references.relinking_config import (
    DocumentLinkRunSpec,
)
from er_commons.document_records.document_references.types import JsonObject


def validate_base_collection_selection(
    *,
    spec: DocumentLinkRunSpec,
    base_production_identity: JsonObject,
    handoff: JsonObject,
    contract_bundle: JsonObject,
) -> None:
    """Prove selected candidates belong to the sealed base handoff using metadata only.

    This deliberately does not open, hash, or compare document payloads. The run
    specification already seals each selected completion and inventory; this
    check establishes their membership in the declared collection.
    """
    if _object(contract_bundle, "handoff") != handoff:
        raise ValueError("base collection bundle and handoff completion differ")
    preimage = _object(handoff, "identity_preimage")
    if handoff.get("handoff_id") != build_collection_handoff_id(preimage):
        raise ValueError("base collection handoff identity does not derive from its preimage")
    production_id = _text(base_production_identity.get("extraction_id"), "base production ID")
    if (
        handoff.get("status") != "ready"
        or handoff.get("blocking_reasons") != []
        or preimage.get("production_extraction_id") != production_id
        or contract_bundle.get("production_extraction_id") != production_id
    ):
        raise ValueError("base collection is not one ready production lineage")

    accounting = _object(contract_bundle, "accounting")
    ordered_sources = _objects(accounting.get("ordered_sources"), "accounting ordered sources")
    rows = _objects(accounting.get("rows"), "accounting rows")
    embedded = _objects(contract_bundle.get("document_completions"), "document completions")
    expected_count = len(spec.documents)
    if not (len(ordered_sources) == len(rows) == len(embedded) == expected_count):
        raise ValueError("base collection membership count differs from relink selection")

    observed_sources: set[str] = set()
    observed_candidates: set[str] = set()
    for ordinal, (selection, source, row, completion_value) in enumerate(
        zip(spec.documents, ordered_sources, rows, embedded, strict=True), start=1
    ):
        completion = DocumentCompletion.model_validate(completion_value)
        source_id = selection.source_id
        candidate_id = selection.source_document.candidate_id
        if source_id in observed_sources or candidate_id in observed_candidates:
            raise ValueError("base collection repeats a selected source or candidate")
        observed_sources.add(source_id)
        observed_candidates.add(candidate_id)
        if (
            source.get("source_id") != source_id
            or completion.source.model_dump(mode="json") != source
            or completion.source.source_id != source_id
            or completion.candidate_id != candidate_id
            or row.get("source_id") != source_id
            or row.get("source_ordinal") != ordinal
            or row.get("candidate_id") != candidate_id
            or row.get("terminal_state") not in {"complete", "complete_with_warnings"}
        ):
            raise ValueError("base collection ordered source membership differs")
        completion_ref = _object(row, "document_completion_ref")
        inventory_ref = _object(row, "candidate_inventory_ref")
        if (
            completion_ref.get("sha256") != selection.source_document.completion_ref.sha256
            or inventory_ref.get("sha256") != selection.source_document.inventory_ref.sha256
            or completion.candidate_inventory.sha256
            != selection.source_document.inventory_ref.sha256
        ):
            raise ValueError("base collection candidate seals differ from relink selection")


def _object(value: Mapping[str, Any], field: str) -> JsonObject:
    observed = value.get(field)
    if not isinstance(observed, dict):
        raise ValueError(f"base collection field must be an object: {field}")
    return observed


def _objects(value: object, label: str) -> list[JsonObject]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"base collection field must be an object list: {label}")
    return cast(list[JsonObject], value)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty text")
    return value


__all__ = ["validate_base_collection_selection"]
