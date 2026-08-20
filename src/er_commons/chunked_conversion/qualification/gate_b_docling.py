"""Narrow Docling adapter for Gate B conversion and stable-output export."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.artifact_io import write_json_atomic, write_json_atomic_streaming, write_jsonl
from er_commons.chunked_conversion.gate_b import (
    CapturedAssembly,
    ExactOutputs,
    GateBStandardPdfPipeline,
    validate_conversion_result,
)
from er_commons.chunked_conversion.qualification.gate_b_contracts import (
    SOURCE_ID,
    SOURCE_PAGE_COUNT,
    THREAD_COUNT,
    GateBContractError,
)
from er_commons.chunked_conversion.range_contract import PageInterval
from er_commons.document_parsing.content_parsing.conversion_identity import (
    COMMON_HEADING_HIERARCHY,
)
from er_commons.document_parsing.content_parsing.evidence import (
    _export_picture_assets,
    _externalize_embedded_images,
)
from er_commons.document_parsing.content_parsing.preparation import PreparedContentParsing
from er_commons.document_parsing.content_parsing.runtime import (
    MemorySampler,
    build_converter_options,
)
from er_commons.document_parsing.heading_evidence_parsing.alignment_projection import (
    alignment_record,
)
from er_commons.document_parsing.heading_evidence_parsing.heading_overlay import (
    split_heading_overlay,
)


@dataclass(frozen=True)
class BoundedConversion:
    """One bounded conversion result and its captured runtime evidence."""

    result: Any
    capture: CapturedAssembly
    warnings: tuple[str, ...]
    peak_rss_bytes: int


def convert_range(
    converter: Any, source_path: Path, interval: PageInterval, role: str
) -> BoundedConversion:
    """Convert and validate one bounded interval while capturing warnings and RSS."""
    with warnings.catch_warnings(record=True) as caught, MemorySampler() as sampler:
        warnings.simplefilter("always")
        result = converter.convert(
            source_path,
            page_range=(interval.start, interval.end),
            max_num_pages=SOURCE_PAGE_COUNT,
            max_file_size=source_path.stat().st_size,
            raises_on_error=False,
        )
    pages = validate_conversion_result(result, interval, path=f"conversions[{role}]")
    capture = gate_b_pipeline(converter).take_capture()
    if capture.pages != pages:
        raise GateBContractError(
            "capture_differs", f"conversions[{role}].capture", "validated pages differ"
        )
    return BoundedConversion(
        result=result,
        capture=capture,
        warnings=tuple(str(item.message) for item in caught),
        peak_rss_bytes=sampler.peak_rss_bytes,
    )


def build_gate_b_converter(prepared: PreparedContentParsing) -> tuple[Any, Any]:
    """Construct the accepted CPU converter with the capture adapter."""
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import DocumentConverter, PdfFormatOption

    options, accepted = build_converter_options(
        prepared.models_root,
        thread_count=THREAD_COUNT,
        heading_hierarchy_options=COMMON_HEADING_HIERARCHY,
    )
    format_option = PdfFormatOption(
        pipeline_cls=GateBStandardPdfPipeline,
        backend=accepted.backend,
        pipeline_options=options,
    )
    converter = DocumentConverter(
        allowed_formats=[InputFormat.PDF], format_options={InputFormat.PDF: format_option}
    )
    return converter, options


def gate_b_pipeline(converter: Any) -> GateBStandardPdfPipeline:
    """Return the sole initialized Gate B pipeline."""
    matches = [
        pipeline
        for pipeline in converter.initialized_pipelines.values()
        if isinstance(pipeline, GateBStandardPdfPipeline)
    ]
    if len(matches) != 1:
        raise GateBContractError(
            "pipeline_count",
            "converter.initialized_pipelines",
            f"expected 1 observed {len(matches)}",
        )
    return matches[0]


def export_exact(result: Any, root: Path, warning_rows: tuple[str, ...]) -> ExactOutputs:
    """Export the exact stable output projection for one conversion result."""
    producer = root / "documents" / SOURCE_ID / "producer"
    docling_root = producer / "docling"
    docling_root.mkdir(parents=True, exist_ok=False)
    assets = _export_picture_assets(result.document, producer)
    externalization = _externalize_embedded_images(result.document)
    document, overlay = split_heading_overlay(result.document.export_to_dict())
    alignment = range_alignment_records(result)
    write_json_atomic_streaming(docling_root / "document.json", document)
    write_jsonl(docling_root / "heading_overlay.jsonl", overlay)
    write_jsonl(docling_root / "alignment_pages.jsonl", alignment)
    write_json_atomic(
        producer / "asset_inventory.json",
        {"assets": assets, "image_externalization": externalization},
    )
    return ExactOutputs(
        document=document,
        heading_overlay=tuple(overlay),
        alignment_pages=alignment,
        assets=tuple(assets),
        warnings=warning_rows,
    )


def range_alignment_records(result: Any) -> tuple[dict[str, Any], ...]:
    """Project ordered physical pages without assuming full-document coverage."""
    records: list[dict[str, Any]] = []
    previous = 0
    for page in result.pages:
        page_no = int(page.page_no)
        if page_no <= previous or page.size is None or page.parsed_page is None:
            raise GateBContractError(
                "invalid_alignment_page", f"alignment_pages[{page_no}]", "incomplete or unordered"
            )
        records.append(
            alignment_record(
                page_no=page_no,
                width=float(page.size.width),
                height=float(page.size.height),
                textline_cells=list(page.parsed_page.textline_cells),
            )
        )
        previous = page_no
    return tuple(records)


__all__ = [
    "BoundedConversion",
    "build_gate_b_converter",
    "convert_range",
    "export_exact",
    "gate_b_pipeline",
]
