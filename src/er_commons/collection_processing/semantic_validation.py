"""Native semantic validation for a published collection contract v2 bundle."""

from __future__ import annotations

from er_commons.collection_processing.artifact_reader import CollectionArtifactReader
from er_commons.collection_processing.contract import (
    JsonObject,
    build_collection_handoff_id,
    build_cross_document_link_id,
    build_record_target_index_id,
)
from er_commons.collection_processing.validation_support import (
    object_array as _objects,
)
from er_commons.collection_processing.validation_support import (
    object_field as _object,
)
from er_commons.collection_processing.validation_support import (
    object_value as _dict,
)
from er_commons.collection_processing.validation_support import (
    verify_digest_ref as _verify_digest_ref,
)
from er_commons.collection_processing.validation_support import (
    verify_inventory as _verify_inventory,
)


def validate_collection_bundle(bundle: JsonObject, reader: CollectionArtifactReader) -> None:
    """Validate v2 identities, joins, counts, and exact referenced bytes."""
    accounting = _object(bundle, "accounting")
    index = _object(bundle, "target_index")
    links = _object(bundle, "resolution_completion")
    handoff = _object(bundle, "handoff")

    _validate_accounting(bundle, accounting, reader)
    _validate_index(accounting, index, reader)
    _validate_links(index, links, reader)
    _validate_handoff(accounting, index, links, handoff, reader)
    _validate_stage_attempts(bundle, reader)


def _validate_accounting(
    bundle: JsonObject, accounting: JsonObject, reader: CollectionArtifactReader
) -> None:
    if accounting.get("schema_version") != "er_commons.collection_accounting.v2":
        raise ValueError("collection accounting schema is not v2")
    if accounting.get("production_extraction_id") != bundle.get("production_extraction_id"):
        raise ValueError("collection accounting production identity differs")
    sources = _objects(accounting, "ordered_sources")
    rows = _objects(accounting, "rows")
    source_ids = [source.get("source_id") for source in sources]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("collection accounting repeats a source")
    if [row.get("source_id") for row in rows] != source_ids:
        raise ValueError("collection accounting rows differ from declared source order")
    if [row.get("source_ordinal") for row in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("collection accounting ordinals are not contiguous")
    observed = {
        "total": len(rows),
        "complete": sum(row.get("terminal_state") == "complete" for row in rows),
        "complete_with_warnings": sum(
            row.get("terminal_state") == "complete_with_warnings" for row in rows
        ),
        "failed_terminal": sum(row.get("terminal_state") == "failed_terminal" for row in rows),
    }
    if accounting.get("counts") != observed:
        raise ValueError("collection accounting counts differ from rows")
    _verify_inventory(accounting, reader)


def _validate_index(
    accounting: JsonObject, index: JsonObject, reader: CollectionArtifactReader
) -> None:
    if index.get("schema_version") != "er_commons.record_target_index_completion.v2":
        raise ValueError("record-target index completion schema is not v2")
    preimage = _object(index, "identity_preimage")
    if index.get("index_id") != build_record_target_index_id(preimage):
        raise ValueError("record-target index ID differs from its v2 preimage")
    if preimage.get("ordering_policy_version") != "record_target_order_v2":
        raise ValueError("record-target index uses a non-v2 ordering policy")
    if reader.read_json(_object(index, "identity_preimage_ref")) != preimage:
        raise ValueError("record-target identity preimage reference differs")
    _verify_digest_ref(
        index,
        "accounting_ref",
        preimage,
        "accounting_sha256",
        reader,
    )
    rows = _objects(accounting, "rows")
    successful = {row["source_id"] for row in rows if row["terminal_state"] != "failed_terminal"}
    failed = {row["source_id"] for row in rows if row["terminal_state"] == "failed_terminal"}
    eligible = _objects(index, "eligible_candidates")
    unavailable = _objects(index, "unavailable_sources")
    if {row.get("source_id") for row in eligible} != successful:
        raise ValueError("record-target eligible candidates differ from accounting")
    if {_object(row, "source").get("source_id") for row in unavailable} != failed:
        raise ValueError("record-target unavailable sources differ from accounting")
    if index.get("entry_count") != len(_objects(index, "entries")):
        raise ValueError("record-target entry count differs")
    if index.get("document_target_count") != len(_objects(index, "document_targets")):
        raise ValueError("record-target document count differs")
    for field in ("unavailable_sources_ref", "entries_ref", "document_targets_ref"):
        reader.read(_object(index, field))
    _verify_inventory(index, reader)


def _validate_links(index: JsonObject, links: JsonObject, reader: CollectionArtifactReader) -> None:
    if links.get("schema_version") != "er_commons.cross_document_link_completion.v2":
        raise ValueError("cross-document link completion schema is not v2")
    if links.get("index_id") != index.get("index_id"):
        raise ValueError("cross-document links name a different record-target index")
    preimage = _object(links, "identity_preimage")
    if links.get("resolution_id") != build_cross_document_link_id(preimage):
        raise ValueError("cross-document link ID differs from its v2 preimage")
    if reader.read_json(_object(links, "identity_preimage_ref")) != preimage:
        raise ValueError("cross-document link identity preimage reference differs")
    _verify_digest_ref(
        links,
        "index_completion_ref",
        preimage,
        "index_completion_sha256",
        reader,
    )
    reader.read(_object(links, "mention_input_manifest_ref"))
    reader.read(_object(links, "resolutions_ref"))
    resolutions = _objects(links, "resolutions")
    observed = {
        "total": len(resolutions),
        "resolved": sum(row.get("status") == "resolved" for row in resolutions),
        "ambiguous": sum(row.get("status") == "ambiguous" for row in resolutions),
        "unresolved": sum(row.get("status") == "unresolved" for row in resolutions),
    }
    if links.get("counts") != observed:
        raise ValueError("cross-document link counts differ from resolutions")
    if links.get("candidate_inventories_before") != links.get("candidate_inventories_after"):
        raise ValueError("cross-document linking changed document candidate inventories")
    manifest = _object(links, "mention_input_manifest")
    if manifest.get("schema_version") != "er_commons.cross_document_mention_manifest.v2":
        raise ValueError("cross-document mention manifest schema is not v2")
    _verify_inventory(links, reader)


def _validate_handoff(
    accounting: JsonObject,
    index: JsonObject,
    links: JsonObject,
    handoff: JsonObject,
    reader: CollectionArtifactReader,
) -> None:
    if handoff.get("schema_version") != "er_commons.collection_handoff.v2":
        raise ValueError("collection handoff schema is not v2")
    if handoff.get("index_id") != index.get("index_id"):
        raise ValueError("collection handoff names a different record-target index")
    if handoff.get("resolution_id") != links.get("resolution_id"):
        raise ValueError("collection handoff names different cross-document links")
    preimage = _object(handoff, "identity_preimage")
    if handoff.get("handoff_id") != build_collection_handoff_id(preimage):
        raise ValueError("collection handoff ID differs from its v2 preimage")
    if reader.read_json(_object(handoff, "identity_preimage_ref")) != preimage:
        raise ValueError("collection handoff identity preimage reference differs")
    for reference_field, digest_field in (
        ("accounting_completion_ref", "accounting_completion_sha256"),
        ("index_completion_ref", "index_completion_sha256"),
        ("resolution_completion_ref", "resolution_completion_sha256"),
    ):
        _verify_digest_ref(handoff, reference_field, preimage, digest_field, reader)
    reader.read(_object(handoff, "blocking_policy_ref"))
    reasons = _objects(handoff, "blocking_reasons")
    strict = handoff.get("blocking_policy") == "all_sources_successful"
    failures = int(_object(accounting, "counts").get("failed_terminal", 0))
    expected_status = "blocked" if strict and failures else "ready"
    if handoff.get("status") != expected_status:
        raise ValueError("collection handoff status differs from policy and accounting")
    if bool(reasons) != (expected_status == "blocked"):
        raise ValueError("collection handoff reasons differ from its status")
    if handoff.get("task04_status") != "not_evaluated":
        raise ValueError("collection handoff may not claim Task 04 evaluation")
    _verify_inventory(handoff, reader)


def _validate_stage_attempts(bundle: JsonObject, reader: CollectionArtifactReader) -> None:
    for attempt in _objects(bundle, "collection_stage_attempts"):
        if attempt.get("schema_version") != "er_commons.collection_stage_attempt.v2":
            raise ValueError("collection stage attempt schema is not v2")
        for reference in attempt.get("state_event_refs", []):
            reader.read(_dict(reference, "state event reference"))
        completion = attempt.get("completion_ref")
        if completion is not None:
            reader.read(_dict(completion, "stage completion reference"))


__all__ = ["CollectionArtifactReader", "validate_collection_bundle"]
