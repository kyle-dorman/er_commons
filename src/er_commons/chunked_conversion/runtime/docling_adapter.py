"""Narrow compatibility boundary around Docling's range and global APIs."""

from __future__ import annotations

import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from er_commons.chunked_conversion.page_evidence import (
    PageCapturePdfPipeline,
    PageEvidence,
    validate_conversion_result,
)
from er_commons.chunked_conversion.range_contract import PageInterval
from er_commons.chunked_conversion.runtime.diagnostics import ChunkedConversionError
from er_commons.document_parsing.content_parsing.conversion_identity import (
    COMMON_HEADING_HIERARCHY,
)
from er_commons.document_parsing.content_parsing.page_projection import (
    PageEvidenceProjection,
    project_page_evidence,
)
from er_commons.document_parsing.content_parsing.preparation import PreparedContentParsing
from er_commons.document_parsing.content_parsing.routing import (
    layout_table_observations,
    page_features,
)
from er_commons.document_parsing.content_parsing.runtime import (
    MemorySampler,
    build_converter_options,
    offline_docling_environment,
    run_log,
    verify_model_files,
)
from er_commons.document_parsing.content_parsing.table_markers import markers_before_first_table


@dataclass(frozen=True)
class RangeConversion:
    """Docling evidence captured immediately before whole-document interpretation."""

    pages: tuple[PageEvidence, ...]
    outline: tuple[dict[str, Any], ...]
    alignment_pages: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]
    wall_seconds: float
    cpu_seconds: float
    peak_rss_bytes: int
    projections: tuple[PageEvidenceProjection, ...]


@dataclass(frozen=True)
class GlobalAssembly:
    """Whole-document interpretation result plus bounded resource observations."""

    document: Any
    warnings: tuple[str, ...]
    wall_seconds: float
    cpu_seconds: float
    peak_rss_bytes: int


class DoclingAdapter:
    """Own every private Docling API used by restartable chunk conversion."""

    def convert_range(
        self,
        prepared: PreparedContentParsing,
        interval: PageInterval,
        *,
        range_id: str,
        data_root: Path,
        log_path: Path,
    ) -> RangeConversion:
        """Convert one bounded range and capture its pre-global page state."""
        verify_model_files(data_root, prepared.model_inventory_path, prepared.model_inventory)
        converter, _options, _backend = self._build_converter(prepared)
        started = time.monotonic()
        cpu_started = time.process_time()
        with offline_docling_environment(), run_log(log_path):
            with warnings.catch_warnings(record=True) as caught, MemorySampler() as sampler:
                warnings.simplefilter("always")
                result = converter.convert(
                    prepared.source.source_path,
                    page_range=(interval.start, interval.end),
                    max_num_pages=prepared.source.source_page_count,
                    max_file_size=prepared.source.source_byte_size,
                    raises_on_error=False,
                )
        pages = validate_conversion_result(result, interval, path="range_conversion")
        capture = self._pipeline(converter).take_capture()
        if capture.pages != pages:
            raise ChunkedConversionError(
                "capture_differs",
                stage="range_conversion",
                path=f"pages[{interval.start}:{interval.end}]",
            )
        return RangeConversion(
            pages=capture.pages,
            outline=capture.outline,
            alignment_pages=tuple(self._alignment_record(page) for page in result.pages),
            warnings=tuple(str(item.message) for item in caught),
            wall_seconds=time.monotonic() - started,
            cpu_seconds=time.process_time() - cpu_started,
            peak_rss_bytes=sampler.peak_rss_bytes,
            projections=tuple(
                self._projection(
                    prepared.source.source_id,
                    prepared.source.source_path,
                    live_page,
                    range_id=range_id,
                )
                for live_page in result.pages
            ),
        )

    def _projection(
        self,
        source_id: str,
        source_path: Path,
        page: Any,
        *,
        range_id: str,
    ) -> PageEvidenceProjection:
        """Build page-local routing evidence from the captured range page."""
        assembled = getattr(page, "assembled", None)
        elements = list(getattr(assembled, "elements", ())) if assembled is not None else []
        element_payloads = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in elements
        ]
        page_height = float(getattr(getattr(page, "size", None), "height", 0.0))
        normalized_elements = [
            self._normalize_live_element(item, page_height=page_height) for item in element_payloads
        ]
        table_payloads = [
            item for item in normalized_elements if item.get("label") in {"table", "document_index"}
        ]
        document_payload = {
            "tables": table_payloads,
            "texts": [
                item
                for item in normalized_elements
                if item.get("label") not in {"table", "document_index"}
            ],
        }
        observations = layout_table_observations(document_payload, page.page_no)
        return project_page_evidence(
            source_id=source_id,
            range_id=str(range_id),
            page_number=page.page_no,
            features=page_features(
                source_path,
                page.page_no,
            ),
            layout_table_observations=observations,
            boundary_markers_before_first_table=markers_before_first_table(
                document_payload, page.page_no, observations
            ),
        )

    @staticmethod
    def _normalize_live_element(element: dict[str, Any], *, page_height: float) -> dict[str, Any]:
        """Expose live pre-global clusters as router-compatible provenance."""
        if element.get("prov") or not isinstance(element.get("cluster"), dict):
            return element
        bbox = element["cluster"].get("bbox")
        if not isinstance(bbox, dict) or page_height <= 0:
            return element
        normalized = dict(element)
        normalized["prov"] = [
            {
                "page_no": int(element["page_no"]),
                "bbox": {
                    "l": float(bbox["l"]),
                    "b": page_height - float(bbox["b"]),
                    "r": float(bbox["r"]),
                    "t": page_height - float(bbox["t"]),
                },
            }
        ]
        return normalized

    def assemble_global(
        self,
        prepared: PreparedContentParsing,
        pages: list[Any],
        outline: tuple[dict[str, Any], ...],
        *,
        data_root: Path,
    ) -> GlobalAssembly:
        """Run reading order and heading inference once over canonical range pages."""
        verify_model_files(data_root, prepared.model_inventory_path, prepared.model_inventory)
        converter, _options, backend = self._build_converter(prepared)
        from docling.datamodel.base_models import AssembledUnit, InputFormat
        from docling.datamodel.document import ConversionResult, InputDocument
        from docling.datamodel.settings import DocumentLimits
        from docling.utils.pdf_outline import _PdfOutlineItem

        converter.initialize_pipeline(InputFormat.PDF)
        pipeline = self._pipeline(converter)
        input_document = InputDocument(
            prepared.source.source_path,
            format=InputFormat.PDF,
            backend=backend,
            limits=DocumentLimits(
                max_num_pages=prepared.source.source_page_count,
                max_file_size=prepared.source.source_byte_size,
                page_range=(1, prepared.source.source_page_count),
            ),
        )
        aggregate = ConversionResult(input=input_document, pages=pages)
        aggregate._pdf_outline = [_PdfOutlineItem.model_validate(item) for item in outline]
        elements = [item for page in pages for item in page.assembled.elements]
        headers = [item for page in pages for item in page.assembled.headers]
        body = [item for page in pages for item in page.assembled.body]
        aggregate.assembled = AssembledUnit(elements=elements, headers=headers, body=body)
        started = time.monotonic()
        cpu_started = time.process_time()
        try:
            with warnings.catch_warnings(record=True) as caught, MemorySampler() as sampler:
                warnings.simplefilter("always")
                aggregate.document = pipeline.reading_order_model(aggregate)
                parsed_pages = {
                    page.page_no: page.parsed_page
                    for page in aggregate.pages
                    if page.parsed_page is not None
                }
                outline_items = aggregate._pdf_outline
                for page in aggregate.pages:
                    cast(Any, page).assembled = None
                cast(Any, aggregate).assembled = None
                elements.clear()
                headers.clear()
                body.clear()
                aggregate.document = pipeline.heading_hierarchy_model.assign_heading_levels(
                    aggregate.document,
                    parsed_pages=parsed_pages,
                    outline=outline_items,
                )
                aggregate._pdf_outline = None
                parsed_pages.clear()
                for page in aggregate.pages:
                    page.parsed_page = None
        finally:
            self.release_backend(input_document)
        if aggregate.document is None:
            raise ChunkedConversionError(
                "missing_document",
                stage="aggregate",
                path="global_interpretation",
            )
        return GlobalAssembly(
            document=aggregate.document,
            warnings=tuple(str(item.message) for item in caught),
            wall_seconds=time.monotonic() - started,
            cpu_seconds=time.process_time() - cpu_started,
            peak_rss_bytes=sampler.peak_rss_bytes,
        )

    def _build_converter(self, prepared: PreparedContentParsing) -> tuple[Any, Any, Any]:
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import DocumentConverter, PdfFormatOption

        options, accepted = build_converter_options(
            prepared.models_root,
            thread_count=prepared.config.thread_count,
            heading_hierarchy_options=COMMON_HEADING_HIERARCHY,
        )
        converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=PageCapturePdfPipeline,
                    backend=accepted.backend,
                    pipeline_options=options,
                )
            },
        )
        return converter, options, accepted.backend

    def _pipeline(self, converter: Any) -> PageCapturePdfPipeline:
        matches = [
            pipeline
            for pipeline in converter.initialized_pipelines.values()
            if isinstance(pipeline, PageCapturePdfPipeline)
        ]
        if len(matches) != 1:
            raise ChunkedConversionError(
                "pipeline_count",
                stage="docling_adapter",
                path="converter.initialized_pipelines",
                expected=1,
                actual=len(matches),
            )
        return matches[0]

    def release_backend(self, input_document: Any) -> None:
        """Release Docling's PDF backend and surface cleanup failures."""
        try:
            input_document._backend.unload()
        except Exception as error:
            raise ChunkedConversionError(
                "backend_unload",
                stage="docling_adapter",
                path="input_document._backend",
                actual=str(error),
            ) from error

    def _alignment_record(self, page: Any) -> dict[str, Any]:
        from er_commons.document_parsing.heading_evidence_parsing.alignment_projection import (
            alignment_record,
        )

        if page.size is None or page.parsed_page is None:
            raise ChunkedConversionError(
                "alignment_source",
                stage="range_conversion",
                path=f"pages[{page.page_no}]",
            )
        return alignment_record(
            page_no=int(page.page_no),
            width=float(page.size.width),
            height=float(page.size.height),
            textline_cells=list(page.parsed_page.textline_cells),
        )


__all__ = ["DoclingAdapter", "GlobalAssembly", "RangeConversion"]
