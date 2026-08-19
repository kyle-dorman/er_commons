"""Close the Task 03H production identity over exact artifacts and owned code."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from er_commons.document_publication.identity import canonical_digest

from .shared import (
    CATALOG_PROJECT_PATH,
    COLLECTION_SPEC_PATH,
    RESOLUTION_POLICY,
    ROOT,
    TARGET_POLICY,
    sha256,
)


def production_identity(
    *,
    sources: list[dict[str, Any]],
    manifest_path: Path,
    completion_path: Path,
    data_root: Path,
    process_paths: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Build the closed production-full identity recipe."""
    process_artifacts = sorted(path for paths in process_paths.values() for path in paths.values())
    document_artifacts = [
        *process_artifacts,
        "benchmarks/er_bench/schemas/document_publication/v2/document_run_spec.schema.json",
        "benchmarks/er_bench/schemas/document_publication/v2/production_identity.schema.json",
        "benchmarks/er_bench/schemas/hierarchy_correction/v1/records.schema.json",
        "benchmarks/er_bench/schemas/canonical_extraction/v2/semantic_structure.schema.json",
        "benchmarks/er_bench/schemas/canonical_extraction/v3/cross_references.schema.json",
        "docs/specs/task03d_appendix_p_mapping_v1.md",
        "docs/specs/hierarchy_correction_v1.md",
        "docs/specs/semantic_structure_v2.md",
        "docs/specs/cross_references_v3.md",
    ]
    collection_artifacts = [
        CATALOG_PROJECT_PATH.relative_to(ROOT).as_posix(),
        COLLECTION_SPEC_PATH.relative_to(ROOT).as_posix(),
        TARGET_POLICY.relative_to(ROOT).as_posix(),
        RESOLUTION_POLICY.relative_to(ROOT).as_posix(),
        "benchmarks/er_bench/schemas/collection_processing/v2/collection_run_spec.schema.json",
        "benchmarks/er_bench/schemas/collection_processing/v2/records.schema.json",
    ]
    preimage = {
        "schema_version": "er_commons.document_publication_identity_preimage.v2",
        "contract_revision": "task_03h_production_full_v1",
        "extraction_version_name": "brisbane_baylands_2025_deir_task03h_candidate_v1",
        "production_scope": _production_scope(
            sources=sources,
            manifest_path=manifest_path,
            completion_path=completion_path,
            data_root=data_root,
        ),
        "document_process_contract": _contract(
            "task03h-six-process-fresh-document-v1",
            document_artifacts,
            (
                "src/er_commons/document_parsing",
                "src/er_commons/hierarchy_inference",
                "src/er_commons/document_records",
                "src/er_commons/document_publication",
                "src/er_commons/source_release",
            ),
            (
                "scripts/prepare_task03h.py",
                "src/er_commons/artifact_io.py",
                "src/er_commons/source_family_catalog.py",
            ),
        ),
        "collection_process_contract": _contract(
            "task03h-collection-handoff-v2",
            collection_artifacts,
            (
                "src/er_commons/collection_processing",
                "src/er_commons/extraction_reporting",
            ),
            (
                "src/er_commons/artifact_io.py",
                "src/er_commons/source_family_catalog.py",
                "src/er_commons/cli.py",
            ),
        ),
    }
    digest = canonical_digest(preimage)
    return {
        "record_type": "production_identity",
        "schema_version": "er_commons.document_publication_identity.v2",
        "fixture_status": "identity_recipe",
        "execution_status": "not_executed",
        "extraction_id": f"exv1-{digest}",
        "identity_sha256": digest,
        "preimage": preimage,
    }


def _production_scope(
    *,
    sources: list[dict[str, Any]],
    manifest_path: Path,
    completion_path: Path,
    data_root: Path,
) -> dict[str, Any]:
    """Bind sealed release records and exact ordered source facts."""
    return {
        "source_release_version": "brisbane_baylands_2025_deir_sources_v1",
        "source_manifest": _external_reference(manifest_path, data_root),
        "release_completion": _external_reference(completion_path, data_root),
        "ordered_source_ids": [source["source_id"] for source in sources],
        "ordered_source_records_sha256": canonical_digest(
            [
                {
                    "source_id": source["source_id"],
                    "sha256": source["sha256"],
                    "pdf_page_count": source["pdf_page_count"],
                }
                for source in sources
            ]
        ),
        "allowed_scope_kinds": ["production_full"],
    }


def _contract(
    version: str,
    artifacts: list[str],
    code_roots: tuple[str, ...],
    extra_code: tuple[str, ...],
) -> dict[str, Any]:
    """Close one process contract over explicit artifacts and owned Python code."""
    code = set(extra_code)
    for root in code_roots:
        code.update(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / root).rglob("*.py")
            if path.is_file()
        )
    return {
        "version": version,
        "artifacts": [_project_reference(path) for path in sorted(set(artifacts))],
        "owned_code": [_project_reference(path) for path in sorted(code)],
    }


def _project_reference(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    return {"path": relative, "sha256": sha256(path), "byte_size": path.stat().st_size}


def _external_reference(path: Path, data_root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(data_root).as_posix(),
        "sha256": sha256(path),
        "byte_size": path.stat().st_size,
    }
