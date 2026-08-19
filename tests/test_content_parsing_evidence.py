"""Behavior tests for memory-bounded durable Docling evidence export."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import docling_core.types.doc.items.picture.picture as picture_module
import pytest
from PIL import Image

from er_commons.artifact_io import artifact_inventory
from er_commons.document_parsing.content_parsing.evidence import (
    CompletedRunInvariantError,
    export_durable_result,
    verify_inventory_metadata,
)


class _Dumpable:
    def __init__(self, value: dict[str, Any]) -> None:
        self.value = value

    def model_dump(self, *, mode: str) -> dict[str, Any]:
        assert mode == "json"
        return self.value


class _Picture:
    def __init__(self, page: Any) -> None:
        self.page = page
        self.image: object | None = object()
        self.prov = [SimpleNamespace(page_no=1)]
        self.self_ref = "#/pictures/0"

    def get_image(self, _document: Any) -> Image.Image:
        assert self.page.image is not None
        assert self.image is not None
        return Image.new("RGB", (4, 3), "blue")


class _Document:
    def __init__(self) -> None:
        self.pages = {1: SimpleNamespace(image=object())}
        self.pictures = [_Picture(self.pages[1])]

    def iterate_items(self) -> list[tuple[_Picture, int]]:
        return [(self.pictures[0], 0)]

    def export_to_dict(self) -> dict[str, Any]:
        assert self.pages[1].image is None
        assert self.pictures[0].image is None
        return {
            "pages": {"1": {"page_no": 1, "image": None}},
            "pictures": [{"self_ref": "#/pictures/0", "image": None}],
        }


def test_export_saves_figures_before_externalizing_embedded_images(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(picture_module, "PictureItem", _Picture)
    result = SimpleNamespace(
        document=_Document(),
        pages=[
            SimpleNamespace(
                page_no=1,
                size=SimpleNamespace(width=10, height=20),
                parsed_page=SimpleNamespace(textline_cells=[SimpleNamespace(text="Heading")]),
            )
        ],
        assembled=_Dumpable({"elements": []}),
        confidence=_Dumpable({"mean": 1.0}),
    )
    producer_root = tmp_path / "run" / "documents" / "source" / "producer"

    document, assets = export_durable_result(result, producer_root)

    assert document["pages"]["1"]["image"] is None
    assert document["pictures"][0]["image"] is None
    assert len(assets) == 1
    asset_path = tmp_path / "run" / assets[0]["path"]
    assert asset_path.is_file()
    assert Image.open(asset_path).size == (4, 3)
    inventory = json.loads((producer_root / "asset_inventory.json").read_text())
    assert inventory["image_externalization"] == {
        "contract_version": "er_commons.docling_image_externalization.v1",
        "embedded_page_images_removed": 1,
        "embedded_picture_images_removed": 1,
        "figure_crops_preserved_as_assets": True,
        "full_page_renders_preserved": False,
    }
    [alignment] = [
        json.loads(line)
        for line in (producer_root / "docling/alignment_pages.jsonl").read_text().splitlines()
    ]
    assert alignment == {
        "schema_version": "er_commons.hierarchy_alignment_page.v1",
        "page_no": 1,
        "width": 10.0,
        "height": 20.0,
        "alignment_index": [["heading", "unique_aligned", 1]],
    }
    assert not (producer_root / "docling/conversion_pages.json").exists()
    assert not (producer_root / "docling/diagnostic.md").exists()
    assert not (producer_root / "docling/diagnostic.html").exists()


@pytest.mark.parametrize(
    ("mutation", "invariant"),
    [
        (lambda value: value["files"].append(dict(value["files"][0])), "unique_inventory_path"),
        (lambda value: value.update(file_count=99), "inventory_file_count"),
        (lambda value: value.update(byte_count=99), "inventory_byte_count"),
        (
            lambda value: value["files"][0].update(sha256="not-a-digest"),
            "inventory_file_digest",
        ),
    ],
)
def test_inventory_metadata_rejects_malformed_sealed_records(
    tmp_path: Path,
    mutation: Any,
    invariant: str,
) -> None:
    payload = tmp_path / "payload.json"
    payload.write_text("{}\n")
    inventory = artifact_inventory(tmp_path, excluded=set())
    mutation(inventory)

    with pytest.raises(CompletedRunInvariantError) as captured:
        verify_inventory_metadata(tmp_path, inventory)

    assert captured.value.invariant == invariant
