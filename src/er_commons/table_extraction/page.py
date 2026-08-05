"""Extract logical tables from one PDF page in the unified project environment.

The page extractor deliberately keeps three concepts separate:

    rendered ruling lines ──> candidate regions
                                  |
                  ┌───────────────┴───────────────┐
                  v                               v
          Lattice grid parse             Network borderless parse
                  └───────────────┬───────────────┘
                                  v
                    stable logical table records

Camelot parser returns are hypotheses, not table identities. Logical IDs are
assigned only after redundant regions are removed and the survivors are sorted
in visual reading order.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import camelot
import cv2
import numpy as np
import pypdfium2 as pdfium  # type: ignore[import-untyped]
from PIL import Image, ImageDraw

from er_commons.table_extraction.learned_fallback import LearnedFallbackRunner
from er_commons.table_extraction.learned_table_page import apply_learned_fallbacks

NUMERIC_CELL = re.compile(
    r"^[\s$()<>+\-–—]*(?:\d[\d,]*(?:\.\d+)?|\.\d+)"
    r"(?:[eE][+\-]?\d+)?(?:\s*[%a-zA-Z/³².-]+)?[\s*†‡]*$"
)
MISSING_VALUE_CELL = re.compile(r"^(?:-|–|—|−)+$")
COORDINATE_KEY = re.compile(r"\b\d{6}\.\d+_\d{7}\.\d+_?")
ExplicitRoute = Literal["full_page_numeric", "layout_regions"]


@dataclass(frozen=True)
class CandidatePayload:
    """Parser-neutral content needed to persist one logical table."""

    metadata: dict[str, Any]
    raw_rows: list[list[str]]
    serialized_cells: list[dict[str, Any]]
    columns_pdf_points: list[dict[str, float]]


def sha256_file(path: Path) -> str:
    """Return one file's SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _candidate_payload(candidate: dict[str, Any]) -> CandidatePayload:
    """Adapt Camelot or TableFormer output without mutating the candidate."""
    excluded = {"table", "raw_rows", "serialized_cells", "columns_pdf_points"}
    metadata = {key: value for key, value in candidate.items() if key not in excluded}
    if candidate["parser"] == "tableformer_accurate":
        return CandidatePayload(
            metadata=metadata,
            raw_rows=[list(row) for row in candidate["raw_rows"]],
            serialized_cells=list(candidate["serialized_cells"]),
            columns_pdf_points=list(candidate["columns_pdf_points"]),
        )
    table = candidate.get("table")
    if table is None:
        raise ValueError("Camelot candidate is missing its parser table")
    return CandidatePayload(
        metadata=metadata,
        raw_rows=table_rows(table),
        serialized_cells=serialize_cells(table),
        columns_pdf_points=[
            {"left": float(left), "right": float(right)} for left, right in table.cols
        ],
    )


def write_json(path: Path, payload: Any) -> None:
    """Write stable UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def normalize_text(value: str) -> str:
    """Normalize text for comparison without changing substantive characters."""
    return " ".join(unicodedata.normalize("NFKC", value).split()).strip()


def table_rows(table: Any) -> list[list[str]]:
    """Return a rectangular normalized row matrix from one Camelot table."""
    return [
        [normalize_text(str(value)) for value in row]
        for row in table.df.fillna("").astype(str).values.tolist()
    ]


def bbox_iou(left_box: list[float], right_box: list[float]) -> float:
    """Return intersection-over-union for bottom-left PDF rectangles."""
    left = max(left_box[0], right_box[0])
    bottom = max(left_box[1], right_box[1])
    right = min(left_box[2], right_box[2])
    top = min(left_box[3], right_box[3])
    intersection = max(0.0, right - left) * max(0.0, top - bottom)
    left_area = max(0.0, left_box[2] - left_box[0]) * max(0.0, left_box[3] - left_box[1])
    right_area = max(0.0, right_box[2] - right_box[0]) * max(0.0, right_box[3] - right_box[1])
    union = left_area + right_area - intersection
    return intersection / union if union else 0.0


def visual_order_key(record: dict[str, Any]) -> tuple[float, float, float]:
    """Sort top-to-bottom, then left-to-right in bottom-left coordinates."""
    left, bottom, _right, top = record["bbox_pdf_points_bottom_left"]
    return (-top, left, -bottom)


def detect_ruled_regions(
    image: Image.Image,
    page_height: float,
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], np.ndarray]:
    """Find connected table grids from horizontal and vertical ruling lines."""
    gray = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)
    binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    horizontal = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (int(config["horizontal_kernel_pixels"]), 1),
        ),
    )
    vertical = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (1, int(config["vertical_kernel_pixels"])),
        ),
    )
    ruling_mask = cv2.bitwise_or(horizontal, vertical)
    intersections = cv2.bitwise_and(horizontal, vertical)
    _, intersection_labels, _, _ = cv2.connectedComponentsWithStats(intersections, connectivity=8)
    component_count, _, stats, _ = cv2.connectedComponentsWithStats(ruling_mask, connectivity=8)

    scale = float(config["render_scale"])
    regions = []
    for component in range(1, component_count):
        left, top, width, height, foreground_pixels = (
            int(value) for value in stats[component].tolist()
        )
        labels = np.unique(intersection_labels[top : top + height, left : left + width])
        intersection_count = int(np.count_nonzero(labels))
        if (
            width < int(config["minimum_region_width_pixels"])
            or height < int(config["minimum_region_height_pixels"])
            or intersection_count < int(config["minimum_intersections"])
        ):
            continue
        right = left + width
        bottom = top + height
        regions.append(
            {
                "bbox_image_pixels_top_left": [left, top, right, bottom],
                "bbox_pdf_points_bottom_left": [
                    left / scale,
                    page_height - bottom / scale,
                    right / scale,
                    page_height - top / scale,
                ],
                "intersection_count": intersection_count,
                "foreground_pixels": foreground_pixels,
            }
        )
    regions.sort(key=visual_order_key)
    for index, region in enumerate(regions, start=1):
        region["region_id"] = f"ruled_{index:03d}"
    return regions, ruling_mask


def rectangle_union_coverage(
    target: list[float],
    ruled_regions: list[dict[str, Any]],
    scale: float,
) -> float:
    """Measure the share of a parser box already explained by ruled boxes."""
    left, bottom, right, top = target
    width = max(1, round((right - left) * scale))
    height = max(1, round((top - bottom) * scale))
    mask = np.zeros((height, width), dtype=np.uint8)
    for region in ruled_regions:
        r_left, r_bottom, r_right, r_top = region["bbox_pdf_points_bottom_left"]
        i_left = max(left, r_left)
        i_bottom = max(bottom, r_bottom)
        i_right = min(right, r_right)
        i_top = min(top, r_top)
        if i_right <= i_left or i_top <= i_bottom:
            continue
        x1 = max(0, round((i_left - left) * scale))
        x2 = min(width, round((i_right - left) * scale))
        y1 = max(0, round((top - i_top) * scale))
        y2 = min(height, round((top - i_bottom) * scale))
        mask[y1:y2, x1:x2] = 1
    return float(mask.mean())


def is_duplicate_stream_table(candidate: Any, accepted: Any) -> bool:
    """Recognize near-identical Stream returns that differ by a leading row."""
    candidate_box = [float(value) for value in candidate._bbox]
    accepted_box = [float(value) for value in accepted._bbox]
    if bbox_iou(candidate_box, accepted_box) < 0.95:
        return False
    candidate_rows = table_rows(candidate)
    accepted_rows = table_rows(accepted)
    shorter, longer = sorted(
        (candidate_rows, accepted_rows),
        key=len,
    )
    if not shorter:
        return True
    difference = len(longer) - len(shorter)
    return difference <= 2 and (shorter == longer[difference:] or shorter == longer[: len(shorter)])


def deduplicate_stream_tables(tables: list[Any]) -> tuple[list[Any], list[dict[str, Any]]]:
    """Keep the larger representative from each duplicate Stream cluster."""
    ordered = sorted(
        tables,
        key=lambda table: (
            -(int(table.shape[0]) * int(table.shape[1])),
            -float(table.parsing_report.get("accuracy", 0.0)),
        ),
    )
    accepted: list[Any] = []
    decisions = []
    for table in ordered:
        duplicate_of = next(
            (
                index
                for index, prior in enumerate(accepted)
                if is_duplicate_stream_table(table, prior)
            ),
            None,
        )
        retained = duplicate_of is None
        decisions.append(
            {
                "parser_order": int(table.order),
                "shape": [int(value) for value in table.shape],
                "retained": retained,
                "duplicate_of_retained_index": (
                    duplicate_of + 1 if duplicate_of is not None else None
                ),
            }
        )
        if retained:
            accepted.append(table)
    return accepted, decisions


def parse_simple_page(
    pdf_path: Path,
    page_number: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse a simple page with fast whole-page Stream extraction."""
    started = time.perf_counter()
    tables = list(
        camelot.read_pdf(  # type: ignore[attr-defined]
            pdf_path,
            pages=str(page_number),
            flavor="stream",
            suppress_stdout=False,
            parallel=False,
        )
    )
    retained, decisions = deduplicate_stream_tables(tables)
    candidates = [
        {
            "parser": "camelot_stream",
            "parser_order": int(table.order),
            "table": table,
            "bbox_pdf_points_bottom_left": [float(value) for value in table._bbox],
        }
        for table in retained
    ]
    return candidates, {
        "stream_return_count": len(tables),
        "stream_retained_count": len(retained),
        "deduplication_decisions": decisions,
        "wall_seconds": time.perf_counter() - started,
    }


def parse_complex_page(
    pdf_path: Path,
    page_number: int,
    ruled_regions: list[dict[str, Any]],
    config: dict[str, Any],
    *,
    include_network: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse ruled grids precisely, then add unexplained borderless regions."""
    started = time.perf_counter()
    table_areas = []
    for region in ruled_regions:
        left, bottom, right, top = region["bbox_pdf_points_bottom_left"]
        table_areas.append(f"{left},{top},{right},{bottom}")
    lattice_tables = list(
        camelot.read_pdf(  # type: ignore[attr-defined]
            pdf_path,
            pages=str(page_number),
            flavor="lattice",
            table_areas=table_areas,
            suppress_stdout=False,
        )
    )

    unmatched_lattice = set(range(len(lattice_tables)))
    candidates: list[dict[str, Any]] = []
    region_matches = []
    for region in ruled_regions:
        region_box = region["bbox_pdf_points_bottom_left"]
        best_index = max(
            unmatched_lattice,
            key=lambda index: bbox_iou(
                region_box,
                [float(value) for value in lattice_tables[index]._bbox],
            ),
            default=None,
        )
        best_iou = (
            bbox_iou(
                region_box,
                [float(value) for value in lattice_tables[best_index]._bbox],
            )
            if best_index is not None
            else 0.0
        )
        matched = best_index is not None and best_iou >= float(config["minimum_region_match_iou"])
        region_matches.append(
            {
                "region_id": region["region_id"],
                "matched": matched,
                "matched_iou": best_iou,
            }
        )
        if not matched:
            continue
        assert best_index is not None
        unmatched_lattice.remove(best_index)
        table = lattice_tables[best_index]
        candidates.append(
            {
                "parser": "camelot_lattice",
                "parser_order": int(table.order),
                "region_id": region["region_id"],
                "table": table,
                "bbox_pdf_points_bottom_left": [float(value) for value in table._bbox],
            }
        )

    network_tables = (
        list(
            camelot.read_pdf(  # type: ignore[attr-defined]
                pdf_path,
                pages=str(page_number),
                flavor="network",
                suppress_stdout=False,
            )
        )
        if include_network
        else []
    )
    network_decisions = []
    for table in network_tables:
        box = [float(value) for value in table._bbox]
        coverage = rectangle_union_coverage(
            box,
            ruled_regions,
            float(config["render_scale"]),
        )
        retained = coverage <= float(config["maximum_network_ruling_coverage"])
        network_decisions.append(
            {
                "parser_order": int(table.order),
                "shape": [int(value) for value in table.shape],
                "ruling_rectangle_coverage": coverage,
                "retained": retained,
            }
        )
        if retained:
            candidates.append(
                {
                    "parser": "camelot_network",
                    "parser_order": int(table.order),
                    "table": table,
                    "bbox_pdf_points_bottom_left": box,
                }
            )
    return candidates, {
        "lattice_return_count": len(lattice_tables),
        "region_matches": region_matches,
        "unmatched_lattice_return_count": len(unmatched_lattice),
        "network_return_count": len(network_tables),
        "network_decisions": network_decisions,
        "wall_seconds": time.perf_counter() - started,
    }


def clean_rows(
    rows: list[list[str]],
    cleanup: dict[str, Any],
) -> tuple[list[list[str]], dict[str, Any]]:
    """Remove page furniture while preserving a rectangular native-text table."""
    footer_counter = re.compile(str(cleanup["footer_counter_pattern"]), re.IGNORECASE)
    filename = re.compile(str(cleanup["leading_filename_pattern"]), re.IGNORECASE)
    removed_footer_rows = [
        index
        for index, row in enumerate(rows)
        if footer_counter.search(" ".join(cell for cell in row if cell))
    ]
    removed_set = set(removed_footer_rows)
    retained = [row for index, row in enumerate(rows) if index not in removed_set]

    removed_filename_rows = []
    while retained:
        nonempty = [cell for cell in retained[0] if cell]
        if len(nonempty) != 1 or not filename.fullmatch(nonempty[0].lower()):
            break
        original_index = next(
            index for index, row in enumerate(rows) if row is retained[0] or row == retained[0]
        )
        removed_filename_rows.append(original_index)
        retained.pop(0)

    width = max((len(row) for row in retained), default=0)
    rectangular = [row + [""] * (width - len(row)) for row in retained]
    retained_columns = [
        column for column in range(width) if any(row[column] for row in rectangular)
    ]
    cleaned = [[row[column] for column in retained_columns] for row in rectangular]
    return cleaned, {
        "removed_footer_row_indices": removed_footer_rows,
        "removed_filename_row_indices": removed_filename_rows,
        "retained_column_indices": retained_columns,
        "effective_column_count": len(retained_columns),
    }


def header_matrix(rows: list[list[str]], cleanup: dict[str, Any]) -> list[list[str]]:
    """Return leading non-data rows as an exact native header signature."""
    header = []
    for row in rows[: int(cleanup["maximum_header_rows"])]:
        nonempty = [cell for cell in row if cell]
        numeric_fraction = (
            sum(bool(NUMERIC_CELL.fullmatch(cell)) for cell in nonempty) / len(nonempty)
            if nonempty
            else 0.0
        )
        if COORDINATE_KEY.search(" ".join(nonempty)) or (
            nonempty
            and numeric_fraction >= float(cleanup["minimum_numeric_cell_fraction_for_data_row"])
        ):
            break
        header.append(row)
    return header if any(cell for row in header for cell in row) else []


def column_type_signatures(rows: list[list[str]]) -> list[dict[str, Any]]:
    """Summarize text, numeric, explicit-missing, and empty column evidence."""
    width = max((len(row) for row in rows), default=0)
    signatures = []
    type_order = ("text", "numeric", "missing", "empty")
    for column in range(width):
        counts = {kind: 0 for kind in type_order}
        for row in rows:
            value = row[column] if column < len(row) else ""
            kind = (
                "empty"
                if not value
                else "missing"
                if MISSING_VALUE_CELL.fullmatch(value)
                else "numeric"
                if NUMERIC_CELL.fullmatch(value)
                else "text"
            )
            counts[kind] += 1
        total = len(rows)
        dominant = max(type_order, key=lambda kind: (counts[kind], -type_order.index(kind)))
        signatures.append(
            {
                "column_index": column,
                "dominant_type": dominant,
                "counts": counts,
                "fractions": {kind: counts[kind] / total if total else 0.0 for kind in type_order},
            }
        )
    return signatures


def parse_footer(text: str, cleanup: dict[str, Any]) -> dict[str, Any] | None:
    """Return the final worksheet footer found in native page text."""
    pattern = re.compile(str(cleanup["footer_pattern"]), re.IGNORECASE)
    matches = list(pattern.finditer(" ".join(text.split())))
    if not matches:
        return None
    match = matches[-1]
    return {
        "sheet_id": normalize_text(match.group("sheet")).lower(),
        "internal_page": int(match.group("page")),
        "internal_total": int(match.group("total")),
        "matched_text": match.group(0),
    }


def write_csv(path: Path, rows: list[list[str]]) -> None:
    """Write one rectangular CSV with explicit UTF-8 and newline handling."""
    with path.open("w", encoding="utf-8", newline="") as stream:
        csv.writer(stream).writerows(rows)


def serialize_cells(table: Any) -> list[dict[str, Any]]:
    """Preserve Camelot cell text and geometry for later inspection."""
    return [
        {
            "row_index": row_index,
            "column_index": column_index,
            "text": normalize_text(str(cell.text)),
            "bbox_pdf_points_bottom_left": [
                float(cell.x1),
                float(cell.y1),
                float(cell.x2),
                float(cell.y2),
            ],
        }
        for row_index, row in enumerate(table.cells)
        for column_index, cell in enumerate(row)
    ]


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
    """Extract one page, optionally omitting reproducible review images."""
    result_path = output_dir / "result.json"
    if result_path.exists():
        return dict(json.loads(result_path.read_text()))
    if output_dir.exists():
        raise FileExistsError(f"incomplete page output already exists: {output_dir}")
    output_dir.mkdir(parents=True)

    started = time.perf_counter()
    document = pdfium.PdfDocument(pdf_path)
    page = document[page_number - 1]
    page_width, page_height = (float(value) for value in page.get_size())
    text_page = page.get_textpage()
    native_text = text_page.get_text_range()
    text_page.close()
    image = (
        page.render(scale=float(detection["render_scale"]), rev_byteorder=True)
        .to_pil()
        .convert("RGB")
    )
    page.close()
    document.close()

    ruled_regions, ruling_mask = detect_ruled_regions(
        image,
        page_height,
        detection,
    )

    complex_page = len(ruled_regions) >= int(detection["complex_page_minimum_regions"])
    if route_mode == "full_page_numeric":
        route = "full_page_numeric"
        candidates, parser_evidence = parse_simple_page(pdf_path, page_number)
    elif route_mode == "layout_regions":
        if not layout_regions:
            raise ValueError("layout_regions route requires at least one table region")
        routed_regions = [
            {
                "region_id": f"layout_{index:03d}",
                "bbox_pdf_points_bottom_left": box,
            }
            for index, box in enumerate(layout_regions, start=1)
        ]
        route = "layout_regions"
        candidates, parser_evidence = parse_complex_page(
            pdf_path,
            page_number,
            routed_regions,
            detection,
            include_network=False,
        )
        if learned_fallback_runner is not None:
            candidates.extend(
                apply_learned_fallbacks(
                    runner=learned_fallback_runner,
                    pdf_path=pdf_path,
                    page_number=page_number,
                    page_size=(page_width, page_height),
                    page_output_root=output_dir,
                    parser_evidence=parser_evidence,
                    layout_regions=routed_regions,
                )
            )
    elif route_mode is not None:
        raise ValueError(f"unsupported explicit table route: {route_mode}")
    elif complex_page:
        route = "complex_segmented"
        candidates, parser_evidence = parse_complex_page(
            pdf_path,
            page_number,
            ruled_regions,
            detection,
        )
    else:
        route = "simple_stream"
        candidates, parser_evidence = parse_simple_page(pdf_path, page_number)

    candidates.sort(key=visual_order_key)
    table_root = output_dir / "tables"
    table_root.mkdir()
    table_records = []
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    colors = {
        "camelot_stream": (0, 140, 0),
        "camelot_lattice": (220, 0, 0),
        "camelot_network": (0, 80, 255),
        "tableformer_accurate": (150, 60, 180),
    }
    scale = float(detection["render_scale"])
    for index, candidate in enumerate(candidates, start=1):
        table_id = f"{table_id_prefix}_p{page_number:05d}_t{index:03d}"
        table_dir = table_root / table_id
        table_dir.mkdir()
        payload = _candidate_payload(candidate)
        raw_rows = payload.raw_rows
        cleaned_rows, cleanup_record = clean_rows(raw_rows, cleanup)
        raw_csv = table_dir / "raw.csv"
        clean_csv = table_dir / "table.csv"
        cells_path = table_dir / "cells.json"
        write_csv(raw_csv, raw_rows)
        write_csv(clean_csv, cleaned_rows)
        write_json(cells_path, payload.serialized_cells)
        box = candidate["bbox_pdf_points_bottom_left"]
        table_record = {
            "table_id": table_id,
            "physical_pdf_page": page_number,
            "page_table_index": index,
            "route": route,
            **payload.metadata,
            "shape_raw": [len(raw_rows), max((len(row) for row in raw_rows), default=0)],
            "shape_clean": [
                len(cleaned_rows),
                max((len(row) for row in cleaned_rows), default=0),
            ],
            "page_size_pdf_points": [page_width, page_height],
            "columns_pdf_points": payload.columns_pdf_points,
            "cleanup": cleanup_record,
            "header_matrix": header_matrix(cleaned_rows, cleanup),
            "raw_column_type_signatures": column_type_signatures(raw_rows),
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
        write_json(table_dir / "table.json", table_record)
        table_records.append(table_record)

        left, bottom, right, top = box
        pixel_box = (
            round(left * scale),
            round((page_height - top) * scale),
            round(right * scale),
            round((page_height - bottom) * scale),
        )
        color = colors[candidate["parser"]]
        draw.rectangle(pixel_box, outline=color, width=4)
        draw.text((pixel_box[0] + 3, pixel_box[1] + 3), table_id, fill=color)

    footer = parse_footer(native_text, cleanup)
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
    artifacts: dict[str, dict[str, str]] = {}
    if retain_review_derivatives:
        page_image_path = output_dir / "page.png"
        image.save(page_image_path, optimize=False, compress_level=9)
        ruling_mask_path = output_dir / "ruling_mask.png"
        cv2.imwrite(
            str(ruling_mask_path),
            ruling_mask,
            [cv2.IMWRITE_PNG_COMPRESSION, 9],
        )
        annotated_path = output_dir / "annotated.png"
        annotated.save(annotated_path, optimize=False, compress_level=9)
        artifacts = {
            "page_image": {
                "path": "page.png",
                "sha256": sha256_file(page_image_path),
            },
            "ruling_mask": {
                "path": "ruling_mask.png",
                "sha256": sha256_file(ruling_mask_path),
            },
            "annotated": {
                "path": "annotated.png",
                "sha256": sha256_file(annotated_path),
            },
        }
    result = {
        "schema_version": "1.0.0",
        "physical_pdf_page": page_number,
        "route": route,
        "route_requested": route_mode,
        "complex_page": complex_page,
        "page_size_pdf_points": [page_width, page_height],
        "ruling_region_count": len(ruled_regions),
        "ruled_regions": ruled_regions,
        "parser_evidence": parser_evidence,
        "table_count": len(table_records),
        "tables": table_records,
        "footer": footer,
        "footer_owner_table_id": footer_owner,
        "artifacts": artifacts,
        "wall_seconds": time.perf_counter() - started,
    }
    write_json(result_path, result)
    return result
