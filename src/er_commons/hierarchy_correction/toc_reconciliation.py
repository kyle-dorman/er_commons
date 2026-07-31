"""Reconcile parsed visible-TOC rows to exact body heading evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from er_commons.hierarchy_correction.text_evidence import normalize_text
from er_commons.hierarchy_correction.toc_regions import TocRegion
from er_commons.hierarchy_correction.toc_text import split_body_title, typographic_canonical

JsonObject = dict[str, Any]

_APPENDIX_MARKER = re.compile(r"^Appendix [A-Z]$")


@dataclass(frozen=True)
class BodyHeadingMatch:
    """One tier-specific body target and all source items supporting it."""

    target: JsonObject
    evidence_keys: tuple[str, ...]


def reconcile_toc_entries(
    entries: list[JsonObject],
    features: list[JsonObject],
    regions: tuple[TocRegion, ...],
    outline_observations: tuple[JsonObject, ...],
    printed_pages: dict[int, str],
    native_heading_observations: dict[str, JsonObject],
) -> tuple[list[JsonObject], list[JsonObject]]:
    """Reconcile rows by exact marker, title, page, depth, and body order."""
    feature_by_key = {feature["stable_item_key"]: feature for feature in features}
    outline_depths = _outline_depth_by_target(outline_observations)
    canonical_outline_depths = _canonical_outline_depth_by_target(outline_observations)
    reconciliations: list[JsonObject] = []
    diagnostics: list[JsonObject] = []
    previous_order_by_region: dict[str, int] = {}
    for entry in entries:
        region = next(
            item for item in regions if item.start <= entry["reading_order_index"] < item.end
        )
        interval = [
            feature
            for feature in features[region.end : region.candidate_end]
            if feature["content_layer"] == "body"
            and not feature["toc_region"]
            and not feature["raw_parent_ref"].startswith("#/pictures/")
        ]
        matches, attempted_basis = _tiered_target_matches(
            entry=entry,
            interval=interval,
            feature_by_key=feature_by_key,
            native_heading_observations=native_heading_observations,
            outline_observations=outline_observations,
        )

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
                    outline_depths,
                    canonical_outline_depths,
                    canonical=attempted_basis == "typographic_canonical",
                    native_title=(
                        entry["title_with_marker_normalized"]
                        if attempted_basis == "native_pdf_bbox_exact"
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
            if state == "exact":
                previous_order_by_region[region.start_key] = candidate["reading_order_index"]

        candidate_keys = [item.target["stable_item_key"] for item in matches]
        exact_match = matches[0] if state == "exact" else None
        evidence_keys = list(dict.fromkeys(key for match in matches for key in match.evidence_keys))
        reconciliation = {
            "toc_entry_id": entry["toc_entry_id"],
            "reading_order_index": entry["reading_order_index"],
            "state": state,
            "match_basis": attempted_basis if matches else "none",
            "candidate_keys": candidate_keys,
            "target_key": exact_match.target["stable_item_key"] if exact_match else None,
            "target_evidence_keys": evidence_keys,
            "native_pdf_evidence": (
                _native_pdf_evidence(
                    matches[0].target,
                    entry,
                    native_heading_observations,
                    outline_observations,
                )
                if len(matches) == 1 and attempted_basis == "native_pdf_bbox_exact"
                else None
            ),
        }
        reconciliations.append(reconciliation)
        if state != "exact":
            diagnostics.append(
                _diagnostic(
                    feature_by_key[entry["source_item_keys"][0]],
                    {
                        "missing": "TOC_TARGET_MISSING",
                        "ambiguous": "TOC_TARGET_AMBIGUOUS",
                        "page_conflict": "TOC_PAGE_CONFLICT",
                        "level_conflict": "TOC_LEVEL_CONFLICT",
                        "order_conflict": "TOC_ORDER_CONFLICT",
                    }[state],
                    f"TOC reconciliation ended as {state}: {entry['toc_entry_id']}",
                )
            )
    return reconciliations, diagnostics


def _tiered_target_matches(
    *,
    entry: JsonObject,
    interval: list[JsonObject],
    feature_by_key: dict[str, JsonObject],
    native_heading_observations: dict[str, JsonObject],
    outline_observations: tuple[JsonObject, ...],
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
        entry, interval, native_heading_observations, outline_observations
    )
    return (native, "native_pdf_bbox_exact") if native else ([], "none")


def _native_pdf_bbox_matches(
    entry: JsonObject,
    interval: list[JsonObject],
    native_heading_observations: dict[str, JsonObject],
    outline_observations: tuple[JsonObject, ...],
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
        exact_outlines = [
            item
            for item in outline_observations
            if item["physical_page"] == feature["physical_page"]
            and item["normalized_title"] == expected
        ]
        if len(exact_outlines) > 1:
            continue
        matches.append(BodyHeadingMatch(feature, (feature["stable_item_key"],)))
    return matches if len(matches) == 1 else []


def _native_pdf_evidence(
    target: JsonObject,
    entry: JsonObject,
    observations: dict[str, JsonObject],
    outlines: tuple[JsonObject, ...],
) -> JsonObject:
    observation = observations[target["stable_item_key"]]
    outline_ids = [
        item["outline_id"]
        for item in outlines
        if item["physical_page"] == target["physical_page"]
        and item["normalized_title"] == entry["title_with_marker_normalized"]
    ]
    return {**observation, "outline_ids": outline_ids}


def _single_item_matches(
    entry: JsonObject, interval: list[JsonObject], *, canonical: bool
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
    entry: JsonObject, interval: list[JsonObject]
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
    interval: list[JsonObject],
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
