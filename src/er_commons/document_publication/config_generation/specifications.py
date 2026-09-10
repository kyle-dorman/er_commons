"""Build catalog and run specifications from explicit source and policy inputs."""

from __future__ import annotations

import os
from typing import Any

from er_commons.artifact_verification import VerificationBudget

from .shared import GenerationSpec


def source_family_catalog(spec: GenerationSpec, sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Preserve explicitly supplied aliases rather than guessing corpus-specific names."""
    bindings = {item.source_id: item for item in spec.sources}
    return {
        "schema_version": "er_commons.source_family_catalog.v1",
        "catalog_version": f"{spec.name_prefix}_source_family_v1",
        "source_family_id": spec.source_family_id,
        "sources": [
            {
                "source": {
                    key: source[key]
                    for key in ("source_id", "sha256", "byte_size", "pdf_page_count")
                },
                "family_root_source_id": spec.family_root_source_id,
                "document_role": "root_report"
                if source["source_id"] == spec.family_root_source_id
                else "top_level_appendix",
                "parent_source_id": None
                if source["source_id"] == spec.family_root_source_id
                else spec.family_root_source_id,
                "reference_aliases": list(bindings[source["source_id"]].reference_aliases),
            }
            for source in sources
        ],
    }


def collection_spec(
    spec: GenerationSpec, sources: list[dict[str, Any]], budget: VerificationBudget
) -> dict[str, Any]:
    """Build explicit physical membership with original logical slots retained."""
    return {
        "schema_version": "er_commons.collection_run_spec.v3",
        "document_run_spec": os.path.relpath(
            spec.document_spec_output, spec.collection_spec_output.parent
        ),
        "source_ids": [source["source_id"] for source in sources],
        "source_membership": [
            {
                "logical_source_id": item.logical_source_id or item.source_id,
                "physical_source_id": item.source_id,
                "substitution_relative_path": item.substitution_relative_path.as_posix()
                if item.substitution_relative_path
                else None,
            }
            for item in spec.sources
        ],
        "source_family_catalog_relative_path": spec.catalog_data_relative_path.as_posix(),
        "blocking_policy": "all_sources_successful",
        "document_evidence_mode": "document_attempt",
        "target_policy_sha256": budget.hash_file(
            spec.project_path(spec.target_policy),
            root=spec.repository_root,
            role="config",
            source_id="generation",
        ),
        "resolution_policy_sha256": budget.hash_file(
            spec.project_path(spec.resolution_policy),
            root=spec.repository_root,
            role="config",
            source_id="generation",
        ),
        "ordering_policy_version": "record_target_order_v2",
    }


def document_spec(
    spec: GenerationSpec, process_paths: dict[str, dict[str, str]], extraction_id: str
) -> dict[str, Any]:
    """Build a new recipe while preserving every selected original source manifest."""
    return {
        "schema_version": "er_commons.document_run_spec.v3",
        "production_extraction_id": extraction_id,
        "production_identity_relative_path": spec.identity_output.as_posix(),
        "scope_kind": "production_full",
        "source_release_version": spec.baseline_release_version,
        "source_manifest_relative_path": spec.baseline_manifest_relative_path.as_posix(),
        "artifact_relative_root": (spec.run_root / "document_publications").as_posix(),
        "document_processes": [
            {
                "source_id": source.source_id,
                "lineage_mode": "fresh_build",
                "configs": process_paths[source.source_id],
                "source_release_version": source.source_release_version,
                "source_manifest_relative_path": source.source_manifest_path.as_posix(),
            }
            for source in spec.sources
        ],
        "hierarchy_dispositions": [
            {"source_id": source.source_id, "authority": "machine_validation"}
            for source in spec.sources
        ],
        "resource_policy": spec.resource_policy.model_dump(mode="json"),
    }
