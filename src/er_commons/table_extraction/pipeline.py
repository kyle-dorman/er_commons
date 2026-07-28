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
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium  # type: ignore[import-untyped]

from er_commons.source_freeze import sha256_file, write_json_atomic
from er_commons.table_extraction.comparison import compare_pipeline_outputs
from er_commons.table_extraction.families import assign_families
from er_commons.table_extraction.models import load_config
from er_commons.table_extraction.page import extract_page

LOGGER = logging.getLogger(__name__)


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


def run_table_extraction(data_root: Path, config_path: Path) -> Path:
    """Run the fixed ten-page review sample and return its manifest."""
    started = time.perf_counter()
    config, config_sha256 = load_config(config_path)
    table_environment = installed_table_environment()
    root = (data_root / config.artifact_relative_root).resolve()
    root.mkdir(parents=True, exist_ok=True)

    configuration_output = root / "configuration.json"
    if configuration_output.exists():
        if sha256_file(configuration_output) != config_sha256:
            raise ValueError("existing run uses a different configuration")
    else:
        configuration_output.write_bytes(config_path.read_bytes())

    source_path, source_manifest_path = source_path_from_manifest(
        data_root,
        config.source_release_version,
        config.source_id,
    )
    if sha256_file(source_path) != config.expected_source_sha256:
        raise ValueError("sealed source checksum changed")
    document = pdfium.PdfDocument(source_path)
    try:
        if len(document) != config.expected_pdf_page_count:
            raise ValueError("sealed source page count changed")
    finally:
        document.close()

    page_results = []
    reused_page_count = 0
    for page in config.physical_pdf_pages:
        page_root = root / "pages" / f"page_{page:05d}"
        if (page_root / "result.json").exists():
            reused_page_count += 1
        result = extract_page(
            source_path,
            page,
            config.detection.model_dump(mode="json"),
            config.cleanup.model_dump(mode="json"),
            page_root,
        )
        page_results.append(result)
        LOGGER.info(
            "Extracted page %s route=%s tables=%s seconds=%.2f",
            page,
            result["route"],
            result["table_count"],
            result["wall_seconds"],
        )
    if [item["physical_pdf_page"] for item in page_results] != sorted(config.physical_pdf_pages):
        raise ValueError("page results are incomplete")

    tables: list[dict[str, Any]] = []
    page_records: list[dict[str, Any]] = []
    for page_result in page_results:
        page_number = int(page_result["physical_pdf_page"])
        page_relative_root = Path("pages") / f"page_{page_number:05d}"
        tables.extend(
            prefix_table_paths(table, page_relative_root) for table in page_result["tables"]
        )
        page_records.append(
            {
                "physical_pdf_page": page_number,
                "route": page_result["route"],
                "complex_page": page_result["complex_page"],
                "ruling_region_count": page_result["ruling_region_count"],
                "table_count": page_result["table_count"],
                "footer": page_result["footer"],
                "footer_owner_table_id": page_result["footer_owner_table_id"],
                "result": (page_relative_root / "result.json").as_posix(),
                "annotated": (page_relative_root / "annotated.png").as_posix(),
                "wall_seconds": page_result["wall_seconds"],
            }
        )
    if len({table["table_id"] for table in tables}) != len(tables):
        raise ValueError("logical table IDs are not unique")

    assignments, families = assign_families(page_records, tables)
    if len(assignments) != len(tables) or len(
        {assignment["table_id"] for assignment in assignments}
    ) != len(tables):
        raise ValueError("family assignments are incomplete or duplicated")
    write_jsonl(root / "pages.jsonl", page_records)
    write_jsonl(root / "tables.jsonl", tables)
    write_jsonl(root / "family_assignments.jsonl", assignments)
    write_json_atomic(root / "table_families.json", {"families": families})

    comparison_path = None
    comparison = None
    if config.comparison_relative_root is not None:
        baseline_root = (data_root / config.comparison_relative_root).resolve()
        comparison = compare_pipeline_outputs(
            baseline_root,
            root,
            baseline_pages_only=config.comparison_scope == "baseline_pages",
        )
        comparison_name = (
            "comparison_to_review_sample.json"
            if config.comparison_scope == "baseline_pages"
            else "comparison_to_task03a12.json"
        )
        comparison_path = root / comparison_name
        write_json_atomic(comparison_path, comparison)

    zero_table_pages = [
        int(page["physical_pdf_page"]) for page in page_results if page["table_count"] == 0
    ]
    unmatched_detected_regions = [
        {
            "physical_pdf_page": int(page["physical_pdf_page"]),
            **match,
        }
        for page in page_results
        for match in page["parser_evidence"].get("region_matches", [])
        if not match["matched"]
    ]
    unmatched_lattice_return_count = sum(
        int(page["parser_evidence"].get("unmatched_lattice_return_count", 0))
        for page in page_results
    )
    summary = {
        "pipeline_id": config.pipeline_id,
        "validation_scope": config.validation_scope,
        "physical_pdf_pages": config.physical_pdf_pages,
        "page_count": len(page_results),
        "simple_page_count": sum(page["route"] == "simple_stream" for page in page_results),
        "complex_page_count": sum(page["route"] == "complex_segmented" for page in page_results),
        "logical_table_count": len(tables),
        "stream_table_count": sum(table["parser"] == "camelot_stream" for table in tables),
        "lattice_table_count": sum(table["parser"] == "camelot_lattice" for table in tables),
        "network_table_count": sum(table["parser"] == "camelot_network" for table in tables),
        "family_count": len(families),
        "footer_owned_table_count": sum(assignment["footer_owned"] for assignment in assignments),
        "zero_table_pages": zero_table_pages,
        "unmatched_detected_regions": unmatched_detected_regions,
        "unmatched_lattice_return_count": unmatched_lattice_return_count,
        "reused_page_count_this_invocation": reused_page_count,
        "page_wall_seconds_sum": sum(float(page["wall_seconds"]) for page in page_results),
        "pipeline_wall_seconds": time.perf_counter() - started,
        "comparison_exact_semantic_match": (
            comparison["exact_semantic_match"] if comparison is not None else None
        ),
        "first_600_pages_ran": config.validation_scope == "first_600",
        "review_status": "draft_awaiting_user_review",
    }
    write_json_atomic(root / "summary.json", summary)
    write_json_atomic(
        root / "environment.json",
        {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "git_commit": subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip(),
            "main_lock_sha256": sha256_file(Path("uv.lock")),
            "table_environment": table_environment,
            "forbidden_stages": {
                "tableformer": False,
                "docling": False,
                "ocr": False,
                "vlm": False,
                "llm_repair": False,
            },
        },
    )

    inventory_path = root / "artifact_inventory.json"
    manifest_path = root / "manifest.json"
    inventory_path.unlink(missing_ok=True)
    manifest_path.unlink(missing_ok=True)
    write_json_atomic(
        inventory_path,
        artifact_inventory(
            root,
            {"artifact_inventory.json", "manifest.json"},
        ),
    )
    write_json_atomic(
        manifest_path,
        {
            "schema_version": "1.0.0",
            "pipeline_id": config.pipeline_id,
            "configuration": "configuration.json",
            "configuration_sha256": config_sha256,
            "source_manifest": source_manifest_path.relative_to(data_root).as_posix(),
            "source_id": config.source_id,
            "source_sha256": config.expected_source_sha256,
            "physical_pdf_pages": config.physical_pdf_pages,
            "summary": "summary.json",
            "pages": "pages.jsonl",
            "tables": "tables.jsonl",
            "family_assignments": "family_assignments.jsonl",
            "table_families": "table_families.json",
            "comparison": (
                comparison_path.relative_to(root).as_posix()
                if comparison_path is not None
                else None
            ),
            "environment": "environment.json",
            "artifact_inventory": "artifact_inventory.json",
        },
    )
    return manifest_path
