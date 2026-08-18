from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path

import pytest

from er_commons.artifact_io import canonical_json_sha256, sha256_file
from er_commons.extraction_reporting import (
    AnomalyPolicy,
    summarize_verified_collection,
    write_extraction_report,
)
from er_commons.extraction_reporting.anomalies import (
    build_anomaly,
    select_bounded_anomalies,
)
from er_commons.extraction_reporting.inputs import read_jsonl_objects
from er_commons.human_review_support import (
    RenderPlan,
    RenderRecipe,
    ReviewArtifactInput,
    ReviewSelection,
    write_render_plan_manifest,
)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def _content_process_fixture(data_root: Path) -> Path:
    """Write the minimal sealed content evidence consumed by the report."""
    root = data_root / "owners/producer/prv1-test"
    conversion = root / "documents/alpha/producer/docling/conversion_observation.json"
    page_result = root / "documents/alpha/producer/tables/pages/page_00001/result.json"
    _write_json(
        conversion,
        {
            "errors": [{"code": "layout_error", "message": "retained error"}],
            "captured_python_warnings": ["deprecated parser option"],
            "source_manifest_warnings": [],
        },
    )
    _write_json(
        page_result,
        {
            "physical_pdf_page": 1,
            "parser_evidence": {
                "learned_fallback_attempts": [
                    {"region_id": "r1", "status": "abstained", "reason": "invalid_shape"}
                ]
            },
        },
    )
    inventory_path = _write_inventory(root, [conversion, page_result])
    completion = root / "records/completion_record.json"
    _write_json(completion, {"artifact_inventory_sha256": sha256_file(inventory_path)})
    return completion


def _hierarchy_process_fixture(data_root: Path) -> Path:
    """Write the minimal sealed hierarchy evidence consumed by the report."""
    root = data_root / "owners/correction/hcorv1-test"
    summary = root / "records/summary.json"
    warnings = root / "artifacts/warnings.jsonl"
    ambiguities = root / "artifacts/ambiguities.jsonl"
    _write_json(summary, {"ambiguity_count": 1, "warning_count": 2})
    _write_jsonl(
        warnings,
        [
            {"stable_item_key": "z", "code": "sparse_depth", "detail": "later"},
            {"stable_item_key": "a", "code": "sparse_depth", "detail": "earlier"},
        ],
    )
    _write_jsonl(
        ambiguities,
        [{"stable_item_key": "b", "code": "level_conflict", "detail": "ambiguous"}],
    )
    inventory_path = _write_inventory(root, [summary, warnings, ambiguities])
    completion = root / "records/completion_record.json"
    inventory = json.loads(inventory_path.read_text())
    _write_json(
        completion,
        {
            "status": "complete_with_ambiguities",
            "artifact_inventory_sha256": canonical_json_sha256(inventory),
        },
    )
    return completion


def _write_inventory(root: Path, files: list[Path]) -> Path:
    """Seal a compact fixture inventory and return its path."""
    path = root / "records/artifact_inventory.json"
    _write_json(
        path,
        {
            "files": [
                {
                    "path": item.relative_to(root).as_posix(),
                    "sha256": sha256_file(item),
                    "byte_size": item.stat().st_size,
                }
                for item in files
            ]
        },
    )
    return path


def test_request_only_manifest_verifies_inputs_without_generated_files(tmp_path: Path) -> None:
    source = tmp_path / "sources/alpha.pdf"
    source.parent.mkdir()
    source.write_bytes(b"sealed-pdf")
    plan = RenderPlan(
        "scopev1-test",
        (ReviewSelection("docv1-alpha", "alpha", (1, 3), ("page", "table")),),
    )
    recipe = RenderRecipe(
        renderer="review-render",
        renderer_version="1.0",
        arguments=("--request-only",),
        inputs=(ReviewArtifactInput("source_pdf", "sources/alpha.pdf", sha256_file(source)),),
    )

    manifest_path = write_render_plan_manifest(
        tmp_path / "review/request.json",
        data_root=tmp_path,
        plan=plan,
        recipe=recipe,
    )
    manifest = json.loads(manifest_path.read_text())

    digest_payload = {key: value for key, value in manifest.items() if key != "request_sha256"}
    expected = hashlib.sha256(
        (json.dumps(digest_payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ).hexdigest()
    assert manifest["schema_version"] == "er_commons.render_request.v2"
    assert manifest["request_sha256"] == expected
    assert manifest["status"] == "requested_not_rendered"
    assert manifest["publication_authority"] is False
    assert manifest["task04_status"] == "not_evaluated"
    assert "files" not in manifest


def test_request_only_manifest_rejects_mismatched_and_escaping_inputs(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf")
    plan = RenderPlan(
        "scope",
        (ReviewSelection("candidate", "source", (1,), ("page",)),),
    )
    with pytest.raises(ValueError, match="checksum differs"):
        write_render_plan_manifest(
            tmp_path / "bad.json",
            data_root=tmp_path,
            plan=plan,
            recipe=RenderRecipe(
                "renderer",
                "1",
                ("--page", "1"),
                (ReviewArtifactInput("pdf", "source.pdf", "a" * 64),),
            ),
        )
    with pytest.raises(ValueError, match="review input requires"):
        write_render_plan_manifest(
            tmp_path / "escape.json",
            data_root=tmp_path,
            plan=plan,
            recipe=RenderRecipe(
                "renderer",
                "1",
                ("--page", "1"),
                (ReviewArtifactInput("pdf", "../source.pdf", sha256_file(source)),),
            ),
        )


def _reporting_fixture(tmp_path: Path) -> tuple[Path, Path, dict[str, object]]:
    data_root = tmp_path / "data"
    extraction_root = data_root / "pipelines/pilot"
    candidate_id = "docv1-alpha"
    candidate_root = extraction_root / "documents/alpha" / candidate_id
    canonical = candidate_root / "content/canonical"
    records = {
        "pages": [{"id": "p1"}, {"id": "p2"}],
        "tables": [{"id": "t1"}],
        "table_families": [{"id": "f1"}],
        "sections": [{"id": "s1"}],
        "target_aliases": [{"id": "a1"}],
        "cross_references": [
            {"id": "m2", "resolution_status": "unresolved"},
            {"id": "m1", "resolution_status": "unresolved"},
        ],
    }
    for name, rows in records.items():
        _write_jsonl(canonical / f"{name}.jsonl", rows)
    _write_jsonl(
        candidate_root / "content/observations/page_labels.jsonl",
        [{"id": "l1"}, {"id": "l2"}],
    )

    producer_completion = _content_process_fixture(data_root)
    correction_completion = _hierarchy_process_fixture(data_root)
    _write_json(
        candidate_root / "records/document_identity.json",
        {
            "stage_completions": {
                "baseline_producer": {
                    "path": producer_completion.relative_to(data_root).as_posix(),
                    "sha256": sha256_file(producer_completion),
                },
                "hierarchy_correction": {
                    "path": correction_completion.relative_to(data_root).as_posix(),
                    "sha256": sha256_file(correction_completion),
                },
            }
        },
    )
    attempt = extraction_root / "attempts/txv1-test.1"
    _write_json(attempt / "attempt_record.json", {"disposition": "complete_with_warnings"})
    _write_json(
        attempt / "observability.json",
        {
            "wall_seconds": 12.5,
            "peak_rss_bytes": 200,
            "output_bytes": 300,
            "stage_timings": {"semantic": 2.0},
        },
    )
    scope_root = extraction_root / "scopes/scopev1-test"
    _write_json(scope_root / "contract_bundle.json", {"fixture": True})
    completion = {
        "candidate_id": candidate_id,
        "source": {"source_id": "alpha"},
    }
    row = {
        "source_id": "alpha",
        "terminal_state": "complete_with_warnings",
        "attempt_record_ref": {
            "path": (attempt / "attempt_record.json").relative_to(extraction_root).as_posix()
        },
    }
    bundle: dict[str, object] = {
        "production_extraction_id": "exv1-test",
        "document_completions": [completion],
        "accounting": {
            "scope_id": "scopev1-test",
            "rows": [row],
            "counts": {
                "total": 1,
                "complete": 0,
                "complete_with_warnings": 1,
                "failed_terminal": 0,
            },
        },
        "target_index": {"entry_count": 4},
        "resolution_completion": {
            "mention_input_manifest": {"eligible_mention_count": 1},
            "counts": {"total": 1, "resolved": 0, "ambiguous": 0, "unresolved": 1},
            "resolutions": [
                {
                    "mention_id": "cm1",
                    "source_candidate_id": candidate_id,
                    "status": "unresolved",
                }
            ],
        },
        "handoff": {"status": "ready"},
    }
    return data_root, extraction_root, bundle


def test_extraction_report_aggregates_sources_and_bounds_anomalies(tmp_path: Path) -> None:
    data_root, extraction_root, bundle = _reporting_fixture(tmp_path)
    candidate_root = extraction_root / "documents/alpha/docv1-alpha"
    before = sorted(
        (path.relative_to(candidate_root).as_posix(), sha256_file(path))
        for path in candidate_root.rglob("*")
        if path.is_file()
    )

    report, anomalies = summarize_verified_collection(
        data_root=data_root,
        extraction_root=extraction_root,
        bundle=bundle,
        anomaly_policy=AnomalyPolicy(max_examples_per_class=5),
    )
    artifacts = write_extraction_report(
        data_root / "review_cache/task_03g2/scopev1-test",
        report=report,
        anomalies=anomalies,
    )
    after = sorted(
        (path.relative_to(candidate_root).as_posix(), sha256_file(path))
        for path in candidate_root.rglob("*")
        if path.is_file()
    )

    assert report["totals"]["pages"] == 2
    assert report["totals"]["tables"] == 1
    assert report["totals"]["hierarchy_warnings"] == 2
    assert report["totals"]["wall_seconds"] == 12.5
    assert report["collection_processing"]["target_index_entry_count"] == 4
    assert report["collection_processing"]["resolution_counts"]["unresolved"] == 1
    warning_class = "hierarchy_warning:sparse_depth"
    assert report["anomaly_summary"]["candidate_counts"][warning_class] == 2
    assert report["anomaly_summary"]["sample_counts"][warning_class] == 2
    assert next(row for row in anomalies if row["category"] == warning_class)["record_id"] == "a"
    assert report["anomaly_summary"]["candidate_counts"]["producer_error:layout_error"] == 1
    assert report["anomaly_summary"]["candidate_counts"]["producer_abstention:invalid_shape"] == 1
    assert report["deterministic_extrema"]["tables"]["minimum"]["source_id"] == "alpha"
    assert report["deterministic_extrema"]["wall_seconds"]["maximum"]["value"] == 12.5
    assert report["anomaly_summary"]["extrema_count"] == 10
    assert json.loads(artifacts.completion.read_text())["completion_last"] is True
    assert before == after


def test_extraction_report_rejects_changed_owner_completion(tmp_path: Path) -> None:
    data_root, extraction_root, bundle = _reporting_fixture(tmp_path)
    completion = data_root / "owners/correction/hcorv1-test/records/completion_record.json"
    completion.write_text('{"status":"changed"}\n')

    with pytest.raises(ValueError, match="hierarchy completion checksum differs"):
        summarize_verified_collection(
            data_root=data_root,
            extraction_root=extraction_root,
            bundle=bundle,
            anomaly_policy=AnomalyPolicy(1),
        )


def test_anomaly_cap_is_global_per_class_with_source_coverage() -> None:
    rows = [
        build_anomaly(
            source,
            "shared_class",
            {"id": f"{source}-{index}"},
            "id",
        )
        for source in ("alpha", "beta", "gamma")
        for index in range(1, 4)
    ]

    selected = select_bounded_anomalies(list(reversed(rows)), AnomalyPolicy(5))

    assert len(selected) == 5
    assert {row["source_id"] for row in selected} == {"alpha", "beta", "gamma"}
    assert [row["record_id"] for row in selected[:3]] == ["alpha-1", "beta-1", "gamma-1"]


def test_reporting_rejects_malformed_bundle_at_named_boundary(tmp_path: Path) -> None:
    """Missing bundle structures fail before nested report construction begins."""
    with pytest.raises(ValueError, match="collection bundle field must be an object: accounting"):
        summarize_verified_collection(
            data_root=tmp_path,
            extraction_root=tmp_path,
            bundle={
                "production_extraction_id": "exv1-test",
                "document_completions": [],
            },
            anomaly_policy=AnomalyPolicy(1),
        )


def test_jsonl_error_names_the_file_and_line(tmp_path: Path) -> None:
    """Operators can locate malformed retained evidence without a traceback hunt."""
    path = tmp_path / "records.jsonl"
    path.write_text('{"valid": true}\nnot-json\n')

    with pytest.raises(ValueError, match=r"records\.jsonl:2"):
        read_jsonl_objects(path)
