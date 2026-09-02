"""Record-mapping tests for unchanged valid and rejected invalid provenance."""

from __future__ import annotations

import math

import pytest

from er_commons.document_records.record_mapping.errors import MappingContractError
from er_commons.document_records.record_mapping.provenance import (
    clipped_table_region,
    project_regions,
    table_region,
)


def test_table_region_clips_only_small_extractor_rounding_overflow() -> None:
    region = table_region(
        [429.32, 713.98, 1181.26, 792.9],
        physical_page=855,
        page_ids={855: "page-855"},
        page_sizes={855: (1224.0, 792.0)},
    )

    assert region["bbox"] == [429.32, 713.98, 1181.26, 792.0]


@pytest.mark.parametrize(
    "bbox",
    [
        [-2.0, 10.0, 40.0, 50.0],
        [10.0, 10.0, 102.0, 50.0],
        [10.0, 50.0, 40.0, 10.0],
        [10.0, 10.0, math.inf, 50.0],
    ],
)
def test_table_region_rejects_invalid_or_materially_out_of_bounds_geometry(
    bbox: list[float],
) -> None:
    with pytest.raises(MappingContractError):
        table_region(
            bbox,
            physical_page=1,
            page_ids={1: "page-1"},
            page_sizes={1: (100.0, 100.0)},
        )


def test_clipped_table_region_bounds_materially_overflowing_geometry() -> None:
    region = clipped_table_region(
        [429.32, 713.98, 1181.26, 807.59],
        physical_page=855,
        page_ids={855: "page-855"},
        page_sizes={855: (1224.0, 792.0)},
    )

    assert region["page_id"] == "page-855"
    assert region["bbox"] == [429.32, 713.98, 1181.26, 792.0]


def test_multi_region_provenance_is_preserved_without_clamping() -> None:
    item = {
        "prov": [
            {
                "page_no": 1,
                "bbox": {"l": 10.0, "b": 20.0, "r": 30.0, "t": 40.0},
            },
            {
                "page_no": 2,
                "bbox": {"l": 5.0, "b": 6.0, "r": 15.0, "t": 16.0},
            },
        ]
    }

    projection = project_regions(
        item=item,
        pointer="#/texts/0",
        page_ids={1: "page-1", 2: "page-2"},
        page_sizes={1: (100.0, 100.0), 2: (50.0, 50.0)},
    )

    assert [region["bbox"] for region in projection.regions] == [
        [10.0, 20.0, 30.0, 40.0],
        [5.0, 6.0, 15.0, 16.0],
    ]
    assert projection.rejected == ()


def test_invalid_provenance_is_omitted_and_accounted_verbatim() -> None:
    raw_provenance = {
        "page_no": 1,
        "bbox": {"l": 10.0, "b": 90.0, "r": 30.0, "t": 110.0},
        "charspan": [2, 5],
    }

    projection = project_regions(
        item={"prov": [raw_provenance]},
        pointer="#/texts/9",
        page_ids={1: "page-1"},
        page_sizes={1: (100.0, 100.0)},
    )

    assert projection.regions == ()
    assert list(projection.rejected) == [
        {
            "raw_object_pointer": "#/texts/9",
            "provenance_index": 0,
            "rejection_reason": "out_of_page_bounds",
            "raw_provenance": raw_provenance,
        }
    ]
