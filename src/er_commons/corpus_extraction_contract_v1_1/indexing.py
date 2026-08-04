"""Candidate eligibility, corpus-index derivation, ordering, and identity gates."""

from __future__ import annotations

from typing import cast

from er_commons.corpus_extraction_contract_v1_1.accounting import (
    ScopeEvidence,
    validate_unavailable_sources,
)
from er_commons.corpus_extraction_contract_v1_1.artifacts import parse_jsonl
from er_commons.corpus_extraction_contract_v1_1.checks import (
    canonical_sha256,
    fail,
    verify_ref,
)
from er_commons.corpus_extraction_contract_v1_1.identity import validate_index_id
from er_commons.corpus_extraction_contract_v1_1.model import ArtifactReader, JsonObject


def validate_target_index(
    bundle: JsonObject,
    scope: ScopeEvidence,
    reader: ArtifactReader,
) -> dict[str, tuple[JsonObject, ...]]:
    """Validate exact index inputs and return authorized targets by lookup key."""
    index = cast(JsonObject, bundle["target_index"])
    accounting = cast(JsonObject, bundle["accounting"])
    _require_ref_value(cast(JsonObject, index["accounting_ref"]), accounting, reader)

    eligible = cast(list[JsonObject], index["eligible_candidates"])
    _validate_eligible_candidates(eligible, accounting, scope)
    for candidate in eligible:
        for field in (
            "document_completion_ref",
            "candidate_inventory_ref",
            "target_aliases_ref",
        ):
            verify_ref(cast(JsonObject, candidate[field]), reader)
        for reference in cast(list[JsonObject], candidate["target_records_ref"]):
            verify_ref(reference, reader)

    unavailable = cast(list[JsonObject], index["unavailable_sources"])
    validate_unavailable_sources(unavailable, scope, reader)
    unavailable_bytes = verify_ref(cast(JsonObject, index["unavailable_sources_ref"]), reader)
    if parse_jsonl(unavailable_bytes, subject="unavailable_sources") != unavailable:
        fail("unavailable_catalog", "serialized unavailable catalog differs")

    entries = cast(list[JsonObject], index["entries"])
    entry_bytes = verify_ref(cast(JsonObject, index["entries_ref"]), reader)
    if parse_jsonl(entry_bytes, subject="target_index_entries") != entries:
        fail("index_entries", "serialized target index differs")
    if index["entry_count"] != len(entries):
        fail("index_count", "target index entry count differs")
    _validate_entry_order(entries)
    _validate_entry_sources(entries, scope)
    if entries != _derive_entries(eligible, reader):
        fail("index_derivation", "target index differs from sealed candidate streams")

    inventory = cast(JsonObject, index["artifact_inventory"])
    verify_ref(inventory, reader)
    preimage = cast(JsonObject, index["identity_preimage"])
    _require_ref_value(cast(JsonObject, index["identity_preimage_ref"]), preimage, reader)
    expected_preimage = {
        "schema_version": "er_commons.corpus_target_index_identity.v1_1",
        "production_extraction_id": bundle["production_extraction_id"],
        "scope_id": accounting["scope_id"],
        "accounting_sha256": index["accounting_ref"]["sha256"],
        "eligible_candidates_sha256": canonical_sha256(eligible),
        "unavailable_sources_sha256": index["unavailable_sources_ref"]["sha256"],
        "entries_sha256": index["entries_ref"]["sha256"],
        "entry_count": len(entries),
        "ordering_policy_version": "corpus_target_order_v1",
        "target_policy_sha256": preimage["target_policy_sha256"],
        "managed_inventory_sha256": inventory["sha256"],
    }
    if preimage != expected_preimage:
        fail("index_identity", "index preimage does not bind exact inputs")
    validate_index_id(cast(str, index["index_id"]), preimage)
    return _targets_by_lookup(entries)


def _validate_eligible_candidates(
    eligible: list[JsonObject], accounting: JsonObject, scope: ScopeEvidence
) -> None:
    rows = cast(list[JsonObject], accounting["rows"])
    expected = [row for row in rows if row["candidate_id"] in scope.candidate_sources]
    if len(eligible) != len(expected):
        fail("index_eligibility", "eligible candidates differ from successful accounting")
    for candidate, row in zip(eligible, expected, strict=True):
        observed = (
            candidate["source_id"],
            candidate["source_ordinal"],
            candidate["candidate_id"],
            candidate["document_completion_ref"],
            candidate["candidate_inventory_ref"],
        )
        required = (
            row["source_id"],
            row["source_ordinal"],
            row["candidate_id"],
            row["document_completion_ref"],
            row["candidate_inventory_ref"],
        )
        if observed != required:
            fail("index_eligibility", "eligible candidate evidence differs from accounting")


def _derive_entries(eligible: list[JsonObject], reader: ArtifactReader) -> list[JsonObject]:
    derived: list[JsonObject] = []
    seen: set[tuple[str, str]] = set()
    for candidate in eligible:
        target_ids: set[str] = set()
        for reference in cast(list[JsonObject], candidate["target_records_ref"]):
            for record in parse_jsonl(verify_ref(reference, reader), subject=reference["path"]):
                record_id = record.get("id")
                if isinstance(record_id, str):
                    target_ids.add(record_id)
        aliases = parse_jsonl(
            verify_ref(cast(JsonObject, candidate["target_aliases_ref"]), reader),
            subject=cast(str, candidate["target_aliases_ref"]["path"]),
        )
        for alias in aliases:
            for target in cast(list[JsonObject], alias.get("targets", [])):
                target_id = cast(str, target.get("target_id"))
                pair = (cast(str, alias.get("id")), target_id)
                if target_id not in target_ids:
                    fail("index_target", "alias target is absent from sealed target streams")
                if pair in seen:
                    continue
                seen.add(pair)
                derived.append(
                    {
                        "alias_id": pair[0],
                        "lookup_key": alias["normalized_alias"],
                        "target_type": target["target_type"],
                        "source_id": candidate["source_id"],
                        "source_ordinal": candidate["source_ordinal"],
                        "target_id": pair[1],
                    }
                )
    return sorted(derived, key=_entry_key)


def _validate_entry_order(entries: list[JsonObject]) -> None:
    keys = [_entry_key(entry) for entry in entries]
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        fail("index_order", "target index is not unique and deterministically ordered")


def _entry_key(entry: JsonObject) -> tuple[str, str, int, str, str]:
    return (
        cast(str, entry["lookup_key"]),
        cast(str, entry["target_type"]),
        cast(int, entry["source_ordinal"]),
        cast(str, entry["target_id"]),
        cast(str, entry["alias_id"]),
    )


def _validate_entry_sources(entries: list[JsonObject], scope: ScopeEvidence) -> None:
    successful = scope.successful_source_ids
    for entry in entries:
        source_id = cast(str, entry["source_id"])
        if (
            source_id not in successful
            or entry["source_ordinal"] != scope.source_ordinals[source_id]
        ):
            fail("index_source", "index entry source is not eligible", subject=source_id)


def _targets_by_lookup(entries: list[JsonObject]) -> dict[str, tuple[JsonObject, ...]]:
    grouped: dict[str, list[JsonObject]] = {}
    for entry in entries:
        grouped.setdefault(cast(str, entry["lookup_key"]), []).append(entry)
    return {key: tuple(values) for key, values in grouped.items()}


def _require_ref_value(
    reference: JsonObject,
    expected: object,
    reader: ArtifactReader,
) -> None:
    import json

    try:
        actual = json.loads(verify_ref(reference, reader))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail("artifact_json", f"referenced JSON is invalid: {error}")
    if actual != expected:
        fail("artifact_join", "referenced artifact differs from persisted record")
