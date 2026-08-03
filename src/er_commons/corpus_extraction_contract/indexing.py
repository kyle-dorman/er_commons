"""Eligibility, ordering, and sealing of the corpus target index."""

from __future__ import annotations

from collections import defaultdict

from er_commons.corpus_extraction_contract.checks import canonical_sha256, fail
from er_commons.corpus_extraction_contract.model import IndexEvidence, JsonObject, ScopeEvidence


def validate_target_index(
    index: JsonObject,
    accounting: JsonObject,
    scope: ScopeEvidence,
) -> IndexEvidence:
    """Validate index provenance and return lookup-key target membership."""
    if set(index["eligible_candidate_ids"]) != set(scope.successful_candidate_ids):
        fail("index_eligibility", "index candidates differ from successful accounting")
    if set(index["unavailable_source_ids"]) != set(scope.unavailable_source_ids):
        fail("unavailable_catalog", "unavailable sources differ from accounting")

    source_ordinals = {
        source["source_id"]: ordinal
        for ordinal, source in enumerate(accounting["ordered_sources"], start=1)
    }
    ordered_keys: list[tuple[str, str, int, str, str]] = []
    targets_by_lookup: dict[str, list[str]] = defaultdict(list)
    for entry in index["entries"]:
        _validate_entry_source(entry, source_ordinals, scope)
        key = (
            entry["lookup_key"],
            entry["target_type"],
            entry["source_ordinal"],
            entry["target_id"],
            entry["alias_id"],
        )
        ordered_keys.append(key)
        targets_by_lookup[entry["lookup_key"]].append(entry["target_id"])

    if ordered_keys != sorted(ordered_keys) or len(ordered_keys) != len(set(ordered_keys)):
        fail("index_order", "target index is not unique and deterministically ordered")
    if index["entries_sha256"] != canonical_sha256(index["entries"]):
        fail("index_digest", "target index digest differs")
    return IndexEvidence(
        target_ids_by_lookup_key={
            key: tuple(dict.fromkeys(target_ids)) for key, target_ids in targets_by_lookup.items()
        }
    )


def _validate_entry_source(
    entry: JsonObject,
    source_ordinals: dict[str, int],
    scope: ScopeEvidence,
) -> None:
    source_id = entry["source_id"]
    expected_ordinal = source_ordinals.get(source_id)
    if expected_ordinal is None or source_id in scope.unavailable_source_ids:
        fail("index_source", "index entry source is not eligible", subject=source_id)
    if entry["source_ordinal"] != expected_ordinal:
        fail("index_source", "index source ordinal differs from accounting", subject=source_id)
