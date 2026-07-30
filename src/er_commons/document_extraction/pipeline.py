"""Run the fixed clean document extraction and table-routing pilot.

The orchestration deliberately reads as a short sequence:

    load contracts
      -> verify sealed sources and models
      -> build one accepted converter
      -> convert six ranges sequentially
      -> invoke the complete clean table stage
      -> evaluate independent acceptance gates
      -> seal either acceptance or a reviewable failure
"""

from __future__ import annotations

import json
import logging
import os
import time
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.document_extraction.acceptance import evaluate_acceptance, require_acceptance
from er_commons.document_extraction.artifacts import (
    directory_bytes,
    export_result,
    read_jsonl,
    result_errors,
    write_jsonl,
)
from er_commons.document_extraction.comparison import (
    compare_range_outputs,
    compare_timings,
)
from er_commons.document_extraction.config import (
    PipelineConfig,
    SelectionSpec,
    contiguous_ranges,
    load_pipeline_config,
    load_selection_spec,
    range_name,
)
from er_commons.document_extraction.reporting import environment_record, seal_run
from er_commons.document_extraction.routing import (
    classify_page,
    layout_table_regions,
    page_features,
)
from er_commons.document_extraction.runtime import (
    MemorySampler,
    build_converter,
    configuration_record,
    verify_model_inventory,
)
from er_commons.document_extraction.sources import (
    ResolvedSource,
    load_sealed_manifest,
    resolve_sources,
)
from er_commons.document_extraction.table_stage import run_table_stage
from er_commons.source_freeze import write_json_atomic

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExtractionRange:
    """One verified source and contiguous physical-page range."""

    source: ResolvedSource
    first_page: int
    last_page: int
    name: str

    @property
    def page_keys(self) -> set[tuple[str, int]]:
        """Return source/page keys used by the acceptance policy."""
        return {
            (self.source.source_id, page) for page in range(self.first_page, self.last_page + 1)
        }


@contextmanager
def offline_docling_environment() -> Iterator[None]:
    """Set Docling's offline guards for the run and restore prior process state."""
    names = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
    previous = {name: os.environ.get(name) for name in names}
    os.environ.update({name: "1" for name in names})
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


@contextmanager
def run_log(path: Path) -> Iterator[None]:
    """Capture library and project logs while always removing the handler."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root_logger = logging.getLogger()
    previous_level = root_logger.level
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    try:
        yield
    finally:
        root_logger.removeHandler(handler)
        root_logger.setLevel(previous_level)
        handler.close()


def _resolved_ranges(
    selection: SelectionSpec,
    sources: list[ResolvedSource],
) -> list[ExtractionRange]:
    """Join the selected range order to verified source paths."""
    by_source = {source.source_id: source for source in sources}
    ranges = []
    for selected_source in selection.sources:
        source = by_source[selected_source.source_id]
        for first_page, last_page in contiguous_ranges(selected_source):
            ranges.append(
                ExtractionRange(
                    source=source,
                    first_page=first_page,
                    last_page=last_page,
                    name=range_name(source.source_id, first_page, last_page),
                )
            )
    return ranges


def convert_review_range(
    converter: Any,
    format_option: Any,
    source: ResolvedSource,
    first_page: int,
    last_page: int,
    destination: Path,
) -> dict[str, Any]:
    """Convert one range, export it, and return its measured timing record."""
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    with warnings.catch_warnings(record=True) as warning_records:
        warnings.simplefilter("always")
        with MemorySampler() as memory:
            result = converter.convert(
                source.source_path,
                raises_on_error=False,
                page_range=(first_page, last_page),
            )
    wall_seconds = time.perf_counter() - started_wall
    cpu_seconds = time.process_time() - started_cpu
    export_result(result, destination)

    errors = result_errors(result)
    status = str(getattr(result.status, "value", result.status))
    conversion_record = {
        "source_id": source.source_id,
        "source_sha256": source.source_sha256,
        "first_page": first_page,
        "last_page": last_page,
        "status": status,
        "errors": errors,
        "captured_python_warnings": [str(item.message) for item in warning_records],
        "source_manifest_warnings": source.warnings,
        "pipeline_class": (
            f"{format_option.pipeline_cls.__module__}.{format_option.pipeline_cls.__name__}"
        ),
        "backend_class": (f"{format_option.backend.__module__}.{format_option.backend.__name__}"),
    }
    write_json_atomic(destination / "conversion_record.json", conversion_record)
    timing = {
        "source_id": source.source_id,
        "first_page": first_page,
        "last_page": last_page,
        "selected_page_count": last_page - first_page + 1,
        "status": status,
        "wall_seconds": wall_seconds,
        "cpu_seconds": cpu_seconds,
        "peak_rss_bytes": memory.peak_rss_bytes,
        "output_bytes": directory_bytes(destination),
        "error_count": len(errors),
    }
    LOGGER.info(
        "Converted source=%s pages=%s-%s status=%s seconds=%.2f",
        source.source_id,
        first_page,
        last_page,
        status,
        wall_seconds,
    )
    return timing


def _classify_range_pages(
    range_root: Path,
    source: ResolvedSource,
    first_page: int,
    last_page: int,
    config: PipelineConfig,
) -> list[dict[str, Any]]:
    """Classify every converted page without bypassing table orchestration."""
    document_payload = json.loads((range_root / "document.json").read_text())
    routes = []
    for page_number in range(first_page, last_page + 1):
        regions = layout_table_regions(document_payload, page_number)
        route = classify_page(
            page_features(source.source_path, page_number),
            regions,
            config.strict_table_dominant_thresholds,
            config.numeric_table_bearing_thresholds,
        )
        route["source_id"] = source.source_id
        routes.append(route)
    return routes


def run_document_extraction(data_root: Path, config_path: Path) -> Path:
    """Run Docling, route tables, invoke the full table stage, and seal evidence."""
    started = time.perf_counter()
    config, config_sha256 = load_pipeline_config(config_path)
    selection_path = config.selection_spec_path
    selection, selection_sha256 = load_selection_spec(selection_path)
    if selection.expected_selected_page_count != config.expected_selected_page_count:
        raise ValueError("selection page count differs from the pipeline contract")

    manifest = load_sealed_manifest(data_root, selection)
    sources = resolve_sources(data_root, selection, manifest)
    ranges = _resolved_ranges(selection, sources)
    if [item.name for item in ranges] != config.expected_range_names:
        raise ValueError("derived ranges differ from the fixed pipeline contract")

    root = (data_root / config.artifact_relative_root).resolve()
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"document pipeline artifact root is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    (root / "configuration.json").write_bytes(config_path.read_bytes())

    model_inventory_path = (data_root / config.model_inventory_relative_path).resolve()
    _inventory, models_root = verify_model_inventory(data_root, model_inventory_path)
    baseline_root = (data_root / config.baseline_run_relative_root).resolve()
    if not baseline_root.is_dir():
        raise FileNotFoundError(f"accepted Task 03A baseline is missing: {baseline_root}")

    log_path = root / "logs" / "document_extraction.log"
    timings: list[dict[str, Any]] = []
    routing_records: list[dict[str, Any]] = []
    with offline_docling_environment(), run_log(log_path):
        converter, options, format_option = build_converter(
            models_root,
            thread_count=config.thread_count,
        )
        write_json_atomic(
            root / "docling_configuration.json",
            configuration_record(config.configuration_id, options, format_option),
        )
        write_json_atomic(
            root / "environment.json",
            environment_record(config_path, selection_path, model_inventory_path),
        )
        for selected_range in ranges:
            range_root = root / "ranges" / selected_range.name
            timings.append(
                convert_review_range(
                    converter,
                    format_option,
                    selected_range.source,
                    selected_range.first_page,
                    selected_range.last_page,
                    range_root,
                )
            )
            routes = _classify_range_pages(
                range_root,
                selected_range.source,
                selected_range.first_page,
                selected_range.last_page,
                config,
            )
            routing_records.extend(routes)

    write_jsonl(root / "timings.jsonl", timings)
    write_jsonl(root / "page_routes.jsonl", routing_records)
    table_stage = run_table_stage(
        data_root,
        root,
        config,
        selection,
        sources,
        routing_records,
    )
    docling_comparison = compare_range_outputs(
        baseline_root,
        root,
        config.expected_range_names,
    )
    range_pages = {selected_range.name: selected_range.page_keys for selected_range in ranges}
    acceptance = evaluate_acceptance(
        docling_comparison,
        range_pages,
        routing_records,
        config.expected_page_routes,
        table_stage,
    )
    old_timings = read_jsonl(baseline_root / "timings.jsonl")
    timing_comparison = compare_timings(old_timings, timings)
    comparison_record = {
        "acceptance": acceptance,
        "docling": docling_comparison,
        "table_stage": table_stage,
        "timing": timing_comparison,
    }
    report_path = root / "comparison_to_task03a.json"
    write_json_atomic(report_path, comparison_record)
    manifest_path = seal_run(
        root,
        config,
        config_sha256,
        selection,
        selection_sha256,
        timings,
        acceptance,
        timing_comparison,
        started,
    )
    require_acceptance(acceptance, report_path)
    return manifest_path
