"""Write reviewable parser artifacts without hiding Docling's raw records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from er_commons.artifact_io import write_json_atomic


def result_errors(result: Any) -> list[dict[str, Any]]:
    """Serialize Docling conversion errors without losing structured fields."""
    return [
        error.model_dump(mode="json") if hasattr(error, "model_dump") else {"message": str(error)}
        for error in result.errors
    ]


def export_result(result: Any, destination: Path) -> None:
    """Export raw JSON, readable diagnostics, and parser-derived images."""
    from docling_core.types.doc.items.picture.picture import PictureItem
    from docling_core.types.doc.items.table.table import TableItem

    destination.mkdir(parents=True, exist_ok=False)
    document = result.document
    write_json_atomic(destination / "document.json", document.export_to_dict())
    write_json_atomic(
        destination / "conversion_pages.json",
        {
            "pages": [page.model_dump(mode="json") for page in result.pages],
            "assembled": result.assembled.model_dump(mode="json"),
            "confidence": result.confidence.model_dump(mode="json"),
        },
    )
    (destination / "diagnostic.md").write_text(document.export_to_markdown())
    (destination / "diagnostic.html").write_text(document.export_to_html())

    for page_number, page in document.pages.items():
        if page.image is None or page.image.pil_image is None:
            continue
        path = destination / "page_images" / f"page_{page_number:05d}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        page.image.pil_image.save(path, "PNG")

    table_index = 0
    picture_index = 0
    for item, _level in document.iterate_items():
        if isinstance(item, TableItem):
            table_index += 1
            kind = "table"
            index = table_index
        elif isinstance(item, PictureItem):
            picture_index += 1
            kind = "picture"
            index = picture_index
        else:
            continue
        image = item.get_image(document)
        if image is None:
            continue
        page_number = item.prov[0].page_no if item.prov else 0
        image_path = (
            destination / f"{kind}_images" / f"page_{page_number:05d}_{kind}_{index:03d}.png"
        )
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(image_path, "PNG")
