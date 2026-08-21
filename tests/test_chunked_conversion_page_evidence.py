"""Offline behavior tests for retained chunk page evidence."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from PIL import Image
from pydantic import BaseModel

from er_commons.chunked_conversion.page_evidence import (
    PageCapturePdfPipeline,
    PageEvidenceError,
    capture_page_evidence,
    validate_conversion_result,
)
from er_commons.chunked_conversion.range_contract import PageInterval


def _page(page_no: int, *, color: tuple[int, int, int] = (10, 20, 30)) -> Any:
    from docling.datamodel.base_models import AssembledUnit, Cluster, Page, TextElement
    from docling_core.types.doc.base import BoundingBox, Size
    from docling_core.types.doc.labels import DocItemLabel

    cluster = Cluster(
        id=1,
        label=DocItemLabel.TEXT,
        bbox=BoundingBox(l=5, b=10, r=80, t=25),
    )
    element = TextElement(
        label=DocItemLabel.TEXT,
        id=1,
        page_no=page_no,
        cluster=cluster,
        text=f"page {page_no}",
    )
    page = Page(
        page_no=page_no,
        size=Size(width=100, height=200),
        assembled=AssembledUnit(elements=[element], body=[element], headers=[]),
    )
    page._default_image_scale = 2.0
    page._image_cache = {2.0: Image.new("RGB", (8, 12), color=color)}
    return page


def test_page_evidence_preserves_ambiguous_element_types_and_shared_membership() -> None:
    from docling.datamodel.base_models import (
        AssembledUnit,
        Cluster,
        ContainerElement,
        FigureElement,
    )
    from docling_core.types.doc.base import BoundingBox
    from docling_core.types.doc.labels import DocItemLabel

    page = _page(12)
    cluster = Cluster(
        id=2,
        label=DocItemLabel.KEY_VALUE_REGION,
        bbox=BoundingBox(l=1, b=2, r=30, t=40),
    )
    container = ContainerElement(
        label=DocItemLabel.KEY_VALUE_REGION,
        id=2,
        page_no=12,
        cluster=cluster,
    )
    figure = FigureElement(
        label=DocItemLabel.PICTURE,
        id=3,
        page_no=12,
        cluster=cluster.model_copy(update={"id": 3, "label": DocItemLabel.PICTURE}),
    )
    page.assembled = AssembledUnit(
        elements=[container, figure],
        body=[container, figure],
        headers=[],
    )

    evidence = capture_page_evidence(page)

    assert evidence.assembled_element_types == ("ContainerElement", "FigureElement")
    assert evidence.assembled_body_indices == (0, 1)
    assert evidence.assembled_header_indices == ()


def test_conversion_validation_requires_clean_ordered_read_coverage() -> None:
    result = SimpleNamespace(
        status=SimpleNamespace(value="success"),
        errors=[],
        pages=[_page(12), _page(13), _page(14), _page(15)],
    )
    evidence = validate_conversion_result(
        result,
        PageInterval(start=12, end=15),
        path="contiguous",
    )

    assert tuple(page.page_no for page in evidence) == (12, 13, 14, 15)

    result.pages = [result.pages[1], result.pages[0], *result.pages[2:]]
    with pytest.raises(PageEvidenceError, match="ordered_read_coverage"):
        validate_conversion_result(
            result,
            PageInterval(start=12, end=15),
            path="contiguous",
        )


class _OutlineItem(BaseModel):
    title: str
    level: int
    page_no: int
    y_top: float


def test_pipeline_captures_exact_outline_then_delegates_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

    sentinel = object()
    calls: list[Any] = []

    def delegated(_pipeline: Any, result: Any) -> object:
        calls.append(result)
        result._pdf_outline = None
        return sentinel

    monkeypatch.setattr(StandardPdfPipeline, "_assemble_document", delegated)
    pipeline = object.__new__(PageCapturePdfPipeline)
    pipeline.pending_captures = []
    result = SimpleNamespace(
        pages=[_page(421), _page(422)],
        _pdf_outline=[_OutlineItem(title="Section", level=2, page_no=421, y_top=44.5)],
    )

    returned = pipeline._assemble_document(result)
    capture = pipeline.take_capture()

    assert returned is sentinel
    assert calls == [result]
    assert capture.outline == ({"title": "Section", "level": 2, "page_no": 421, "y_top": 44.5},)
    assert tuple(page.page_no for page in capture.pages) == (421, 422)
    assert result._pdf_outline is None


def test_pipeline_requires_exactly_one_pending_capture() -> None:
    pipeline = object.__new__(PageCapturePdfPipeline)
    pipeline.pending_captures = []
    with pytest.raises(PageEvidenceError, match="one_pending_capture"):
        pipeline.take_capture()
