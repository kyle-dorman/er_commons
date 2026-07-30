"""Hierarchy-aware semantic comparison for two Docling documents."""

from __future__ import annotations

from collections import Counter

from er_commons.document_extraction.comparison import structural_diff
from er_commons.document_extraction.hierarchy.document import (
    DocumentIndex,
    JsonObject,
    normalize_references,
    normalized_text_item,
    stable_text_key,
)


def _empty_report(reason: str, *, alignment: JsonObject | None = None) -> JsonObject:
    """Return the stable inconclusive report shape with a diagnostic reason."""
    return {
        "status": "inconclusive",
        "reason": reason,
        "item_alignment": alignment or {},
        "hierarchy_changes": [],
        "reference_rewrites": [],
        "unexpected_changes": [],
        "review_items": [],
    }


def _text_change(
    stable_key: str,
    baseline: JsonObject,
    candidate: JsonObject,
    *,
    kind: str,
    permitted: bool,
) -> JsonObject:
    """Describe one text-item change with enough context to inspect it."""
    provenance = baseline["prov"][0]
    return {
        "stable_item_key": stable_key,
        "baseline_ref": baseline.get("self_ref"),
        "candidate_ref": candidate.get("self_ref"),
        "physical_page": provenance.get("page_no"),
        "bbox": provenance.get("bbox"),
        "text": baseline.get("text"),
        "orig": baseline.get("orig"),
        "baseline_label": baseline.get("label"),
        "candidate_label": candidate.get("label"),
        "baseline_level": baseline.get("level"),
        "candidate_level": candidate.get("level"),
        "change_kind": kind,
        "permitted": permitted,
    }


def _compare_text_item(
    stable_key: str,
    baseline: JsonObject,
    candidate: JsonObject,
    baseline_index: DocumentIndex,
    candidate_index: DocumentIndex,
) -> tuple[list[JsonObject], list[JsonObject], list[JsonObject], bool]:
    """Compare one aligned text item and return changes by policy category."""
    hierarchy_changes: list[JsonObject] = []
    reference_rewrites: list[JsonObject] = []
    unexpected: list[JsonObject] = []

    baseline_label = baseline.get("label")
    candidate_label = candidate.get("label")
    promoted = baseline_label == "list_item" and candidate_label == "section_header"
    level_changed = (
        baseline_label == "section_header"
        and candidate_label == "section_header"
        and baseline.get("level") != candidate.get("level")
    )
    if promoted:
        hierarchy_changes.append(
            _text_change(
                stable_key,
                baseline,
                candidate,
                kind="list_item_promotion",
                permitted=True,
            )
        )
    elif level_changed:
        hierarchy_changes.append(
            _text_change(
                stable_key,
                baseline,
                candidate,
                kind="heading_level",
                permitted=True,
            )
        )
    elif baseline_label != candidate_label:
        unexpected.append(
            _text_change(
                stable_key,
                baseline,
                candidate,
                kind="undeclared_label_change",
                permitted=False,
            )
        )

    _compare_semantic_relationship(
        stable_key,
        baseline,
        candidate,
        baseline_index,
        candidate_index,
        field="parent",
        unexpected=unexpected,
    )
    _compare_semantic_relationship(
        stable_key,
        baseline,
        candidate,
        baseline_index,
        candidate_index,
        field="children",
        unexpected=unexpected,
    )
    for field in ("self_ref", "parent", "children"):
        if baseline.get(field) != candidate.get(field):
            reference_rewrites.append(
                {
                    **_text_change(
                        stable_key,
                        baseline,
                        candidate,
                        kind=f"raw_{field}_rewrite",
                        permitted=True,
                    ),
                    "baseline_value": baseline.get(field),
                    "candidate_value": candidate.get(field),
                }
            )

    normalized_baseline = normalized_text_item(
        baseline,
        baseline_index.references,
        remove_level=baseline_label == "section_header",
        project_promotion_source=promoted,
    )
    normalized_candidate = normalized_text_item(
        candidate,
        candidate_index.references,
        remove_level=candidate_label == "section_header",
        project_promotion_source=False,
    )
    diff = structural_diff(normalized_baseline, normalized_candidate)
    if diff["total_difference_count"]:
        unexpected.append(
            {
                **_text_change(
                    stable_key,
                    baseline,
                    candidate,
                    kind="unexpected_item_field_change",
                    permitted=False,
                ),
                "diff": diff,
            }
        )
    return hierarchy_changes, reference_rewrites, unexpected, promoted


def _compare_semantic_relationship(
    stable_key: str,
    baseline: JsonObject,
    candidate: JsonObject,
    baseline_index: DocumentIndex,
    candidate_index: DocumentIndex,
    *,
    field: str,
    unexpected: list[JsonObject],
) -> None:
    """Append a failure when parent or child meaning changed after ref normalization."""
    baseline_value = normalize_references(
        baseline.get(field),
        baseline_index.references,
    )
    candidate_value = normalize_references(
        candidate.get(field),
        candidate_index.references,
    )
    if baseline_value == candidate_value:
        return
    unexpected.append(
        {
            **_text_change(
                stable_key,
                baseline,
                candidate,
                kind=f"semantic_{field}_change",
                permitted=False,
            ),
            f"baseline_{field}": baseline_value,
            f"candidate_{field}": candidate_value,
        }
    )


def _review_items(
    index: DocumentIndex,
    review_pages: set[int],
) -> list[JsonObject]:
    """Build the pre-populated human-review rows for declared physical pages."""
    rows: list[JsonObject] = []
    for stable_key in index.text_order:
        item = index.text_items[stable_key]
        provenance = item["prov"][0]
        if provenance.get("page_no") not in review_pages:
            continue
        if item.get("label") not in {"section_header", "list_item"}:
            continue
        rows.append(
            {
                "stable_item_key": stable_key,
                "physical_page": provenance.get("page_no"),
                "bbox": provenance.get("bbox"),
                "text": item.get("text"),
                "orig": item.get("orig"),
                "label": item.get("label"),
                "level": item.get("level"),
                "content_layer": item.get("content_layer"),
                "visible_heading": None,
                "expected_level": None,
                "relative_level_correct": None,
                "bookmark_covered": None,
                "bookmark_expected_level": None,
                "promotion_correct": None,
                "failure_type": None,
                "severity": None,
                "review_note": "",
            }
        )
    return rows


def compare_docling_hierarchy(
    baseline: JsonObject,
    candidate: JsonObject,
    *,
    review_pages: set[int] | None = None,
) -> JsonObject:
    """Compare complete Docling documents while permitting only hierarchy deltas."""
    try:
        baseline_index = DocumentIndex.build(baseline)
        candidate_index = DocumentIndex.build(candidate)
    except (KeyError, TypeError, ValueError) as error:
        return _empty_report(str(error))

    baseline_keys = set(baseline_index.text_items)
    candidate_keys = set(candidate_index.text_items)
    if baseline_keys != candidate_keys:
        return _empty_report(
            "baseline and candidate stable text key sets differ",
            alignment={
                "baseline_count": len(baseline_keys),
                "candidate_count": len(candidate_keys),
                "stable_key_sets_equal": False,
                "missing_keys": sorted(baseline_keys - candidate_keys),
                "unexpected_keys": sorted(candidate_keys - baseline_keys),
            },
        )

    hierarchy_changes: list[JsonObject] = []
    reference_rewrites: list[JsonObject] = []
    unexpected: list[JsonObject] = []
    promotions = 0
    for stable_key in baseline_index.text_order:
        changes, rewrites, failures, promoted = _compare_text_item(
            stable_key,
            baseline_index.text_items[stable_key],
            candidate_index.text_items[stable_key],
            baseline_index,
            candidate_index,
        )
        hierarchy_changes.extend(changes)
        reference_rewrites.extend(rewrites)
        unexpected.extend(failures)
        promotions += int(promoted)

    baseline_reading_order = baseline_index.reading_order(baseline)
    candidate_reading_order = candidate_index.reading_order(candidate)
    if baseline_reading_order != candidate_reading_order:
        unexpected.append(
            {
                "change_kind": "semantic_reading_order_change",
                "permitted": False,
                "diff": structural_diff(baseline_reading_order, candidate_reading_order),
            }
        )

    baseline_non_text = {
        key: normalize_references(value, baseline_index.references)
        for key, value in baseline.items()
        if key != "texts"
    }
    candidate_non_text = {
        key: normalize_references(value, candidate_index.references)
        for key, value in candidate.items()
        if key != "texts"
    }
    non_text_diff = structural_diff(baseline_non_text, candidate_non_text)
    if non_text_diff["total_difference_count"]:
        unexpected.append(
            {
                "change_kind": "unexpected_non_text_document_change",
                "permitted": False,
                "diff": non_text_diff,
            }
        )

    collection_reordered = baseline_index.text_order != candidate_index.text_order
    if collection_reordered and promotions == 0:
        unexpected.append(
            {
                "change_kind": "unexpected_text_collection_reorder",
                "permitted": False,
                "diff": structural_diff(
                    baseline_index.text_order,
                    candidate_index.text_order,
                ),
            }
        )

    return {
        "status": "pass" if not unexpected else "reject",
        "reason": None,
        "item_alignment": {
            "baseline_count": len(baseline_index.text_items),
            "candidate_count": len(candidate_index.text_items),
            "stable_key_sets_equal": True,
            "text_collection_order_equal": not collection_reordered,
            "semantic_reading_order_equal": baseline_reading_order == candidate_reading_order,
        },
        "hierarchy_changes": hierarchy_changes,
        "reference_rewrites": reference_rewrites,
        "unexpected_changes": unexpected,
        "review_items": _review_items(candidate_index, review_pages or set()),
    }


def stable_key_collision_count(document: JsonObject) -> int:
    """Count collisions under the frozen stable-text-key policy."""
    texts = document.get("texts", [])
    keys = [stable_text_key(item) for item in texts]
    return sum(count - 1 for count in Counter(keys).values() if count > 1)
