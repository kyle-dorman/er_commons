"""Persist table candidates and optional page-review artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
from PIL import Image, ImageDraw

from er_commons.document_parsing.table_reconstruction.page_content import (
    candidate_payload,
    clean_rows,
    column_type_signatures,
    header_matrix,
    sha256_file,
    write_csv,
    write_json,
)
from er_commons.document_parsing.table_reconstruction.page_geometry import visual_order_key
from er_commons.document_parsing.table_reconstruction.page_types import ExplicitRoute, RenderedPage


def persist_table_candidates(
    *,
    candidates: list[dict[str, Any]],
    output_dir: Path,
    page_number: int,
    page_size: tuple[float, float],
    route: str,
    cleanup: dict[str, Any],
    table_id_prefix: str,
) -> list[dict[str, Any]]:
    """Persist candidate-owned records after parser-neutral cleanup."""
    candidates.sort(key=visual_order_key)
    table_root = output_dir / "tables"
    table_root.mkdir()
    page_width, page_height = page_size
    table_records: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        table_id = f"{table_id_prefix}_p{page_number:05d}_t{index:03d}"
        table_dir = table_root / table_id
        table_dir.mkdir()
        payload = candidate_payload(candidate)
        cleaned_rows, cleanup_record = clean_rows(payload.raw_rows, cleanup)
        raw_csv = table_dir / "raw.csv"
        clean_csv = table_dir / "table.csv"
        cells_path = table_dir / "cells.json"
        write_csv(raw_csv, payload.raw_rows)
        write_csv(clean_csv, cleaned_rows)
        write_json(cells_path, payload.serialized_cells)
        record = {
            "table_id": table_id,
            "physical_pdf_page": page_number,
            "page_table_index": index,
            "route": route,
            **payload.metadata,
            "shape_raw": [
                len(payload.raw_rows),
                max((len(row) for row in payload.raw_rows), default=0),
            ],
            "shape_clean": [
                len(cleaned_rows),
                max((len(row) for row in cleaned_rows), default=0),
            ],
            "page_size_pdf_points": [page_width, page_height],
            "columns_pdf_points": payload.columns_pdf_points,
            "cleanup": cleanup_record,
            "header_matrix": header_matrix(cleaned_rows, cleanup),
            "raw_column_type_signatures": column_type_signatures(payload.raw_rows),
            "raw_csv": {
                "path": raw_csv.relative_to(output_dir).as_posix(),
                "sha256": sha256_file(raw_csv),
            },
            "clean_csv": {
                "path": clean_csv.relative_to(output_dir).as_posix(),
                "sha256": sha256_file(clean_csv),
            },
            "cells": {
                "path": cells_path.relative_to(output_dir).as_posix(),
                "sha256": sha256_file(cells_path),
            },
        }
        write_json(table_dir / "table.json", record)
        table_records.append(record)
    return table_records


def annotate_candidates(
    image: Image.Image,
    candidates: list[dict[str, Any]],
    table_records: list[dict[str, Any]],
    *,
    page_height: float,
    scale: float,
) -> Image.Image:
    """Draw deterministic parser-colored boxes without affecting table records."""
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    colors = {
        "camelot_stream": (0, 140, 0),
        "camelot_lattice": (220, 0, 0),
        "camelot_network": (0, 80, 255),
        "tableformer_accurate": (150, 60, 180),
    }
    for candidate, record in zip(candidates, table_records, strict=True):
        left, bottom, right, top = candidate["bbox_pdf_points_bottom_left"]
        pixel_box = (
            round(left * scale),
            round((page_height - top) * scale),
            round(right * scale),
            round((page_height - bottom) * scale),
        )
        color = colors[candidate["parser"]]
        draw.rectangle(pixel_box, outline=color, width=4)
        draw.text((pixel_box[0] + 3, pixel_box[1] + 3), record["table_id"], fill=color)
    return annotated


def persist_review_artifacts(
    *,
    output_dir: Path,
    image: Image.Image,
    ruling_mask: Any,
    annotated: Image.Image,
) -> dict[str, dict[str, str]]:
    """Persist optional reproducible images and return their checksum references."""
    paths = {
        "page_image": output_dir / "page.png",
        "ruling_mask": output_dir / "ruling_mask.png",
        "annotated": output_dir / "annotated.png",
    }
    image.save(paths["page_image"], optimize=False, compress_level=9)
    cv2.imwrite(str(paths["ruling_mask"]), ruling_mask, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    annotated.save(paths["annotated"], optimize=False, compress_level=9)
    return {role: {"path": path.name, "sha256": sha256_file(path)} for role, path in paths.items()}


def page_result_record(
    *,
    page_number: int,
    route: str,
    route_mode: ExplicitRoute | None,
    rendered: RenderedPage,
    ruled_regions: list[dict[str, Any]],
    parser_evidence: dict[str, Any],
    table_records: list[dict[str, Any]],
    footer: dict[str, Any] | None,
    artifacts: dict[str, dict[str, str]],
    elapsed: float,
    complex_page: bool,
) -> dict[str, Any]:
    """Assemble the serialized page boundary after all artifacts are durable."""
    footer_owner = (
        min(
            table_records,
            key=lambda item: (
                item["bbox_pdf_points_bottom_left"][1],
                -item["bbox_pdf_points_bottom_left"][2],
            ),
        )["table_id"]
        if footer and table_records
        else None
    )
    return {
        "schema_version": "1.0.0",
        "physical_pdf_page": page_number,
        "route": route,
        "route_requested": route_mode,
        "complex_page": complex_page,
        "page_size_pdf_points": [rendered.width, rendered.height],
        "ruling_region_count": len(ruled_regions),
        "ruled_regions": ruled_regions,
        "parser_evidence": parser_evidence,
        "table_count": len(table_records),
        "tables": table_records,
        "footer": footer,
        "footer_owner_table_id": footer_owner,
        "artifacts": artifacts,
        "wall_seconds": elapsed,
    }
