"""Offline tests for bounded Gate B page evidence and exact comparison."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest
from PIL import Image
from pydantic import BaseModel

from er_commons.chunked_conversion.gate_b import (
    CapturedRange,
    ExactOutputs,
    GateBComparisonError,
    GateBStandardPdfPipeline,
    PageEvidence,
    assert_exact_outputs,
    assert_exact_split_vs_contiguous,
    capture_page_evidence,
    restore_page_evidence,
    select_core_page_evidence,
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


def _evidence(page_no: int, *, token: str = "same") -> PageEvidence:
    evidence = capture_page_evidence(_page(page_no))
    return replace(
        evidence,
        page_payload={**evidence.page_payload, "gate_b_test_token": token},
    )


def test_page_evidence_round_trip_preserves_json_and_private_raster() -> None:
    original = capture_page_evidence(_page(7))

    restored = restore_page_evidence(original)
    repeated = capture_page_evidence(restored)

    assert repeated == original
    assert repeated.semantic_sha256 == original.semantic_sha256
    assert restored.page_no == 7
    assert restored.get_image(scale=2.0) is not None


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

    restored = restore_page_evidence(capture_page_evidence(page))

    assert restored.assembled is not None
    assert [type(item) for item in restored.assembled.elements] == [
        ContainerElement,
        FigureElement,
    ]
    assert restored.assembled.body[0] is restored.assembled.elements[0]
    assert restored.assembled.body[1] is restored.assembled.elements[1]


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
    with pytest.raises(GateBComparisonError, match="ordered_read_coverage"):
        validate_conversion_result(
            result,
            PageInterval(start=12, end=15),
            path="contiguous",
        )


def test_overlapping_children_compare_overlap_and_emit_each_core_once() -> None:
    pages = {page: _evidence(page) for page in range(12, 16)}
    left = CapturedRange(
        range_id="left",
        core=PageInterval(start=12, end=13),
        read=PageInterval(start=12, end=14),
        pages=(pages[12], pages[13], pages[14]),
    )
    right = CapturedRange(
        range_id="right",
        core=PageInterval(start=14, end=15),
        read=PageInterval(start=13, end=15),
        pages=(pages[13], pages[14], pages[15]),
    )

    selected = select_core_page_evidence(left, right)

    assert tuple(page.page_no for page in selected) == (12, 13, 14, 15)
    assert selected == (pages[12], pages[13], pages[14], pages[15])


def test_overlap_difference_fails_with_page_and_field_context() -> None:
    pages = {page: _evidence(page) for page in range(12, 16)}
    left = CapturedRange(
        "left",
        PageInterval(start=12, end=13),
        PageInterval(start=12, end=14),
        (pages[12], pages[13], pages[14]),
    )
    changed = replace(pages[14], page_payload={**pages[14].page_payload, "changed": True})
    right = CapturedRange(
        "right",
        PageInterval(start=14, end=15),
        PageInterval(start=13, end=15),
        (pages[13], changed, pages[15]),
    )

    with pytest.raises(
        GateBComparisonError,
        match=r"path=children\.overlap\[14\]\.page_payload invariant=exact_page_evidence",
    ):
        select_core_page_evidence(left, right)


def test_split_comparison_rejects_any_pre_global_page_difference() -> None:
    contiguous = tuple(_evidence(page) for page in range(85, 89))
    assert_exact_split_vs_contiguous(contiguous, contiguous)

    changed = (*contiguous[:2], replace(contiguous[2], image_pixels_sha256="f" * 64), contiguous[3])
    with pytest.raises(GateBComparisonError, match="image_pixels_sha256"):
        assert_exact_split_vs_contiguous(changed, contiguous)


def test_final_output_comparison_names_the_differing_projection() -> None:
    expected = ExactOutputs(
        document={"texts": []},
        heading_overlay=(),
        alignment_pages=({"page_no": 1},),
        assets=(),
        warnings=(),
    )
    assert_exact_outputs(expected, expected)

    changed = replace(expected, warnings=("new warning",))
    with pytest.raises(
        GateBComparisonError,
        match=r"path=split_vs_contiguous\.outputs\.warnings invariant=exact_output",
    ):
        assert_exact_outputs(expected, changed)


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
    pipeline = object.__new__(GateBStandardPdfPipeline)
    pipeline.gate_b_captures = []
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
    pipeline = object.__new__(GateBStandardPdfPipeline)
    pipeline.gate_b_captures = []
    with pytest.raises(GateBComparisonError, match="one_pending_capture"):
        pipeline.take_capture()
