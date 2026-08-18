"""Offline runtime tests for the restartable whole-document stage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.document_publication.records import (
    DOCUMENT_PROCESS_NAMES,
    DOCUMENT_PRODUCT_ROLES,
    ArtifactRef,
    PipelineResult,
)


def _source_record(root: Path, source_id: str, pages: int = 2) -> dict[str, Any]:
    path = root / "sources" / f"{source_id}.pdf"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(f"%PDF-{source_id}".encode())
    return {
        "source_id": source_id,
        "official_title": source_id.replace("_", " ").title(),
        "document_type": "appendix",
        "source_role": "model_corpus",
        "landing_page_key": "page",
        "landing_page_url": "https://example.test",
        "linked_file_url": f"https://example.test/{source_id}.pdf",
        "final_resolved_url": f"https://example.test/{source_id}.pdf",
        "access_timestamp_utc": "2026-01-01T00:00:00Z",
        "http_status": 200,
        "response_headers": {},
        "redirect_history": [],
        "local_path": path.relative_to(root).as_posix(),
        "original_filename": path.name,
        "sha256": sha256_file(path),
        "byte_size": path.stat().st_size,
        "delivered_mime_type": "application/pdf",
        "detected_file_type": "pdf",
        "pdf_signature_valid": True,
        "pdf_page_count": pages,
        "retrieval_status": "complete",
        "validation_status": "accepted",
        "warnings": [],
        "visible_terms_note": "",
    }


def _workspace(tmp_path: Path, *, retry_limit: int = 0) -> tuple[Path, Path]:
    data_root = tmp_path / "data"
    records = data_root / "release" / "records"
    records.mkdir(parents=True)
    sources = [_source_record(data_root, "alpha"), _source_record(data_root, "beta", 3)]
    manifest_path = records / "source_manifest.json"
    write_json_atomic(
        manifest_path,
        {
            "manifest_schema_version": "1",
            "source_release_version": "release",
            "generated_at_utc": "2026-01-01T00:00:00Z",
            "source_spec_schema_version": "1",
            "source_spec_sha256": "a" * 64,
            "visible_terms_note": "",
            "landing_pages": [],
            "sources": sources,
            "aggregates": {},
            "warnings": [],
        },
    )
    write_json_atomic(
        records / "completion_record.json",
        {
            "source_release_version": "release",
            "manifest": {
                "local_path": manifest_path.relative_to(data_root).as_posix(),
                "sha256": sha256_file(manifest_path),
                "byte_size": manifest_path.stat().st_size,
            },
        },
    )
    configs = {
        name: f"configs/{name}.json"
        for name in (
            "content_parsing",
            "heading_evidence_parsing",
            "record_mapping",
            "hierarchy_inference",
            "document_structure",
            "document_reference_linking",
        )
    }
    spec_path = tmp_path / "run_spec.json"
    production_identity_path = Path(
        "benchmarks/er_bench/fixtures/document_publication/v2/production_identity.json"
    )
    production_id = json.loads(production_identity_path.read_text())["extraction_id"]
    write_json_atomic(
        spec_path,
        {
            "schema_version": "er_commons.document_run_spec.v2",
            "production_extraction_id": production_id,
            "production_identity_relative_path": production_identity_path.as_posix(),
            "scope_kind": "fixture",
            "source_release_version": "release",
            "source_manifest_relative_path": manifest_path.relative_to(data_root).as_posix(),
            "artifact_relative_root": "pipelines/test/task_03f",
            "document_processes": [
                {
                    "source_id": "alpha",
                    "configs": configs,
                },
                {"source_id": "beta", "configs": configs},
            ],
            "hierarchy_dispositions": [
                {"source_id": "alpha", "authority": "machine_validation"},
                {"source_id": "beta", "authority": "machine_validation"},
            ],
            "resource_policy": {
                "document_concurrency": 1,
                "page_batch_size": 4,
                "stage_batch_size": 4,
                "queue_capacity": 100,
                "cpu_threads_per_document": 4,
                "device": "cpu",
                "memory_estimate_bytes": 1_000_000,
                "storage_estimate_bytes": 1_000_000,
                "docling_timeout_seconds": 10,
                "outer_process_deadline_seconds": 20,
                "cancellation_grace_seconds": 1,
                "retry_limit": retry_limit,
            },
        },
    )
    return data_root, spec_path


def _result(
    tmp_path: Path, source_id: str, *, pages: int = 2, status: str = "SUCCESS"
) -> PipelineResult:
    data_root = tmp_path / "data"
    candidate = data_root / f"owner-{source_id}"
    candidate.mkdir(exist_ok=True)
    (candidate / "records.jsonl").write_text('{"record":"preserved"}\n')
    document_path = candidate / "canonical" / "documents.jsonl"
    document_path.parent.mkdir(exist_ok=True)
    source_path = data_root / "sources" / f"{source_id}.pdf"
    document_path.write_text(
        json.dumps(
            {
                "source_id": source_id,
                "source_sha256": sha256_file(source_path),
                "page_count": pages,
            }
        )
        + "\n"
    )
    completion = candidate / "records" / "completion_record.json"
    completion.parent.mkdir(exist_ok=True)
    completion.write_text('{"status":"complete"}\n')
    return PipelineResult(
        source_id=source_id,
        raw_docling_status=status,
        processed_pages=list(range(1, pages + 1)),
        structured_errors=[],
        warnings=[],
        final_candidate_root=str(candidate),
        stage_completions={
            role: ArtifactRef(
                path=completion.relative_to(data_root).as_posix(),
                sha256=sha256_file(completion),
            )
            for role in DOCUMENT_PRODUCT_ROLES
        },
        stage_timings={name: 0.01 for name in DOCUMENT_PROCESS_NAMES},
        resource_enforcement="validated_before_document_processes",
    )
