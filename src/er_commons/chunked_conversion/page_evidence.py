"""Capture, validate, and restore restartable Docling page evidence."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Never

import rfc8785
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

from er_commons.chunked_conversion.range_contract import PageInterval


class PageEvidenceError(ValueError):
    """Persisted or overlapping page evidence violates an exact runtime invariant."""


@dataclass(frozen=True)
class PageEvidence:
    """Serializable Page fields plus the private raster state needed for assembly."""

    page_no: int
    page_payload: dict[str, Any]
    assembled_element_types: tuple[str, ...]
    assembled_body_indices: tuple[int, ...]
    assembled_header_indices: tuple[int, ...]
    image_scale: float
    image_mode: str
    image_size: tuple[int, int]
    image_pixels_sha256: str
    image_png_sha256: str
    image_png: bytes | None
    image_path: Path | None

    @property
    def semantic_sha256(self) -> str:
        """Hash every JSON field and decoded raster pixel without PNG metadata."""
        return hashlib.sha256(
            rfc8785.dumps(
                {
                    "page_no": self.page_no,
                    "page_payload": self.page_payload,
                    "assembled_element_types": list(self.assembled_element_types),
                    "assembled_body_indices": list(self.assembled_body_indices),
                    "assembled_header_indices": list(self.assembled_header_indices),
                    "image_scale": self.image_scale,
                    "image_mode": self.image_mode,
                    "image_size": list(self.image_size),
                    "image_pixels_sha256": self.image_pixels_sha256,
                    "image_png_sha256": self.image_png_sha256,
                }
            )
        ).hexdigest()


@dataclass(frozen=True)
class CapturedAssembly:
    """Exact page evidence and transient outline captured before global assembly."""

    pages: tuple[PageEvidence, ...]
    page_object_ids: tuple[int, ...]
    outline: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class _LivePageSemantics:
    """Semantic fields that must remain stable after a page is captured."""

    page_no: int
    page_payload: dict[str, Any]
    assembled_element_types: tuple[str, ...]
    assembled_body_indices: tuple[int, ...]
    assembled_header_indices: tuple[int, ...]


def _fail(path: str, invariant: str, expected: object, actual: object) -> Never:
    raise PageEvidenceError(
        f"path={path} invariant={invariant} expected={expected!r} actual={actual!r}"
    )


def _read_live_page_semantics(page: Any) -> _LivePageSemantics:
    """Read semantic page state without copying or hashing its raster."""
    page_no = getattr(page, "page_no", None)
    if not isinstance(page_no, int) or page_no < 1:
        _fail("page.page_no", "positive_physical_page", "positive integer", page_no)
    payload = page.model_dump(mode="json")
    if not isinstance(payload, dict):
        _fail(f"pages[{page_no}]", "page_payload", "JSON object", type(payload).__name__)
    assembled = getattr(page, "assembled", None)
    if assembled is None:
        _fail(f"pages[{page_no}].assembled", "assembled_page", "available", None)
    element_indices = {id(item): index for index, item in enumerate(assembled.elements)}
    if len(element_indices) != len(assembled.elements):
        _fail(
            f"pages[{page_no}].assembled.elements",
            "unique_element_identity",
            len(assembled.elements),
            len(element_indices),
        )
    try:
        body_indices = tuple(element_indices[id(item)] for item in assembled.body)
        header_indices = tuple(element_indices[id(item)] for item in assembled.headers)
    except KeyError as error:
        _fail(
            f"pages[{page_no}].assembled",
            "body_header_membership",
            "members of elements",
            str(error),
        )
    return _LivePageSemantics(
        page_no=page_no,
        page_payload=payload,
        assembled_element_types=tuple(type(item).__name__ for item in assembled.elements),
        assembled_body_indices=body_indices,
        assembled_header_indices=header_indices,
    )


def assert_live_page_matches_evidence(
    expected: PageEvidence,
    live_page: Any,
    *,
    path: str,
) -> None:
    """Verify that a captured page's live semantic state has not changed."""
    actual = _read_live_page_semantics(live_page)
    fields = (
        "page_no",
        "page_payload",
        "assembled_element_types",
        "assembled_body_indices",
        "assembled_header_indices",
    )
    for field in fields:
        expected_value = getattr(expected, field)
        actual_value = getattr(actual, field)
        if actual_value != expected_value:
            _fail(
                f"{path}.{field}",
                "captured_page_semantics",
                expected_value,
                actual_value,
            )


def capture_page_evidence(page: Any) -> PageEvidence:
    """Copy one assembled Docling Page, including its private default-scale raster."""
    semantics = _read_live_page_semantics(page)
    page_no = semantics.page_no
    scale = getattr(page, "_default_image_scale", None)
    image = page.get_image(scale=scale) if isinstance(scale, int | float) else None
    if image is None or not isinstance(scale, int | float) or scale <= 0:
        _fail(f"pages[{page_no}].image", "default_scale_raster", "available image", None)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    pixels_sha256 = hashlib.sha256(image.tobytes()).hexdigest()
    return PageEvidence(
        page_no=page_no,
        page_payload=semantics.page_payload,
        assembled_element_types=semantics.assembled_element_types,
        assembled_body_indices=semantics.assembled_body_indices,
        assembled_header_indices=semantics.assembled_header_indices,
        image_scale=float(scale),
        image_mode=str(image.mode),
        image_size=(int(image.width), int(image.height)),
        image_pixels_sha256=pixels_sha256,
        image_png_sha256=hashlib.sha256(buffer.getvalue()).hexdigest(),
        image_png=buffer.getvalue(),
        image_path=None,
    )


def validate_conversion_pages(
    result: Any,
    expected: PageInterval,
    *,
    path: str,
) -> tuple[Any, ...]:
    """Require one clean bounded success with exact ordered live-page coverage."""
    raw_status = str(getattr(getattr(result, "status", None), "value", result.status))
    if raw_status != "success":
        _fail(f"{path}.status", "clean_conversion_success", "success", raw_status)
    errors = tuple(getattr(result, "errors", ()))
    if errors:
        _fail(f"{path}.errors", "zero_conversion_errors", (), errors)
    pages = tuple(getattr(result, "pages", ()))
    actual = tuple(int(page.page_no) for page in pages)
    if actual != expected.pages:
        _fail(f"{path}.pages", "ordered_read_coverage", expected.pages, actual)
    return pages


def validate_conversion_result(
    result: Any,
    expected: PageInterval,
    *,
    path: str,
) -> tuple[PageEvidence, ...]:
    """Require one clean bounded success and capture its exact ordered pages."""
    pages = validate_conversion_pages(result, expected, path=path)
    return tuple(capture_page_evidence(page) for page in pages)


def assert_exact_page_evidence(
    expected: PageEvidence,
    actual: PageEvidence,
    *,
    path: str,
) -> None:
    """Name the first exact page-evidence field that differs."""
    fields = (
        "page_no",
        "page_payload",
        "assembled_element_types",
        "assembled_body_indices",
        "assembled_header_indices",
        "image_scale",
        "image_mode",
        "image_size",
        "image_pixels_sha256",
        "image_png_sha256",
    )
    for field in fields:
        expected_value = getattr(expected, field)
        actual_value = getattr(actual, field)
        if actual_value != expected_value:
            _fail(f"{path}.{field}", "exact_page_evidence", expected_value, actual_value)


def _outline_payload(conv_res: Any) -> tuple[dict[str, Any], ...]:
    outline = getattr(conv_res, "_pdf_outline", None) or ()
    payloads: list[dict[str, Any]] = []
    for index, item in enumerate(outline):
        payload = item.model_dump(mode="json")
        if not isinstance(payload, dict):
            _fail(f"outline[{index}]", "outline_payload", "JSON object", type(payload).__name__)
        payloads.append(payload)
    return tuple(payloads)


class PageCapturePdfPipeline(StandardPdfPipeline):
    """Capture pre-global page evidence without running document interpretation."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.pending_captures: list[CapturedAssembly] = []

    def _assemble_document(self, conv_res: Any) -> Any:
        """Capture exact pages and defer reading order and headings to aggregation."""
        pages = tuple(conv_res.pages)
        self.pending_captures.append(
            CapturedAssembly(
                pages=tuple(capture_page_evidence(page) for page in pages),
                page_object_ids=tuple(id(page) for page in pages),
                outline=_outline_payload(conv_res),
            )
        )
        return conv_res

    def _enrich_document(self, conv_res: Any) -> Any:
        """Skip document enrichment because range conversion has no global document."""
        return conv_res

    def take_capture(self) -> CapturedAssembly:
        """Return the sole pending capture and remove it from pipeline state."""
        if len(self.pending_captures) != 1:
            _fail(
                "pipeline.pending_captures",
                "one_pending_capture",
                1,
                len(self.pending_captures),
            )
        return self.pending_captures.pop()


__all__ = [
    "CapturedAssembly",
    "PageEvidenceError",
    "PageCapturePdfPipeline",
    "PageEvidence",
    "assert_live_page_matches_evidence",
    "assert_exact_page_evidence",
    "capture_page_evidence",
    "validate_conversion_pages",
    "validate_conversion_result",
]
