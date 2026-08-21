from types import SimpleNamespace
from typing import Any, cast

import pytest

from er_commons.chunked_conversion.range_contract import PageInterval
from er_commons.chunked_conversion.runtime.aggregate import (
    collect_warning_evidence,
    core_alignment_records,
    raster_memory_evidence,
)
from er_commons.chunked_conversion.runtime.diagnostics import ChunkedConversionError
from er_commons.chunked_conversion.runtime.range_store import VerifiedConvertedRange


def _child(
    range_id: str,
    core: tuple[int, int],
    alignment_pages: tuple[dict[str, Any], ...],
    warnings: tuple[str, ...] = (),
) -> VerifiedConvertedRange:
    planned = SimpleNamespace(
        range_id=range_id,
        core=PageInterval(start=core[0], end=core[1]),
    )
    return cast(
        VerifiedConvertedRange,
        SimpleNamespace(
            planned=planned,
            alignment_pages=alignment_pages,
            warnings=warnings,
        ),
    )


def test_alignment_emits_core_rows_once_after_exact_overlap_comparison() -> None:
    page1 = {"page_no": 1, "cells": ["one"]}
    page2 = {"page_no": 2, "cells": ["shared"]}
    page3 = {"page_no": 3, "cells": ["three"]}
    children = (
        _child("left", (1, 1), (page1, page2)),
        _child("right", (2, 3), (page2.copy(), page3)),
    )

    assert core_alignment_records(children) == (page1, page2, page3)


def test_alignment_rejects_overlap_row_drift_with_range_provenance() -> None:
    children = (
        _child("left", (1, 1), ({"page_no": 1}, {"page_no": 2, "value": "left"})),
        _child("right", (2, 2), ({"page_no": 2, "value": "right"},)),
    )

    with pytest.raises(ChunkedConversionError, match="alignment_overlap") as captured:
        core_alignment_records(children)

    assert captured.value.expected == {
        "range_id": "left",
        "record": {"page_no": 2, "value": "left"},
    }
    assert captured.value.actual == {
        "range_id": "right",
        "record": {"page_no": 2, "value": "right"},
    }


def test_warning_evidence_preserves_child_then_global_order_and_duplicates() -> None:
    children = (
        _child("left", (1, 1), ({"page_no": 1},), ("shared", "left-only")),
        _child("right", (2, 2), ({"page_no": 2},), ("shared",)),
    )

    combined, evidence = collect_warning_evidence(children, ("global",))

    assert combined == ("shared", "left-only", "shared", "global")
    assert evidence == {
        "child_ranges": [
            {"range_id": "left", "warnings": ["shared", "left-only"]},
            {"range_id": "right", "warnings": ["shared"]},
        ],
        "global": ["global"],
        "child_warning_count": 3,
        "global_warning_count": 1,
        "combined_warning_count": 4,
        "combined_order": "range-plan order, then global interpretation",
    }


def test_raster_memory_evidence_reports_single_page_asset_decoding() -> None:
    assert raster_memory_evidence(has_assets=True) == {
        "range_page_rasters": "verified_path_backed_png",
        "all_page_png_bytes_materialized": False,
        "global_interpretation_decoded_page_rasters": 0,
        "asset_crop_peak_decoded_page_rasters": 1,
    }
