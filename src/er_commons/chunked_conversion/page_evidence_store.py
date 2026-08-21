"""Persist compact page evidence and restore global conversion inputs."""

from __future__ import annotations

import hashlib
import io
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from PIL import Image

from er_commons.artifact_io import read_json_object, sha256_file, write_json_atomic
from er_commons.chunked_conversion.page_evidence import PageEvidence, PageEvidenceError


def compact_page_evidence(page: PageEvidence) -> PageEvidence:
    """Retain only global-assembly fields while keeping exact raster evidence external."""
    payload = page.page_payload
    parsed_page = payload.get("parsed_page")
    if not isinstance(parsed_page, dict):
        raise PageEvidenceError(f"page {page.page_no} lacks parsed-page evidence")
    dimension = parsed_page.get("dimension")
    textline_cells = parsed_page.get("textline_cells")
    if not isinstance(dimension, dict) or not isinstance(textline_cells, list):
        raise PageEvidenceError(f"page {page.page_no} lacks heading-style evidence")
    compact = {
        "page_no": page.page_no,
        "size": payload.get("size"),
        "assembled": payload.get("assembled"),
        "parsed_page": {
            "dimension": dimension,
            "textline_cells": textline_cells,
            "char_cells": [],
            "word_cells": [],
        },
    }
    if not isinstance(compact["size"], dict) or not isinstance(compact["assembled"], dict):
        raise PageEvidenceError(f"page {page.page_no} lacks size or assembled evidence")
    return replace(page, page_payload=compact)


def write_page_evidence(root: Path, pages: tuple[PageEvidence, ...]) -> None:
    """Persist compact typed page state and one independently checksummed raster per page."""
    root.mkdir(parents=True, exist_ok=False)
    records: list[dict[str, Any]] = []
    for page in pages:
        payload_path = root / f"p{page.page_no:05d}.json"
        image_path = root / f"p{page.page_no:05d}.png"
        write_json_atomic(payload_path, page.page_payload)
        if page.image_png is None:
            raise PageEvidenceError(f"page {page.page_no} has no publishable raster bytes")
        image_path.write_bytes(page.image_png)
        records.append(
            {
                "page_no": page.page_no,
                "page_payload": payload_path.name,
                "page_payload_sha256": sha256_file(payload_path),
                "assembled_element_types": list(page.assembled_element_types),
                "assembled_body_indices": list(page.assembled_body_indices),
                "assembled_header_indices": list(page.assembled_header_indices),
                "image": image_path.name,
                "image_sha256": sha256_file(image_path),
                "image_scale": page.image_scale,
                "image_mode": page.image_mode,
                "image_size": list(page.image_size),
                "image_pixels_sha256": page.image_pixels_sha256,
                "semantic_sha256": page.semantic_sha256,
            }
        )
    write_json_atomic(root / "index.json", {"pages": records})


def read_page_evidence(
    root: Path,
    *,
    load_rasters: bool = False,
) -> tuple[PageEvidence, ...]:
    """Verify one closed evidence directory and return path-backed rasters by default."""
    index = read_json_object(root / "index.json")
    records = index.get("pages")
    if not isinstance(records, list):
        raise PageEvidenceError(f"page evidence index is invalid: {root}")
    pages: list[PageEvidence] = []
    declared_files = {"index.json"}
    declared_pages: set[int] = set()
    for position, record in enumerate(records):
        if not isinstance(record, dict):
            raise PageEvidenceError(f"page evidence row is invalid: {root}/{position}")
        page_no = record.get("page_no")
        if not isinstance(page_no, int) or page_no < 1:
            raise PageEvidenceError(f"page evidence number is invalid: {root}/{position}")
        if page_no in declared_pages:
            raise PageEvidenceError(
                f"page evidence number is duplicated: {root}/pages[{position}]/{page_no}"
            )
        declared_pages.add(page_no)
        payload_path = _contained_evidence_path(
            root,
            record.get("page_payload"),
            path=f"pages[{position}].page_payload",
        )
        image_path = _contained_evidence_path(
            root,
            record.get("image"),
            path=f"pages[{position}].image",
        )
        for artifact in (payload_path, image_path):
            relative = artifact.relative_to(root.resolve()).as_posix()
            if relative in declared_files:
                raise PageEvidenceError(f"page evidence path is duplicated: {root}/{relative}")
            declared_files.add(relative)
        if sha256_file(payload_path) != record.get("page_payload_sha256"):
            raise PageEvidenceError(f"page payload checksum differs: {payload_path}")
        if sha256_file(image_path) != record.get("image_sha256"):
            raise PageEvidenceError(f"page raster checksum differs: {image_path}")
        size = record.get("image_size")
        element_types = record.get("assembled_element_types")
        body_indices = record.get("assembled_body_indices")
        header_indices = record.get("assembled_header_indices")
        image_scale = record.get("image_scale")
        if (
            not isinstance(size, list)
            or len(size) != 2
            or not all(isinstance(value, int) for value in size)
            or not isinstance(element_types, list)
            or not all(isinstance(value, str) for value in element_types)
            or not isinstance(body_indices, list)
            or not all(isinstance(value, int) for value in body_indices)
            or not isinstance(header_indices, list)
            or not all(isinstance(value, int) for value in header_indices)
            or not isinstance(image_scale, int | float)
        ):
            raise PageEvidenceError(f"page raster size is invalid: {image_path}")
        page = PageEvidence(
            page_no=page_no,
            page_payload=read_json_object(payload_path),
            assembled_element_types=tuple(cast(list[str], element_types)),
            assembled_body_indices=tuple(cast(list[int], body_indices)),
            assembled_header_indices=tuple(cast(list[int], header_indices)),
            image_scale=float(image_scale),
            image_mode=str(record.get("image_mode")),
            image_size=cast(tuple[int, int], tuple(cast(list[int], size))),
            image_pixels_sha256=str(record.get("image_pixels_sha256")),
            image_png_sha256=str(record.get("image_sha256")),
            image_png=image_path.read_bytes() if load_rasters else None,
            image_path=None if load_rasters else image_path,
        )
        if page.semantic_sha256 != record.get("semantic_sha256"):
            raise PageEvidenceError(f"page semantic checksum differs: {root}/{page_no}")
        pages.append(page)
    actual_files = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    if actual_files != declared_files:
        raise PageEvidenceError(
            f"page evidence file set differs: {root} "
            f"missing={sorted(declared_files - actual_files)} "
            f"extra={sorted(actual_files - declared_files)}"
        )
    actual = tuple(page.page_no for page in pages)
    if actual != tuple(sorted(actual)) or len(actual) != len(set(actual)):
        raise PageEvidenceError(f"page evidence order/uniqueness differs: {root}")
    return tuple(pages)


def _contained_evidence_path(root: Path, value: object, *, path: str) -> Path:
    """Resolve one indexed artifact while rejecting absolute or escaping paths."""
    if not isinstance(value, str) or not value or value == ".":
        raise PageEvidenceError(f"page evidence path is invalid: {root}/{path}")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise PageEvidenceError(f"page evidence path escapes root: {root}/{path}={value!r}")
    resolved_root = root.resolve()
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise PageEvidenceError(f"page evidence path escapes root: {root}/{path}={value!r}")
    return resolved


def restore_global_page(evidence: PageEvidence) -> Any:
    """Restore typed assembled elements without decoding the page raster or parsed cells."""
    from docling.datamodel.base_models import (
        AssembledUnit,
        ContainerElement,
        FigureElement,
        Page,
        Table,
        TextElement,
    )
    from docling_core.types.doc import Size  # type: ignore[attr-defined]

    payload = evidence.page_payload
    assembled = payload.get("assembled")
    size_payload = payload.get("size")
    if not isinstance(assembled, dict) or not isinstance(assembled.get("elements"), list):
        raise PageEvidenceError(f"assembled evidence is invalid: {evidence.page_no}")
    if not isinstance(size_payload, dict):
        raise PageEvidenceError(f"page size evidence is invalid: {evidence.page_no}")
    classes = {cls.__name__: cls for cls in (TextElement, Table, FigureElement, ContainerElement)}
    raw_elements = assembled["elements"]
    if len(raw_elements) != len(evidence.assembled_element_types):
        raise PageEvidenceError(f"typed element count differs: {evidence.page_no}")
    elements = []
    for raw, class_name in zip(raw_elements, evidence.assembled_element_types, strict=True):
        cls = classes.get(class_name)
        if cls is None:
            raise PageEvidenceError(f"unknown assembled element type: {class_name}")
        elements.append(cls.model_validate(raw))
    try:
        unit = AssembledUnit(
            elements=elements,
            body=[elements[index] for index in evidence.assembled_body_indices],
            headers=[elements[index] for index in evidence.assembled_header_indices],
        )
    except IndexError as error:
        raise PageEvidenceError(f"assembled membership differs: {evidence.page_no}") from error
    from docling_core.types.doc.page import SegmentedPdfPage

    parsed_page = payload.get("parsed_page")
    if not isinstance(parsed_page, dict):
        raise PageEvidenceError(f"parsed-page style evidence is invalid: {evidence.page_no}")
    return Page(
        page_no=evidence.page_no,
        size=Size.model_validate(size_payload),
        assembled=unit,
        parsed_page=SegmentedPdfPage.model_validate(parsed_page),
    )


def raster_from_evidence(evidence: PageEvidence) -> Image.Image:
    """Decode one eager or path-backed raster and return one detached verified image."""
    if evidence.image_png is not None:
        source: Any = io.BytesIO(evidence.image_png)
    elif evidence.image_path is not None:
        source = evidence.image_path
    else:
        raise PageEvidenceError(f"page raster location is missing: {evidence.page_no}")
    opened = Image.open(source)
    opened.load()
    image = opened.copy()
    opened.close()
    digest = hashlib.sha256(image.tobytes()).hexdigest()
    if (
        image.mode != evidence.image_mode
        or image.size != evidence.image_size
        or digest != evidence.image_pixels_sha256
    ):
        raise PageEvidenceError(f"page raster round trip differs: {evidence.page_no}")
    return image


__all__ = [
    "compact_page_evidence",
    "raster_from_evidence",
    "read_page_evidence",
    "restore_global_page",
    "write_page_evidence",
]
