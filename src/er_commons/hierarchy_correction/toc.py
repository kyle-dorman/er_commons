"""Visible-TOC row ownership and body-reconciliation policies."""

from __future__ import annotations

from er_commons.hierarchy_correction.bundle import CorrectionBundleView, JsonRecord
from er_commons.hierarchy_correction.checks import require, require_sorted, require_unique


def toc_rows_are_ordered_and_owned(view: CorrectionBundleView) -> None:
    """Require unique ordered TOC rows backed only by TOC-region items."""
    toc_ids = [item["toc_entry_id"] for item in view.toc_entries]
    require_unique(toc_ids, "duplicate TOC entry ID")
    require_sorted(
        (item["reading_order_index"] for item in view.toc_entries),
        "TOC entry order differs",
    )

    known_features = set(view.features_by_key)
    for entry in view.toc_entries:
        source_keys = set(entry["source_item_keys"])
        require(source_keys <= known_features, f"unknown TOC source key: {entry['toc_entry_id']}")
        require(
            all(view.features_by_key[key]["toc_region"] for key in source_keys),
            f"TOC source item is outside TOC region: {entry['toc_entry_id']}",
        )

    represented_items = {key for entry in view.toc_entries for key in entry["source_item_keys"]}
    represented_items.update(_unparseable_toc_item_keys(view))
    expected_items = {
        feature["stable_item_key"]
        for feature in view.features
        if feature["toc_region"] and feature["raw_role"] != "section_header"
    }
    require(expected_items <= represented_items, "TOC region item lacks row or diagnostic")


def toc_reconciliations_are_complete(view: CorrectionBundleView) -> None:
    """Require one ordered, cardinality-correct reconciliation per TOC row."""
    reconciliation_ids = [item["toc_entry_id"] for item in view.reconciliations]
    require_unique(reconciliation_ids, "duplicate reconciliation")
    require_sorted(
        (item["reading_order_index"] for item in view.reconciliations),
        "reconciliation order differs",
    )
    require(
        set(reconciliation_ids) == set(view.toc_entries_by_id),
        "TOC reconciliation coverage differs",
    )

    for reconciliation in view.reconciliations:
        toc_id = reconciliation["toc_entry_id"]
        candidates = reconciliation["candidate_keys"]
        require(toc_id in view.toc_entries_by_id, f"unknown reconciliation TOC ID: {toc_id}")
        require(
            set(candidates) <= set(view.features_by_key),
            f"unknown reconciliation candidate: {toc_id}",
        )
        require(
            all(_is_body_target(view, key) for key in candidates),
            f"reconciliation candidate is not body content: {toc_id}",
        )
        _validate_state_cardinality(reconciliation)


def _unparseable_toc_item_keys(view: CorrectionBundleView) -> set[str]:
    """Return TOC-region keys explicitly retained as parser diagnostics."""
    return {
        item["stable_item_key"]
        for item in view.bundle["warnings"] + view.bundle["ambiguities"]
        if item["code"] == "TOC_ROW_UNPARSEABLE" and item["stable_item_key"] is not None
    }


def _is_body_target(view: CorrectionBundleView, key: str) -> bool:
    feature = view.features_by_key[key]
    return feature["content_layer"] == "body" and not feature["toc_region"]


def _validate_state_cardinality(reconciliation: JsonRecord) -> None:
    """Match each terminal reconciliation state to its candidate count."""
    state = reconciliation["state"]
    candidates = reconciliation["candidate_keys"]
    target = reconciliation["target_key"]
    if state == "exact":
        require(candidates == [target], "exact reconciliation target differs")
    else:
        require(target is None, "non-exact reconciliation has target")

    if state == "missing":
        require(not candidates, "missing reconciliation has candidates")
    elif state == "ambiguous":
        require(len(candidates) > 1, "ambiguous reconciliation cardinality differs")
    elif state != "exact":
        require(len(candidates) == 1, "conflict reconciliation cardinality differs")
