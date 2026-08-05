"""Geometry, hierarchy, text, and table-content policies."""

from __future__ import annotations

import unicodedata
from collections import Counter

from er_commons.canonical_extraction.bundle import BundleView, Record, regions
from er_commons.canonical_extraction.errors import ContractError

CANONICAL_CONTENT_COLLECTIONS = ("blocks", "tables", "figures")


def regions_match_their_pages(view: BundleView) -> None:
    """Require bounded regions expressed against their declared page size."""
    for record in view.records:
        for region in regions(record):
            _validate_region(view, region)


def _validate_region(view: BundleView, region: Record) -> None:
    left, lower, right, upper = region["bbox"]
    width = region["page_width"]
    height = region["page_height"]
    if not (0 <= left < right <= width and 0 <= lower < upper <= height):
        raise ContractError(f"out-of-bounds region on {region['page_id']}")

    page = view.pages_by_id[region["page_id"]]
    if region["units"] == "pdf_points":
        expected_width = page["width_pdf_points"]
        expected_height = page["height_pdf_points"]
    else:
        scale = region["render_scale"]
        if scale is None:
            raise ContractError("pixel region is missing render scale")
        expected_width = page["width_pdf_points"] * scale
        expected_height = page["height_pdf_points"] * scale
    if (width, height) != (expected_width, expected_height):
        raise ContractError(f"region page geometry mismatch on {region['page_id']}")


def section_hierarchy_is_consistent(view: BundleView) -> None:
    """Reject cycles and require each section to list its direct children."""
    parent_by_section = {
        section["id"]: section["parent_section_id"] for section in view.bundle["sections"]
    }
    for section_id in parent_by_section:
        seen = {section_id}
        parent_id = parent_by_section[section_id]
        while parent_id is not None:
            if parent_id in seen:
                raise ContractError(f"section hierarchy cycle at {section_id}")
            seen.add(parent_id)
            parent_id = parent_by_section[parent_id]

    for section in view.bundle["sections"]:
        section_id = section["id"]
        actual_children = {
            child["id"]
            for child in view.from_collections("sections", "blocks", "tables", "figures")
            if (
                child.get("parent_section_id") == section_id
                or child.get("section_id") == section_id
            )
        }
        if set(section["ordered_child_ids"]) != actual_children:
            raise ContractError(f"section children differ for {section_id}")


def table_families_are_consistent(view: BundleView) -> None:
    """Require symmetric, complete family membership for full documents."""
    family_records = view.bundle["table_families"]
    member_counts = Counter(
        table_id for family in family_records for table_id in family["member_table_ids"]
    )
    family_id_by_table = {
        table_id: family["id"]
        for family in family_records
        for table_id in family["member_table_ids"]
    }

    for document in view.bundle["documents"]:
        document_id = document["id"]
        document_tables = [
            table for table in view.bundle["tables"] if table["document_id"] == document_id
        ]
        document_family_ids = {
            family["id"] for family in family_records if family["document_id"] == document_id
        }
        if not document["document_scope_complete"]:
            if document_family_ids or any(table["table_family_id"] for table in document_tables):
                raise ContractError("partial document emitted finalized table families")
            continue

        for table in document_tables:
            table_id = table["id"]
            if member_counts[table_id] != 1:
                raise ContractError(f"table is not assigned exactly once: {table_id}")
            if table["table_family_id"] not in document_family_ids:
                raise ContractError(f"table has unknown family: {table_id}")
            if family_id_by_table[table_id] != table["table_family_id"]:
                raise ContractError(f"table family membership differs: {table_id}")


def table_shapes_are_complete(view: BundleView) -> None:
    """Require nonoverlapping logical cells to cover every declared grid position."""
    for table in view.bundle["tables"]:
        row_count, column_count = table["shape"]
        covered: set[tuple[int, int]] = set()
        for cell in table["cells"]:
            start_row = cell["row_index"]
            start_column = cell["column_index"]
            end_row = cell.get("end_row_offset_idx", start_row + 1)
            end_column = cell.get("end_column_offset_idx", start_column + 1)
            if not (
                0 <= start_row < end_row <= row_count
                and 0 <= start_column < end_column <= column_count
                and cell.get("row_span", end_row - start_row) == end_row - start_row
                and cell.get("column_span", end_column - start_column) == end_column - start_column
            ):
                raise ContractError(f"cell is outside declared shape in {table['id']}")
            positions = {
                (row, column)
                for row in range(start_row, end_row)
                for column in range(start_column, end_column)
            }
            if covered & positions:
                raise ContractError(f"overlapping cell position in {table['id']}")
            covered |= positions
        expected = {(row, column) for row in range(row_count) for column in range(column_count)}
        if covered != expected:
            raise ContractError(f"cell count differs from declared shape coverage in {table['id']}")


def table_stage_mappings_are_consistent(view: BundleView) -> None:
    """Represent zero, one, and many table mappings without ambiguity."""
    for observation in view.bundle["table_stage_observations"]:
        table_ids = observation["canonical_table_ids"]
        reason = observation["unmapped_reason"]
        if not table_ids and not reason:
            raise ContractError("zero-table mapping requires an unmapped reason")
        if table_ids and reason is not None:
            raise ContractError("mapped table observation cannot have an unmapped reason")
        if len(table_ids) != len(set(table_ids)):
            raise ContractError("table observation merged duplicate table IDs")


def canonical_text_is_explainable(view: BundleView) -> None:
    """Allow only the lossless normalization operations declared by a block."""
    for block in view.bundle["blocks"]:
        expected = block["raw_text"]
        operations = block["normalization_operations"]
        if operations != ["none"]:
            if "unicode_nfc" in operations:
                expected = unicodedata.normalize("NFC", expected)
            if "line_ending_lf" in operations:
                expected = expected.replace("\r\n", "\n").replace("\r", "\n")
        if block["canonical_text"] != expected:
            raise ContractError(f"unexplained canonical text change in {block['id']}")


def page_content_lists_are_complete(view: BundleView) -> None:
    """Match each page's reading-order list to spatial content on that page."""
    for page in view.bundle["pages"]:
        page_id = page["id"]
        actual_content_ids = {
            record["id"]
            for record in view.from_collections(*CANONICAL_CONTENT_COLLECTIONS)
            if page_id in {region["page_id"] for region in record["regions"]}
        }
        if set(page["ordered_content_ids"]) != actual_content_ids:
            raise ContractError(f"page content differs for {page_id}")
