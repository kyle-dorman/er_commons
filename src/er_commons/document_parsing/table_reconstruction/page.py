"""Coordinate one-page table reconstruction behind the stable public facade.

Parser selection, geometry detection, content cleanup, and artifact persistence
have named owners. This module deliberately retains the established imports and
the sequential read-route-persist-seal lifecycle used by the table pipeline.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium  # type: ignore[import-untyped]

from er_commons.document_parsing.table_reconstruction.learned_fallback import (
    LearnedFallbackRunner,
)
from er_commons.document_parsing.table_reconstruction.page_content import (
    clean_rows,
    column_type_signatures,
    header_matrix,
    normalize_text,
    parse_footer,
    serialize_cells,
    sha256_file,
    table_rows,
    write_csv,
    write_json,
)
from er_commons.document_parsing.table_reconstruction.page_geometry import (
    bbox_iou,
    detect_ruled_regions,
    rectangle_union_coverage,
    visual_order_key,
)
from er_commons.document_parsing.table_reconstruction.page_parsers import (
    deduplicate_stream_tables,
    is_duplicate_stream_table,
    parse_complex_page,
    parse_simple_page,
)
from er_commons.document_parsing.table_reconstruction.page_persistence import (
    annotate_candidates,
    page_result_record,
    persist_review_artifacts,
    persist_table_candidates,
)
from er_commons.document_parsing.table_reconstruction.page_routing import route_page_candidates
from er_commons.document_parsing.table_reconstruction.page_types import (
    CandidatePayload,
    ExplicitRoute,
    RenderedPage,
)

__all__ = [
    "CandidatePayload",
    "ExplicitRoute",
    "RenderedPage",
    "bbox_iou",
    "clean_rows",
    "column_type_signatures",
    "deduplicate_stream_tables",
    "detect_ruled_regions",
    "extract_page",
    "header_matrix",
    "is_duplicate_stream_table",
    "normalize_text",
    "parse_complex_page",
    "parse_footer",
    "parse_simple_page",
    "rectangle_union_coverage",
    "route_page_candidates",
    "serialize_cells",
    "sha256_file",
    "table_rows",
    "visual_order_key",
    "write_csv",
    "write_json",
]


def _read_rendered_page(pdf_path: Path, page_number: int, render_scale: float) -> RenderedPage:
    """Read native text and render one page while always closing PDFium handles."""
    document = pdfium.PdfDocument(pdf_path)
    page = document[page_number - 1]
    try:
        width, height = (float(value) for value in page.get_size())
        text_page = page.get_textpage()
        try:
            native_text = text_page.get_text_range()
        finally:
            text_page.close()
        image = page.render(scale=render_scale, rev_byteorder=True).to_pil().convert("RGB")
        return RenderedPage(width, height, native_text, image)
    finally:
        page.close()
        document.close()


def extract_page(
    pdf_path: Path,
    page_number: int,
    detection: dict[str, Any],
    cleanup: dict[str, Any],
    output_dir: Path,
    *,
    route_mode: ExplicitRoute | None = None,
    layout_regions: list[list[float]] | None = None,
    table_id_prefix: str = "g3",
    retain_review_derivatives: bool = True,
    learned_fallback_runner: LearnedFallbackRunner | None = None,
) -> dict[str, Any]:
    """Run one page through read, route, persist, annotate, and seal phases."""
    result_path = output_dir / "result.json"
    if result_path.exists():
        return dict(json.loads(result_path.read_text()))
    if output_dir.exists():
        raise FileExistsError(f"incomplete page output already exists: {output_dir}")
    output_dir.mkdir(parents=True)

    started = time.perf_counter()
    scale = float(detection["render_scale"])
    rendered = _read_rendered_page(pdf_path, page_number, scale)
    ruled_regions, ruling_mask = detect_ruled_regions(rendered.image, rendered.height, detection)
    complex_page = len(ruled_regions) >= int(detection["complex_page_minimum_regions"])
    route, candidates, parser_evidence = route_page_candidates(
        pdf_path=pdf_path,
        page_number=page_number,
        rendered=rendered,
        ruled_regions=ruled_regions,
        detection=detection,
        route_mode=route_mode,
        layout_regions=layout_regions,
        output_dir=output_dir,
        cleanup=cleanup,
        learned_fallback_runner=learned_fallback_runner,
    )
    table_records = persist_table_candidates(
        candidates=candidates,
        output_dir=output_dir,
        page_number=page_number,
        page_size=(rendered.width, rendered.height),
        route=route,
        cleanup=cleanup,
        table_id_prefix=table_id_prefix,
    )
    annotated = annotate_candidates(
        rendered.image,
        candidates,
        table_records,
        page_height=rendered.height,
        scale=scale,
    )
    footer = parse_footer(rendered.native_text, cleanup)
    artifacts = (
        persist_review_artifacts(
            output_dir=output_dir,
            image=rendered.image,
            ruling_mask=ruling_mask,
            annotated=annotated,
        )
        if retain_review_derivatives
        else {}
    )
    result = page_result_record(
        page_number=page_number,
        route=route,
        route_mode=route_mode,
        rendered=rendered,
        ruled_regions=ruled_regions,
        parser_evidence=parser_evidence,
        table_records=table_records,
        footer=footer,
        artifacts=artifacts,
        elapsed=time.perf_counter() - started,
        complex_page=complex_page,
    )
    write_json(result_path, result)
    return result
