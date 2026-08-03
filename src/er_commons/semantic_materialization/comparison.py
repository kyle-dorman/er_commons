"""Exact cross-version preservation checks after narrow semantic normalization."""

from __future__ import annotations

import copy
from typing import Any

from er_commons.semantic_structure.constants import ALLOWED_DIFFERENCE_CATEGORIES

JsonObject = dict[str, Any]

DEFAULT_ALLOWED_FIELDS: dict[str, frozenset[str]] = {
    "blocks": frozenset({"section_id", "semantic_placement", "is_toc_row", "stable_item_key"}),
    "tables": frozenset(
        {"section_id", "content_layer", "semantic_placement", "is_toc_row", "stable_item_key"}
    ),
    "figures": frozenset(
        {"section_id", "content_layer", "semantic_placement", "is_toc_row", "stable_item_key"}
    ),
    "pages": frozenset({"printed_page_label", "page_label_observation_id"}),
}


def compare_baseline_collections(
    baseline: dict[str, list[JsonObject]],
    candidate: dict[str, list[JsonObject]],
    *,
    baseline_candidate_id: str,
    new_candidate_id: str,
    allowed_fields: dict[str, frozenset[str]] | None = None,
) -> JsonObject:
    """Report undeclared record differences after ID and schema normalization."""
    allowed_fields = DEFAULT_ALLOWED_FIELDS if allowed_fields is None else allowed_fields
    differences: list[JsonObject] = []
    families = sorted(set(baseline) | set(candidate))
    for family in families:
        if family in {"sections", "page_label_observations", "target_aliases"}:
            continue
        old_records = baseline.get(family, [])
        new_records = candidate.get(family, [])
        if len(old_records) != len(new_records):
            differences.append(
                {
                    "family": family,
                    "reason": "record_count",
                    "baseline": len(old_records),
                    "candidate": len(new_records),
                }
            )
            continue
        ignored = allowed_fields.get(family, frozenset())
        for index, (old, new) in enumerate(zip(old_records, new_records, strict=True)):
            old_value = _normalize(old, baseline_candidate_id, ignored)
            new_value = _normalize(new, new_candidate_id, ignored)
            if old_value != new_value:
                differences.append({"family": family, "index": index, "reason": "record_value"})
    return {
        "baseline_candidate_id": baseline_candidate_id,
        "new_candidate_id": new_candidate_id,
        "allowed_difference_categories": list(ALLOWED_DIFFERENCE_CATEGORIES),
        "undeclared_difference_count": len(differences),
        "status": (
            "equivalent_with_declared_semantic_extensions"
            if not differences
            else "undeclared_differences"
        ),
        "differences": differences,
    }


def _normalize(value: Any, candidate_id: str, ignored_fields: frozenset[str]) -> Any:
    value = copy.deepcopy(value)
    if not isinstance(value, dict):
        return _replace_candidate_id(value, candidate_id)
    for field in ignored_fields | {"schema_version"}:
        value.pop(field, None)
    return _replace_candidate_id(value, candidate_id)


def _replace_candidate_id(value: Any, candidate_id: str) -> Any:
    if isinstance(value, dict):
        return {key: _replace_candidate_id(child, candidate_id) for key, child in value.items()}
    if isinstance(value, list):
        return [_replace_candidate_id(child, candidate_id) for child in value]
    if isinstance(value, str):
        return value.replace(candidate_id, "{extraction_id}")
    return value
