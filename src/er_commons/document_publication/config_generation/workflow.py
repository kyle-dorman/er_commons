"""Generate explicit current configurations from compact sealed metadata only."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from er_commons.artifact_verification import VerificationBudget
from er_commons.collection_processing.config import CollectionRunSpec
from er_commons.document_parsing.content_parsing.config import ContentParsingConfig
from er_commons.document_parsing.content_parsing.configured_application import (
    ChunkedExecutionPolicy,
)
from er_commons.document_parsing.content_parsing.sources import load_sealed_manifest_metadata
from er_commons.document_publication.config import DocumentRunSpec
from er_commons.document_publication.identity import canonical_digest
from er_commons.document_publication.production_identity import validate_production_identity
from er_commons.document_publication.sources import ManifestSelection
from er_commons.document_records.document_references.config import DocumentReferenceConfig
from er_commons.document_records.document_structure.config import DocumentStructureConfig
from er_commons.document_records.record_mapping.config import RecordMappingConfig
from er_commons.hierarchy_inference.config import HierarchyInferenceConfig
from er_commons.source_family_catalog import SourceFamilyCatalog
from er_commons.source_release.models import SourceRole
from er_commons.source_release.retained_processing import validate_processing_source

from .process_templates import generate_process_configs
from .production_identity import production_identity
from .shared import GenerationSpec, json_bytes, json_sha256, load_generation_spec, write_or_check
from .specifications import collection_spec, document_spec, source_family_catalog


@dataclass(frozen=True)
class GeneratedConfigs:
    """Proposed current bytes and their metadata-only verification accounting."""

    values: dict[Path, dict[str, Any]]
    budget: VerificationBudget


def build_document_configs(spec: GenerationSpec) -> GeneratedConfigs:
    """Build every output before checking or publishing any path."""
    budget = VerificationBudget()
    sources, scope = _source_records(spec, budget)
    budget.read_json(
        spec.data_root / spec.model_inventory_relative_path,
        root=spec.data_root,
        role="model_descriptor",
        source_id="generation",
    )
    titles = {source["source_id"]: source["official_title"] for source in sources}
    catalog = source_family_catalog(spec, sources)
    processes, paths = generate_process_configs(spec, sources, titles, json_sha256(catalog))
    _validate_process_proposals(processes)
    proposed = {
        spec.project_path(spec.catalog_output): catalog,
        spec.project_path(spec.collection_spec_output): collection_spec(spec, sources, budget),
        **{path: spec.chunked_policy for path in spec.chunked_policy_paths(sources)},
        **processes,
    }
    identity = production_identity(spec, sources, proposed, paths, scope, budget)
    proposed.update(
        {
            spec.project_path(spec.identity_output): identity,
            spec.project_path(spec.document_spec_output): document_spec(
                spec, paths, identity["extraction_id"]
            ),
        }
    )
    if len(proposed) != len(processes) + len(spec.chunked_policy_paths(sources)) + 4:
        raise ValueError("generated output paths overlap")
    _validate_proposals(spec, proposed, sources)
    return GeneratedConfigs(proposed, budget)


def generate_document_configs(generation_spec: Path, *, check: bool = False) -> GeneratedConfigs:
    """Compare or publish only the current outputs selected by an explicit request."""
    generated = build_document_configs(load_generation_spec(generation_spec))
    write_or_check(generated.values, check=check)
    return generated


def _source_records(
    spec: GenerationSpec, budget: VerificationBudget
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Preserve source manifest membership and produce one baseline-bound scope."""
    baseline = ManifestSelection(
        spec.baseline_release_version, spec.baseline_manifest_relative_path
    )
    manifests = {
        (
            baseline.source_release_version,
            baseline.source_manifest_path,
        ): load_sealed_manifest_metadata(spec.data_root, baseline, budget)
    }
    sources = []
    for binding in spec.sources:
        key = (binding.source_release_version, binding.source_manifest_path)
        if key not in manifests:
            manifests[key] = load_sealed_manifest_metadata(spec.data_root, binding, budget)
        matches = [
            record
            for record in manifests[key].sources
            if record.source_id == binding.source_id
            and (
                record.source_role == SourceRole.MODEL_CORPUS
                or (
                    binding.logical_source_id == "deir_appendix_f1"
                    and binding.substitution_relative_path is not None
                    and record.source_role == SourceRole.QUALIFIED_SUBSTITUTE
                )
            )
        ]
        if len(matches) != 1 or matches[0].sha256 != binding.expected_sha256:
            raise ValueError(f"generation source binding differs: {binding.source_id}")
        validate_processing_source(spec.data_root, manifests[key], matches[0])
        completion = budget.read_json(
            spec.data_root / binding.source_manifest_path.parent / "completion_record.json",
            root=spec.data_root,
            role="completion",
            source_id=binding.source_id,
        )
        assert isinstance(completion, dict) and isinstance(completion["manifest"], dict)
        sources.append(
            {
                **matches[0].model_dump(mode="json"),
                "manifest_sha256": completion["manifest"]["sha256"],
            }
        )
    completion_path = (
        spec.data_root / baseline.source_manifest_path.parent / "completion_record.json"
    )
    completion = budget.read_json(
        completion_path, root=spec.data_root, role="completion", source_id="generation"
    )
    assert isinstance(completion, dict)
    scope: dict[str, Any] = {
        "source_release_version": baseline.source_release_version,
        "source_manifest": completion["manifest"],
        "release_completion": {
            "path": completion_path.relative_to(spec.data_root).as_posix(),
            "sha256": budget.hash_file(
                completion_path, root=spec.data_root, role="completion", source_id="generation"
            ),
            "byte_size": completion_path.stat().st_size,
        },
        "ordered_source_ids": [source["source_id"] for source in sources],
        "ordered_source_records_sha256": canonical_digest(
            [
                {key: source[key] for key in ("source_id", "sha256", "pdf_page_count")}
                for source in sources
            ]
        ),
        "allowed_scope_kinds": ["production_full"],
    }
    return sources, scope


def _validate_proposals(
    spec: GenerationSpec, proposed: dict[Path, dict[str, Any]], sources: list[dict[str, Any]]
) -> None:
    """Reject invalid control documents before creating any generated file."""
    DocumentRunSpec.model_validate(proposed[spec.project_path(spec.document_spec_output)])
    CollectionRunSpec.model_validate(proposed[spec.project_path(spec.collection_spec_output)])
    SourceFamilyCatalog.from_bytes(json_bytes(proposed[spec.project_path(spec.catalog_output)]))
    validate_production_identity(
        proposed[spec.project_path(spec.identity_output)],
        expected_source_ids=[source["source_id"] for source in sources],
        expected_scope_kind="production_full",
    )
    policy = ChunkedExecutionPolicy.model_validate(spec.chunked_policy)
    if policy.source_selection.pdf_page_count_greater_than != spec.chunked_page_threshold:
        raise ValueError("chunked policy and generation selection thresholds differ")


def _validate_process_proposals(processes: dict[Path, dict[str, Any]]) -> None:
    """Validate all six generated owners without opening their downstream artifacts."""
    models = {
        "content_parsing": ContentParsingConfig,
        "heading_evidence_parsing": ContentParsingConfig,
        "record_mapping": RecordMappingConfig,
        "hierarchy_inference": HierarchyInferenceConfig,
        "document_structure": DocumentStructureConfig,
        "document_reference_linking": DocumentReferenceConfig,
    }
    for path, value in processes.items():
        TypeAdapter(models[path.stem]).validate_python(value)
