"""Retain structural markers that can block a cross-page table continuation."""

from __future__ import annotations

from typing import Any

MARKER_LABELS = frozenset({"caption", "section_header"})


def markers_before_first_table(
    document_payload: dict[str, Any],
    page_number: int,
    table_observations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return caption/section evidence above the first observed table on one page."""
    if not table_observations:
        return []
    first_table_top = max(
        float(observation["bbox_pdf_points_bottom_left"][3]) for observation in table_observations
    )
    markers: list[dict[str, Any]] = []
    for text_index, item in enumerate(document_payload.get("texts", [])):
        label = str(item.get("label", ""))
        if label not in MARKER_LABELS:
            continue
        for provenance_index, provenance in enumerate(item.get("prov", [])):
            if int(provenance.get("page_no", -1)) != page_number:
                continue
            bbox = provenance.get("bbox", {})
            bottom = float(bbox["b"])
            if bottom < first_table_top:
                continue
            markers.append(
                {
                    "raw_object_ref": f"#/texts/{text_index}",
                    "provenance_index": provenance_index,
                    "label": label,
                    "text": str(item.get("text", "")),
                    "bbox_pdf_points_bottom_left": [
                        float(bbox["l"]),
                        bottom,
                        float(bbox["r"]),
                        float(bbox["t"]),
                    ],
                }
            )
    return sorted(
        markers,
        key=lambda marker: (
            -float(marker["bbox_pdf_points_bottom_left"][3]),
            str(marker["raw_object_ref"]),
        ),
    )
