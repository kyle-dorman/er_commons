"""Behavior tests for compact range evidence storage and global restoration."""

from __future__ import annotations

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
