"""Visible-TOC row ownership and body-reconciliation policies."""

from __future__ import annotations

import re

from er_commons.document_parsing.heading_evidence_parsing.text_evidence import normalize_text
from er_commons.hierarchy_inference.bundle import HierarchyBundleView, JsonRecord
from er_commons.hierarchy_inference.checks import require, require_sorted, require_unique
from er_commons.hierarchy_inference.toc_text import (
    split_heading_text as _split_body_title,
)
from er_commons.hierarchy_inference.toc_text import (
    typographic_canonical as _typographic_canonical,
)

_NUMERIC_MARKER = re.compile(r"^[0-9]+(?:\.[0-9]+){0,5}$")
_APPENDIX_MARKER = re.compile(r"^appendix [a-z]$")


def toc_rows_are_ordered_and_owned(view: HierarchyBundleView) -> None:
    """Require unique ordered TOC rows backed only by TOC-region items."""
    toc_ids = [item["toc_entry_id"] for item in view.toc_entries]
    require_unique(toc_ids, "duplicate TOC entry ID")
    require_sorted(
        (item["reading_order_index"] for item in view.toc_entries),
        "TOC entry order differs",
    )

    known_features = set(view.features_by_key)
    for entry in view.toc_entries:
        _validate_normalized_numeric_marker(entry)
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


def _validate_normalized_numeric_marker(entry: JsonRecord) -> None:
    """Require numeric row markers to retain a token without terminal punctuation."""
    title_with = entry["title_with_marker_normalized"]
    title_without = entry["title_without_marker_normalized"]
    if title_with == title_without:
        return
    first, separator, remainder = title_with.partition(" ")
    normalized = first.removesuffix(".")
    if not separator or not _NUMERIC_MARKER.fullmatch(normalized):
        return
    require(remainder == title_without, f"numeric TOC title differs: {entry['toc_entry_id']}")
    require(
        entry["numbering_token"] == normalized,
        f"numeric TOC token retains terminal punctuation: {entry['toc_entry_id']}",
    )


def toc_reconciliations_are_complete(view: HierarchyBundleView) -> None:
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
        _validate_match_basis(view, reconciliation)


def _unparseable_toc_item_keys(view: HierarchyBundleView) -> set[str]:
    """Return TOC-region keys explicitly retained as parser diagnostics."""
    return {
        item["stable_item_key"]
        for item in view.bundle["warnings"] + view.bundle["ambiguities"]
        if item["code"] == "TOC_ROW_UNPARSEABLE" and item["stable_item_key"] is not None
    }


def _is_body_target(view: HierarchyBundleView, key: str) -> bool:
    feature = view.features_by_key[key]
    return (
        feature["content_layer"] == "body"
        and not feature["toc_region"]
        and not feature["raw_parent_ref"].startswith("#/pictures/")
    )


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


def _validate_match_basis(view: HierarchyBundleView, reconciliation: JsonRecord) -> None:
    """Recompute each exact tier's evidence boundary independently."""
    basis = reconciliation["match_basis"]
    evidence = reconciliation["target_evidence_keys"]
    target = reconciliation["target_key"]
    _validate_native_pdf_evidence(view, reconciliation)
    if reconciliation["state"] == "missing":
        require(basis == "none", "non-exact reconciliation has match basis")
        require(not evidence, "non-exact reconciliation has target evidence")
        return
    if reconciliation["state"] != "exact":
        require(basis != "none", "conflict reconciliation lacks attempted match basis")
        require(
            set(reconciliation["candidate_keys"]) <= set(evidence),
            "conflict candidate evidence differs",
        )
        require(
            set(evidence) <= set(view.features_by_key),
            "unknown reconciliation target evidence",
        )
        return
    require(
        target is not None and evidence[0] == target, "target evidence does not start at target"
    )
    require(
        set(evidence) <= set(view.features_by_key),
        "unknown reconciliation target evidence",
    )
    entry = view.toc_entries_by_id[reconciliation["toc_entry_id"]]
    target_feature = view.features_by_key[target]
    marker, title = _split_body_title(target_feature["text"])
    expected_marker = entry["numbering_token"]
    marker_matches = expected_marker is None or marker.casefold() == expected_marker.casefold()
    strict = title == entry["title_without_marker_normalized"] and marker_matches
    canonical = (
        _typographic_canonical(title)
        == _typographic_canonical(entry["title_without_marker_normalized"])
        and marker_matches
    )
    if basis == "strict_exact":
        require(strict and evidence == [target], "strict TOC match evidence differs")
    elif basis == "typographic_canonical":
        require(not strict and canonical and evidence == [target], "canonical TOC match differs")
    elif basis == "composite_appendix":
        require(
            isinstance(expected_marker, str)
            and _APPENDIX_MARKER.fullmatch(normalize_text(expected_marker)) is not None
            and target_feature["raw_role"] == "section_header"
            and normalize_text(target_feature["text"]) == normalize_text(expected_marker)
            and 1 <= len(evidence) <= 2,
            "composite Appendix evidence differs",
        )
    elif basis == "multi_item_heading":
        require(len(evidence) == 2, "multi-item TOC evidence cardinality differs")
        second = view.features_by_key[evidence[1]]
        source_marker = view.features_by_key[entry["source_item_keys"][0]]
        require(
            target_feature["raw_role"] in {"text", "section_header"}
            and target_feature["physical_page"] == second["physical_page"]
            and target_feature["reading_order_index"] + 1 == second["reading_order_index"]
            and normalize_text(target_feature["text"]) == normalize_text(source_marker["text"])
            and _typographic_canonical(second["text"])
            == _typographic_canonical(entry["title_without_marker_normalized"]),
            "multi-item TOC evidence differs",
        )
    elif basis == "native_pdf_bbox_exact":
        require(evidence == [target], "native-PDF TOC evidence keys differ")
    else:
        require(False, f"unknown exact TOC match basis: {basis}")


def _validate_native_pdf_evidence(view: HierarchyBundleView, reconciliation: JsonRecord) -> None:
    """Independently enforce the narrow bbox-exact tail-artifact record."""
    basis = reconciliation["match_basis"]
    native = reconciliation["native_pdf_evidence"]
    if basis != "native_pdf_bbox_exact":
        require(native is None, "non-native TOC match has native-PDF evidence")
        return
    require(native is not None, "native TOC match lacks native-PDF evidence")
    candidates = reconciliation["candidate_keys"]
    require(len(candidates) == 1, "native TOC match candidate is not unique")
    candidate = view.features_by_key[candidates[0]]
    entry = view.toc_entries_by_id[reconciliation["toc_entry_id"]]
    expected = entry["title_with_marker_normalized"]
    candidate_text = normalize_text(candidate["text"])
    marker, _title = _split_body_title(candidate["text"])
    expected_marker = entry["numbering_token"]
    require(
        candidate["raw_role"] == "section_header"
        and (expected_marker is None or marker.casefold() == expected_marker.casefold())
        and candidate_text.startswith(expected)
        and re.fullmatch(r" [a-z]", candidate_text.removeprefix(expected)) is not None,
        "native TOC candidate is not a narrow tail artifact",
    )
    require(
        native["physical_page"] == candidate["physical_page"]
        and native["bbox"] == candidate["bbox"]
        and native["normalized_text"] == expected,
        "native TOC bbox evidence differs",
    )
