"""Offline behavior tests for retained chunk page evidence."""

from __future__ import annotations

from pathlib import Path
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
from er_commons.chunked_conversion.runtime.docling_adapter import DoclingAdapter


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


def test_live_cluster_is_normalized_to_ordered_bottom_left_bbox() -> None:
    table = {
        "label": "table",
        "page_no": 42,
        "cluster": {"bbox": {"l": 157.0, "t": 277.0, "r": 454.0, "b": 358.0}},
    }

    normalized = DoclingAdapter._normalize_live_element(table, page_height=792.0)

    assert normalized["prov"] == [
        {
            "page_no": 42,
            "bbox": {"l": 157.0, "b": 434.0, "r": 454.0, "t": 515.0},
        }
    ]


class _OutlineItem(BaseModel):
    title: str
    level: int
    page_no: int
    y_top: float


def test_pipeline_captures_exact_outline_without_global_assembly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

    def forbidden(_pipeline: Any, _result: Any) -> object:
        raise AssertionError("range conversion must not run global assembly")

    monkeypatch.setattr(StandardPdfPipeline, "_assemble_document", forbidden)
    pipeline = object.__new__(PageCapturePdfPipeline)
    pipeline.pending_captures = []
    result = SimpleNamespace(
        pages=[_page(421), _page(422)],
        _pdf_outline=[_OutlineItem(title="Section", level=2, page_no=421, y_top=44.5)],
    )

    returned = pipeline._assemble_document(result)
    capture = pipeline.take_capture()

    assert returned is result
    assert capture.outline == ({"title": "Section", "level": 2, "page_no": 421, "y_top": 44.5},)
    assert tuple(page.page_no for page in capture.pages) == (421, 422)
    assert capture.page_object_ids == tuple(id(page) for page in result.pages)
    assert result._pdf_outline == [_OutlineItem(title="Section", level=2, page_no=421, y_top=44.5)]


def test_pipeline_skips_enrichment_without_global_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

    def forbidden(_pipeline: Any, _result: Any) -> object:
        raise AssertionError("range conversion must not enrich a global document")

    monkeypatch.setattr(StandardPdfPipeline, "_enrich_document", forbidden)
    pipeline = object.__new__(PageCapturePdfPipeline)
    result = SimpleNamespace(document=None)

    assert pipeline._enrich_document(result) is result


def test_adapter_reports_conversion_failure_before_missing_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from er_commons.chunked_conversion.runtime import docling_adapter as adapter_module

    result = SimpleNamespace(
        status=SimpleNamespace(value="failure"),
        errors=[],
        pages=[],
    )
    converter = SimpleNamespace(convert=lambda *_args, **_kwargs: result)
    prepared = SimpleNamespace(
        model_inventory_path=tmp_path / "inventory.json",
        model_inventory=object(),
        source=SimpleNamespace(
            source_path=tmp_path / "source.pdf",
            source_page_count=1,
            source_byte_size=1,
        ),
    )
    adapter = DoclingAdapter()
    monkeypatch.setattr(adapter_module, "verify_model_files", lambda *_args: None)
    monkeypatch.setattr(adapter, "_build_converter", lambda _prepared: (converter, None, None))

    def forbidden(_converter: Any) -> Any:
        raise AssertionError("failed conversion must be validated before capture lookup")

    monkeypatch.setattr(adapter, "_pipeline", forbidden)

    with pytest.raises(PageEvidenceError, match="clean_conversion_success"):
        adapter.convert_range(
            prepared,
            PageInterval(start=1, end=1),
            range_id="failed-range",
            data_root=tmp_path,
            log_path=tmp_path / "worker.log",
        )


def test_adapter_uses_exact_successful_capture_without_recapturing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from er_commons.chunked_conversion.page_evidence import CapturedAssembly
    from er_commons.chunked_conversion.runtime import docling_adapter as adapter_module

    page = _page(1)
    evidence = capture_page_evidence(page)
    capture = CapturedAssembly(
        pages=(evidence,),
        page_object_ids=(id(page),),
        outline=({"title": "Captured", "level": 1, "page_no": 1, "y_top": 10.0},),
    )
    result = SimpleNamespace(
        status=SimpleNamespace(value="success"),
        errors=[],
        pages=[page],
    )
    converter = SimpleNamespace(convert=lambda *_args, **_kwargs: result)
    pipeline = SimpleNamespace(take_capture=lambda: capture)
    prepared = SimpleNamespace(
        model_inventory_path=tmp_path / "inventory.json",
        model_inventory=object(),
        source=SimpleNamespace(
            source_id="source",
            source_path=tmp_path / "source.pdf",
            source_page_count=1,
            source_byte_size=1,
        ),
    )
    adapter = DoclingAdapter()
    projection = SimpleNamespace(page_no=1)

    def forbidden_image_read(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("adapter consistency validation must not reread raster bytes")

    monkeypatch.setattr(adapter_module, "verify_model_files", lambda *_args: None)
    monkeypatch.setattr(adapter, "_build_converter", lambda _prepared: (converter, None, None))
    monkeypatch.setattr(adapter, "_pipeline", lambda _converter: pipeline)
    monkeypatch.setattr(adapter, "_alignment_record", lambda _page: {"page_no": 1})
    monkeypatch.setattr(adapter, "_projection", lambda *_args, **_kwargs: projection)
    monkeypatch.setattr(type(page), "get_image", forbidden_image_read)

    conversion = adapter.convert_range(
        prepared,
        PageInterval(start=1, end=1),
        range_id="successful-range",
        data_root=tmp_path,
        log_path=tmp_path / "worker.log",
    )

    assert conversion.pages == (evidence,)
    assert conversion.outline == capture.outline
    assert conversion.alignment_pages == ({"page_no": 1},)
    assert conversion.projections == (projection,)


def test_adapter_rejects_page_mutated_after_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from er_commons.chunked_conversion.page_evidence import CapturedAssembly
    from er_commons.chunked_conversion.runtime import docling_adapter as adapter_module

    page = _page(1)
    evidence = capture_page_evidence(page)
    capture = CapturedAssembly(
        pages=(evidence,),
        page_object_ids=(id(page),),
        outline=(),
    )
    result = SimpleNamespace(
        status=SimpleNamespace(value="success"),
        errors=[],
        pages=[page],
    )

    def convert(*_args: Any, **_kwargs: Any) -> Any:
        page.assembled.elements[0].text = "mutated after capture"
        return result

    converter = SimpleNamespace(convert=convert)
    pipeline = SimpleNamespace(take_capture=lambda: capture)
    prepared = SimpleNamespace(
        model_inventory_path=tmp_path / "inventory.json",
        model_inventory=object(),
        source=SimpleNamespace(
            source_id="source",
            source_path=tmp_path / "source.pdf",
            source_page_count=1,
            source_byte_size=1,
        ),
    )
    adapter = DoclingAdapter()
    monkeypatch.setattr(adapter_module, "verify_model_files", lambda *_args: None)
    monkeypatch.setattr(adapter, "_build_converter", lambda _prepared: (converter, None, None))
    monkeypatch.setattr(adapter, "_pipeline", lambda _converter: pipeline)

    with pytest.raises(
        PageEvidenceError,
        match=r"page_payload.*captured_page_semantics",
    ):
        adapter.convert_range(
            prepared,
            PageInterval(start=1, end=1),
            range_id="mutated-range",
            data_root=tmp_path,
            log_path=tmp_path / "worker.log",
        )


def test_pipeline_requires_exactly_one_pending_capture() -> None:
    pipeline = object.__new__(PageCapturePdfPipeline)
    pipeline.pending_captures = []
    with pytest.raises(PageEvidenceError, match="one_pending_capture"):
        pipeline.take_capture()
