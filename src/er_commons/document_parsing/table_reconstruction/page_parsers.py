"""Invoke Camelot and reconcile parser returns into page candidates."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import camelot

from er_commons.document_parsing.table_reconstruction.page_content import table_rows
from er_commons.document_parsing.table_reconstruction.page_geometry import (
    bbox_iou,
    rectangle_union_coverage,
)


def is_duplicate_stream_table(candidate: Any, accepted: Any) -> bool:
    """Recognize near-identical Stream returns that differ by a leading row."""
    candidate_box = [float(value) for value in candidate._bbox]
    accepted_box = [float(value) for value in accepted._bbox]
    if bbox_iou(candidate_box, accepted_box) < 0.95:
        return False
    candidate_rows = table_rows(candidate)
    accepted_rows = table_rows(accepted)
    shorter, longer = sorted((candidate_rows, accepted_rows), key=len)
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


def _match_lattice_candidates(
    lattice_tables: list[Any],
    ruled_regions: list[dict[str, Any]],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """Match ruled regions one-to-one to sufficiently overlapping lattice returns."""
    unmatched_lattice = set(range(len(lattice_tables)))
    candidates: list[dict[str, Any]] = []
    region_matches: list[dict[str, Any]] = []
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
            bbox_iou(region_box, [float(value) for value in lattice_tables[best_index]._bbox])
            if best_index is not None
            else 0.0
        )
        matched = best_index is not None and best_iou >= float(config["minimum_region_match_iou"])
        region_matches.append(
            {"region_id": region["region_id"], "matched": matched, "matched_iou": best_iou}
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
    return candidates, region_matches, len(unmatched_lattice)


def _network_candidates(
    network_tables: list[Any],
    ruled_regions: list[dict[str, Any]],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Keep borderless candidates only when ruling rectangles do not explain them."""
    candidates: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for table in network_tables:
        box = [float(value) for value in table._bbox]
        coverage = rectangle_union_coverage(box, ruled_regions, float(config["render_scale"]))
        retained = coverage <= float(config["maximum_network_ruling_coverage"])
        decisions.append(
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
    return candidates, decisions


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
    candidates, region_matches, unmatched_count = _match_lattice_candidates(
        lattice_tables, ruled_regions, config
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
    retained_network, network_decisions = _network_candidates(network_tables, ruled_regions, config)
    candidates.extend(retained_network)
    return candidates, {
        "lattice_return_count": len(lattice_tables),
        "region_matches": region_matches,
        "unmatched_lattice_return_count": unmatched_count,
        "network_return_count": len(network_tables),
        "network_decisions": network_decisions,
        "wall_seconds": time.perf_counter() - started,
    }
