from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from er_commons.extraction_review import (
    AnomalyPolicy,
    PilotReviewRequest,
    PilotReviewSelection,
    RenderRecipe,
    ReviewInput,
    pilot_reporting,
    summarize_verified_pilot,
    write_pilot_report,
    write_review_request_manifest,
)
from er_commons.source_freeze import sha256_file


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def test_request_only_manifest_verifies_inputs_without_generated_files(tmp_path: Path) -> None:
    source = tmp_path / "sources/alpha.pdf"
    source.parent.mkdir()
    source.write_bytes(b"sealed-pdf")
    request = PilotReviewRequest(
        "scopev1-test",
        (PilotReviewSelection("docv1-alpha", "alpha", (1, 3), ("page", "table")),),
    )
    recipe = RenderRecipe(
        renderer="review-render",
        renderer_version="1.0",
        arguments=("--request-only",),
        inputs=(ReviewInput("source_pdf", "sources/alpha.pdf", sha256_file(source)),),
    )

    manifest_path = write_review_request_manifest(
        tmp_path / "review/request.json",
        data_root=tmp_path,
        request=request,
        recipe=recipe,
    )
    manifest = json.loads(manifest_path.read_text())

    digest_payload = {key: value for key, value in manifest.items() if key != "request_sha256"}
    expected = hashlib.sha256(
        (json.dumps(digest_payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ).hexdigest()
    assert manifest["request_sha256"] == expected
    assert manifest["status"] == "requested_not_rendered"
    assert manifest["publication_authority"] is False
    assert manifest["task04_status"] == "not_evaluated"
    assert "files" not in manifest


def test_request_only_manifest_rejects_mismatched_and_escaping_inputs(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf")
    request = PilotReviewRequest(
        "scope",
        (PilotReviewSelection("candidate", "source", (1,), ("page",)),),
    )
    with pytest.raises(ValueError, match="checksum differs"):
        write_review_request_manifest(
            tmp_path / "bad.json",
            data_root=tmp_path,
            request=request,
            recipe=RenderRecipe(
                "renderer",
                "1",
                ("--page", "1"),
                (ReviewInput("pdf", "source.pdf", "a" * 64),),
            ),
        )
    with pytest.raises(ValueError, match="review input requires"):
        write_review_request_manifest(
            tmp_path / "escape.json",
            data_root=tmp_path,
            request=request,
            recipe=RenderRecipe(
                "renderer",
                "1",
                ("--page", "1"),
                (ReviewInput("pdf", "../source.pdf", sha256_file(source)),),
            ),
        )


def _pilot_fixture(tmp_path: Path) -> tuple[Path, Path, dict[str, object]]:
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
        "page_labels": [{"id": "l1"}, {"id": "l2"}],
        "target_aliases": [{"id": "a1"}],
        "cross_references": [
            {"id": "m2", "resolution_status": "unresolved"},
            {"id": "m1", "resolution_status": "unresolved"},
        ],
    }
    for name, rows in records.items():
        _write_jsonl(canonical / f"{name}.jsonl", rows)

    producer = data_root / "owners/producer/prv1-test"
    producer_completion = producer / "records/completion_record.json"
    conversion = producer / "documents/alpha/producer/docling/conversion_observation.json"
    page_result = producer / "documents/alpha/producer/tables/pages/page_00001/result.json"
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
                    {
                        "region_id": "r1",
                        "status": "abstained",
                        "reason": "invalid_shape",
                    }
                ]
            },
        },
    )
    producer_files = [conversion, page_result]
    _write_json(
        producer / "records/artifact_inventory.json",
        {
            "files": [
                {
                    "path": path.relative_to(producer).as_posix(),
                    "sha256": sha256_file(path),
                    "byte_size": path.stat().st_size,
                }
                for path in producer_files
            ]
        },
    )
    _write_json(
        producer_completion,
        {"artifact_inventory_sha256": sha256_file(producer / "records/artifact_inventory.json")},
    )

    correction = data_root / "owners/correction/hcorv1-test"
    correction_completion = correction / "records/completion_record.json"
    _write_json(
        correction / "records/summary.json",
        {"ambiguity_count": 1, "warning_count": 2},
    )
    _write_jsonl(
        correction / "artifacts/warnings.jsonl",
        [
            {"stable_item_key": "z", "code": "sparse_depth", "detail": "later"},
            {"stable_item_key": "a", "code": "sparse_depth", "detail": "earlier"},
        ],
    )
    _write_jsonl(
        correction / "artifacts/ambiguities.jsonl",
        [{"stable_item_key": "b", "code": "level_conflict", "detail": "ambiguous"}],
    )
    correction_files = [
        correction / "records/summary.json",
        correction / "artifacts/warnings.jsonl",
        correction / "artifacts/ambiguities.jsonl",
    ]
    _write_json(
        correction / "records/artifact_inventory.json",
        {
            "files": [
                {
                    "path": path.relative_to(correction).as_posix(),
                    "sha256": sha256_file(path),
                    "byte_size": path.stat().st_size,
                }
                for path in correction_files
            ]
        },
    )
    _write_json(
        correction_completion,
        {
            "status": "complete_with_ambiguities",
            "artifact_inventory_sha256": sha256_file(
                correction / "records/artifact_inventory.json"
            ),
        },
    )
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


def test_pilot_report_aggregates_sources_and_bounds_anomalies(tmp_path: Path) -> None:
    data_root, extraction_root, bundle = _pilot_fixture(tmp_path)
    candidate_root = extraction_root / "documents/alpha/docv1-alpha"
    before = sorted(
        (path.relative_to(candidate_root).as_posix(), sha256_file(path))
        for path in candidate_root.rglob("*")
        if path.is_file()
    )

    report, anomalies = summarize_verified_pilot(
        data_root=data_root,
        extraction_root=extraction_root,
        bundle=bundle,
        anomaly_policy=AnomalyPolicy(max_examples_per_class=5),
    )
    artifacts = write_pilot_report(
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
    assert report["stage_two"]["target_index_entry_count"] == 4
    assert report["stage_two"]["resolution_counts"]["unresolved"] == 1
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


def test_pilot_report_rejects_changed_owner_completion(tmp_path: Path) -> None:
    data_root, extraction_root, bundle = _pilot_fixture(tmp_path)
    completion = data_root / "owners/correction/hcorv1-test/records/completion_record.json"
    completion.write_text('{"status":"changed"}\n')

    with pytest.raises(ValueError, match="input reference differs"):
        summarize_verified_pilot(
            data_root=data_root,
            extraction_root=extraction_root,
            bundle=bundle,
            anomaly_policy=AnomalyPolicy(1),
        )


def test_anomaly_cap_is_global_per_class_with_source_coverage() -> None:
    rows = [
        pilot_reporting._anomaly(  # noqa: SLF001 - focused policy seam
            source,
            "shared_class",
            {"id": f"{source}-{index}"},
            "id",
        )
        for source in ("alpha", "beta", "gamma")
        for index in range(1, 4)
    ]

    selected = pilot_reporting._bounded_anomalies(  # noqa: SLF001 - focused policy seam
        list(reversed(rows)), AnomalyPolicy(5)
    )

    assert len(selected) == 5
    assert {row["source_id"] for row in selected} == {"alpha", "beta", "gamma"}
    assert [row["record_id"] for row in selected[:3]] == ["alpha-1", "beta-1", "gamma-1"]
