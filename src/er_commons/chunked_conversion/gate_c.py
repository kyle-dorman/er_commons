"""Full-document G1 qualification helpers for restartable chunked conversion."""

from __future__ import annotations

import hashlib
import io
from collections.abc import Iterable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, cast

from PIL import Image

from er_commons.artifact_io import read_json_object, sha256_file, write_json_atomic
from er_commons.chunked_conversion.gate_b import (
    CapturedRange,
    GateBComparisonError,
    PageEvidence,
    assert_exact_page_evidence,
)
from er_commons.chunked_conversion.range_contract import PageInterval


@dataclass(frozen=True)
class G1Boundary:
    """One reviewed source-authored divider that begins a new core range."""

    next_page: int
    outline_title: str
    previous_page_evidence: str
    next_page_evidence: str


G1_BOUNDARIES = (
    G1Boundary(233, "Building Construction Blocks A8 and A9", "report page 67/67", "divider"),
    G1Boundary(448, "Building Construction Blocks B1 through B4", "report page 76/76", "divider"),
    G1Boundary(670, "Building Construction Blocks B10 and B11", "report page 76/76", "divider"),
    G1Boundary(888, "Building Construction Blocks C4 and C5 alternate", "report end", "divider"),
    G1Boundary(1108, "Open Spaces", "report page 72/72", "divider"),
    G1Boundary(1333, "Earthwork", "report end", "divider"),
    G1Boundary(1591, "Area D, OS-E, and G Earthwork West", "report end", "divider"),
    G1Boundary(1812, "Middle School", "report page 39/39", "divider"),
    G1Boundary(1958, "Relocated Fire Station", "report end", "divider"),
    G1Boundary(2147, "Substation", "report page 76/76", "divider"),
    G1Boundary(2233, "Water Recycling Facility", "report page 85/85", "divider"),
)


def g1_core_intervals(page_count: int = 2488) -> tuple[PageInterval, ...]:
    """Return the reviewed twelve-range G1 core plan in physical-page order."""
    starts = (1, *(item.next_page for item in G1_BOUNDARIES))
    ends = (*(page - 1 for page in starts[1:]), page_count)
    return tuple(
        PageInterval(start=start, end=end) for start, end in zip(starts, ends, strict=True)
    )


def g1_captured_ranges(
    range_ids: Iterable[str], page_count: int = 2488
) -> tuple[tuple[str, PageInterval, PageInterval], ...]:
    """Add one comparison page on each available side of every G1 core."""
    cores = g1_core_intervals(page_count)
    ids = tuple(range_ids)
    if len(ids) != len(cores):
        raise ValueError(f"G1 range ID count differs: {len(ids)} != {len(cores)}")
    return tuple(
        (
            range_id,
            core,
            PageInterval(start=max(1, core.start - 1), end=min(page_count, core.end + 1)),
        )
        for range_id, core in zip(ids, cores, strict=True)
    )


def compact_page_evidence(page: PageEvidence) -> PageEvidence:
    """Retain only global-assembly fields while keeping exact raster evidence external."""
    payload = page.page_payload
    parsed_page = payload.get("parsed_page")
    if not isinstance(parsed_page, dict):
        raise GateBComparisonError(f"page {page.page_no} lacks parsed-page evidence")
    dimension = parsed_page.get("dimension")
    textline_cells = parsed_page.get("textline_cells")
    if not isinstance(dimension, dict) or not isinstance(textline_cells, list):
        raise GateBComparisonError(f"page {page.page_no} lacks heading-style evidence")
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
        raise GateBComparisonError(f"page {page.page_no} lacks size or assembled evidence")
    return replace(page, page_payload=compact)


def write_page_evidence(root: Path, pages: tuple[PageEvidence, ...]) -> None:
    """Persist compact typed page state and one independently checksummed raster per page."""
    root.mkdir(parents=True, exist_ok=False)
    records: list[dict[str, Any]] = []
    for page in pages:
        payload_path = root / f"p{page.page_no:05d}.json"
        image_path = root / f"p{page.page_no:05d}.png"
        write_json_atomic(payload_path, page.page_payload)
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


def read_page_evidence(root: Path) -> tuple[PageEvidence, ...]:
    """Load one closed, contained, checksum-verified page-evidence directory."""
    index = read_json_object(root / "index.json")
    records = index.get("pages")
    if not isinstance(records, list):
        raise GateBComparisonError(f"page evidence index is invalid: {root}")
    pages: list[PageEvidence] = []
    declared_files = {"index.json"}
    declared_pages: set[int] = set()
    for position, record in enumerate(records):
        if not isinstance(record, dict):
            raise GateBComparisonError(f"page evidence row is invalid: {root}/{position}")
        page_no = record.get("page_no")
        if not isinstance(page_no, int) or page_no < 1:
            raise GateBComparisonError(f"page evidence number is invalid: {root}/{position}")
        if page_no in declared_pages:
            raise GateBComparisonError(
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
                raise GateBComparisonError(f"page evidence path is duplicated: {root}/{relative}")
            declared_files.add(relative)
        if sha256_file(payload_path) != record.get("page_payload_sha256"):
            raise GateBComparisonError(f"page payload checksum differs: {payload_path}")
        if sha256_file(image_path) != record.get("image_sha256"):
            raise GateBComparisonError(f"page raster checksum differs: {image_path}")
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
            raise GateBComparisonError(f"page raster size is invalid: {image_path}")
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
            image_png=image_path.read_bytes(),
        )
        if page.semantic_sha256 != record.get("semantic_sha256"):
            raise GateBComparisonError(f"page semantic checksum differs: {root}/{page_no}")
        pages.append(page)
    actual_files = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    if actual_files != declared_files:
        raise GateBComparisonError(
            f"page evidence file set differs: {root} "
            f"missing={sorted(declared_files - actual_files)} "
            f"extra={sorted(actual_files - declared_files)}"
        )
    actual = tuple(page.page_no for page in pages)
    if actual != tuple(sorted(actual)) or len(actual) != len(set(actual)):
        raise GateBComparisonError(f"page evidence order/uniqueness differs: {root}")
    return tuple(pages)


def _contained_evidence_path(root: Path, value: object, *, path: str) -> Path:
    """Resolve one indexed artifact while rejecting absolute or escaping paths."""
    if not isinstance(value, str) or not value or value == ".":
        raise GateBComparisonError(f"page evidence path is invalid: {root}/{path}")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise GateBComparisonError(f"page evidence path escapes root: {root}/{path}={value!r}")
    resolved_root = root.resolve()
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise GateBComparisonError(f"page evidence path escapes root: {root}/{path}={value!r}")
    return resolved


def select_full_core_pages(children: tuple[CapturedRange, ...]) -> tuple[PageEvidence, ...]:
    """Verify every adjacent overlap and emit exact 1..N core evidence once."""
    if not children:
        raise GateBComparisonError("no range children supplied")
    selected: list[PageEvidence] = []
    previous: CapturedRange | None = None
    for child in children:
        actual = tuple(page.page_no for page in child.pages)
        if actual != child.read.pages:
            raise GateBComparisonError(f"range read coverage differs: {child.range_id}")
        by_page = {page.page_no: page for page in child.pages}
        if previous is not None:
            if previous.core.end + 1 != child.core.start:
                raise GateBComparisonError("range cores are not adjacent")
            previous_by_page = {page.page_no: page for page in previous.pages}
            overlap = tuple(sorted(set(previous_by_page) & set(by_page)))
            if overlap != (previous.core.end, child.core.start):
                raise GateBComparisonError(
                    f"adjacent overlap differs: {previous.range_id}/{child.range_id}/{overlap}"
                )
            for page_no in overlap:
                assert_exact_page_evidence(
                    previous_by_page[page_no],
                    by_page[page_no],
                    path=f"full_g1.overlap[{page_no}]",
                )
        selected.extend(by_page[page_no] for page_no in child.core.pages)
        previous = child
    actual_pages = tuple(page.page_no for page in selected)
    expected_pages = tuple(range(1, children[-1].core.end + 1))
    if actual_pages != expected_pages:
        raise GateBComparisonError("full G1 core page coverage differs")
    return tuple(selected)


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
        raise GateBComparisonError(f"assembled evidence is invalid: {evidence.page_no}")
    if not isinstance(size_payload, dict):
        raise GateBComparisonError(f"page size evidence is invalid: {evidence.page_no}")
    classes = {cls.__name__: cls for cls in (TextElement, Table, FigureElement, ContainerElement)}
    raw_elements = assembled["elements"]
    if len(raw_elements) != len(evidence.assembled_element_types):
        raise GateBComparisonError(f"typed element count differs: {evidence.page_no}")
    elements = []
    for raw, class_name in zip(raw_elements, evidence.assembled_element_types, strict=True):
        cls = classes.get(class_name)
        if cls is None:
            raise GateBComparisonError(f"unknown assembled element type: {class_name}")
        elements.append(cls.model_validate(raw))
    try:
        unit = AssembledUnit(
            elements=elements,
            body=[elements[index] for index in evidence.assembled_body_indices],
            headers=[elements[index] for index in evidence.assembled_header_indices],
        )
    except IndexError as error:
        raise GateBComparisonError(f"assembled membership differs: {evidence.page_no}") from error
    from docling_core.types.doc.page import SegmentedPdfPage

    parsed_page = payload.get("parsed_page")
    if not isinstance(parsed_page, dict):
        raise GateBComparisonError(f"parsed-page style evidence is invalid: {evidence.page_no}")
    return Page(
        page_no=evidence.page_no,
        size=Size.model_validate(size_payload),
        assembled=unit,
        parsed_page=SegmentedPdfPage.model_validate(parsed_page),
    )


def raster_from_evidence(evidence: PageEvidence) -> Image.Image:
    """Decode one page raster and require its recorded mode, size, and pixels."""
    image = Image.open(io.BytesIO(evidence.image_png))
    image.load()
    digest = hashlib.sha256(image.tobytes()).hexdigest()
    if (
        image.mode != evidence.image_mode
        or image.size != evidence.image_size
        or digest != evidence.image_pixels_sha256
    ):
        raise GateBComparisonError(f"page raster round trip differs: {evidence.page_no}")
    return image


__all__ = [
    "G1Boundary",
    "G1_BOUNDARIES",
    "compact_page_evidence",
    "g1_captured_ranges",
    "g1_core_intervals",
    "raster_from_evidence",
    "read_page_evidence",
    "restore_global_page",
    "select_full_core_pages",
    "write_page_evidence",
]
