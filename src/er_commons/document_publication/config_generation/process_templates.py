"""Specialize six explicitly selected current process templates."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .shared import (
    ZERO_EXV1,
    ZERO_HCORV1,
    ZERO_PRV1,
    ZERO_SHA256,
    GenerationSpec,
    SourceBinding,
    load_object,
)

PROCESS_ROLES = (
    "content_parsing",
    "heading_evidence_parsing",
    "record_mapping",
    "hierarchy_inference",
    "document_structure",
    "document_reference_linking",
)


def load_process_templates(spec: GenerationSpec) -> dict[str, dict[str, Any]]:
    """Load only the six explicitly selected current templates."""
    return {role: load_object(spec.project_path(spec.templates[role])) for role in PROCESS_ROLES}


def generate_process_configs(
    spec: GenerationSpec,
    sources: list[dict[str, Any]],
    titles: dict[str, str],
    catalog_sha256: str,
) -> tuple[dict[Path, dict[str, Any]], dict[str, dict[str, str]]]:
    """Generate all source-specialized configs and their project-relative paths."""
    templates = load_process_templates(spec)
    outputs: dict[Path, dict[str, Any]] = {}
    paths_by_source: dict[str, dict[str, str]] = {}
    for source in sources:
        source_id = source["source_id"]
        directory = spec.project_path(spec.config_root / source_id)
        relative_paths = {
            role: (directory / f"{role}.json").relative_to(spec.repository_root).as_posix()
            for role in templates
        }
        paths_by_source[source_id] = relative_paths
        values = specialize_source_processes(
            source,
            titles[source_id],
            templates,
            catalog_sha256,
            spec=spec,
            binding=next(item for item in spec.sources if item.source_id == source_id),
        )
        outputs.update(
            {spec.repository_root / relative_paths[role]: value for role, value in values.items()}
        )
    return outputs, paths_by_source


def specialize_source_processes(
    source: dict[str, Any],
    title: str,
    templates: dict[str, dict[str, Any]],
    catalog_sha256: str,
    *,
    spec: GenerationSpec,
    binding: SourceBinding,
) -> dict[str, dict[str, Any]]:
    """Specialize each current owner template for one sealed source record."""
    source_id = source["source_id"]
    producer_source = {
        "source_id": source_id,
        "official_title": title,
        "expected_sha256": source["sha256"],
        "expected_byte_size": source["byte_size"],
        "expected_pdf_page_count": source["pdf_page_count"],
    }
    values = {
        "content_parsing": _producer_config(
            templates["content_parsing"], source_id, producer_source, "content", spec, binding
        ),
        "heading_evidence_parsing": _producer_config(
            templates["heading_evidence_parsing"],
            source_id,
            producer_source,
            "heading",
            spec,
            binding,
        ),
        "record_mapping": _record_mapping_config(templates["record_mapping"], source, spec),
        "hierarchy_inference": _hierarchy_config(
            templates["hierarchy_inference"], source_id, producer_source, spec
        ),
        "document_structure": _document_structure_config(
            templates["document_structure"], source, spec
        ),
        "document_reference_linking": _reference_config(
            templates["document_reference_linking"],
            source_id,
            catalog_sha256,
            spec,
            binding,
            source["manifest_sha256"],
        ),
    }
    for value in values.values():
        if "source_release_version" in value:
            value["source_release_version"] = binding.source_release_version
        if "source_manifest_relative_path" in value:
            value["source_manifest_relative_path"] = binding.source_manifest_path.as_posix()
        if "source_manifest_sha256" in value:
            value["source_manifest_sha256"] = source["manifest_sha256"]
    return values


def _producer_config(
    template: dict[str, Any],
    source_id: str,
    producer_source: dict[str, Any],
    role_name: str,
    spec: GenerationSpec,
    binding: SourceBinding,
) -> dict[str, Any]:
    value = copy.deepcopy(template)
    value.update(
        {
            "pipeline_id": f"{spec.name_prefix}_{source_id}_{role_name}_v1",
            "source": producer_source,
            "source_release_version": binding.source_release_version,
            "source_manifest_relative_path": binding.source_manifest_path.as_posix(),
            "model_inventory_relative_path": spec.model_inventory_relative_path.as_posix(),
            "thread_count": spec.resource_policy.cpu_threads_per_document,
            "device": spec.resource_policy.device,
            "document_timeout_seconds": spec.resource_policy.docling_timeout_seconds,
            "artifact_relative_root": (spec.run_root / "document_parse_evidence").as_posix(),
        }
    )
    return value


def _record_mapping_config(
    template: dict[str, Any], source: dict[str, Any], spec: GenerationSpec
) -> dict[str, Any]:
    source_id = source["source_id"]
    value = copy.deepcopy(template)
    value.update(
        {
            "candidate_version_name": f"{source_id}_{spec.name_prefix}_core_candidate_v1",
            "ordered_materialization_scope": [
                {
                    "source_id": source_id,
                    "source_sha256": source["sha256"],
                    "pdf_page_count": source["pdf_page_count"],
                }
            ],
            "producer_artifact_relative_root": (
                spec.run_root / "document_parse_evidence"
            ).as_posix(),
            "producer_run_id": ZERO_PRV1,
            "artifact_relative_root": (spec.run_root / "document_records").as_posix(),
        }
    )
    return value


def _hierarchy_config(
    template: dict[str, Any], source_id: str, producer_source: dict[str, Any], spec: GenerationSpec
) -> dict[str, Any]:
    value = copy.deepcopy(template)
    value.update(
        {
            "pipeline_id": f"{spec.name_prefix}_{source_id}_hierarchy_v1",
            "publication_authorization": "machine_validation",
            "source": producer_source,
            "producer_artifact_relative_root": (
                spec.run_root / "document_parse_evidence"
            ).as_posix(),
            "producer_run_id": ZERO_PRV1,
            "artifact_relative_root": (spec.run_root / "hierarchy_inference").as_posix(),
            "bounded_acceptance_artifact_relative_root": None,
            "bounded_acceptance_config_relative_path": None,
        }
    )
    return value


def _document_structure_config(
    template: dict[str, Any], source: dict[str, Any], spec: GenerationSpec
) -> dict[str, Any]:
    source_id = source["source_id"]
    value = copy.deepcopy(template)
    value.update(
        {
            "candidate_version_name": f"{source_id}_{spec.name_prefix}_semantic_candidate_v2",
            "control_profile": "strict_quality_gate",
            "source": {
                "source_id": source_id,
                "source_sha256": source["sha256"],
                "physical_page_count": source["pdf_page_count"],
            },
            "baseline_candidate_relative_root": (
                spec.run_root / "document_records" / ZERO_EXV1
            ).as_posix(),
            "baseline_candidate_id": ZERO_EXV1,
            "baseline_producer_relative_root": (
                spec.run_root / "document_parse_evidence"
            ).as_posix(),
            "baseline_producer_run_id": ZERO_PRV1,
            "hierarchy_producer_relative_root": (
                spec.run_root / "document_parse_evidence"
            ).as_posix(),
            "hierarchy_producer_run_id": ZERO_PRV1,
            "hierarchy_candidate_relative_root": (
                spec.run_root / "hierarchy_inference" / ZERO_HCORV1
            ).as_posix(),
            "hierarchy_candidate_id": ZERO_HCORV1,
            "bounded_acceptance_relative_path": None,
            "bounded_acceptance_policy_relative_path": None,
            "producer_comparison_relative_path": None,
            "artifact_relative_root": (spec.run_root / "document_structure").as_posix(),
        }
    )
    value.pop("expectations", None)
    return value


def _reference_config(
    template: dict[str, Any],
    source_id: str,
    catalog_sha256: str,
    spec: GenerationSpec,
    binding: SourceBinding,
    manifest_sha256: str,
) -> dict[str, Any]:
    value = copy.deepcopy(template)
    value.update(
        {
            "upstream_candidate_id": ZERO_EXV1,
            "upstream_completion_sha256": ZERO_SHA256,
            "upstream_inventory_sha256": ZERO_SHA256,
            "source_id": source_id,
            "candidate_version_name": f"{source_id}_{spec.name_prefix}_cross_references_v3",
            "artifact_relative_root": (spec.run_root / "document_structure").as_posix(),
            "source_manifest_relative_path": binding.source_manifest_path.as_posix(),
            "source_manifest_sha256": manifest_sha256,
            "source_family_catalog_relative_path": spec.catalog_data_relative_path.as_posix(),
            "source_family_catalog_sha256": catalog_sha256,
        }
    )
    return value
