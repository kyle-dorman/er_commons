"""Orchestrate responsibility-specific visible-TOC analysis stages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from er_commons.hierarchy_correction.semantic_types import ObservedItem, TocClassifiedItem
from er_commons.hierarchy_correction.toc_reconciliation import reconcile_toc_entries
from er_commons.hierarchy_correction.toc_regions import (
    TocRegion,
    detect_toc_regions,
    printed_page_observations,
)
from er_commons.hierarchy_correction.toc_rows import parse_toc_region

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class TocBuildResult:
    """Feature copies, parsed rows, reconciliation, and diagnostics."""

    features: tuple[TocClassifiedItem, ...]
    regions: tuple[TocRegion, ...]
    entries: tuple[JsonObject, ...]
    reconciliations: tuple[JsonObject, ...]
    diagnostics: tuple[JsonObject, ...]


def build_visible_toc(
    features: list[ObservedItem],
    outline_observations: tuple[JsonObject, ...],
    *,
    native_heading_observations: dict[str, JsonObject] | None = None,
    document_index_text_refs: frozenset[str] = frozenset(),
) -> TocBuildResult:
    """Detect regions, parse their rows, then reconcile exact body targets."""
    projected: list[JsonObject] = [
        dict(
            feature,
            toc_region=feature["raw_self_ref"] in document_index_text_refs,
        )
        for feature in features
    ]
    printed_pages = printed_page_observations(projected)
    regions = detect_toc_regions(projected, outline_observations, printed_pages)
    diagnostics: list[JsonObject] = []
    entries: list[JsonObject] = []
    detected_indexes: set[int] = set()
    for region in regions:
        for index in range(region.start, region.end):
            if projected[index]["content_layer"] == "body":
                projected[index]["toc_region"] = True
                detected_indexes.add(index)
        rows, row_diagnostics = parse_toc_region(projected, region, outline_observations)
        entries.extend(rows)
        diagnostics.extend(row_diagnostics)
    diagnostics.extend(
        {
            "reading_order_index": feature["reading_order_index"],
            "stable_item_key": feature["stable_item_key"],
            "code": "TOC_ROW_UNPARSEABLE",
            "detail": "document-index text retained without a parseable TOC row",
        }
        for index, feature in enumerate(projected)
        if feature["raw_self_ref"] in document_index_text_refs
        and feature["raw_role"] != "section_header"
        and index not in detected_indexes
    )
    reconciliations, reconciliation_diagnostics = reconcile_toc_entries(
        entries,
        projected,
        regions,
        outline_observations,
        printed_pages,
        native_heading_observations or {},
    )
    diagnostics.extend(reconciliation_diagnostics)
    return TocBuildResult(
        features=cast(tuple[TocClassifiedItem, ...], tuple(projected)),
        regions=regions,
        entries=tuple(entries),
        reconciliations=tuple(reconciliations),
        diagnostics=tuple(diagnostics),
    )
