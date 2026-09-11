"""Narrow code and dependency ownership for document-structure identity."""

from __future__ import annotations

import json
from importlib.metadata import version
from pathlib import Path


def owned_code_paths(project_root: Path, config_path: Path) -> tuple[Path, ...]:
    """Return code and contracts that can change document-structure bytes."""
    package = project_root / "src/er_commons/document_records/document_structure"
    module_names = (
        "__init__.py",
        "aliases.py",
        "baseline.py",
        "bridge.py",
        "bundle.py",
        "code_inventory.py",
        "comparison.py",
        "config.py",
        "constants.py",
        "construction.py",
        "errors.py",
        "handoff.py",
        "identity.py",
        "inputs.py",
        "lifecycle.py",
        "normalization.py",
        "page_labels.py",
        "parser_evidence.py",
        "policies/__init__.py",
        "policies/aliases.py",
        "policies/bridge.py",
        "policies/control.py",
        "policies/correspondence.py",
        "policies/page_labels.py",
        "policies/sections.py",
        "producer_alignment.py",
        "publication.py",
        "replacement_evidence.py",
        "runtime.py",
        "sealing.py",
        "sections.py",
        "support.py",
        "validation.py",
        "workflow.py",
    )
    paths = {(package / name).resolve() for name in module_names}
    cross_owner_modules = (
        "src/er_commons/document_records/record_mapping/layout.py",
        "src/er_commons/document_records/record_mapping/no_table_handoff.py",
        "src/er_commons/document_records/record_mapping/table_text_ownership.py",
        "src/er_commons/hierarchy_inference/bounded_acceptance.py",
        "src/er_commons/hierarchy_inference/bundle.py",
        "src/er_commons/hierarchy_inference/candidate_records.py",
        "src/er_commons/hierarchy_inference/candidate_storage.py",
        "src/er_commons/hierarchy_inference/candidate_verification.py",
        "src/er_commons/hierarchy_inference/checks.py",
        "src/er_commons/hierarchy_inference/config.py",
        "src/er_commons/hierarchy_inference/constants.py",
        "src/er_commons/hierarchy_inference/digests.py",
        "src/er_commons/hierarchy_inference/progress.py",
        "src/er_commons/hierarchy_inference/publication.py",
        "src/er_commons/hierarchy_inference/publication_authorization.py",
        "src/er_commons/hierarchy_inference/record_schema.py",
        "src/er_commons/hierarchy_inference/validation.py",
        "src/er_commons/artifact_io.py",
        "src/er_commons/document_parsing/content_parsing/evidence.py",
        "src/er_commons/document_parsing/content_parsing/records.py",
        "src/er_commons/document_parsing/content_parsing/references.py",
        "src/er_commons/document_parsing/heading_evidence_parsing/document.py",
        "src/er_commons/document_parsing/heading_evidence_parsing/heading_overlay.py",
        "src/er_commons/document_records/record_mapping/candidate_identity.py",
        "src/er_commons/document_records/record_mapping/errors.py",
        "src/er_commons/document_records/record_mapping/identity.py",
        "src/er_commons/document_records/record_mapping/provenance.py",
        "src/er_commons/document_records/record_mapping/publication.py",
        "src/er_commons/document_records/record_mapping/record_sets.py",
        "src/er_commons/document_records/record_mapping/table_artifacts.py",
        "src/er_commons/document_records/record_mapping/table_cleanup.py",
        "src/er_commons/document_records/record_mapping/table_families.py",
        "src/er_commons/document_records/record_mapping/table_projection.py",
        "src/er_commons/document_records/record_mapping/table_records.py",
        "src/er_commons/document_records/record_mapping/table_regions.py",
        "src/er_commons/document_records/record_mapping/tables.py",
    )
    paths.update(
        {
            *((project_root / relative).resolve() for relative in cross_owner_modules),
            config_path.resolve(),
            (project_root / "docs/specs/semantic_structure_v2.md").resolve(),
            (
                project_root
                / (
                    "benchmarks/er_bench/schemas/canonical_extraction/v2/"
                    "semantic_structure.schema.json"
                )
            ).resolve(),
        }
    )
    config_value = json.loads(config_path.read_bytes())
    if config_value.get("schema_version") == "2.0.0":
        paths.update(
            {
                (package / "repeated_headings.py").resolve(),
                (package / "repeated_heading_policy.py").resolve(),
                (package / "repeated_heading_projection.py").resolve(),
                (package / "repeated_heading_qualification.py").resolve(),
                (project_root / "docs/specs/repeated_heading_repair_v1.md").resolve(),
                (
                    project_root
                    / (
                        "benchmarks/er_bench/schemas/task06_recovery/v1/"
                        "repeated_heading_decision.schema.json"
                    )
                ).resolve(),
            }
        )
    return tuple(sorted(paths))


def runtime_dependency_versions() -> dict[str, str]:
    """Bind only third-party runtimes used by document-structure construction."""
    return {name: version(name) for name in ("jsonschema", "pydantic", "rfc8785")}
