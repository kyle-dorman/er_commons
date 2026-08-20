"""Behavior tests for full-G1 compact range evidence and planning."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image

from er_commons.artifact_io import read_json_object, write_json_atomic
from er_commons.chunked_conversion.gate_b import CapturedRange, PageEvidence
from er_commons.chunked_conversion.gate_c import (
    compact_page_evidence,
    g1_core_intervals,
    raster_from_evidence,
    read_page_evidence,
    restore_global_page,
    select_full_core_pages,
    write_page_evidence,
)
from er_commons.chunked_conversion.range_contract import PageInterval


def _page(page_no: int, *, text: str | None = None) -> PageEvidence:
    image = Image.new("RGB", (2, 2), (page_no % 255, 2, 3))
    import hashlib
    import io

    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    page_bbox = {
        "l": 0.0,
        "t": 200.0,
        "r": 100.0,
        "b": 0.0,
        "coord_origin": "BOTTOMLEFT",
    }
    payload = {
        "page_no": page_no,
        "size": {"width": 100.0, "height": 200.0},
        "parsed_page": {
            "dimension": {
                "angle": 0.0,
                "rect": {
                    "r_x0": 0.0,
                    "r_y0": 0.0,
                    "r_x1": 100.0,
                    "r_y1": 0.0,
                    "r_x2": 100.0,
                    "r_y2": 200.0,
                    "r_x3": 0.0,
                    "r_y3": 200.0,
                    "coord_origin": "BOTTOMLEFT",
                },
                "boundary_type": "crop_box",
                "art_bbox": page_bbox,
                "bleed_bbox": page_bbox,
                "crop_bbox": page_bbox,
                "media_bbox": page_bbox,
                "trim_bbox": page_bbox,
            },
            "textline_cells": [],
            "char_cells": [],
            "word_cells": [],
        },
        "predictions": {"discarded": True},
        "assembled": {"elements": [], "body": [], "headers": []},
        "test": text,
    }
    return PageEvidence(
        page_no=page_no,
        page_payload=payload,
        assembled_element_types=(),
        assembled_body_indices=(),
        assembled_header_indices=(),
        image_scale=2.0,
        image_mode="RGB",
        image_size=(2, 2),
        image_pixels_sha256=hashlib.sha256(image.tobytes()).hexdigest(),
        image_png=buffer.getvalue(),
    )


def test_g1_plan_uses_twelve_bounded_source_authored_ranges() -> None:
    cores = g1_core_intervals()
    assert [(core.start, core.end) for core in cores] == [
        (1, 232),
        (233, 447),
        (448, 669),
        (670, 887),
        (888, 1107),
        (1108, 1332),
        (1333, 1590),
        (1591, 1811),
        (1812, 1957),
        (1958, 2146),
        (2147, 2232),
        (2233, 2488),
    ]
    assert max(len(core.pages) for core in cores) == 258
    assert tuple(page for core in cores for page in core.pages) == tuple(range(1, 2489))


def test_compaction_retains_only_global_fields_and_external_raster() -> None:
    page = _page(1)
    compact = compact_page_evidence(page)
    assert compact.page_payload.keys() == {"page_no", "size", "assembled", "parsed_page"}
    assert compact.page_payload["parsed_page"]["textline_cells"] == []
    assert compact.image_png == page.image_png
    assert raster_from_evidence(compact).size == (2, 2)
    assert restore_global_page(compact).parsed_page.dimension.height == 200.0


def test_page_bundle_round_trip_and_checksum_rejection(tmp_path: Path) -> None:
    pages = tuple(compact_page_evidence(_page(page)) for page in (1, 2))
    root = tmp_path / "pages"
    write_page_evidence(root, pages)
    assert read_page_evidence(root) == pages
    (root / "p00002.png").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="raster checksum"):
        read_page_evidence(root)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("escaping_path", "path escapes root"),
        ("duplicate_path", "path is duplicated"),
        ("duplicate_page", "number is duplicated"),
        ("unlisted_file", "file set differs"),
    ],
)
def test_page_bundle_rejects_uncontained_or_unclosed_index(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    root = tmp_path / "pages"
    pages = tuple(compact_page_evidence(_page(page)) for page in (1, 2))
    write_page_evidence(root, pages)
    index_path = root / "index.json"
    index = read_json_object(index_path)
    records = index["pages"]
    if mutation == "escaping_path":
        records[0]["page_payload"] = "../outside.json"
        write_json_atomic(index_path, index)
    elif mutation == "duplicate_path":
        records[1]["image"] = records[0]["image"]
        write_json_atomic(index_path, index)
    elif mutation == "duplicate_page":
        records[1]["page_no"] = records[0]["page_no"]
        write_json_atomic(index_path, index)
    else:
        (root / "unlisted.json").write_text("{}\n")

    with pytest.raises(ValueError, match=message) as caught:
        read_page_evidence(root)

    assert str(root) in str(caught.value)


def test_full_core_selection_reconciles_both_seam_pages() -> None:
    page1, page2, page3, page4 = (compact_page_evidence(_page(page)) for page in range(1, 5))
    children = (
        CapturedRange(
            "a", PageInterval(start=1, end=2), PageInterval(start=1, end=3), (page1, page2, page3)
        ),
        CapturedRange(
            "b", PageInterval(start=3, end=4), PageInterval(start=2, end=4), (page2, page3, page4)
        ),
    )
    assert tuple(page.page_no for page in select_full_core_pages(children)) == (1, 2, 3, 4)


def test_full_core_selection_rejects_semantic_overlap_drift() -> None:
    page1, page2, page3, page4 = (compact_page_evidence(_page(page)) for page in range(1, 5))
    changed = replace(page2, page_payload={**page2.page_payload, "page_no": 99})
    children = (
        CapturedRange(
            "a", PageInterval(start=1, end=2), PageInterval(start=1, end=3), (page1, page2, page3)
        ),
        CapturedRange(
            "b", PageInterval(start=3, end=4), PageInterval(start=2, end=4), (changed, page3, page4)
        ),
    )
    with pytest.raises(ValueError, match="exact_page_evidence"):
        select_full_core_pages(children)
