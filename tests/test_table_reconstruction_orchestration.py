"""Offline tests for the typed table-reconstruction orchestration boundary."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from er_commons.artifact_io import write_json_atomic
from er_commons.document_parsing.table_reconstruction.boundaries import (
    PageExtractionRequest,
    PageExtractionResult,
)
from er_commons.document_parsing.table_reconstruction.pipeline import (
    TablePipelineServices,
    run_table_extraction,
)


def _config(source_sha256: str) -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "pipeline_id": "offline_test",
        "source_release_version": "release",
        "source_id": "document",
        "expected_source_sha256": source_sha256,
        "expected_pdf_page_count": 1,
        "physical_pdf_pages": [1],
        "artifact_relative_root": "runs/tables",
        "validation_scope": "routed_pages",
        "table_id_prefix": "doc",
        "family_id_prefix": "doc_table",
        "routed_pages": [{"physical_pdf_page": 1, "route": "full_page_numeric"}],
        "retain_review_derivatives": False,
        "execution": {"maximum_workers": 1},
        "detection": {
            "render_scale": 2,
            "horizontal_kernel_pixels": 10,
            "vertical_kernel_pixels": 10,
            "minimum_region_width_pixels": 10,
            "minimum_region_height_pixels": 10,
            "minimum_intersections": 4,
            "complex_page_minimum_regions": 2,
            "maximum_network_ruling_coverage": 0.5,
            "minimum_region_match_iou": 0.5,
        },
        "cleanup": {
            "footer_pattern": "footer",
            "footer_counter_pattern": "counter",
            "leading_filename_pattern": "filename",
            "maximum_header_rows": 2,
            "minimum_numeric_cell_fraction_for_data_row": 0.5,
        },
        "learned_fallback": {"enabled": False},
    }


def _page_result(request: PageExtractionRequest) -> PageExtractionResult:
    request.output_root.mkdir(parents=True, exist_ok=True)
    path = request.output_root / "result.json"
    if path.exists():
        return PageExtractionResult.from_record(json.loads(path.read_text()))
    record = {
        "schema_version": "1.0.0",
        "physical_pdf_page": request.physical_pdf_page,
        "route": request.route,
        "route_requested": request.route,
        "complex_page": False,
        "page_size_pdf_points": [612.0, 792.0],
        "ruling_region_count": 0,
        "ruled_regions": [],
        "parser_evidence": {},
        "table_count": 0,
        "tables": [],
        "footer": None,
        "footer_owner_table_id": None,
        "artifacts": {},
        "wall_seconds": 0.25,
    }
    write_json_atomic(path, record)
    return PageExtractionResult.from_record(record)


def test_pipeline_runs_and_reuses_without_pdf_or_repository_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Injected edges exercise prepare/extract/assemble/seal entirely offline."""
    data_root = tmp_path / "data"
    data_root.mkdir()
    source = data_root / "source.pdf"
    source.write_bytes(b"synthetic-not-opened")
    import hashlib

    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    config_path = tmp_path / "table.json"
    config_path.write_text(json.dumps(_config(digest)))
    manifest = data_root / "records/source_manifest.json"
    manifest.parent.mkdir()
    manifest.write_text("{}")
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "uv.lock").write_text("lock")
    calls = 0

    def extract(request: PageExtractionRequest) -> PageExtractionResult:
        nonlocal calls
        calls += 1
        return _page_result(request)

    clock = iter((10.0, 11.0, 20.0, 21.0))
    services = TablePipelineServices(
        resolve_source=lambda *_args: (source, manifest),
        pdf_page_count=lambda _path: 1,
        extract_page=extract,
        table_environment=lambda: {"offline": True},
        git_commit=lambda root: f"commit:{root.name}",
        monotonic=lambda: next(clock),
    )
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    first = run_table_extraction(
        data_root, config_path, services=services, project_root=project_root
    )
    second = run_table_extraction(
        data_root, config_path, services=services, project_root=project_root
    )

    assert first == second
    assert calls == 2
    summary = json.loads((first.parent / "summary.json").read_text())
    assert summary["reused_page_count_this_invocation"] == 1
    environment = json.loads((first.parent / "environment.json").read_text())
    assert environment["git_commit"] == "commit:project"
    assert environment["table_environment"] == {"offline": True}


def test_page_result_rejects_an_untyped_table_contract() -> None:
    """Malformed page/table records fail at the boundary, before run assembly."""
    with pytest.raises(ValueError, match="raw_csv"):
        PageExtractionResult.from_record(
            {
                "physical_pdf_page": 1,
                "table_count": 1,
                "tables": [{"table_id": "table"}],
            }
        )


@pytest.mark.parametrize(
    ("filename", "limit"),
    [("pipeline.py", 80), ("page.py", 90)],
)
def test_orchestration_functions_remain_human_sized(filename: str, limit: int) -> None:
    """New responsibilities must stay named and locally reviewable."""
    root = Path("src/er_commons/document_parsing/table_reconstruction")
    for node in ast.walk(ast.parse((root / filename).read_text())):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            assert length <= limit, f"split {filename}:{node.name} ({length} lines)"
