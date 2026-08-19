"""Reconcile parsed visible-TOC rows to exact body heading evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from er_commons.document_parsing.heading_evidence_parsing.text_evidence import normalize_text
from er_commons.hierarchy_inference.toc_regions import TocRegion
from er_commons.hierarchy_inference.toc_text import split_body_title, typographic_canonical

JsonObject = dict[str, Any]

_APPENDIX_MARKER = re.compile(r"^Appendix [A-Z]$")


@dataclass(frozen=True)
class BodyHeadingMatch:
    """One tier-specific body target and all source items supporting it."""

    target: JsonObject
    evidence_keys: tuple[str, ...]


@dataclass(frozen=True)
class ReconciliationIndexes:
    """Document-wide lookups shared by every TOC-entry reconciliation."""

    features_by_key: dict[str, JsonObject]
    body_intervals_by_region: dict[str, tuple[JsonObject, ...]]
    outline_depths: dict[tuple[int, str], int]
    canonical_outline_depths: dict[tuple[int, str], int]
    outline_ids_by_target: dict[tuple[int, str], tuple[str, ...]]


@dataclass(frozen=True)
class TargetAssessment:
    """Tiered target matches plus their terminal reconciliation state."""

    matches: tuple[BodyHeadingMatch, ...]
    match_basis: str
    state: str


def reconcile_toc_entries(
    entries: list[JsonObject],
    features: list[JsonObject],
    regions: tuple[TocRegion, ...],
    outline_observations: tuple[JsonObject, ...],
    printed_pages: dict[int, str],
    native_heading_observations: dict[str, JsonObject],
) -> tuple[list[JsonObject], list[JsonObject]]:
    """Reconcile rows by exact marker, title, page, depth, and body order."""
    indexes = _build_reconciliation_indexes(features, regions, outline_observations)
    reconciliations: list[JsonObject] = []
    diagnostics: list[JsonObject] = []
    previous_order_by_region: dict[str, int] = {}
    for entry in entries:
        region = _region_for_entry(entry, regions)
        matches, match_basis = _tiered_target_matches(
            entry=entry,
            interval=indexes.body_intervals_by_region[region.start_key],
            feature_by_key=indexes.features_by_key,
            native_heading_observations=native_heading_observations,
            outline_ids_by_target=indexes.outline_ids_by_target,
        )
        assessment = _assess_target_matches(
            entry=entry,
            region=region,
            matches=matches,
            match_basis=match_basis,
            indexes=indexes,
            printed_pages=printed_pages,
            previous_order_by_region=previous_order_by_region,
        )
        if assessment.state == "exact":
            previous_order_by_region[region.start_key] = matches[0].target["reading_order_index"]
        reconciliations.append(
            _reconciliation_record(
                entry,
                assessment,
                native_heading_observations,
                indexes.outline_ids_by_target,
            )
        )
        if assessment.state != "exact":
            diagnostics.append(
                _diagnostic(
                    indexes.features_by_key[entry["source_item_keys"][0]],
                    {
                        "missing": "TOC_TARGET_MISSING",
                        "ambiguous": "TOC_TARGET_AMBIGUOUS",
                        "page_conflict": "TOC_PAGE_CONFLICT",
                        "level_conflict": "TOC_LEVEL_CONFLICT",
                        "order_conflict": "TOC_ORDER_CONFLICT",
                    }[assessment.state],
                    f"TOC reconciliation ended as {assessment.state}: {entry['toc_entry_id']}",
                )
            )
    return reconciliations, diagnostics


def _build_reconciliation_indexes(
    features: list[JsonObject],
    regions: tuple[TocRegion, ...],
    outlines: tuple[JsonObject, ...],
) -> ReconciliationIndexes:
    """Build target intervals and outline lookups once per document."""
    body_intervals = {
        region.start_key: tuple(
            feature
            for feature in features[region.end : region.candidate_end]
            if feature["content_layer"] == "body"
            and not feature["toc_region"]
            and not feature["raw_parent_ref"].startswith("#/pictures/")
        )
        for region in regions
    }
    outline_ids: dict[tuple[int, str], list[str]] = {}
    for outline in outlines:
        outline_ids.setdefault((outline["physical_page"], outline["normalized_title"]), []).append(
            outline["outline_id"]
        )
    return ReconciliationIndexes(
        features_by_key={feature["stable_item_key"]: feature for feature in features},
        body_intervals_by_region=body_intervals,
        outline_depths=_outline_depth_by_target(outlines),
        canonical_outline_depths=_canonical_outline_depth_by_target(outlines),
        outline_ids_by_target={key: tuple(value) for key, value in outline_ids.items()},
    )


def _region_for_entry(entry: JsonObject, regions: tuple[TocRegion, ...]) -> TocRegion:
    """Resolve the one detected region that owns a parsed entry."""
    return next(
        region for region in regions if region.start <= entry["reading_order_index"] < region.end
    )


def _assess_target_matches(
    *,
    entry: JsonObject,
    region: TocRegion,
    matches: list[BodyHeadingMatch],
    match_basis: str,
    indexes: ReconciliationIndexes,
    printed_pages: dict[int, str],
    previous_order_by_region: dict[str, int],
) -> TargetAssessment:
    """Apply uniqueness, page, level, and within-region order policies."""
    state = "exact"
    if len(matches) > 1:
        state = "ambiguous"
    elif not matches:
        state = "missing"
    else:
        candidate = matches[0].target
        printed_page = entry["printed_page"]
        observed_page = printed_pages.get(candidate["physical_page"])
        if (
            printed_page is not None
            and observed_page is not None
            and printed_page.casefold() != observed_page.casefold()
        ):
            state = "page_conflict"
        else:
            candidate_depth = _candidate_depth(
                candidate,
                indexes.outline_depths,
                indexes.canonical_outline_depths,
                canonical=match_basis == "typographic_canonical",
                native_title=(
                    entry["title_with_marker_normalized"]
                    if match_basis == "native_pdf_bbox_exact"
                    else None
                ),
            )
            if (
                entry["depth_source"] != "default"
                and candidate_depth is not None
                and candidate_depth != entry["depth"]
            ):
                state = "level_conflict"
            elif candidate["reading_order_index"] <= previous_order_by_region.get(
                region.start_key, -1
            ):
                state = "order_conflict"
    return TargetAssessment(tuple(matches), match_basis, state)


def _reconciliation_record(
    entry: JsonObject,
    assessment: TargetAssessment,
    native_heading_observations: dict[str, JsonObject],
    outline_ids_by_target: dict[tuple[int, str], tuple[str, ...]],
) -> JsonObject:
    """Serialize one assessed target without changing match evidence order."""
    matches = assessment.matches
    exact_match = matches[0] if assessment.state == "exact" else None
    evidence_keys = list(dict.fromkeys(key for match in matches for key in match.evidence_keys))
    return {
        "toc_entry_id": entry["toc_entry_id"],
        "reading_order_index": entry["reading_order_index"],
        "state": assessment.state,
        "match_basis": assessment.match_basis if matches else "none",
        "candidate_keys": [item.target["stable_item_key"] for item in matches],
        "target_key": exact_match.target["stable_item_key"] if exact_match else None,
        "target_evidence_keys": evidence_keys,
        "native_pdf_evidence": (
            _native_pdf_evidence(
                matches[0].target,
                entry,
                native_heading_observations,
                outline_ids_by_target,
            )
            if len(matches) == 1 and assessment.match_basis == "native_pdf_bbox_exact"
            else None
        ),
    }


def _tiered_target_matches(
    *,
    entry: JsonObject,
    interval: tuple[JsonObject, ...],
    feature_by_key: dict[str, JsonObject],
    native_heading_observations: dict[str, JsonObject],
    outline_ids_by_target: dict[tuple[int, str], tuple[str, ...]],
) -> tuple[list[BodyHeadingMatch], str]:
    """Apply strict, canonical, composite, multi-item, then native matching."""
    strict = _single_item_matches(entry, interval, canonical=False)
    if strict:
        return strict, "strict_exact"
    canonical = _single_item_matches(entry, interval, canonical=True)
    if canonical:
        return canonical, "typographic_canonical"
    composite = _composite_appendix_matches(entry, interval)
    if composite:
        return composite, "composite_appendix"
    multi_item = _multi_item_heading_matches(entry, interval, feature_by_key)
    if multi_item:
        return multi_item, "multi_item_heading"
    native = _native_pdf_bbox_matches(
        entry, interval, native_heading_observations, outline_ids_by_target
    )
    return (native, "native_pdf_bbox_exact") if native else ([], "none")


def _native_pdf_bbox_matches(
    entry: JsonObject,
    interval: tuple[JsonObject, ...],
    native_heading_observations: dict[str, JsonObject],
    outline_ids_by_target: dict[tuple[int, str], tuple[str, ...]],
) -> list[BodyHeadingMatch]:
    expected = entry["title_with_marker_normalized"]
    expected_marker = entry["numbering_token"]
    matches: list[BodyHeadingMatch] = []
    for feature in interval:
        if feature["raw_role"] != "section_header":
            continue
        marker, _title = split_body_title(feature)
        if expected_marker is not None and marker.casefold() != expected_marker.casefold():
            continue
        docling_text = normalize_text(feature["text"])
        suffix = docling_text.removeprefix(expected)
        if not docling_text.startswith(expected) or re.fullmatch(r" [a-z]", suffix) is None:
            continue
        native = native_heading_observations.get(feature["stable_item_key"])
        if native is None or native["normalized_text"] != expected:
            continue
        exact_outline_ids = outline_ids_by_target.get((feature["physical_page"], expected), ())
        if len(exact_outline_ids) > 1:
            continue
        matches.append(BodyHeadingMatch(feature, (feature["stable_item_key"],)))
    return matches if len(matches) == 1 else []


def _native_pdf_evidence(
    target: JsonObject,
    entry: JsonObject,
    observations: dict[str, JsonObject],
    outline_ids_by_target: dict[tuple[int, str], tuple[str, ...]],
) -> JsonObject:
    observation = observations[target["stable_item_key"]]
    outline_ids = list(
        outline_ids_by_target.get(
            (target["physical_page"], entry["title_with_marker_normalized"]), ()
        )
    )
    return {**observation, "outline_ids": outline_ids}


def _single_item_matches(
    entry: JsonObject, interval: tuple[JsonObject, ...], *, canonical: bool
) -> list[BodyHeadingMatch]:
    expected_title = entry["title_without_marker_normalized"]
    if canonical:
        expected_title = typographic_canonical(expected_title)
    expected_marker = entry["numbering_token"]
    matches: list[BodyHeadingMatch] = []
    for feature in interval:
        marker, title = split_body_title(feature)
        compared_title = typographic_canonical(title) if canonical else title
        if compared_title != expected_title:
            continue
        if expected_marker is not None and marker.casefold() != expected_marker.casefold():
            continue
        if canonical and title == entry["title_without_marker_normalized"]:
            continue
        matches.append(BodyHeadingMatch(feature, (feature["stable_item_key"],)))
    return matches


def _composite_appendix_matches(
    entry: JsonObject, interval: tuple[JsonObject, ...]
) -> list[BodyHeadingMatch]:
    expected_marker = entry["numbering_token"]
    if not isinstance(expected_marker, str) or _APPENDIX_MARKER.fullmatch(expected_marker) is None:
        return []
    matches: list[BodyHeadingMatch] = []
    expected_title = typographic_canonical(entry["title_without_marker_normalized"])
    for index, feature in enumerate(interval):
        if feature["raw_role"] != "section_header":
            continue
        if normalize_text(feature["text"], casefold=False) != expected_marker:
            continue
        evidence = [feature["stable_item_key"]]
        if index + 1 < len(interval):
            description = interval[index + 1]
            if (
                description["physical_page"] == feature["physical_page"]
                and description["raw_role"] != "section_header"
                and typographic_canonical(description["normalized_text"]) == expected_title
            ):
                evidence.append(description["stable_item_key"])
        matches.append(BodyHeadingMatch(feature, tuple(evidence)))
    return matches


def _multi_item_heading_matches(
    entry: JsonObject,
    interval: tuple[JsonObject, ...],
    feature_by_key: dict[str, JsonObject],
) -> list[BodyHeadingMatch]:
    expected_marker = entry["numbering_token"]
    if expected_marker is None:
        return []
    source_marker = feature_by_key[entry["source_item_keys"][0]]
    marker_text = normalize_text(source_marker["text"])
    expected_title = entry["title_without_marker_normalized"]
    matches: list[BodyHeadingMatch] = []
    for first, second in zip(interval, interval[1:], strict=False):
        if first["physical_page"] != second["physical_page"]:
            continue
        if first["reading_order_index"] + 1 != second["reading_order_index"]:
            continue
        if first["raw_role"] not in {"text", "section_header"}:
            continue
        if second["raw_role"] not in {"text", "section_header"}:
            continue
        if normalize_text(first["text"]) != marker_text:
            continue
        second_title = normalize_text(second["text"])
        if second_title != expected_title and typographic_canonical(
            second_title
        ) != typographic_canonical(expected_title):
            continue
        matches.append(
            BodyHeadingMatch(
                first,
                (first["stable_item_key"], second["stable_item_key"]),
            )
        )
    return matches


def _candidate_depth(
    candidate: JsonObject,
    outline_depths: dict[tuple[int, str], int],
    canonical_outline_depths: dict[tuple[int, str], int],
    *,
    canonical: bool,
    native_title: str | None,
) -> int | None:
    depth = outline_depths.get((candidate["physical_page"], candidate["normalized_text"]))
    if depth is None and native_title is not None:
        depth = outline_depths.get((candidate["physical_page"], native_title))
    if depth is None and canonical:
        depth = canonical_outline_depths.get(
            (candidate["physical_page"], typographic_canonical(candidate["normalized_text"]))
        )
    return candidate["numbering_depth"] if depth is None else depth


def _outline_depth_by_target(
    outlines: tuple[JsonObject, ...],
) -> dict[tuple[int, str], int]:
    grouped: dict[tuple[int, str], set[int]] = {}
    for item in outlines:
        key = (item["physical_page"], item["normalized_title"])
        grouped.setdefault(key, set()).add(item["raw_depth"])
    return {key: next(iter(values)) for key, values in grouped.items() if len(values) == 1}


def _canonical_outline_depth_by_target(
    outlines: tuple[JsonObject, ...],
) -> dict[tuple[int, str], int]:
    grouped: dict[tuple[int, str], set[int]] = {}
    for item in outlines:
        key = (item["physical_page"], typographic_canonical(item["normalized_title"]))
        grouped.setdefault(key, set()).add(item["raw_depth"])
    return {key: next(iter(values)) for key, values in grouped.items() if len(values) == 1}


def _diagnostic(feature: JsonObject, code: str, detail: str) -> JsonObject:
    return {
        "reading_order_index": feature["reading_order_index"],
        "stable_item_key": feature["stable_item_key"],
        "code": code,
        "detail": detail,
    }
