"""Bounded Docling conversion without complete-document publication semantics."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.document_extraction.artifacts import result_errors
from er_commons.document_extraction.producer_conversion import (
    conversion_page_numbers,
    map_conversion_status,
)
from er_commons.document_extraction.producer_services import ProducerServices
from er_commons.document_extraction.runtime import offline_docling_environment, run_log
from er_commons.document_extraction.sources import CompleteResolvedSource
from er_commons.source_freeze import write_json_atomic


@dataclass(frozen=True)
class RangeDiagnostic:
    """One bounded conversion result and its machine observations."""

    document_payload: dict[str, Any]
    converted_pages: list[int]
    raw_status: str
    status: str
    errors: list[dict[str, Any]]
    source_manifest_warnings: list[str]
    conversion_warnings: list[str]
    wall_seconds: float
    cpu_seconds: float
    peak_rss_bytes: int


def convert_range(
    converter: Any,
    source: CompleteResolvedSource,
    first_page: int,
    last_page: int,
    output_root: Path,
    services: ProducerServices,
) -> RangeDiagnostic:
    """Convert one selected contiguous range and retain only diagnostic records."""
    wall_started = services.monotonic()
    cpu_started = services.process_time()
    output_root.mkdir(parents=True, exist_ok=False)
    with offline_docling_environment(), run_log(output_root / "conversion.log"):
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            with services.memory_observation() as memory:
                result = converter.convert(
                    source.source_path,
                    raises_on_error=False,
                    max_num_pages=source.source_page_count,
                    max_file_size=source.source_byte_size,
                    page_range=(first_page, last_page),
                )
    python_warnings = [str(item.message) for item in captured]
    errors = result_errors(result)
    raw_status = str(getattr(result.status, "value", result.status))
    status = map_conversion_status(
        raw_status,
        errors=errors,
        warnings_out=python_warnings,
    )
    document_payload = result.document.export_to_dict()
    converted_pages = conversion_page_numbers(document_payload, result)
    wall_seconds = services.monotonic() - wall_started
    cpu_seconds = services.process_time() - cpu_started
    observation = {
        "diagnostic_scope": "bounded_page_range",
        "source_id": source.source_id,
        "requested_physical_pages": list(range(first_page, last_page + 1)),
        "converted_physical_pages": converted_pages,
        "raw_status": raw_status,
        "status": status,
        "errors": errors,
        "captured_python_warnings": python_warnings,
        "source_warning_evidence": "../../source_warnings.json",
        "wall_seconds": wall_seconds,
        "cpu_seconds": cpu_seconds,
        "peak_rss_bytes": memory.peak_rss_bytes,
    }
    write_json_atomic(output_root / "document.json", document_payload)
    write_json_atomic(
        output_root / "conversion_pages.json",
        {
            "pages": [page.model_dump(mode="json") for page in result.pages],
            "assembled": result.assembled.model_dump(mode="json"),
            "confidence": result.confidence.model_dump(mode="json"),
        },
    )
    write_json_atomic(output_root / "observation.json", observation)
    return RangeDiagnostic(
        document_payload=document_payload,
        converted_pages=converted_pages,
        raw_status=raw_status,
        status=status,
        errors=errors,
        source_manifest_warnings=source.warnings,
        conversion_warnings=python_warnings,
        wall_seconds=wall_seconds,
        cpu_seconds=cpu_seconds,
        peak_rss_bytes=memory.peak_rss_bytes,
    )
