"""Behavior tests for compact range evidence storage and global restoration."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest
from PIL import Image

from er_commons.artifact_io import read_json_object, write_json_atomic
from er_commons.chunked_conversion.page_evidence import PageEvidence
from er_commons.chunked_conversion.page_evidence_store import (
    compact_page_evidence,
    raster_from_evidence,
    read_page_evidence,
    restore_global_page,
    write_page_evidence,
)
from er_commons.chunked_conversion.runtime.aggregate_memory import (
    restore_ordering_page,
    suppress_confirmed_table_regions,
)
from er_commons.document_parsing.content_parsing.ordering_projection import (
    build_ordering_projection,
    classify_table_evidence,
)
from er_commons.document_parsing.content_parsing.page_projection import PageEvidenceProjection


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
    image_bytes = buffer.getvalue()
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
        image_png_sha256=hashlib.sha256(image_bytes).hexdigest(),
        image_png=image_bytes,
        image_path=None,
    )


def test_compaction_retains_only_global_fields_and_external_raster() -> None:
    page = _page(1)
    compact = compact_page_evidence(page)
    assert compact.page_payload.keys() == {"page_no", "size", "assembled", "parsed_page"}
    assert compact.page_payload["parsed_page"]["textline_cells"] == []
    assert compact.image_png == page.image_png
    assert raster_from_evidence(compact).size == (2, 2)
    assert restore_global_page(compact).parsed_page.dimension.height == 200.0


def test_aggregate_ordering_restore_omits_parsed_style_evidence() -> None:
    """Reading-order pages retain assembled content and size without style cells."""
    compact = compact_page_evidence(_page(1))

    ordering_page = restore_ordering_page(compact)
    eager_page = restore_global_page(compact)

    assert ordering_page.page_no == eager_page.page_no
    assert ordering_page.size == eager_page.size
    assert ordering_page.assembled.model_dump(mode="json") == eager_page.assembled.model_dump(
        mode="json"
    )
    assert ordering_page.parsed_page is None


def test_confirmed_table_geometry_removes_table_text_but_keeps_narrative() -> None:
    """Exercise the production TOPLEFT cluster and displayed-region coordinate shapes."""
    raw_elements = [
        {
            "id": 1,
            "page_no": 1,
            "label": "text",
            "text": "custom table duplicate",
            "cluster": {
                "id": 1,
                "label": "text",
                "bbox": {"l": 10.0, "t": 110.0, "r": 90.0, "b": 130.0, "coord_origin": "TOPLEFT"},
                "confidence": 1.0,
                "cells": [],
                "children": [],
            },
        },
        {
            "id": 2,
            "page_no": 1,
            "label": "text",
            "text": "narrative outside table",
            "cluster": {
                "id": 2,
                "label": "text",
                "bbox": {"l": 10.0, "t": 20.0, "r": 90.0, "b": 40.0, "coord_origin": "TOPLEFT"},
                "confidence": 1.0,
                "cells": [],
                "children": [],
            },
        },
    ]
    evidence = _page(1)
    payload = dict(evidence.page_payload)
    payload["assembled"] = {
        "elements": raw_elements,
        "body": raw_elements,
        "headers": [],
    }
    evidence = replace(
        evidence,
        page_payload=payload,
        assembled_element_types=("TextElement", "TextElement"),
        assembled_body_indices=(0, 1),
    )
    page = restore_ordering_page(evidence)
    page_projection = PageEvidenceProjection(
        source_id="source",
        physical_pdf_page=1,
        features={
            "physical_pdf_page": 1,
            "page_size_pdf_points": [100.0, 200.0],
            "displayed_page_size_pdf_points": [100.0, 200.0],
            "source_page_bbox_pdf_points_bottom_left": [0.0, 0.0, 100.0, 200.0],
            "routing_page_bbox_pdf_points_bottom_left": [0.0, 0.0, 100.0, 200.0],
            "routing_coordinate_system": "displayed_pdf_points_bottom_left",
            "page_rotation_degrees": 0,
            "native_character_count": 1,
            "nonspace_character_count": 1,
            "native_text_rectangle_count": 1,
            "nonempty_line_count": 1,
            "text_width_fraction": 0.1,
            "text_height_fraction": 0.1,
            "nonspace_characters_per_square_point": 0.0001,
            "digit_fraction": 0.0,
            "coordinate_key_count": 0,
        },
        layout_table_observations=[],
        boundary_markers_before_first_table=[],
        range_id="range-1",
    )
    decision = classify_table_evidence(
        physical_pdf_page=1,
        route="layout_regions",
        page_record={"table_count": 1},
        table_records=[
            {
                "table_id": "table-1-1",
                "bbox_pdf_points_bottom_left": [0.0, 0.0, 100.0, 100.0],
                "page_size_pdf_points": [100.0, 200.0],
            }
        ],
    )
    projection = build_ordering_projection([page_projection], [decision]).pages[0]

    suppress_confirmed_table_regions(page, projection)

    assert [item.text for item in page.assembled.elements] == ["narrative outside table"]
    assert page.assembled.body == page.assembled.elements


def test_page_bundle_round_trip_and_checksum_rejection(tmp_path: Path) -> None:
    pages = tuple(compact_page_evidence(_page(page)) for page in (1, 2))
    root = tmp_path / "pages"
    write_page_evidence(root, pages)
    loaded = read_page_evidence(root)
    assert tuple(page.page_no for page in loaded) == (1, 2)
    assert all(page.image_png is None and page.image_path is not None for page in loaded)
    assert tuple(raster_from_evidence(page).size for page in loaded) == ((2, 2), (2, 2))
    (root / "p00002.png").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="raster checksum"):
        read_page_evidence(root)


def test_page_bundle_verification_does_not_materialize_png_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "pages"
    write_page_evidence(root, tuple(compact_page_evidence(_page(page)) for page in (1, 2, 3)))
    original_read_bytes = Path.read_bytes

    def guarded_read_bytes(path: Path) -> bytes:
        if path.suffix == ".png":
            raise AssertionError(f"raster bytes were materialized during verification: {path}")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)

    loaded = read_page_evidence(root)

    assert all(page.image_png is None for page in loaded)
    assert [page.image_path for page in loaded] == [
        (root / f"p{page:05d}.png").resolve() for page in (1, 2, 3)
    ]


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
    records = cast(list[dict[str, Any]], index["pages"])
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
