"""Schema contracts for the Task 04C text-based effective TOC view."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

SCHEMA_ROOT = Path(__file__).parents[1] / "benchmarks/er_bench/schemas/navigation_overlay/v1/gate_c"
LINK_VIEW_ID = "navlinkv1-" + "1" * 64
SEMANTIC_VIEW_ID = "navsemanticv1-" + "2" * 64
OVERLAY_PLAN_ID = "navoverlayplanv1-" + "3" * 64
ENTRY_ID = "navtocentryv1-" + "4" * 24
PAGE_ID = "navtocpagev1-" + "5" * 24
RECONCILIATION_ID = "navtocentryrecv1-" + "6" * 24
LINK_ID = "navlinkentryv1-" + "7" * 24


def _validator(filename: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_ROOT / filename).read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _bbox() -> dict[str, object]:
    return {"l": 1.0, "t": 2.0, "r": 3.0, "b": 4.0, "coord_origin": "TOPLEFT"}


def _artifact(path: str, digest: str = "a" * 64) -> dict[str, object]:
    return {"path": path, "byte_size": 123, "sha256": digest}


def _page() -> dict[str, Any]:
    return {
        "schema_version": "er_commons.navigation_overlay.v1.toc_text_page",
        "link_view_id": LINK_VIEW_ID,
        "semantic_view_id": SEMANTIC_VIEW_ID,
        "overlay_plan_id": OVERLAY_PLAN_ID,
        "toc_text_page_id": PAGE_ID,
        "source_id": "deir_main",
        "candidate_id": "docv1-" + "8" * 64,
        "source_page_id": "deir_main/page/p000011",
        "physical_page": 11,
        "source_table_id": "deir_main/table/tbl000001",
        "table_disposition_id": "navdispv1-" + "9" * 24,
        "representation": "docling_text_supersedes_canonical_table_for_effective_navigation_view",
        "parser_version": "docling_toc_text_v1",
        "raw_docling_evidence": {
            "plan_id": "dplan1-example",
            "range_id": "drange1-example",
            "candidate_identity": _artifact("records/document_identity.json"),
            "stable_content_completion": _artifact("stable/records/completion_record.json"),
            "stable_content_inventory": _artifact("stable/records/artifact_inventory.json"),
            "conversion_input": _artifact("stable/records/conversion_input.json"),
            "conversion_completion": _artifact("conversion/records/completion_record.json"),
            "conversion_inventory": _artifact("conversion/records/artifact_inventory.json"),
            "aggregate_observation": _artifact("conversion/records/aggregate_observation.json"),
            "range_completion": _artifact("range/records/completion_record.json"),
            "range_inventory": _artifact("range/records/artifact_inventory.json"),
            "page_record": _artifact("range/pages/p00011.json"),
            "document_index_element_id": 0,
            "document_index_bbox": _bbox(),
            "cell_count": 3,
        },
        "lines": [
            {
                "line_index": 0,
                "text": "4.2.1 Soil 38",
                "bbox": [1.0, 2.0, 3.0, 4.0],
                "cell_indices": [0, 1, 2],
            }
        ],
        "entry_ids": [ENTRY_ID],
        "model_text": "4.2.1 Soil 38",
        "warnings": [],
    }


def _entry() -> dict[str, Any]:
    return {
        "schema_version": "er_commons.navigation_overlay.v1.toc_text_entry",
        "link_view_id": LINK_VIEW_ID,
        "semantic_view_id": SEMANTIC_VIEW_ID,
        "overlay_plan_id": OVERLAY_PLAN_ID,
        "toc_text_entry_id": ENTRY_ID,
        "toc_text_page_id": PAGE_ID,
        "source_id": "deir_main",
        "candidate_id": "docv1-" + "8" * 64,
        "source_page_id": "deir_main/page/p000011",
        "physical_page": 11,
        "source_table_id": "deir_main/table/tbl000001",
        "table_disposition_id": "navdispv1-" + "9" * 24,
        "entry_index": 0,
        "entry_locator": {
            "line_start": 0,
            "line_end": 0,
            "source_cell_indices": [0, 1, 2],
            "source_cell_text_sha256": "b" * 64,
        },
        "raw_lines": ["4.2.1 Soil ........ 38"],
        "raw_text": "4.2.1 Soil ........ 38",
        "model_text": "4.2.1 Soil 38",
        "marker_kind": "section",
        "raw_marker": "4.2.1",
        "normalized_marker": "4.2.1",
        "terminal_destination_token": "38",
        "parser_version": "docling_toc_text_v1",
        "warnings": [],
    }


def _reconciliation() -> dict[str, Any]:
    return {
        "schema_version": "er_commons.navigation_overlay.v1.toc_entry_reconciliation",
        "link_view_id": LINK_VIEW_ID,
        "semantic_view_id": SEMANTIC_VIEW_ID,
        "overlay_plan_id": OVERLAY_PLAN_ID,
        "reconciliation_id": RECONCILIATION_ID,
        "toc_text_entry_id": ENTRY_ID,
        "source_id": "deir_main",
        "candidate_id": "docv1-" + "8" * 64,
        "source_page_id": "deir_main/page/p000011",
        "physical_page": 11,
        "entry_locator": {
            "toc_text_page_id": PAGE_ID,
            "entry_index": 0,
            "entry_text_sha256": "c" * 64,
        },
        "raw_entry_text": "4.2.1 Soil ........ 38",
        "normalized_entry_text": "4.2.1 soil ........ 38",
        "supported_marker_count": 1,
        "marker_kind": "section",
        "raw_marker": "4.2.1",
        "normalized_marker": "4.2.1",
        "marker_normalization_rule": (
            "sealed_ascii_whitespace_casefold_then_trim_spaces_around_literal_dots_only"
        ),
        "terminal_destination_token": "38",
        "target_alias_ids": ["alias-1"],
        "selected_target_alias_ids": ["alias-1"],
        "distinct_target_ids": ["section-1"],
        "target_alias_count": 1,
        "page_consistent_target_ids": ["section-1"],
        "page_disambiguation_applied": False,
        "destination_page_alias_ids": ["page-alias-1"],
        "distinct_destination_page_ids": ["page-38"],
        "destination_page_count": 1,
        "target_physical_page_ids": ["page-38"],
        "entry_outcome": "resolved_unique",
        "link_overlay_id": LINK_ID,
    }


def test_text_page_and_entry_schemas_require_the_effective_text_view() -> None:
    page_validator = _validator("toc_text_page_row.schema.json")
    entry_validator = _validator("toc_text_entry_row.schema.json")
    assert not list(page_validator.iter_errors(_page()))
    assert not list(entry_validator.iter_errors(_entry()))

    legacy_page = _page()
    legacy_page["canonical_table_rows"] = []
    assert list(page_validator.iter_errors(legacy_page))

    table_representation = _page()
    table_representation["representation"] = "canonical_table_rows"
    assert list(page_validator.iter_errors(table_representation))


def test_entry_reconciliation_is_keyed_to_the_text_entry() -> None:
    validator = _validator("toc_entry_reconciliation_row.schema.json")
    assert not list(validator.iter_errors(_reconciliation()))

    legacy = _reconciliation()
    legacy["row_locator"] = {"row_index": 0}
    assert list(validator.iter_errors(legacy))


def test_link_overlay_references_a_text_entry_not_a_table_row() -> None:
    validator = _validator("link_overlay_row.schema.json")
    link = {
        "schema_version": "er_commons.navigation_overlay.v1.link_overlay",
        "link_view_id": LINK_VIEW_ID,
        "semantic_view_id": SEMANTIC_VIEW_ID,
        "link_overlay_id": LINK_ID,
        "reconciliation_id": RECONCILIATION_ID,
        "source_toc_entry_id": ENTRY_ID,
        "source_id": "deir_main",
        "candidate_id": "docv1-" + "8" * 64,
        "operation": "add",
        "normalized_marker": "4.2.1",
        "terminal_destination_token": "38",
        "existing_body_alias_id": "alias-1",
        "target_id": "section-1",
        "target_page_id": "page-38",
        "destination_page_alias_ids": ["page-alias-1"],
        "resolution_method": "existing_unique_body_alias_and_independent_printed_page_agreement",
    }
    assert not list(validator.iter_errors(link))

    legacy = dict(link, row_index=0, ordered_cell_values_sha256="d" * 64)
    assert list(validator.iter_errors(legacy))
