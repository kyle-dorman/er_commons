"""Run and reconcile one complete Docling conversion."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.document_extraction.artifacts import result_errors
from er_commons.document_extraction.producer_artifacts import export_durable_result
from er_commons.document_extraction.producer_records import (
    ConversionObservation,
    MachineStatus,
)
from er_commons.document_extraction.producer_services import ProducerServices
from er_commons.document_extraction.runtime import offline_docling_environment, run_log
from er_commons.document_extraction.sources import CompleteResolvedSource
from er_commons.source_freeze import write_json_atomic


@dataclass(frozen=True)
class ConversionOutput:
    """Durable conversion payload plus its validated terminal observation."""

    document_payload: dict[str, Any]
    assets: list[dict[str, Any]]
    observation: ConversionObservation


def map_conversion_status(
    raw_status: str,
    *,
    errors: list[dict[str, Any]],
    warnings_out: list[str],
) -> MachineStatus:
    """Map every known Docling state into the project machine vocabulary."""
    if raw_status == "success":
        if errors:
            return "failed"
        return "complete_with_warnings" if warnings_out else "complete"
    if raw_status == "partial_success":
        return "partial"
    if raw_status in {"failure", "pending", "started", "skipped"}:
        return "failed"
    raise ValueError(f"unknown Docling conversion status: {raw_status}")


def conversion_page_numbers(
    document_payload: dict[str, Any],
    result: Any,
) -> list[int]:
    """Require Docling's document and conversion records to name the same pages."""
    document_pages = sorted(int(value) for value in document_payload.get("pages", {}))
    conversion_pages = [int(page.page_no) for page in result.pages]
    if len(conversion_pages) != len(set(conversion_pages)):
        raise ValueError("Docling conversion contains duplicate physical pages")
    if document_pages != sorted(conversion_pages):
        raise ValueError("Docling document pages differ from conversion-page records")
    return document_pages


def run_complete_conversion(
    *,
    converter: Any,
    source: CompleteResolvedSource,
    producer_root: Path,
    log_path: Path,
    services: ProducerServices,
) -> ConversionOutput:
    """Convert, export durable records, write metrics, and enforce page coverage."""
    wall_started = services.monotonic()
    cpu_started = services.process_time()
    with offline_docling_environment(), run_log(log_path):
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            with services.memory_observation() as memory:
                result = converter.convert(
                    source.source_path,
                    raises_on_error=False,
                    max_num_pages=source.source_page_count,
                    max_file_size=source.source_byte_size,
                    page_range=(1, source.source_page_count),
                )

    python_warnings = [str(item.message) for item in captured]
    errors = result_errors(result)
    raw_status = str(getattr(result.status, "value", result.status))
    status = map_conversion_status(
        raw_status,
        errors=errors,
        warnings_out=[*source.warnings, *python_warnings],
    )
    document_payload, assets = export_durable_result(result, producer_root)
    converted_pages = conversion_page_numbers(document_payload, result)
    expected_pages = list(range(1, source.source_page_count + 1))
    observation = ConversionObservation(
        source_id=source.source_id,
        raw_status=raw_status,
        status=status,
        errors=errors,
        captured_python_warnings=python_warnings,
        source_manifest_warnings=source.warnings,
        expected_physical_pages=expected_pages,
        converted_physical_pages=converted_pages,
        page_coverage_complete=converted_pages == expected_pages,
        asset_count=len(assets),
        wall_seconds=services.monotonic() - wall_started,
        cpu_seconds=services.process_time() - cpu_started,
        peak_rss_bytes=memory.peak_rss_bytes,
    )
    write_json_atomic(
        producer_root / "docling" / "conversion_observation.json",
        observation.model_dump(mode="json"),
    )
    if observation.status not in {"complete", "complete_with_warnings"}:
        raise RuntimeError(f"Docling conversion did not complete: {raw_status}")
    if not observation.page_coverage_complete:
        raise RuntimeError("Docling conversion did not cover the complete document")
    return ConversionOutput(
        document_payload=document_payload,
        assets=assets,
        observation=observation,
    )
