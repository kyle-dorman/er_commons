"""Validate new collection products while preserving imported document authority."""

from __future__ import annotations

from pathlib import PurePosixPath

from er_commons.authority_reference import AuthorityReference
from er_commons.collection_processing.artifact_reader import CollectionArtifactReader
from er_commons.collection_processing.authority_refs import CollectionArtifactReference
from er_commons.collection_processing.contract import (
    JsonObject,
    canonical_sha256,
    collection_identity_fields,
)
from er_commons.collection_processing.semantic_validation import (
    _validate_accounting,
    _validate_handoff,
    _validate_index,
    _validate_links,
    _validate_stage_attempts,
)
from er_commons.collection_processing.storage import json_bytes, jsonl_bytes
from er_commons.collection_processing.validation_support import object_array, object_field


def _reference(value: object, authority: str) -> JsonObject:
    """Check reference shape and authority; the resolver owns imported byte verification."""
    reference = (
        AuthorityReference.model_validate(value)
        if authority == "artifact_root"
        else CollectionArtifactReference.model_validate(value)
    )
    if reference.authority != authority:
        raise ValueError("imported collection reference uses another authority")
    return reference.model_dump(mode="json")


def _imported_evidence(bundle: JsonObject, accounting: JsonObject) -> None:
    """Require the complete once-only selected population without rewriting any row."""
    imported = object_field(bundle, "imported_document_evidence")
    if set(imported) != {
        "selection_ref",
        "selection_sha256",
        "document_production_identity_ref",
        "document_run_spec_ref",
        "document_input_root_relative_path",
        "selections",
    }:
        raise ValueError("imported document evidence envelope fields differ")
    relative = imported.get("document_input_root_relative_path")
    if (
        not isinstance(relative, str)
        or not relative
        or PurePosixPath(relative).is_absolute()
        or ".." in PurePosixPath(relative).parts
        or relative == "."
        or "\\" in relative
        or PurePosixPath(relative).as_posix() != relative
    ):
        raise ValueError("imported document root must be a normalized relative path")
    selection_ref = _reference(bundle.get("imported_selection_ref"), "artifact_root")
    if (
        imported.get("selection_ref") != selection_ref
        or imported.get("selection_sha256") != bundle.get("imported_selection_sha256")
        or selection_ref["sha256"] != bundle.get("imported_selection_sha256")
    ):
        raise ValueError("imported selection reference or digest differs")
    _reference(bundle.get("collection_production_identity_ref"), "artifact_root")
    for field in ("document_production_identity_ref", "document_run_spec_ref"):
        _reference(imported.get(field), "document_input_root")
    _selected_rows(imported, accounting)


def _selected_rows(imported: JsonObject, accounting: JsonObject) -> None:
    """Join the frozen selection rows to once-only ordered successful accounting."""
    selections = object_array(imported, "selections")
    rows = object_array(accounting, "rows")
    sources = object_array(accounting, "ordered_sources")
    if len(selections) != 35 or len(rows) != 35 or len(sources) != 35:
        raise ValueError("imported collection requires exactly 35 selected documents")
    for field in ("logical_source_id", "physical_source_id", "candidate_id"):
        values = [row.get(field) for row in selections]
        if (
            any(not isinstance(value, str) or not value for value in values)
            or len(set(values)) != 35
        ):
            raise ValueError(f"imported selection repeats or omits {field}")
    for ordinal, (selected, row, source) in enumerate(
        zip(selections, rows, sources, strict=True), 1
    ):
        if (
            selected.get("source_ordinal") != ordinal
            or selected.get("physical_source_id") != row.get("source_id")
            or selected.get("physical_source_id") != source.get("source_id")
            or selected.get("source_identity") != source
            or selected.get("candidate_id") != row.get("candidate_id")
            or row.get("evidence_kind") != "downstream_replay"
            or row.get("terminal_state") not in {"complete", "complete_with_warnings"}
        ):
            raise ValueError("imported selection differs from ordered successful accounting")
        roots = {
            "candidate_root": (
                "candidate_id",
                {
                    "document_identity_ref": "document_identity.json",
                    "document_completion_ref": "completion_record.json",
                    "candidate_inventory_ref": "artifact_inventory.json",
                    "downstream_replay_ref": "downstream_replay.json",
                },
            ),
            "linked_candidate_root": (
                "linked_candidate_id",
                {
                    "linked_identity_ref": "extraction_identity.json",
                    "linked_completion_ref": "completion_record.json",
                    "linked_inventory_ref": "artifact_inventory.json",
                },
            ),
        }
        for root_field, (id_field, references) in roots.items():
            root = selected.get(root_field)
            if not isinstance(root, str) or PurePosixPath(root).name != selected.get(id_field):
                raise ValueError("imported candidate root differs from its identity")
            for field, filename in references.items():
                ref = _reference(selected.get(field), "document_input_root")
                if ref["path"] != f"{root}/records/{filename}":
                    raise ValueError("imported candidate reference differs from its pinned root")
                if field in {
                    "document_completion_ref",
                    "candidate_inventory_ref",
                    "downstream_replay_ref",
                }:
                    if row.get(field) != ref:
                        raise ValueError("accounting reference differs from imported selection")


def _new_output_closure(bundle: JsonObject, reader: CollectionArtifactReader) -> None:
    """Bind embedded stage populations and selected candidate joins to their exact payloads."""
    accounting, index, links, handoff = (
        object_field(bundle, field)
        for field in ("accounting", "target_index", "resolution_completion", "handoff")
    )
    expected = [(row["source_id"], row["candidate_id"]) for row in object_array(accounting, "rows")]
    eligible = object_array(index, "eligible_candidates")
    if [(row.get("source_id"), row.get("candidate_id")) for row in eligible] != expected:
        raise ValueError("v3 index candidate selection differs from accounting")
    manifest = object_field(links, "mention_input_manifest")
    if [
        (row.get("source_id"), row.get("candidate_id"))
        for row in object_array(manifest, "candidates")
    ] != expected:
        raise ValueError("v3 mention candidate selection differs from accounting")
    for stage, ref_field, rows_field, digest_field in (
        (index, "entries_ref", "entries", "entries_sha256"),
        (index, "document_targets_ref", "document_targets", "document_targets_sha256"),
        (index, "unavailable_sources_ref", "unavailable_sources", "unavailable_sources_sha256"),
        (links, "resolutions_ref", "resolutions", "resolutions_sha256"),
    ):
        ref = object_field(stage, ref_field)
        if reader.read(ref) != jsonl_bytes(object_array(stage, rows_field)):
            raise ValueError("v3 embedded stage rows differ from sealed payload")
        if object_field(stage, "identity_preimage").get(digest_field) != ref.get("sha256"):
            raise ValueError("v3 stage payload digest differs from identity")
    if object_field(index, "identity_preimage").get(
        "eligible_candidates_sha256"
    ) != canonical_sha256(eligible):
        raise ValueError("v3 eligible candidate digest differs")
    if reader.read(object_field(links, "mention_input_manifest_ref")) != json_bytes(manifest):
        raise ValueError("v3 mention manifest differs from its reference")
    if object_field(links, "identity_preimage").get("counts_sha256") != canonical_sha256(
        links["counts"]
    ):
        raise ValueError("v3 resolution counts digest differs")
    if handoff.get("scope_id") != accounting.get("scope_id"):
        raise ValueError("v3 handoff scope differs")


def validate_imported_collection_bundle(
    bundle: JsonObject, reader: CollectionArtifactReader
) -> None:
    """Validate v3 joins and new output bytes, retaining distinct original evidence."""
    if any(
        field in bundle
        for field in (
            "production_extraction_id",
            "state_events",
            "document_attempts",
            "document_completions",
            "downstream_replays",
        )
    ):
        raise ValueError("v3 collection cannot impersonate original document publication")
    controls = collection_identity_fields(
        "", bundle.get("collection_production_id"), bundle.get("imported_selection_sha256")
    )
    accounting = object_field(bundle, "accounting")
    index = object_field(bundle, "target_index")
    links = object_field(bundle, "resolution_completion")
    handoff = object_field(bundle, "handoff")
    for record in (
        accounting,
        *(object_field(stage, "identity_preimage") for stage in (index, links, handoff)),
    ):
        if "production_extraction_id" in record or any(
            record.get(key) != value for key, value in controls.items()
        ):
            raise ValueError("v3 stage collection identity or imported selection differs")
        if record.get("scope_id") != accounting.get("scope_id"):
            raise ValueError("v3 stages use different collection scopes")
    _imported_evidence(bundle, accounting)
    _validate_accounting(bundle, accounting, reader, version="v3")
    _validate_index(accounting, index, reader, version="v3")
    _validate_links(index, links, reader, version="v3")
    _validate_handoff(accounting, index, links, handoff, reader, version="v3")
    _new_output_closure(bundle, reader)
    _validate_stage_attempts(bundle, reader)
