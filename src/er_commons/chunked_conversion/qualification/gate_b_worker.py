"""Isolated seam execution and publication for Gate B."""

from __future__ import annotations

import time
import traceback
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.artifact_io import (
    artifact_inventory,
    canonical_json_sha256,
    read_json_object,
    sha256_file,
    write_json_atomic,
)
from er_commons.chunked_conversion.gate_b import (
    CapturedRange,
    ExactOutputs,
    GateBStandardPdfPipeline,
    PageEvidence,
    assert_exact_outputs,
    assert_exact_split_vs_contiguous,
    select_core_page_evidence,
)
from er_commons.chunked_conversion.qualification.gate_b_contracts import (
    CONVERSION_ID,
    THREAD_COUNT,
    GateBContractError,
    GateBWorkerSpec,
    parse_worker_spec,
    seam_payload,
)
from er_commons.chunked_conversion.qualification.gate_b_docling import (
    BoundedConversion,
    build_gate_b_converter,
    convert_range,
    export_exact,
    gate_b_pipeline,
)
from er_commons.chunked_conversion.qualification.gate_b_inputs import verified_inputs
from er_commons.chunked_conversion.qualification.gate_b_trace import (
    compare_sealed_page_trace,
    subset_trace,
    trace_from_outputs,
)
from er_commons.document_parsing.content_parsing.evidence import verify_inventory
from er_commons.document_parsing.content_parsing.runtime import (
    offline_docling_environment,
    run_log,
    verify_model_files,
)


def run_worker_spec(spec_path: Path) -> Path:
    """Validate and execute one persisted worker request, retaining failure evidence."""
    try:
        spec = parse_worker_spec(spec_path)
    except GateBContractError as error:
        fallback_root = spec_path.parent
        write_failure(fallback_root, error, stage="worker_preflight")
        raise
    try:
        return run_seam_worker(spec)
    except BaseException as error:
        write_failure(spec.seam_root, error, stage="seam_execution", seam_id=spec.seam.seam_id)
        raise


def run_seam_worker(spec: GateBWorkerSpec) -> Path:
    """Run the four bounded conversions and publish one completion-sealed seam proof."""
    _, prepared = verified_inputs(spec.source_root, spec.config_path, spec.data_root)
    verify_model_files(spec.data_root, prepared.model_inventory_path, prepared.model_inventory)
    converter, options = build_gate_b_converter(prepared)
    started = time.monotonic()
    with offline_docling_environment(), run_log(spec.seam_root / "records/worker.log"):
        results = _convert_control_and_children(converter, prepared.source.source_path, spec)
        split_result, split_warnings, selected = _assemble_split(converter, spec, results)
    exact = _export_and_compare(spec, results, split_result, split_warnings, selected)
    differences = _compare_baseline_trace(spec, exact)
    report = _seam_report(spec, options, results.peak_rss_bytes, started, differences)
    write_json_atomic(spec.seam_root / "records/seam_report.json", report)
    return _publish_completion(spec)


@dataclass(frozen=True)
class ConversionSet:
    """The duplicate control and adjacent children for one seam proof."""

    contiguous_a: BoundedConversion
    contiguous_b: BoundedConversion
    left: BoundedConversion
    right: BoundedConversion

    @property
    def peak_rss_bytes(self) -> int:
        """Return the largest observed converter RSS."""
        return max(
            item.peak_rss_bytes
            for item in (self.contiguous_a, self.contiguous_b, self.left, self.right)
        )


def _convert_control_and_children(
    converter: Any, source_path: Path, spec: GateBWorkerSpec
) -> ConversionSet:
    seam = spec.seam
    results = ConversionSet(
        convert_range(converter, source_path, seam.window, "contiguous_a"),
        convert_range(converter, source_path, seam.window, "contiguous_b"),
        convert_range(converter, source_path, seam.left_read, "left"),
        convert_range(converter, source_path, seam.right_read, "right"),
    )
    if results.peak_rss_bytes > spec.max_rss_bytes:
        raise GateBContractError(
            "worker_rss_exceeded",
            f"seams[{seam.seam_id}].resource_observation",
            f"peak={results.peak_rss_bytes} limit={spec.max_rss_bytes}",
        )
    return results


def _assemble_split(
    converter: Any, spec: GateBWorkerSpec, results: ConversionSet
) -> tuple[Any, tuple[str, ...], tuple[PageEvidence, ...]]:
    assert_exact_split_vs_contiguous(
        results.contiguous_b.capture.pages,
        results.contiguous_a.capture.pages,
        path="duplicate_contiguous.pages",
    )
    selected = select_core_page_evidence(
        CapturedRange("left", spec.seam.left_core, spec.seam.left_read, results.left.capture.pages),
        CapturedRange(
            "right", spec.seam.right_core, spec.seam.right_read, results.right.capture.pages
        ),
    )
    assert_exact_split_vs_contiguous(selected, results.contiguous_a.capture.pages)
    pipeline = gate_b_pipeline(converter)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        split = pipeline.assemble_captured_pages(
            template_result=results.contiguous_a.result,
            pages=selected,
            outline=results.contiguous_a.capture.outline,
        )
    return split, tuple(str(item.message) for item in caught), selected


def _export_and_compare(
    spec: GateBWorkerSpec,
    results: ConversionSet,
    split_result: Any,
    split_warnings: tuple[str, ...],
    selected: tuple[PageEvidence, ...],
) -> ExactOutputs:
    evidence = spec.seam_root / "evidence"
    exact_a = export_exact(
        results.contiguous_a.result,
        evidence / "contiguous_a",
        results.contiguous_a.warnings,
    )
    exact_b = export_exact(
        results.contiguous_b.result,
        evidence / "contiguous_b",
        results.contiguous_b.warnings,
    )
    exact_split = export_exact(split_result, evidence / "split", split_warnings)
    assert_exact_outputs(exact_a, exact_b, path="duplicate_contiguous.outputs")
    assert_exact_outputs(exact_a, exact_split)
    if results.left.warnings or results.right.warnings:
        raise GateBContractError(
            "unrepresented_child_warnings",
            f"seams[{spec.seam.seam_id}].warnings",
            f"left={results.left.warnings!r} right={results.right.warnings!r}",
        )
    write_page_evidence(evidence / "selected_pages", selected)
    return exact_a


def _compare_baseline_trace(spec: GateBWorkerSpec, exact: ExactOutputs) -> list[dict[str, Any]]:
    pages = set(spec.seam.comparison_pages)
    expected = subset_trace(read_json_object(spec.sealed_trace_path), pages)
    actual = trace_from_outputs(
        exact.document, exact.heading_overlay, exact.alignment_pages, exact.assets, pages
    )
    try:
        return compare_sealed_page_trace(expected, actual, seam_id=spec.seam.seam_id)
    except ValueError:
        write_json_atomic(spec.seam_root / "records/live_page_trace.json", actual)
        write_json_atomic(spec.seam_root / "records/expected_page_trace.json", expected)
        raise


def _seam_report(
    spec: GateBWorkerSpec,
    options: Any,
    peak_rss_bytes: int,
    started: float,
    heading_differences: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "er_commons.task03h2_gate_b_seam_report.v1",
        "status": "passed",
        "seam": seam_payload(spec.seam),
        "source_conversion_id": CONVERSION_ID,
        "device": "cpu",
        "thread_count": THREAD_COUNT,
        "pipeline_class": (
            f"{GateBStandardPdfPipeline.__module__}.{GateBStandardPdfPipeline.__name__}"
        ),
        "effective_options_sha256": canonical_json_sha256(
            options.model_dump(mode="json", serialize_as_any=True)
        ),
        "checks": {
            "duplicate_contiguous_determinism": True,
            "left_right_overlap_exact": True,
            "split_pre_global_exact": True,
            "source_free_global_recomposition_exact": True,
            "sealed_page_local_trace_exact_except_global_heading_levels": True,
            "clean_status_and_exact_page_coverage": True,
            "warnings_exact": True,
        },
        "classified_global_heading_level_differences": heading_differences,
        "resource_observation": {
            "peak_rss_bytes": peak_rss_bytes,
            "wall_seconds": time.monotonic() - started,
        },
    }


def _publish_completion(spec: GateBWorkerSpec) -> Path:
    inventory_path = spec.seam_root / "records/artifact_inventory.json"
    inventory = artifact_inventory(
        spec.seam_root,
        excluded={"records/artifact_inventory.json", "records/completion_record.json"},
    )
    write_json_atomic(inventory_path, inventory)
    verify_inventory(spec.seam_root, inventory)
    completion_path = spec.seam_root / "records/completion_record.json"
    write_json_atomic(
        completion_path,
        {
            "schema_version": "er_commons.task03h2_gate_b_seam_completion.v1",
            "status": "complete",
            "seam_id": spec.seam.seam_id,
            "artifact_inventory": "records/artifact_inventory.json",
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "completion_last": True,
        },
    )
    return completion_path


def write_page_evidence(root: Path, pages: tuple[PageEvidence, ...]) -> None:
    """Persist selected typed page evidence with a navigable index."""
    root.mkdir(parents=True)
    records: list[dict[str, Any]] = []
    for page in pages:
        png = root / f"p{page.page_no:05d}.png"
        png.write_bytes(page.image_png)
        payload = root / f"p{page.page_no:05d}.json"
        write_json_atomic(payload, page.page_payload)
        records.append(
            {
                "page_no": page.page_no,
                "page_payload": payload.name,
                "assembled_element_types": list(page.assembled_element_types),
                "assembled_body_indices": list(page.assembled_body_indices),
                "assembled_header_indices": list(page.assembled_header_indices),
                "image": png.name,
                "image_scale": page.image_scale,
                "image_mode": page.image_mode,
                "image_size": list(page.image_size),
                "image_pixels_sha256": page.image_pixels_sha256,
                "semantic_sha256": page.semantic_sha256,
            }
        )
    write_json_atomic(root / "index.json", {"pages": records})


def write_failure(
    root: Path, error: BaseException, *, stage: str, seam_id: str | None = None
) -> Path:
    """Retain one stable, contextual failure record without overwriting first evidence."""
    failure = root / "records/failure.json"
    if failure.exists():
        return failure
    active_traceback: str | None = traceback.format_exc()
    if active_traceback == "NoneType: None\n":
        active_traceback = None
    write_json_atomic(
        failure,
        {
            "schema_version": "er_commons.task03h2_gate_b_failure.v2",
            "status": "failed",
            "stage": stage,
            "seam_id": seam_id,
            "error_code": getattr(error, "code", "unexpected_error"),
            "error_path": getattr(error, "path", None),
            "error_type": type(error).__name__,
            "message": str(error),
            "traceback": active_traceback,
            "retained": True,
            "completion_published": False,
        },
    )
    return failure


__all__ = ["run_seam_worker", "run_worker_spec", "write_failure"]
