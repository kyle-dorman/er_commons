"""Cross-producer lineage bridge policies."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from er_commons.semantic_structure.bundle import JsonObject, SemanticBundleView
from er_commons.semantic_structure.constants import PERMITTED_BRIDGE_DISPOSITIONS
from er_commons.semantic_structure.errors import SemanticContractError


@dataclass(frozen=True)
class BridgeSourceEvidence:
    """Verified producer pointers and disposition for one stable item."""

    hierarchy_raw_pointer: str
    baseline_raw_pointer: str
    disposition: str | None


BridgeEvidence = Mapping[str, BridgeSourceEvidence]


def validate_cross_producer_bridge(
    view: SemanticBundleView,
    evidence_by_key: BridgeEvidence,
) -> None:
    """Require each bridge row to reproduce verified producer evidence exactly."""
    _validate_unique_stable_keys(view.bridge_entries)
    _validate_unique_raw_pointers(view.bridge_entries)
    _validate_exact_source_evidence(view.bridge_entries, evidence_by_key)
    mapped_targets: list[str] = []
    for entry in view.bridge_entries:
        _validate_producer_ids(view, entry)
        if entry["status"] == "mapped":
            mapped_targets.append(_validate_mapped_entry(view, entry))
        else:
            _validate_permitted_unmapped_entry(entry)
    _validate_unique_mapped_targets(mapped_targets)
    _validate_retained_content_coverage(view)


def _validate_unique_stable_keys(entries: list[JsonObject]) -> None:
    """Reject two bridge rows for the same hierarchy item."""
    stable_keys = [entry["stable_item_key"] for entry in entries]
    if len(stable_keys) != len(set(stable_keys)):
        raise SemanticContractError("bridge stable-item keys collide")


def _validate_exact_source_evidence(
    entries: list[JsonObject],
    evidence_by_key: BridgeEvidence,
) -> None:
    """Reject missing, invented, or changed producer correspondence rows."""
    entry_keys = {entry["stable_item_key"] for entry in entries}
    evidence_keys = set(evidence_by_key)
    if entry_keys != evidence_keys:
        missing = sorted(evidence_keys - entry_keys)
        extra = sorted(entry_keys - evidence_keys)
        raise SemanticContractError(
            f"bridge source-evidence coverage differs: missing={missing}, extra={extra}"
        )

    for entry in entries:
        stable_key = entry["stable_item_key"]
        expected = evidence_by_key[stable_key]
        actual = (
            entry["hierarchy_raw_pointer"],
            entry["baseline_raw_pointer"],
            entry["disposition"],
        )
        required = (
            expected.hierarchy_raw_pointer,
            expected.baseline_raw_pointer,
            expected.disposition,
        )
        if actual != required:
            raise SemanticContractError(f"bridge producer correspondence differs: {stable_key}")


def _validate_producer_ids(view: SemanticBundleView, entry: JsonObject) -> None:
    """Keep every bridge row bound to the two verified producer candidates."""
    if entry["hierarchy_producer_run_id"] != view.bundle["hierarchy_producer_run_id"]:
        raise SemanticContractError(
            f"bridge hierarchy producer differs for {entry['stable_item_key']}"
        )
    if entry["baseline_producer_run_id"] != view.bundle["baseline_producer_run_id"]:
        raise SemanticContractError(
            f"bridge baseline producer differs for {entry['stable_item_key']}"
        )


def _validate_mapped_entry(view: SemanticBundleView, entry: JsonObject) -> str:
    """Return the sole canonical target of a valid mapped bridge row."""
    canonical_ids = entry["canonical_record_ids"]
    if entry["disposition"] is not None or len(canonical_ids) != 1:
        raise SemanticContractError(
            f"mapped bridge entry is not one-to-one: {entry['stable_item_key']}"
        )
    canonical_id = cast(str, canonical_ids[0])
    canonical_record = view.content_by_id.get(canonical_id)
    if canonical_record is None or canonical_record["record_type"] != "block":
        raise SemanticContractError(
            f"mapped bridge target is not a canonical block: {entry['stable_item_key']}"
        )
    if canonical_record["stable_item_key"] != entry["stable_item_key"]:
        raise SemanticContractError(
            f"mapped bridge stable key differs from canonical block: {entry['stable_item_key']}"
        )
    return canonical_id


def _validate_permitted_unmapped_entry(entry: JsonObject) -> None:
    """Allow only the two evidence-backed replacement dispositions."""
    if entry["disposition"] not in PERMITTED_BRIDGE_DISPOSITIONS or entry["canonical_record_ids"]:
        raise SemanticContractError(
            f"bridge unmapped disposition is not permitted: {entry['stable_item_key']}"
        )


def _validate_unique_mapped_targets(mapped_targets: list[str]) -> None:
    """Reject two stable items mapping directly to the same canonical record."""
    if len(mapped_targets) != len(set(mapped_targets)):
        raise SemanticContractError("bridge canonical targets collide")


def _validate_retained_content_coverage(view: SemanticBundleView) -> None:
    """Require bridge rows for every retained, non-TOC hierarchy item."""
    required_keys = {
        item["stable_item_key"]
        for item in view.content
        if item["stable_item_key"] is not None and not item["is_toc_row"]
    }
    entry_by_key = {entry["stable_item_key"]: entry for entry in view.bridge_entries}
    bridged_keys = set(entry_by_key)
    missing_keys = sorted(required_keys - bridged_keys)
    if missing_keys:
        raise SemanticContractError(
            f"bridge does not cover retained hierarchy keys: {missing_keys}"
        )
    wrongly_unmapped = sorted(
        stable_key for stable_key in required_keys if entry_by_key[stable_key]["status"] != "mapped"
    )
    if wrongly_unmapped:
        raise SemanticContractError(
            f"retained canonical blocks cannot use unmapped bridge dispositions: {wrongly_unmapped}"
        )

    for item in view.content:
        stable_key = item["stable_item_key"]
        if stable_key is None or item["is_toc_row"]:
            continue
        if entry_by_key[stable_key]["canonical_record_ids"] != [item["id"]]:
            raise SemanticContractError(
                f"bridge target differs from retained canonical block: {stable_key}"
            )


def _validate_unique_raw_pointers(entries: list[JsonObject]) -> None:
    """Require each producer item pointer to participate in at most one bridge row."""
    for field in ("hierarchy_raw_pointer", "baseline_raw_pointer"):
        pointers = [entry[field] for entry in entries]
        if len(pointers) != len(set(pointers)):
            raise SemanticContractError(f"bridge {field} values collide")
