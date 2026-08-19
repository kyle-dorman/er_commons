"""Align baseline and hierarchy producer text identities."""

from __future__ import annotations

from typing import Any

from er_commons.document_parsing.heading_evidence_parsing.document import DocumentIndex
from er_commons.document_records.document_structure.errors import (
    DocumentStructureInvariantError,
)

JsonObject = dict[str, Any]


def stable_key_by_pointer(document: JsonObject) -> dict[str, str]:
    """Index saved Docling text-item pointers by their stable item keys."""
    index = DocumentIndex.build(document)
    return {item["self_ref"]: key for key, item in index.text_items.items()}


def aligned_stable_key_maps(
    baseline_document: JsonObject,
    hierarchy_document: JsonObject,
    *,
    bbox_tolerance_points: float = 0.5,
) -> tuple[dict[str, str], dict[str, str]]:
    """Align producer text identities while tolerating bounded model bbox drift."""
    baseline_index = DocumentIndex.build(baseline_document)
    hierarchy_index = DocumentIndex.build(hierarchy_document)
    baseline_raw = {item["self_ref"]: key for key, item in baseline_index.text_items.items()}
    hierarchy_raw = {item["self_ref"]: key for key, item in hierarchy_index.text_items.items()}
    shared = set(baseline_raw.values()) & set(hierarchy_raw.values())
    aligned = {pointer: key for pointer, key in baseline_raw.items() if key in shared}
    baseline_groups = _group_items_by_text_signature(_unmatched_items(baseline_index, shared))
    hierarchy_groups = _group_items_by_text_signature(_unmatched_items(hierarchy_index, shared))
    if set(baseline_groups) != set(hierarchy_groups):
        _raise_alignment_error(len(baseline_raw), len(hierarchy_raw))
    for signature in sorted(baseline_groups, key=repr):
        _align_signature_group(
            baseline_groups[signature],
            hierarchy_groups[signature],
            baseline_raw,
            aligned,
            bbox_tolerance_points,
            len(hierarchy_raw),
        )
    if set(aligned.values()) != set(hierarchy_raw.values()):
        _raise_alignment_error(len(baseline_raw), len(hierarchy_raw))
    return aligned, hierarchy_raw


def _align_signature_group(
    baseline_group: list[tuple[str, JsonObject]],
    hierarchy_group: list[tuple[str, JsonObject]],
    baseline_raw: dict[str, str],
    aligned: dict[str, str],
    tolerance: float,
    hierarchy_count: int,
) -> None:
    """Add one uniquely matched text-signature group to the baseline index."""
    if len(baseline_group) != len(hierarchy_group):
        _raise_alignment_error(len(baseline_raw), hierarchy_count)
    candidates = {
        baseline_key: [
            hierarchy_key
            for hierarchy_key, hierarchy_item in hierarchy_group
            if _bbox_delta(baseline_item, hierarchy_item) <= tolerance
        ]
        for baseline_key, baseline_item in baseline_group
    }
    reverse = {
        hierarchy_key: [
            baseline_key
            for baseline_key, baseline_item in baseline_group
            if _bbox_delta(baseline_item, hierarchy_item) <= tolerance
        ]
        for hierarchy_key, hierarchy_item in hierarchy_group
    }
    if any(len(values) != 1 for values in candidates.values()) or any(
        len(values) != 1 for values in reverse.values()
    ):
        _raise_alignment_error(len(baseline_raw), hierarchy_count)
    hierarchy_key_by_baseline = {key: values[0] for key, values in candidates.items()}
    for pointer, baseline_key in baseline_raw.items():
        if baseline_key in hierarchy_key_by_baseline:
            aligned[pointer] = hierarchy_key_by_baseline[baseline_key]


def _unmatched_items(index: DocumentIndex, shared: set[str]) -> list[tuple[str, JsonObject]]:
    return [(key, item) for key, item in index.text_items.items() if key not in shared]


def _group_items_by_text_signature(
    items: list[tuple[str, JsonObject]],
) -> dict[tuple[Any, ...], list[tuple[str, JsonObject]]]:
    groups: dict[tuple[Any, ...], list[tuple[str, JsonObject]]] = {}
    for key, item in items:
        provenance = item["prov"][0]
        signature = (
            item.get("text"),
            item.get("orig"),
            provenance.get("page_no"),
            tuple(provenance.get("charspan", [])),
        )
        groups.setdefault(signature, []).append((key, item))
    return groups


def _bbox_delta(left_item: JsonObject, right_item: JsonObject) -> float:
    left = left_item["prov"][0]["bbox"]
    right = right_item["prov"][0]["bbox"]
    if left.get("coord_origin") != right.get("coord_origin"):
        return float("inf")
    try:
        return max(abs(float(left[name]) - float(right[name])) for name in ("l", "t", "r", "b"))
    except (KeyError, TypeError, ValueError):
        return float("inf")


def _raise_alignment_error(baseline_count: int, hierarchy_count: int) -> None:
    raise DocumentStructureInvariantError(
        stage="producer evidence",
        invariant="baseline and hierarchy producer text items align uniquely",
        expected=baseline_count,
        observed=hierarchy_count,
        subject="producer document pair",
    )
