"""Coordinate the declared table-parser and fallback sequence for one page."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from er_commons.document_parsing.table_reconstruction.learned_fallback import (
    LearnedFallbackRunner,
)
from er_commons.document_parsing.table_reconstruction.learned_table_page import (
    apply_learned_fallbacks,
)
from er_commons.document_parsing.table_reconstruction.page_content import (
    clean_rows,
    table_rows,
)
from er_commons.document_parsing.table_reconstruction.page_parsers import (
    parse_complex_page,
    parse_simple_page,
)
from er_commons.document_parsing.table_reconstruction.page_types import (
    ExplicitRoute,
    RenderedPage,
)
from er_commons.document_parsing.table_reconstruction.region_stream_fallback import (
    apply_region_stream_fallbacks,
)


def _layout_candidates(
    *,
    pdf_path: Path,
    page_number: int,
    rendered: RenderedPage,
    ruled_regions: list[dict[str, Any]],
    layout_regions: list[list[float]],
    detection: dict[str, Any],
    cleanup: dict[str, Any],
    output_dir: Path,
    learned_fallback_runner: LearnedFallbackRunner | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run layout-owned parsers and fallbacks in their established order."""
    routed_regions = [
        {"region_id": f"layout_{index:03d}", "bbox_pdf_points_bottom_left": box}
        for index, box in enumerate(layout_regions, start=1)
    ]
    candidates, evidence = parse_complex_page(
        pdf_path,
        page_number,
        routed_regions,
        detection,
        include_network=False,
    )
    if detection.get("region_stream_fallback_enabled", False):
        candidates.extend(
            apply_region_stream_fallbacks(
                pdf_path=pdf_path,
                page_number=page_number,
                page_size=(rendered.width, rendered.height),
                opencv_ruled_regions=ruled_regions,
                accepted_candidates=candidates,
                parser_evidence=evidence,
                layout_regions=routed_regions,
                detection=detection,
                cleanup=cleanup,
                table_rows=table_rows,
                clean_rows=clean_rows,
            )
        )
    if learned_fallback_runner is not None:
        candidates.extend(
            apply_learned_fallbacks(
                runner=learned_fallback_runner,
                pdf_path=pdf_path,
                page_number=page_number,
                page_size=(rendered.width, rendered.height),
                page_output_root=output_dir,
                parser_evidence=evidence,
                layout_regions=routed_regions,
            )
        )
    return candidates, evidence


def route_page_candidates(
    *,
    pdf_path: Path,
    page_number: int,
    rendered: RenderedPage,
    ruled_regions: list[dict[str, Any]],
    detection: dict[str, Any],
    route_mode: ExplicitRoute | None,
    layout_regions: list[list[float]] | None,
    output_dir: Path,
    cleanup: dict[str, Any],
    learned_fallback_runner: LearnedFallbackRunner | None,
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """Choose one declared parsing route without changing fallback order."""
    complex_page = len(ruled_regions) >= int(detection["complex_page_minimum_regions"])
    if route_mode == "full_page_numeric":
        candidates, evidence = parse_simple_page(pdf_path, page_number)
        return "full_page_numeric", candidates, evidence
    if route_mode == "layout_regions":
        if not layout_regions:
            raise ValueError("layout_regions route requires at least one table region")
        candidates, evidence = _layout_candidates(
            pdf_path=pdf_path,
            page_number=page_number,
            rendered=rendered,
            ruled_regions=ruled_regions,
            layout_regions=layout_regions,
            detection=detection,
            cleanup=cleanup,
            output_dir=output_dir,
            learned_fallback_runner=learned_fallback_runner,
        )
        return "layout_regions", candidates, evidence
    if route_mode is not None:
        raise ValueError(f"unsupported explicit table route: {route_mode}")
    if complex_page:
        candidates, evidence = parse_complex_page(pdf_path, page_number, ruled_regions, detection)
        return "complex_segmented", candidates, evidence
    candidates, evidence = parse_simple_page(pdf_path, page_number)
    return "simple_stream", candidates, evidence
