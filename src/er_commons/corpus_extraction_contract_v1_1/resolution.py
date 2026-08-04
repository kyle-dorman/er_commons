"""Independent mention derivation and immutable corpus-resolution validation."""

from __future__ import annotations

import json
from collections import Counter
from typing import cast

from er_commons.corpus_extraction_contract_v1_1.accounting import (
    ScopeEvidence,
    unavailable_source_digest,
    validate_unavailable_sources,
)
from er_commons.corpus_extraction_contract_v1_1.artifacts import (
    parse_json_object,
    parse_jsonl,
)
from er_commons.corpus_extraction_contract_v1_1.checks import (
    canonical_sha256,
    fail,
    verify_ref,
)
from er_commons.corpus_extraction_contract_v1_1.identity import validate_resolution_id
from er_commons.corpus_extraction_contract_v1_1.model import ArtifactReader, JsonObject


def validate_resolution_completion(
    bundle: JsonObject,
    scope: ScopeEvidence,
    targets_by_lookup: dict[str, tuple[JsonObject, ...]],
    reader: ArtifactReader,
) -> None:
    """Derive exact eligibility, validate results, and prove stage-one immutability."""
    index = cast(JsonObject, bundle["target_index"])
    completion = cast(JsonObject, bundle["resolution_completion"])
    _require_ref_value(cast(JsonObject, completion["index_completion_ref"]), index, reader)
    if completion["index_id"] != index["index_id"]:
        fail("stale_resolution", "resolution references a different index")

    manifest = cast(JsonObject, completion["mention_input_manifest"])
    _require_ref_value(cast(JsonObject, completion["mention_input_manifest_ref"]), manifest, reader)
    catalog = _load_catalog(cast(JsonObject, manifest["corpus_catalog_ref"]), reader)
    expected_mentions = _derive_manifest(index, manifest, catalog, reader)

    resolutions = cast(list[JsonObject], completion["resolutions"])
    serialized = parse_jsonl(
        verify_ref(cast(JsonObject, completion["resolutions_ref"]), reader),
        subject="corpus_resolutions",
    )
    if serialized != resolutions:
        fail("resolution_bytes", "serialized resolution stream differs")
    if [row["mention_id"] for row in resolutions] != [
        mention["mention_id"] for mention in expected_mentions
    ]:
        fail("mention_coverage", "resolution rows do not exactly cover derived mentions")

    unavailable = validate_unavailable_sources(
        cast(list[JsonObject], index["unavailable_sources"]), scope, reader
    )
    candidate_by_source = {
        source_id: candidate_id for candidate_id, source_id in scope.candidate_sources.items()
    }
    for resolution, mention in zip(resolutions, expected_mentions, strict=True):
        _validate_resolution(
            resolution,
            mention,
            scope,
            unavailable,
            candidate_by_source,
            catalog,
            targets_by_lookup,
            index,
            cast(JsonObject, manifest["corpus_catalog_ref"]),
        )

    expected_counts = _counts(resolutions)
    if completion["counts"] != expected_counts:
        fail("resolution_counts", "resolution aggregates do not recompute")
    before = cast(list[JsonObject], completion["candidate_inventories_before"])
    after = cast(list[JsonObject], completion["candidate_inventories_after"])
    expected_snapshots = [
        {
            "candidate_id": candidate["candidate_id"],
            "inventory_ref": candidate["candidate_inventory_ref"],
        }
        for candidate in cast(list[JsonObject], manifest["candidates"])
    ]
    if before != expected_snapshots or after != before:
        fail("stage_one_mutation", "before/after candidate inventories differ")
    for snapshot in before:
        verify_ref(cast(JsonObject, snapshot["inventory_ref"]), reader)

    inventory_ref = cast(JsonObject, completion["artifact_inventory"])
    verify_ref(inventory_ref, reader)
    preimage = cast(JsonObject, completion["identity_preimage"])
    _require_ref_value(cast(JsonObject, completion["identity_preimage_ref"]), preimage, reader)
    expected_preimage = {
        "schema_version": "er_commons.corpus_resolution_identity.v1_1",
        "production_extraction_id": bundle["production_extraction_id"],
        "scope_id": bundle["accounting"]["scope_id"],
        "index_completion_sha256": completion["index_completion_ref"]["sha256"],
        "mention_input_manifest_sha256": completion["mention_input_manifest_ref"]["sha256"],
        "resolutions_sha256": completion["resolutions_ref"]["sha256"],
        "counts_sha256": canonical_sha256(expected_counts),
        "before_after_inventories_sha256": canonical_sha256({"before": before, "after": after}),
        "resolution_policy_sha256": preimage["resolution_policy_sha256"],
        "managed_inventory_sha256": inventory_ref["sha256"],
    }
    if preimage != expected_preimage:
        fail("resolution_identity", "resolution preimage does not bind exact inputs")
    validate_resolution_id(cast(str, completion["resolution_id"]), preimage)


def _derive_manifest(
    index: JsonObject,
    manifest: JsonObject,
    catalog: dict[str, tuple[JsonObject, ...]],
    reader: ArtifactReader,
) -> list[JsonObject]:
    candidates = cast(list[JsonObject], manifest["candidates"])
    indexed = cast(list[JsonObject], index["eligible_candidates"])
    if len(candidates) != len(indexed) or manifest["candidate_count"] != len(indexed):
        fail("mention_candidates", "mention manifest omits a successful candidate")
    all_mentions: list[JsonObject] = []
    persisted_mentions: list[JsonObject] = []
    for candidate, eligible in zip(candidates, indexed, strict=True):
        if any(
            candidate[field] != eligible[field]
            for field in (
                "source_id",
                "source_ordinal",
                "candidate_id",
                "document_completion_ref",
                "candidate_inventory_ref",
            )
        ):
            fail("mention_candidates", "mention candidate differs from sealed index input")
        records = parse_jsonl(
            verify_ref(cast(JsonObject, candidate["cross_references_ref"]), reader),
            subject=cast(str, candidate["cross_references_ref"]["path"]),
        )
        derived: list[JsonObject] = []
        for record in records:
            if (
                record.get("resolution_status") != "unresolved"
                or record.get("unresolved_reason") != "deferred_cross_document"
            ):
                continue
            if record.get("mention_class") != "document":
                fail("mention_eligibility", "deferred mention is not a document mention")
            lookup_key = cast(str, record["lookup_key"])
            sources = catalog.get(lookup_key)
            if not sources:
                fail("mention_catalog", "deferred mention lacks sealed corpus ownership")
            derived.append(
                {
                    "mention_id": record["id"],
                    "candidate_local_sequence": record["sequence"],
                    "document_id": record["document_id"],
                    "mention_class": "document",
                    "lookup_key": lookup_key,
                    "intended_target_source_ids": [source["source_id"] for source in sources],
                }
            )
        derived.sort(key=lambda row: (row["candidate_local_sequence"], row["mention_id"]))
        if candidate["eligible_mentions"] != derived or candidate["eligible_mention_count"] != len(
            derived
        ):
            fail("mention_coverage", "mention manifest differs from stage-one bytes")
        persisted_mentions.extend(derived)
        all_mentions.extend(
            {**mention, "_source_candidate_id": candidate["candidate_id"]} for mention in derived
        )
    if manifest["eligible_mention_count"] != len(all_mentions) or manifest[
        "eligible_mentions_sha256"
    ] != canonical_sha256(persisted_mentions):
        fail("mention_coverage", "mention manifest aggregate differs")
    return all_mentions


def _validate_resolution(
    resolution: JsonObject,
    mention: JsonObject,
    scope: ScopeEvidence,
    unavailable: dict[str, JsonObject],
    candidate_by_source: dict[str, str],
    catalog: dict[str, tuple[JsonObject, ...]],
    targets_by_lookup: dict[str, tuple[JsonObject, ...]],
    index: JsonObject,
    corpus_catalog_ref: JsonObject,
) -> None:
    expected_source_candidate = mention["_source_candidate_id"]
    if any(
        resolution[field] != value
        for field, value in {
            "mention_id": mention["mention_id"],
            "source_candidate_id": expected_source_candidate,
            "candidate_local_sequence": mention["candidate_local_sequence"],
            "lookup_key": mention["lookup_key"],
            "target_type": "document",
            "intended_target_source_ids": mention["intended_target_source_ids"],
        }.items()
    ):
        fail("resolution_source", "resolution differs from its derived mention")
    expected_inventory = scope.candidate_inventory_refs[cast(str, expected_source_candidate)]
    if (
        resolution["source_inventory_before_ref"] != expected_inventory
        or resolution["source_inventory_after_ref"] != expected_inventory
    ):
        fail("stage_one_mutation", "resolution source inventory differs")
    matching = [
        {
            "target_id": entry["target_id"],
            "target_source_id": entry["source_id"],
            "target_type": entry["target_type"],
        }
        for entry in targets_by_lookup.get(cast(str, mention["lookup_key"]), ())
        if entry["target_type"] == "document"
        and entry["source_id"] in mention["intended_target_source_ids"]
    ]
    matching = list({item["target_id"]: item for item in matching}.values())
    if resolution["candidate_targets"] != matching:
        fail("resolution_target", "candidate targets differ from sealed index order")
    expected_status = (
        "unresolved" if not matching else "resolved" if len(matching) == 1 else "ambiguous"
    )
    if resolution["status"] != expected_status:
        fail("resolution_cardinality", "resolution status differs from candidate cardinality")
    if matching:
        if resolution["unresolved_reason"] is not None or resolution["reason_evidence"] is not None:
            fail("resolution_reason", "resolved result carries unresolved evidence")
    else:
        reason, evidence = _unresolved_evidence(
            mention,
            scope,
            unavailable,
            candidate_by_source,
            catalog,
            index,
            corpus_catalog_ref,
        )
        if resolution["unresolved_reason"] != reason or resolution["reason_evidence"] != evidence:
            fail("resolution_reason", "unresolved evidence does not follow precedence")


def _unresolved_evidence(
    mention: JsonObject,
    scope: ScopeEvidence,
    unavailable: dict[str, JsonObject],
    candidate_by_source: dict[str, str],
    catalog: dict[str, tuple[JsonObject, ...]],
    index: JsonObject,
    corpus_catalog_ref: JsonObject,
) -> tuple[str, JsonObject]:
    intended = cast(list[str], mention["intended_target_source_ids"])
    successful = [source_id for source_id in intended if source_id in scope.successful_source_ids]
    if successful:
        source_id = successful[0]
        return "target_unavailable", {
            "reason": "target_unavailable",
            "target_source_id": source_id,
            "target_candidate_id": candidate_by_source[source_id],
            "index_id": index["index_id"],
            "entries_sha256": index["entries_ref"]["sha256"],
        }
    failed = [source_id for source_id in intended if source_id in unavailable]
    if failed:
        source_id = failed[0]
        return "target_source_failed", {
            "reason": "target_source_failed",
            "target_source_id": source_id,
            "unavailable_source_sha256": unavailable_source_digest(unavailable[source_id]),
        }
    in_scope = set(scope.sources)
    if all(source_id not in in_scope for source_id in intended):
        source_id = intended[0]
        source = next(
            item
            for item in catalog[cast(str, mention["lookup_key"])]
            if item["source_id"] == source_id
        )
        return "target_not_in_scope", {
            "reason": "target_not_in_scope",
            "target_source": source,
            "production_manifest_ref": corpus_catalog_ref,
            "scope_id": index["identity_preimage"]["scope_id"],
        }
    fail("resolution_reason", "no supported unresolved disposition applies")


def _load_catalog(
    reference: JsonObject, reader: ArtifactReader
) -> dict[str, tuple[JsonObject, ...]]:
    payload = parse_json_object(verify_ref(reference, reader), subject="corpus_catalog")
    documents = payload.get("documents")
    if not isinstance(documents, list):
        fail("mention_catalog", "corpus catalog lacks document records")
    result: dict[str, list[JsonObject]] = {}
    for document in documents:
        if not isinstance(document, dict) or not isinstance(document.get("source"), dict):
            fail("mention_catalog", "corpus catalog document is invalid")
        for key in document.get("lookup_keys", []):
            if not isinstance(key, str):
                fail("mention_catalog", "corpus lookup key is invalid")
            result.setdefault(key, []).append(cast(JsonObject, document["source"]))
    return {key: tuple(values) for key, values in result.items()}


def _counts(resolutions: list[JsonObject]) -> JsonObject:
    counts = Counter(row["status"] for row in resolutions)
    return {
        "total": len(resolutions),
        "resolved": counts["resolved"],
        "ambiguous": counts["ambiguous"],
        "unresolved": counts["unresolved"],
    }


def _require_ref_value(reference: JsonObject, expected: object, reader: ArtifactReader) -> None:
    try:
        actual = json.loads(verify_ref(reference, reader))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail("artifact_json", f"referenced JSON is invalid: {error}")
    if actual != expected:
        fail("artifact_join", "referenced artifact differs from persisted record")
