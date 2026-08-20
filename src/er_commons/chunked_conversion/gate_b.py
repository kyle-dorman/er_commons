"""Bounded live-evidence helpers for Task 03H.2 Gate B."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from typing import Any, Never

import rfc8785
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

from er_commons.chunked_conversion.range_contract import PageInterval


class GateBComparisonError(ValueError):
    """Live split evidence differs from its contiguous control."""


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
    image_png: bytes

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
                }
            )
        ).hexdigest()


@dataclass(frozen=True)
class CapturedAssembly:
    """Exact page evidence and transient outline captured before global assembly."""

    pages: tuple[PageEvidence, ...]
    outline: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class CapturedRange:
    """One bounded child conversion and its core/read ownership."""

    range_id: str
    core: PageInterval
    read: PageInterval
    pages: tuple[PageEvidence, ...]


@dataclass(frozen=True)
class ExactOutputs:
    """Declared Gate B outputs compared without normalization or waiver."""

    document: dict[str, Any]
    heading_overlay: tuple[dict[str, Any], ...]
    alignment_pages: tuple[dict[str, Any], ...]
    assets: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]


def _fail(path: str, invariant: str, expected: object, actual: object) -> Never:
    raise GateBComparisonError(
        f"path={path} invariant={invariant} expected={expected!r} actual={actual!r}"
    )


def capture_page_evidence(page: Any) -> PageEvidence:
    """Copy one assembled Docling Page, including its private default-scale raster."""
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
    scale = getattr(page, "_default_image_scale", None)
    image = page.get_image(scale=scale) if isinstance(scale, int | float) else None
    if image is None or not isinstance(scale, int | float) or scale <= 0:
        _fail(f"pages[{page_no}].image", "default_scale_raster", "available image", None)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    pixels_sha256 = hashlib.sha256(image.tobytes()).hexdigest()
    return PageEvidence(
        page_no=page_no,
        page_payload=payload,
        assembled_element_types=tuple(type(item).__name__ for item in assembled.elements),
        assembled_body_indices=body_indices,
        assembled_header_indices=header_indices,
        image_scale=float(scale),
        image_mode=str(image.mode),
        image_size=(int(image.width), int(image.height)),
        image_pixels_sha256=pixels_sha256,
        image_png=buffer.getvalue(),
    )


def restore_page_evidence(evidence: PageEvidence) -> Any:
    """Rebuild one Docling Page and verify its private raster before global assembly."""
    from docling.datamodel.base_models import (
        AssembledUnit,
        ContainerElement,
        FigureElement,
        Page,
        Table,
        TextElement,
    )
    from PIL import Image

    page = Page.model_validate(evidence.page_payload)
    if int(page.page_no) != evidence.page_no:
        _fail(
            f"pages[{evidence.page_no}].page_no",
            "payload_page_identity",
            evidence.page_no,
            page.page_no,
        )
    raw_assembled = evidence.page_payload.get("assembled")
    if not isinstance(raw_assembled, dict) or not isinstance(raw_assembled.get("elements"), list):
        _fail(
            f"pages[{evidence.page_no}].assembled",
            "serialized_assembled_elements",
            "JSON list",
            raw_assembled,
        )
    classes = {cls.__name__: cls for cls in (TextElement, Table, FigureElement, ContainerElement)}
    raw_elements = raw_assembled["elements"]
    if len(raw_elements) != len(evidence.assembled_element_types):
        _fail(
            f"pages[{evidence.page_no}].assembled.elements",
            "typed_element_count",
            len(evidence.assembled_element_types),
            len(raw_elements),
        )
    elements = []
    for index, (payload, class_name) in enumerate(
        zip(raw_elements, evidence.assembled_element_types, strict=True)
    ):
        cls = classes.get(class_name)
        if cls is None:
            _fail(
                f"pages[{evidence.page_no}].assembled.elements[{index}]",
                "known_element_type",
                sorted(classes),
                class_name,
            )
        elements.append(cls.model_validate(payload))
    try:
        page.assembled = AssembledUnit(
            elements=elements,
            body=[elements[index] for index in evidence.assembled_body_indices],
            headers=[elements[index] for index in evidence.assembled_header_indices],
        )
    except IndexError as error:
        _fail(
            f"pages[{evidence.page_no}].assembled",
            "membership_index_bounds",
            f"0..{len(elements) - 1}",
            str(error),
        )
    image = Image.open(io.BytesIO(evidence.image_png))
    image.load()
    if (
        image.mode != evidence.image_mode
        or image.size != evidence.image_size
        or hashlib.sha256(image.tobytes()).hexdigest() != evidence.image_pixels_sha256
    ):
        _fail(
            f"pages[{evidence.page_no}].image",
            "raster_round_trip",
            (evidence.image_mode, evidence.image_size, evidence.image_pixels_sha256),
            (image.mode, image.size, hashlib.sha256(image.tobytes()).hexdigest()),
        )
    page._default_image_scale = evidence.image_scale
    page._image_cache = {evidence.image_scale: image.copy()}
    return page


def validate_conversion_result(
    result: Any,
    expected: PageInterval,
    *,
    path: str,
) -> tuple[PageEvidence, ...]:
    """Require one clean bounded success with exact ordered page coverage."""
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
    return tuple(capture_page_evidence(page) for page in pages)


def _validate_captured_range(child: CapturedRange, *, path: str) -> dict[int, PageEvidence]:
    if child.read.start > child.core.start or child.read.end < child.core.end:
        _fail(f"{path}.read", "read_contains_core", child.core, child.read)
    pages = tuple(page.page_no for page in child.pages)
    if pages != child.read.pages:
        _fail(f"{path}.pages", "exact_ordered_read_pages", child.read.pages, pages)
    return {page.page_no: page for page in child.pages}


def select_core_page_evidence(
    left: CapturedRange,
    right: CapturedRange,
) -> tuple[PageEvidence, ...]:
    """Reconcile two overlapping reads and emit each adjacent core page exactly once."""
    left_by_page = _validate_captured_range(left, path=f"children[{left.range_id}]")
    right_by_page = _validate_captured_range(right, path=f"children[{right.range_id}]")
    if left.core.end + 1 != right.core.start:
        _fail("children.core", "adjacent_core_intervals", left.core.end + 1, right.core.start)
    overlap = tuple(sorted(set(left_by_page) & set(right_by_page)))
    if not overlap:
        _fail("children.overlap", "declared_overlap", "at least one page", overlap)
    for page_no in overlap:
        assert_exact_page_evidence(
            left_by_page[page_no],
            right_by_page[page_no],
            path=f"children.overlap[{page_no}]",
        )
    selected = tuple(
        [*(left_by_page[page] for page in left.core.pages)]
        + [*(right_by_page[page] for page in right.core.pages)]
    )
    expected = tuple(range(left.core.start, right.core.end + 1))
    actual = tuple(page.page_no for page in selected)
    if actual != expected:
        _fail("children.core_pages", "exact_core_emission", expected, actual)
    return selected


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
        "image_png",
    )
    for field in fields:
        expected_value = getattr(expected, field)
        actual_value = getattr(actual, field)
        if actual_value != expected_value:
            _fail(f"{path}.{field}", "exact_page_evidence", expected_value, actual_value)


def assert_exact_split_vs_contiguous(
    split_pages: tuple[PageEvidence, ...],
    contiguous_pages: tuple[PageEvidence, ...],
    *,
    path: str = "split_vs_contiguous",
) -> None:
    """Require exact pre-global page evidence for split and contiguous conversion."""
    expected_pages = tuple(page.page_no for page in contiguous_pages)
    actual_pages = tuple(page.page_no for page in split_pages)
    if actual_pages != expected_pages:
        _fail(f"{path}.pages", "exact_page_sequence", expected_pages, actual_pages)
    for index, (expected, actual) in enumerate(zip(contiguous_pages, split_pages, strict=True)):
        assert_exact_page_evidence(expected, actual, path=f"{path}.pages[{index}]")


def assert_exact_outputs(
    expected: ExactOutputs,
    actual: ExactOutputs,
    *,
    path: str = "split_vs_contiguous.outputs",
) -> None:
    """Require every declared final output to match without field normalization."""
    for field in (
        "document",
        "heading_overlay",
        "alignment_pages",
        "assets",
        "warnings",
    ):
        expected_value = getattr(expected, field)
        actual_value = getattr(actual, field)
        if actual_value != expected_value:
            _fail(f"{path}.{field}", "exact_output", expected_value, actual_value)


def _outline_payload(conv_res: Any) -> tuple[dict[str, Any], ...]:
    outline = getattr(conv_res, "_pdf_outline", None) or ()
    payloads: list[dict[str, Any]] = []
    for index, item in enumerate(outline):
        payload = item.model_dump(mode="json")
        if not isinstance(payload, dict):
            _fail(f"outline[{index}]", "outline_payload", "JSON object", type(payload).__name__)
        payloads.append(payload)
    return tuple(payloads)


def _restore_outline(payloads: tuple[dict[str, Any], ...]) -> list[Any]:
    from docling.utils.pdf_outline import _PdfOutlineItem

    return [_PdfOutlineItem.model_validate(payload) for payload in payloads]


class GateBStandardPdfPipeline(StandardPdfPipeline):
    """Capture transient evidence, then delegate unchanged global assembly to Docling."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.gate_b_captures: list[CapturedAssembly] = []

    def _assemble_document(self, conv_res: Any) -> Any:
        """Capture exact pages/outline immediately before Docling consumes the outline."""
        self.gate_b_captures.append(
            CapturedAssembly(
                pages=tuple(capture_page_evidence(page) for page in conv_res.pages),
                outline=_outline_payload(conv_res),
            )
        )
        return super()._assemble_document(conv_res)

    def take_capture(self) -> CapturedAssembly:
        """Return the sole pending capture and remove it from pipeline state."""
        if len(self.gate_b_captures) != 1:
            _fail(
                "pipeline.gate_b_captures",
                "one_pending_capture",
                1,
                len(self.gate_b_captures),
            )
        return self.gate_b_captures.pop()

    def assemble_captured_pages(
        self,
        *,
        template_result: Any,
        pages: tuple[PageEvidence, ...],
        outline: tuple[dict[str, Any], ...],
    ) -> Any:
        """Run Docling global assembly once over restored pages and exact captured outline."""
        from docling.datamodel.document import ConversionResult

        aggregate = ConversionResult(
            input=template_result.input,
            pages=[restore_page_evidence(page) for page in pages],
        )
        aggregate._pdf_outline = _restore_outline(outline)
        # Call the maintained implementation directly so this aggregate pass is not recaptured.
        return super()._assemble_document(aggregate)


__all__ = [
    "CapturedAssembly",
    "CapturedRange",
    "ExactOutputs",
    "GateBComparisonError",
    "GateBStandardPdfPipeline",
    "PageEvidence",
    "assert_exact_outputs",
    "assert_exact_page_evidence",
    "assert_exact_split_vs_contiguous",
    "capture_page_evidence",
    "restore_page_evidence",
    "select_core_page_evidence",
    "validate_conversion_result",
]
