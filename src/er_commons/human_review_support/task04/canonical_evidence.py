"""Read canonical page, text, table, and family evidence for Task 04."""

from __future__ import annotations

import re
from pathlib import Path
from typing import cast

from er_commons.document_parsing.content_parsing.routing_geometry import DisplayedPageTransform
from er_commons.human_review_support.task04.geometry import (
    bboxes_overlap,
    canonical_region_display_bbox,
    parse_bbox,
    source_page_transforms,
)
from er_commons.human_review_support.task04.json_io import (
    read_jsonl_objects,
    require_list,
    require_mapping,
    require_string,
)
from er_commons.human_review_support.task04.models import (
    BlockEvidence,
    JsonValue,
    PageEvidence,
    PageProfile,
    TableEvidence,
    TableFamilyCandidate,
)

PAGE_ID_RE = re.compile(r"/page/[^/]+/p(\d+)$")
CHAPTER_RE = re.compile(r"^CHAPTER\s+(\d+)\b", re.IGNORECASE)
TABLE_POINTER_RE = re.compile(r"#/tables/(\d+)")


def canonical_files(candidate: Path) -> dict[str, Path]:
    """Resolve expected canonical files beneath one complete candidate."""
    canonical_roots = sorted(candidate.rglob("canonical"))
    if len(canonical_roots) != 1:
        raise ValueError(
            f"expected exactly one canonical directory below {candidate}; "
            f"found {len(canonical_roots)}"
        )
    canonical = canonical_roots[0]
    return {
        name: canonical / name
        for name in (
            "pages.jsonl",
            "blocks.jsonl",
            "sections.jsonl",
            "tables.jsonl",
            "table_families.jsonl",
        )
        if (canonical / name).is_file()
    }


def page_number(page_id: str) -> int:
    """Extract a physical page number from a canonical page identity."""
    match = PAGE_ID_RE.search(page_id)
    if match is None:
        raise ValueError(f"canonical page ID has no physical page: {page_id}")
    return int(match.group(1))


def page_rows(candidate: Path) -> list[dict[str, JsonValue]]:
    """Load canonical pages in physical order, requiring page evidence."""
    path = canonical_files(candidate).get("pages.jsonl")
    if path is None:
        raise ValueError(f"candidate has no canonical pages.jsonl: {candidate}")
    rows = read_jsonl_objects(path)
    return sorted(rows, key=lambda row: _physical_page(row, path))


def page_profiles(candidate: Path) -> dict[int, PageProfile]:
    """Summarize reviewable page content without retaining full record payloads."""
    files = canonical_files(candidate)
    counters = {
        _physical_page(row, files["pages.jsonl"]): _empty_profile() for row in page_rows(candidate)
    }
    if "blocks.jsonl" in files:
        _count_blocks(files["blocks.jsonl"], counters)
    if "tables.jsonl" in files:
        _count_tables(files["tables.jsonl"], counters)
    return {page: PageProfile(physical_page=page, **values) for page, values in counters.items()}


def _empty_profile() -> dict[str, int]:
    """Create mutable counters for one page profile."""
    return {
        "body_text_chars": 0,
        "body_block_count": 0,
        "heading_count": 0,
        "list_item_count": 0,
        "table_count": 0,
        "table_text_chars": 0,
    }


def _count_blocks(path: Path, counters: dict[int, dict[str, int]]) -> None:
    """Accumulate non-furniture block content into page profiles."""
    for index, block in enumerate(read_jsonl_objects(path)):
        block_type = str(block.get("block_type") or "other")
        if block_type in {"page_header", "page_footer"}:
            continue
        text = str(block.get("canonical_text") or block.get("raw_text") or "").strip()
        for page in _record_pages(block, path=f"{path}:{index + 1}.regions"):
            profile = counters.setdefault(page, _empty_profile())
            profile["body_text_chars"] += len(text)
            profile["body_block_count"] += 1
            profile["heading_count"] += int(block_type == "heading")
            profile["list_item_count"] += int(block_type == "list_item")


def _count_tables(path: Path, counters: dict[int, dict[str, int]]) -> None:
    """Accumulate canonical table content into page profiles."""
    for index, table in enumerate(read_jsonl_objects(path)):
        cells = require_list(table.get("cells", []), path=f"{path}:{index + 1}.cells")
        cell_chars = sum(
            len(str(require_mapping(cell, path="table.cells[]").get("text") or ""))
            for cell in cells
        )
        for page in _record_pages(table, path=f"{path}:{index + 1}.regions"):
            if page not in counters:
                raise ValueError(f"table at {path}:{index + 1} references undeclared page {page}")
            counters[page]["table_count"] += 1
            counters[page]["table_text_chars"] += cell_chars


def page_review_evidence(
    candidate: Path, selected_pages: set[int], source_pdf: Path
) -> dict[int, PageEvidence]:
    """Load ordered block, table, and display geometry for selected pages."""
    files = canonical_files(candidate)
    transforms = source_page_transforms(source_pdf, selected_pages)
    page_data, order_by_page = _selected_page_shells(candidate, selected_pages)
    _load_selected_blocks(files, page_data, transforms)
    _load_selected_tables(files, page_data)
    rotated_pages = {page for page, transform in transforms.items() if transform.rotation_degrees}
    return _finalize_page_evidence(page_data, order_by_page, rotated_pages)


def _selected_page_shells(
    candidate: Path, selected_pages: set[int]
) -> tuple[dict[int, dict[str, object]], dict[int, dict[str, int]]]:
    """Create typed-ready page shells and reading-order indexes."""
    pages: dict[int, dict[str, object]] = {}
    orders: dict[int, dict[str, int]] = {}
    for row in page_rows(candidate):
        physical_page = _required_int(
            row.get("physical_page_number"), path="pages.physical_page_number"
        )
        if physical_page not in selected_pages:
            continue
        pages[physical_page] = {
            "width": _required_float(row.get("width_pdf_points"), path="pages.width"),
            "height": _required_float(row.get("height_pdf_points"), path="pages.height"),
            "printed_page_label": (
                str(row["printed_page_label"])
                if row.get("printed_page_label") is not None
                else None
            ),
            "blocks": [],
            "tables": [],
        }
        ordered_ids = require_list(
            row.get("ordered_content_ids", []), path=f"page {physical_page}.ordered_content_ids"
        )
        orders[physical_page] = {
            str(content_id): index for index, content_id in enumerate(ordered_ids)
        }
    missing = selected_pages - pages.keys()
    if missing:
        raise ValueError(f"selected pages absent from candidate {candidate}: {sorted(missing)}")
    return pages, orders


def _load_selected_blocks(
    files: dict[str, Path],
    pages: dict[int, dict[str, object]],
    transforms: dict[int, DisplayedPageTransform],
) -> None:
    """Attach selected canonical text records to page shells."""
    path = files.get("blocks.jsonl")
    if path is None:
        return
    for index, block in enumerate(read_jsonl_objects(path)):
        text = str(block.get("canonical_text") or block.get("raw_text") or "").strip()
        for region in _regions(block, path=f"{path}:{index + 1}.regions"):
            page_id = require_string(region.get("page_id"), path=f"{path}:{index + 1}.page_id")
            page = page_number(page_id)
            if page not in pages:
                continue
            page_blocks = cast(list[object], pages[page]["blocks"])
            page_blocks.append(
                {
                    "id": require_string(block.get("id"), path=f"{path}:{index + 1}.id"),
                    "block_type": str(block.get("block_type") or "other"),
                    "text": text,
                    "bbox": canonical_region_display_bbox(
                        region,
                        _required_float(pages[page]["width"], path="page.width"),
                        _required_float(pages[page]["height"], path="page.height"),
                        transforms.get(page),
                    ),
                    "sequence": block.get("sequence"),
                }
            )


def _load_selected_tables(files: dict[str, Path], pages: dict[int, dict[str, object]]) -> None:
    """Attach selected canonical tables to page shells."""
    path = files.get("tables.jsonl")
    if path is None:
        return
    for index, table in enumerate(read_jsonl_objects(path)):
        for region in _regions(table, path=f"{path}:{index + 1}.regions"):
            page_id = require_string(region.get("page_id"), path=f"{path}:{index + 1}.page_id")
            page = page_number(page_id)
            if page not in pages:
                continue
            page_tables = cast(list[object], pages[page]["tables"])
            page_tables.append(
                {
                    "id": require_string(table.get("id"), path=f"{path}:{index + 1}.id"),
                    "table_family_id": table.get("table_family_id"),
                    "parser": table.get("parser"),
                    "shape": table.get("shape", []),
                    "cells": table.get("cells", []),
                    "bbox": parse_bbox(region.get("bbox")),
                    "sequence": table.get("sequence"),
                }
            )


def _finalize_page_evidence(
    pages: dict[int, dict[str, object]],
    orders: dict[int, dict[str, int]],
    rotated_pages: set[int],
) -> dict[int, PageEvidence]:
    """Convert mutable page shells into immutable presentation models."""
    result: dict[int, PageEvidence] = {}
    for page, value in pages.items():
        order = orders[page]
        block_rows = cast(list[dict[str, object]], value["blocks"])
        table_rows = cast(list[dict[str, object]], value["tables"])
        block_rows.sort(key=lambda row: _content_order(row, order))
        table_rows.sort(key=lambda row: _content_order(row, order))
        tables = tuple(_table_evidence(row) for row in table_rows)
        table_boxes = [table.bbox for table in tables]
        blocks = tuple(_block_evidence(row, table_boxes) for row in block_rows)
        result[page] = PageEvidence(
            physical_page=page,
            width=_required_float(value["width"], path=f"page {page}.width"),
            height=_required_float(value["height"], path=f"page {page}.height"),
            printed_page_label=(
                str(value["printed_page_label"])
                if value["printed_page_label"] is not None
                else None
            ),
            blocks=blocks,
            tables=tables,
            geometry_note=(
                "Text boxes aligned using the source PDF page rotation; table boxes were "
                "already recorded in displayed-page coordinates."
                if page in rotated_pages
                else None
            ),
        )
    return result


def _block_evidence(
    row: dict[str, object], table_boxes: list[tuple[float, float, float, float] | None]
) -> BlockEvidence:
    """Build one immutable block and its table-overlap flag."""
    bbox = parse_bbox(row.get("bbox"))
    return BlockEvidence(
        identifier=str(row["id"]),
        block_type=str(row["block_type"]),
        text=str(row["text"]),
        bbox=bbox,
        sequence=_optional_int(row.get("sequence")),
        overlaps_table=any(bboxes_overlap(bbox, table_bbox) for table_bbox in table_boxes),
    )


def _table_evidence(row: dict[str, object]) -> TableEvidence:
    """Build one immutable table presentation record."""
    cells = require_list(row.get("cells", []), path="table.cells")
    shape = require_list(row.get("shape", []), path="table.shape")
    return TableEvidence(
        identifier=str(row["id"]),
        table_family_id=str(row["table_family_id"]) if row.get("table_family_id") else None,
        parser=str(row["parser"]) if row.get("parser") else None,
        shape=tuple(_required_int(value, path="table.shape[]") for value in shape),
        cells=tuple(require_mapping(cell, path="table.cells[]") for cell in cells),
        bbox=parse_bbox(row.get("bbox")),
        sequence=_optional_int(row.get("sequence")),
    )


def chapter_pages(candidate: Path) -> dict[int, str]:
    """Find one physical page for each major numbered main-report chapter."""
    path = canonical_files(candidate).get("blocks.jsonl")
    if path is None:
        return {}
    result: dict[int, str] = {}
    for index, block in enumerate(read_jsonl_objects(path)):
        text = str(block.get("canonical_text") or "").strip()
        match = CHAPTER_RE.match(text) if block.get("block_type") == "heading" else None
        if match is None:
            continue
        for page in _record_pages(block, path=f"{path}:{index + 1}.regions"):
            result.setdefault(page, f"chapter_{match.group(1)}")
    return result


def table_candidates(
    candidate: Path, source_id: str
) -> tuple[list[TableFamilyCandidate], dict[str, list[int]]]:
    """Build table-family summaries and physical-page anchors."""
    files = canonical_files(candidate)
    tables_path = files.get("tables.jsonl")
    families_path = files.get("table_families.jsonl")
    if tables_path is None or families_path is None:
        return [], {}
    tables = {str(row["id"]): row for row in read_jsonl_objects(tables_path)}
    candidates: list[TableFamilyCandidate] = []
    family_pages: dict[str, list[int]] = {}
    for index, family in enumerate(read_jsonl_objects(families_path)):
        family_id = require_string(family.get("id"), path=f"{families_path}:{index + 1}.id")
        members = require_list(
            family.get("member_table_ids", []),
            path=f"{families_path}:{index + 1}.member_table_ids",
        )
        pages = {
            page
            for table_id in members
            for page in _record_pages(
                tables.get(str(table_id), {}), path=f"table family {family_id}"
            )
        }
        if not pages:
            continue
        family_pages[family_id] = sorted(pages)
        candidates.append(TableFamilyCandidate(source_id, family_id, len(pages), len(members)))
    return candidates, family_pages


def table_index_pages(candidate: Path) -> dict[int, int]:
    """Map producer table-pointer indexes to physical pages."""
    canonical = next(iter(canonical_files(candidate).values())).parent
    observations = canonical.parent / "observations" / "table_stage.jsonl"
    if not observations.is_file():
        return {}
    result: dict[int, int] = {}
    for index, observation in enumerate(read_jsonl_objects(observations)):
        link = observation.get("source_region_raw_link")
        pointer = (
            require_mapping(link, path=f"{observations}:{index + 1}.link").get("object_pointer")
            if isinstance(link, dict)
            else None
        )
        match = TABLE_POINTER_RE.fullmatch(str(pointer or ""))
        page_id = observation.get("page_id")
        if match is not None and isinstance(page_id, str):
            result.setdefault(int(match.group(1)), page_number(page_id))
    return result


def _record_pages(record: dict[str, JsonValue], *, path: str) -> set[int]:
    """Return unique physical pages from one canonical record's regions."""
    pages: set[int] = set()
    for region in _regions(record, path=path):
        page_id = region.get("page_id")
        if isinstance(page_id, str):
            pages.add(page_number(page_id))
    return pages


def _regions(record: dict[str, JsonValue], *, path: str) -> list[dict[str, JsonValue]]:
    """Narrow a canonical regions array to JSON objects."""
    return [
        require_mapping(region, path=f"{path}[]")
        for region in require_list(record.get("regions", []), path=path)
    ]


def _physical_page(row: dict[str, JsonValue], path: Path) -> int:
    """Read one positive physical page field."""
    value = row.get("physical_page_number")
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"invalid physical_page_number in {path}: {value!r}")
    return value


def _content_order(row: dict[str, object], order: dict[str, int]) -> tuple[int, int]:
    """Sort page content by canonical order, then stable sequence."""
    return order.get(str(row.get("id")), 10**9), _optional_int(row.get("sequence")) or 0


def _optional_int(value: object) -> int | None:
    """Narrow optional sequence metadata."""
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _required_int(value: object, *, path: str) -> int:
    """Narrow a required integer field at the canonical artifact boundary."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"expected integer at {path}, found {value!r}")
    return value


def _required_float(value: object, *, path: str) -> float:
    """Narrow a required numeric field at the canonical artifact boundary."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"expected number at {path}, found {value!r}")
    return float(value)


__all__ = [
    "chapter_pages",
    "page_number",
    "page_profiles",
    "page_review_evidence",
    "table_candidates",
    "table_index_pages",
]
