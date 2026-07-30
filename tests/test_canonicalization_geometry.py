"""Canonicalization tests for unchanged valid and rejected invalid provenance."""

from __future__ import annotations

from er_commons.canonical_extraction.provenance import project_regions


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
