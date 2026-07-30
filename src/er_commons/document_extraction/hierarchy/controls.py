"""Frozen Task 03E main-report controls and disposable review renders."""

from __future__ import annotations

import json
import shutil
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.document_extraction.config import (
    PipelineConfig,
    load_pipeline_config,
    load_selection_spec,
    range_name,
)
from er_commons.document_extraction.hierarchy.document import JsonObject
from er_commons.document_extraction.hierarchy.document_comparison import (
    compare_docling_hierarchy,
)
from er_commons.document_extraction.hierarchy.specification import (
    HierarchyEvaluationSpec,
)
from er_commons.document_extraction.pipeline import (
    convert_review_range,
    offline_docling_environment,
    run_log,
)
from er_commons.document_extraction.runtime import build_converter, verify_model_inventory
from er_commons.document_extraction.sources import (
    ResolvedSource,
    load_sealed_manifest,
    resolve_sources,
)
from er_commons.source_freeze import sha256_file, write_json_atomic


@dataclass(frozen=True)
class ControlInputs:
    """Verified accepted artifacts, source, models, and pipeline configuration."""

    config: PipelineConfig
    source: ResolvedSource
    accepted_root: Path
    models_root: Path


def _verify_accepted_root(root: Path) -> None:
    """Verify every file sealed by the accepted Task 03A v4 inventory."""
    inventory_path = root / "artifact_inventory.json"
    if not inventory_path.is_file():
        raise FileNotFoundError("accepted Task 03A v4 inventory is missing")
    inventory = json.loads(inventory_path.read_text())
    for record in inventory["files"]:
        path = root / record["path"]
        if (
            not path.is_file()
            or path.stat().st_size != record["byte_size"]
            or sha256_file(path) != record["sha256"]
        ):
            raise ValueError(f"accepted Task 03A v4 artifact changed: {path}")


def _load_control_inputs(
    data_root: Path,
    spec: HierarchyEvaluationSpec,
) -> ControlInputs:
    """Resolve and verify every external input before running a control conversion."""
    control = spec.control_harness
    config, _config_sha256 = load_pipeline_config(control.accepted_pipeline_config_path)
    selection, _selection_sha256 = load_selection_spec(config.selection_spec_path)
    manifest = load_sealed_manifest(data_root, selection)
    sources = resolve_sources(data_root, selection, manifest)
    source = next(item for item in sources if item.source_id == control.source_id)

    accepted_root = (data_root / config.artifact_relative_root).resolve()
    _verify_accepted_root(accepted_root)
    inventory_path = (data_root / config.model_inventory_relative_path).resolve()
    _inventory, models_root = verify_model_inventory(data_root, inventory_path)
    return ControlInputs(
        config=config,
        source=source,
        accepted_root=accepted_root,
        models_root=models_root,
    )


def _copy_review_images(
    *,
    accepted_root: Path,
    candidate_root: Path,
    review_root: Path,
    range_names: Sequence[str],
) -> list[dict[str, str]]:
    """Copy only declared control renders into the disposable review cache."""
    images: list[dict[str, str]] = []
    for range_name_value in range_names:
        for variant, source_root in (
            ("baseline", accepted_root),
            ("candidate", candidate_root),
        ):
            page_root = source_root / "ranges" / range_name_value / "page_images"
            for source in sorted(page_root.glob("*.png")):
                destination = review_root / "controls" / variant / source.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                images.append(
                    {
                        "variant": variant,
                        "range": range_name_value,
                        "path": destination.as_posix(),
                        "sha256": sha256_file(destination),
                    }
                )
    return images


def _convert_and_compare_controls(
    *,
    inputs: ControlInputs,
    spec: HierarchyEvaluationSpec,
    candidate_root: Path,
) -> tuple[dict[str, JsonObject], list[dict[str, Any]]]:
    """Convert the fixed ranges and compare each candidate with accepted output."""
    comparisons: dict[str, JsonObject] = {}
    timings: list[dict[str, Any]] = []
    converter, _options, format_option = build_converter(
        inputs.models_root,
        thread_count=inputs.config.thread_count,
        heading_hierarchy_options=spec.heading_hierarchy_options,
    )
    for selected in spec.main_report_controls:
        name = range_name(
            spec.control_harness.source_id,
            selected.first_page,
            selected.last_page,
        )
        if name not in spec.control_harness.expected_range_names:
            raise ValueError(f"undeclared Task 03E control range: {name}")
        range_root = candidate_root / "ranges" / name
        timings.append(
            convert_review_range(
                converter,
                format_option,
                inputs.source,
                selected.first_page,
                selected.last_page,
                range_root,
            )
        )
        baseline_document = json.loads(
            (inputs.accepted_root / "ranges" / name / "document.json").read_text()
        )
        candidate_document = json.loads((range_root / "document.json").read_text())
        reviewed_pages = set(range(selected.first_page, selected.last_page + 1))
        reviewed_pages -= set(selected.context_only_pages)
        comparisons[name] = {
            "purpose": selected.purpose,
            "context_only_pages": selected.context_only_pages,
            "comparison": compare_docling_hierarchy(
                baseline_document,
                candidate_document,
                review_pages=reviewed_pages,
            ),
        }
    return comparisons, timings


def run_hierarchy_controls(
    *,
    data_root: Path,
    spec: HierarchyEvaluationSpec,
    comparison_root: Path,
) -> JsonObject:
    """Convert the two fixed controls and compare them with accepted v4 output."""
    inputs = _load_control_inputs(data_root, spec)
    candidate_root = comparison_root / "controls"
    if candidate_root.exists():
        raise FileExistsError(f"Task 03E controls already exist: {candidate_root}")
    candidate_root.mkdir(parents=True)

    with (
        offline_docling_environment(),
        run_log(candidate_root / "logs" / "hierarchy_controls.log"),
    ):
        comparisons, timings = _convert_and_compare_controls(
            inputs=inputs,
            spec=spec,
            candidate_root=candidate_root,
        )

    review_root = (data_root / spec.review_cache.relative_root / comparison_root.name).resolve()
    if not review_root.is_relative_to(data_root.resolve()):
        raise ValueError("Task 03E review cache escapes ER_COMMONS_DATA_ROOT")
    images = _copy_review_images(
        accepted_root=inputs.accepted_root,
        candidate_root=candidate_root,
        review_root=review_root,
        range_names=spec.control_harness.expected_range_names,
    )
    status = (
        "pass"
        if all(value["comparison"]["status"] == "pass" for value in comparisons.values())
        else "reject"
    )
    report: JsonObject = {
        "schema_version": "1.0.0",
        "diagnostic_only": spec.control_harness.diagnostic_only,
        "status": status,
        "accepted_pipeline_root": inputs.accepted_root.as_posix(),
        "candidate_root": candidate_root.as_posix(),
        "timings": timings,
        "comparisons": comparisons,
        "review_images": images,
    }
    write_json_atomic(candidate_root / "control_report.json", report)
    return report
