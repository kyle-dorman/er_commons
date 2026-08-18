"""Orchestrate restartable page extraction and build table-family manifests.

The clean pipeline is a single readable call graph:

    verify sealed source
              |
              v
    extract_page(...) for each physical page
              |
              v
    assign contiguous table families
              |
              v
    compare stable logical fields and seal the manifest

Each page still owns a complete result directory. A completed ``result.json``
is the restart boundary; no secondary Python project or subprocess is needed.
"""

from __future__ import annotations

import json
import logging
import platform
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium  # type: ignore[import-untyped]

from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.document_parsing.table_reconstruction.boundaries import (
    PageExtractionRequest,
    PageExtractionResult,
)
from er_commons.document_parsing.table_reconstruction.continuations import continuation_decisions
from er_commons.document_parsing.table_reconstruction.families import assign_families
from er_commons.document_parsing.table_reconstruction.fragments import project_logical_tables
from er_commons.document_parsing.table_reconstruction.learned_fallback import (
    VerifiedTableFormerFallback,
)
from er_commons.document_parsing.table_reconstruction.models import (
    TableExtractionConfig,
    load_config,
)
from er_commons.document_parsing.table_reconstruction.page import extract_page

LOGGER = logging.getLogger(__name__)
CONTINUATION_STATUSES = (
    "accepted",
    "rejected",
    "ambiguous",
    "not_evaluable_missing_table",
)


def _learned_fallback_counts(
    page_results: list[dict[str, Any]],
    tables: list[dict[str, Any]],
) -> dict[str, int]:
    """Summarize learned attempts separately from accepted parser tables."""
    attempts = [
        attempt
        for page in page_results
        for attempt in page["parser_evidence"].get("learned_fallback_attempts", [])
    ]
    return {
        "tableformer_table_count": sum(
            table["parser"] == "tableformer_accurate" for table in tables
        ),
        "learned_fallback_attempt_count": len(attempts),
        "learned_fallback_abstention_count": sum(
            attempt["status"] == "abstained" for attempt in attempts
        ),
    }


def _continuation_counts(decisions: list[dict[str, Any]]) -> dict[str, int]:
    """Return a closed count map including zero-count dispositions."""
    return {
        status: sum(decision["status"] == status for decision in decisions)
        for status in CONTINUATION_STATUSES
    }


def source_path_from_manifest(
    data_root: Path,
    source_release_version: str,
    source_id: str,
) -> tuple[Path, Path]:
    """Resolve one sealed source from its recorded relative path."""
    release_root = (
        data_root / "datasets/ceqa/raw/brisbane_baylands" / source_release_version
    ).resolve()
    manifest_path = release_root / "records/source_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    source = next(
        (item for item in manifest["sources"] if item["source_id"] == source_id),
        None,
    )
    if source is None:
        raise ValueError(f"source not found in sealed manifest: {source_id}")
    return (data_root / source["local_path"]).resolve(), manifest_path


def installed_table_environment() -> dict[str, Any]:
    """Verify and describe the single supported table-extraction environment."""
    expected = {
        "camelot-py": "2.0.0",
        "docling": "2.115.0",
        "opencv-python-headless": "5.0.0.93",
        "rapidocr": "3.9.2",
    }
    installed = {package: version(package) for package in expected}
    mismatches = {
        package: {"expected": expected_version, "installed": installed[package]}
        for package, expected_version in expected.items()
        if installed[package] != expected_version
    }
    if mismatches:
        raise RuntimeError(f"unexpected table dependency versions: {mismatches}")
    try:
        gui_opencv = version("opencv-python")
    except PackageNotFoundError:
        gui_opencv = None
    if gui_opencv is not None:
        raise RuntimeError(
            "opencv-python and opencv-python-headless share cv2; "
            f"remove the GUI distribution ({gui_opencv})"
        )
    return {
        "distributions": installed,
        "opencv_python_installed": False,
        "single_cv2_distribution": True,
    }


def prefix_table_paths(
    table: dict[str, Any],
    page_relative_root: Path,
) -> dict[str, Any]:
    """Make page-local paths relative to the complete pipeline root."""
    record = dict(table)
    for key in ("raw_csv", "clean_csv", "cells"):
        artifact = dict(record[key])
        artifact["path"] = (page_relative_root / str(artifact["path"])).as_posix()
        record[key] = artifact
    record["table_record"] = (
        page_relative_root / "tables" / str(record["table_id"]) / "table.json"
    ).as_posix()
    return record


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    """Write stable one-record-per-line JSON."""
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    )


def artifact_inventory(root: Path, excluded: set[str]) -> dict[str, Any]:
    """Inventory generated files without hashing the inventory itself."""
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        files.append(
            {
                "path": relative,
                "byte_size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "file_count": len(files),
        "byte_count": sum(item["byte_size"] for item in files),
        "files": files,
    }


def _pdf_page_count(path: Path) -> int:
    document = pdfium.PdfDocument(path)
    try:
        return len(document)
    finally:
        document.close()


def _extract_page(request: PageExtractionRequest) -> PageExtractionResult:
    record = extract_page(
        request.source_path,
        request.physical_pdf_page,
        request.detection,
        request.cleanup,
        request.output_root,
        route_mode=request.route,
        layout_regions=request.layout_regions,
        table_id_prefix=request.table_id_prefix,
        retain_review_derivatives=request.retain_review_derivatives,
        learned_fallback_runner=request.learned_fallback_runner,
    )
    return PageExtractionResult.from_record(record)


def _git_commit(project_root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@dataclass(frozen=True)
class TablePipelineServices:
    """Replaceable external edges for fast, offline orchestration tests."""

    resolve_source: Callable[[Path, str, str], tuple[Path, Path]] = source_path_from_manifest
    pdf_page_count: Callable[[Path], int] = _pdf_page_count
    extract_page: Callable[[PageExtractionRequest], PageExtractionResult] = _extract_page
    table_environment: Callable[[], dict[str, Any]] = installed_table_environment
    git_commit: Callable[[Path], str] = _git_commit
    monotonic: Callable[[], float] = time.perf_counter


@dataclass(frozen=True)
class PreparedTableRun:
    """Verified immutable inputs and resolved output locations."""

    data_root: Path
    project_root: Path
    root: Path
    source_path: Path
    source_manifest_path: Path
    config: TableExtractionConfig
    config_sha256: str
    table_environment: dict[str, Any]
    fallback_runner: VerifiedTableFormerFallback | None
    started: float


@dataclass(frozen=True)
class AssembledTableRun:
    """Cross-page records ready for summary and manifest sealing."""

    page_results: list[dict[str, Any]]
    page_records: list[dict[str, Any]]
    tables: list[dict[str, Any]]
    assignments: list[dict[str, Any]]
    families: list[dict[str, Any]]
    continuations: list[dict[str, Any]]
    fragment_pages: list[int]
    reused_page_count: int


def prepare_table_run(
    data_root: Path,
    config_path: Path,
    artifact_root_override: Path | None,
    services: TablePipelineServices,
    project_root: Path,
) -> PreparedTableRun:
    """Validate configuration, environment, source bytes, and page count."""
    started = services.monotonic()
    config, config_sha256 = load_config(config_path)
    table_environment = services.table_environment()
    root = (
        artifact_root_override.resolve()
        if artifact_root_override is not None
        else (data_root / config.artifact_relative_root).resolve()
    )
    if not root.is_relative_to(data_root.resolve()):
        raise ValueError("table artifact root escapes ER_COMMONS_DATA_ROOT")
    root.mkdir(parents=True, exist_ok=True)
    configuration_output = root / "configuration.json"
    if configuration_output.exists() and sha256_file(configuration_output) != config_sha256:
        raise ValueError("existing run uses a different configuration")
    if not configuration_output.exists():
        configuration_output.write_bytes(config_path.read_bytes())
    source_path, source_manifest_path = services.resolve_source(
        data_root, config.source_release_version, config.source_id
    )
    if sha256_file(source_path) != config.expected_source_sha256:
        raise ValueError("sealed source checksum changed")
    if services.pdf_page_count(source_path) != config.expected_pdf_page_count:
        raise ValueError("sealed source page count changed")
    fallback = (
        VerifiedTableFormerFallback(data_root=data_root, policy=config.learned_fallback)
        if config.learned_fallback.enabled
        else None
    )
    return PreparedTableRun(
        data_root=data_root,
        project_root=project_root.resolve(),
        root=root,
        source_path=source_path,
        source_manifest_path=source_manifest_path,
        config=config,
        config_sha256=config_sha256,
        table_environment=table_environment,
        fallback_runner=fallback,
        started=started,
    )


def extract_table_pages(
    run: PreparedTableRun, services: TablePipelineServices
) -> tuple[list[PageExtractionResult], int]:
    """Extract or reuse each configured page through one typed boundary."""
    results = []
    reused = 0
    routed_by_page = {item.physical_pdf_page: item for item in run.config.routed_pages}
    for page in run.config.physical_pdf_pages:
        page_root = run.root / "pages" / f"page_{page:05d}"
        reused += int((page_root / "result.json").exists())
        routed = routed_by_page.get(page)
        result = services.extract_page(
            PageExtractionRequest(
                source_path=run.source_path,
                physical_pdf_page=page,
                detection=run.config.detection.model_dump(mode="json"),
                cleanup=run.config.cleanup.model_dump(mode="json"),
                output_root=page_root,
                route=routed.route if routed is not None else None,
                layout_regions=(
                    routed.layout_regions_pdf_points_bottom_left if routed is not None else None
                ),
                table_id_prefix=run.config.table_id_prefix,
                retain_review_derivatives=run.config.retain_review_derivatives,
                learned_fallback_runner=run.fallback_runner,
            )
        )
        results.append(result)
        LOGGER.info(
            "Extracted page %s route=%s tables=%s seconds=%.2f",
            page,
            result.record["route"],
            result.record["table_count"],
            result.record["wall_seconds"],
        )
    if [item.record["physical_pdf_page"] for item in results] != sorted(
        run.config.physical_pdf_pages
    ):
        raise ValueError("page results are incomplete")
    return results, reused


def assemble_table_run(
    run: PreparedTableRun,
    results: list[PageExtractionResult],
    reused_page_count: int,
) -> AssembledTableRun:
    """Project page results, assign families, and persist cross-page streams."""
    page_results = [item.record for item in results]
    tables: list[dict[str, Any]] = []
    page_records: list[dict[str, Any]] = []
    routed_by_page = {item.physical_pdf_page: item for item in run.config.routed_pages}
    for result in results:
        page_result = result.record
        page_number = int(page_result["physical_pdf_page"])
        routed = routed_by_page.get(page_number)
        relative_root = Path("pages") / f"page_{page_number:05d}"
        tables.extend(prefix_table_paths(table.record, relative_root) for table in result.tables)
        record = {
            "physical_pdf_page": page_number,
            "route": page_result["route"],
            "complex_page": page_result["complex_page"],
            "ruling_region_count": page_result["ruling_region_count"],
            "table_count": page_result["table_count"],
            "footer": page_result["footer"],
            "footer_owner_table_id": page_result["footer_owner_table_id"],
            "result": (relative_root / "result.json").as_posix(),
            "wall_seconds": page_result["wall_seconds"],
            "boundary_markers_before_first_table": (
                [
                    item.model_dump(mode="json")
                    for item in routed.boundary_markers_before_first_table
                ]
                if routed is not None
                else []
            ),
        }
        if run.config.retain_review_derivatives:
            record["annotated"] = (relative_root / "annotated.png").as_posix()
        page_records.append(record)
    if len({table["table_id"] for table in tables}) != len(tables):
        raise ValueError("logical table IDs are not unique")
    projection = project_logical_tables(page_results, page_records, tables)
    for projected_result in projection.page_results:
        page_number = int(projected_result["physical_pdf_page"])
        write_json_atomic(
            run.root / "pages" / f"page_{page_number:05d}" / "result.json",
            projected_result,
        )
    continuations = continuation_decisions(projection.page_records, projection.tables)
    assignments, families = assign_families(
        projection.page_records,
        projection.tables,
        family_id_prefix=run.config.family_id_prefix,
        continuation_records=continuations,
    )
    if len(assignments) != len(projection.tables) or len(
        {item["table_id"] for item in assignments}
    ) != len(projection.tables):
        raise ValueError("family assignments are incomplete or duplicated")
    write_jsonl(run.root / "pages.jsonl", projection.page_records)
    write_jsonl(run.root / "tables.jsonl", projection.tables)
    write_jsonl(run.root / "family_assignments.jsonl", assignments)
    write_json_atomic(
        run.root / "table_families.json",
        {"families": families, "continuation_decisions": continuations},
    )
    return AssembledTableRun(
        page_results=projection.page_results,
        page_records=projection.page_records,
        tables=projection.tables,
        assignments=assignments,
        families=families,
        continuations=continuations,
        fragment_pages=[int(item["physical_pdf_page"]) for item in projection.fragments],
        reused_page_count=reused_page_count,
    )


def _summary(run: PreparedTableRun, assembled: AssembledTableRun, elapsed: float) -> dict[str, Any]:
    pages, tables = assembled.page_results, assembled.tables
    zero_pages = [
        int(page["physical_pdf_page"])
        for page in assembled.page_records
        if page["table_count"] == 0
    ]
    unmatched = [
        {"physical_pdf_page": int(page["physical_pdf_page"]), **match}
        for page in pages
        for match in page["parser_evidence"].get("region_matches", [])
        if not match["matched"]
    ]
    return {
        "pipeline_id": run.config.pipeline_id,
        "validation_scope": run.config.validation_scope,
        "physical_pdf_pages": run.config.physical_pdf_pages,
        "page_count": len(pages),
        "simple_page_count": sum(page["route"] == "simple_stream" for page in pages),
        "complex_page_count": sum(page["route"] == "complex_segmented" for page in pages),
        "full_page_numeric_count": sum(page["route"] == "full_page_numeric" for page in pages),
        "layout_regions_count": sum(page["route"] == "layout_regions" for page in pages),
        "logical_table_count": len(tables),
        "header_only_continuation_fragment_count": len(assembled.fragment_pages),
        "header_only_continuation_fragment_pages": assembled.fragment_pages,
        "stream_table_count": sum(table["parser"] == "camelot_stream" for table in tables),
        "lattice_table_count": sum(table["parser"] == "camelot_lattice" for table in tables),
        "network_table_count": sum(table["parser"] == "camelot_network" for table in tables),
        **_learned_fallback_counts(pages, tables),
        "family_count": len(assembled.families),
        "continuation_decision_counts": _continuation_counts(assembled.continuations),
        "footer_owned_table_count": sum(item["footer_owned"] for item in assembled.assignments),
        "zero_table_pages": zero_pages,
        "unmatched_detected_regions": unmatched,
        "unmatched_lattice_return_count": sum(
            int(page["parser_evidence"].get("unmatched_lattice_return_count", 0)) for page in pages
        ),
        "reused_page_count_this_invocation": assembled.reused_page_count,
        "page_wall_seconds_sum": sum(float(page["wall_seconds"]) for page in pages),
        "pipeline_wall_seconds": elapsed,
        "first_600_pages_ran": run.config.validation_scope == "first_600",
        "review_status": (
            "component_complete"
            if run.config.validation_scope == "routed_pages"
            else "draft_awaiting_user_review"
        ),
        "review_derivatives_retained": run.config.retain_review_derivatives,
    }


def seal_table_run(
    run: PreparedTableRun,
    assembled: AssembledTableRun,
    services: TablePipelineServices,
) -> Path:
    """Write summary, environment, inventory, and completion manifest last."""
    write_json_atomic(
        run.root / "summary.json",
        _summary(run, assembled, services.monotonic() - run.started),
    )
    write_json_atomic(
        run.root / "environment.json",
        {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "git_commit": services.git_commit(run.project_root),
            "main_lock_sha256": sha256_file(run.project_root / "uv.lock"),
            "table_environment": run.table_environment,
            "forbidden_stages": {
                "tableformer": False,
                "docling": False,
                "ocr": False,
                "vlm": False,
                "llm_repair": False,
            },
            "learned_fallback_model_identity": (
                run.fallback_runner.model_identity if run.fallback_runner is not None else None
            ),
        },
    )
    inventory_path = run.root / "artifact_inventory.json"
    manifest_path = run.root / "manifest.json"
    inventory_path.unlink(missing_ok=True)
    manifest_path.unlink(missing_ok=True)
    write_json_atomic(
        inventory_path,
        artifact_inventory(run.root, {"artifact_inventory.json", "manifest.json"}),
    )
    write_json_atomic(
        manifest_path,
        {
            "schema_version": "1.0.0",
            "pipeline_id": run.config.pipeline_id,
            "configuration": "configuration.json",
            "configuration_sha256": run.config_sha256,
            "source_manifest": run.source_manifest_path.relative_to(run.data_root).as_posix(),
            "source_id": run.config.source_id,
            "source_sha256": run.config.expected_source_sha256,
            "physical_pdf_pages": run.config.physical_pdf_pages,
            "summary": "summary.json",
            "pages": "pages.jsonl",
            "tables": "tables.jsonl",
            "family_assignments": "family_assignments.jsonl",
            "table_families": "table_families.json",
            "environment": "environment.json",
            "artifact_inventory": "artifact_inventory.json",
        },
    )
    return manifest_path


def run_table_extraction(
    data_root: Path,
    config_path: Path,
    artifact_root_override: Path | None = None,
    *,
    services: TablePipelineServices | None = None,
    project_root: Path | None = None,
) -> Path:
    """Run one validated request through prepare, extract, assemble, and seal."""
    active_services = services or TablePipelineServices()
    run = prepare_table_run(
        data_root,
        config_path,
        artifact_root_override,
        active_services,
        project_root or Path(__file__).resolve().parents[4],
    )
    results, reused = extract_table_pages(run, active_services)
    assembled = assemble_table_run(run, results, reused)
    return seal_table_run(run, assembled, active_services)
