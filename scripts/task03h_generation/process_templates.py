"""Specialize six source-neutral current Task 03H process templates."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .shared import (
    CATALOG_DATA_RELATIVE,
    HIERARCHY_ROOT,
    MANIFEST_RELATIVE,
    MANIFEST_SHA256,
    PARSE_ROOT,
    RECORD_ROOT,
    ROOT,
    TASK_CONFIG_ROOT,
    TASK_TEMPLATE_ROOT,
    ZERO_EXV1,
    ZERO_HCORV1,
    ZERO_PRV1,
    ZERO_SHA256,
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


def load_process_templates() -> dict[str, dict[str, Any]]:
    """Load only the six current source-neutral Task 03H templates."""
    return {role: load_object(TASK_TEMPLATE_ROOT / f"{role}.json") for role in PROCESS_ROLES}


def generate_process_configs(
    sources: list[dict[str, Any]],
    titles: dict[str, str],
    catalog_sha256: str,
) -> tuple[dict[Path, dict[str, Any]], dict[str, dict[str, str]]]:
    """Generate all source-specialized configs and their project-relative paths."""
    templates = load_process_templates()
    outputs: dict[Path, dict[str, Any]] = {}
    paths_by_source: dict[str, dict[str, str]] = {}
    for source in sources:
        source_id = source["source_id"]
        directory = TASK_CONFIG_ROOT / source_id
        relative_paths = {
            role: (directory / f"{role}.json").relative_to(ROOT).as_posix() for role in templates
        }
        paths_by_source[source_id] = relative_paths
        values = specialize_source_processes(source, titles[source_id], templates, catalog_sha256)
        outputs.update({ROOT / relative_paths[role]: value for role, value in values.items()})
    return outputs, paths_by_source


def specialize_source_processes(
    source: dict[str, Any],
    title: str,
    templates: dict[str, dict[str, Any]],
    catalog_sha256: str,
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
    return {
        "content_parsing": _producer_config(
            templates["content_parsing"], source_id, producer_source, "content"
        ),
        "heading_evidence_parsing": _producer_config(
            templates["heading_evidence_parsing"], source_id, producer_source, "heading"
        ),
        "record_mapping": _record_mapping_config(templates["record_mapping"], source),
        "hierarchy_inference": _hierarchy_config(
            templates["hierarchy_inference"], source_id, producer_source
        ),
        "document_structure": _document_structure_config(templates["document_structure"], source),
        "document_reference_linking": _reference_config(
            templates["document_reference_linking"], source_id, catalog_sha256
        ),
    }


def _producer_config(
    template: dict[str, Any],
    source_id: str,
    producer_source: dict[str, Any],
    role_name: str,
) -> dict[str, Any]:
    value = copy.deepcopy(template)
    value.update(
        {
            "pipeline_id": f"brisbane_baylands_2025_deir_task03h_{source_id}_{role_name}_v1",
            "source": producer_source,
            "artifact_relative_root": PARSE_ROOT,
        }
    )
    return value


def _record_mapping_config(template: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    source_id = source["source_id"]
    value = copy.deepcopy(template)
    value.update(
        {
            "candidate_version_name": f"{source_id}_task03h_core_candidate_v1",
            "ordered_materialization_scope": [
                {
                    "source_id": source_id,
                    "source_sha256": source["sha256"],
                    "pdf_page_count": source["pdf_page_count"],
                }
            ],
            "producer_artifact_relative_root": PARSE_ROOT,
            "producer_run_id": ZERO_PRV1,
            "artifact_relative_root": RECORD_ROOT,
        }
    )
    return value


def _hierarchy_config(
    template: dict[str, Any], source_id: str, producer_source: dict[str, Any]
) -> dict[str, Any]:
    value = copy.deepcopy(template)
    value.update(
        {
            "pipeline_id": f"brisbane_baylands_2025_deir_task03h_{source_id}_hierarchy_v1",
            "publication_authorization": "machine_validation",
            "source": producer_source,
            "producer_artifact_relative_root": PARSE_ROOT,
            "producer_run_id": ZERO_PRV1,
            "artifact_relative_root": HIERARCHY_ROOT,
            "bounded_acceptance_artifact_relative_root": None,
            "bounded_acceptance_config_relative_path": None,
        }
    )
    return value


def _document_structure_config(template: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    source_id = source["source_id"]
    value = copy.deepcopy(template)
    value.update(
        {
            "candidate_version_name": f"{source_id}_task03h_semantic_candidate_v2",
            "control_profile": "strict_quality_gate",
            "source": {
                "source_id": source_id,
                "source_sha256": source["sha256"],
                "physical_page_count": source["pdf_page_count"],
            },
            "baseline_candidate_relative_root": f"{RECORD_ROOT}/{ZERO_EXV1}",
            "baseline_candidate_id": ZERO_EXV1,
            "baseline_producer_relative_root": PARSE_ROOT,
            "baseline_producer_run_id": ZERO_PRV1,
            "hierarchy_producer_relative_root": PARSE_ROOT,
            "hierarchy_producer_run_id": ZERO_PRV1,
            "hierarchy_candidate_relative_root": f"{HIERARCHY_ROOT}/{ZERO_HCORV1}",
            "hierarchy_candidate_id": ZERO_HCORV1,
            "bounded_acceptance_relative_path": None,
            "bounded_acceptance_policy_relative_path": None,
            "producer_comparison_relative_path": None,
            "artifact_relative_root": RECORD_ROOT,
        }
    )
    value.pop("expectations", None)
    return value


def _reference_config(
    template: dict[str, Any], source_id: str, catalog_sha256: str
) -> dict[str, Any]:
    value = copy.deepcopy(template)
    value.update(
        {
            "upstream_candidate_id": ZERO_EXV1,
            "upstream_completion_sha256": ZERO_SHA256,
            "upstream_inventory_sha256": ZERO_SHA256,
            "source_id": source_id,
            "candidate_version_name": f"{source_id}_task03h_cross_references_v3",
            "artifact_relative_root": RECORD_ROOT,
            "source_manifest_relative_path": MANIFEST_RELATIVE.as_posix(),
            "source_manifest_sha256": MANIFEST_SHA256,
            "source_family_catalog_relative_path": CATALOG_DATA_RELATIVE.as_posix(),
            "source_family_catalog_sha256": catalog_sha256,
        }
    )
    return value
