"""Write reviewable parser artifacts without hiding Docling's raw records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.source_freeze import sha256_file, write_json_atomic


def directory_bytes(path: Path) -> int:
    """Return the total size of regular files below a directory."""
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


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


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    """Write deterministic one-record-per-line JSON."""
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read non-empty JSONL records from one artifact."""
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def artifact_inventory(root: Path, excluded: set[str]) -> dict[str, Any]:
    """Hash every generated file except self-referential seal records."""
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        files.append(
            {
                "path": relative,
                "byte_size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "file_count": len(files),
        "byte_count": sum(record["byte_size"] for record in files),
        "files": files,
    }


def load_json(path: Path) -> Any:
    """Read one JSON artifact."""
    return json.loads(path.read_text())


def stable_json_sha256(payload: Any) -> str:
    """Hash one JSON value with deterministic key ordering and separators."""
    import hashlib

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()
