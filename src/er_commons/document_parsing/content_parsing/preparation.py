"""Prepare verified content-parsing inputs and deterministic identities."""

from __future__ import annotations

from pathlib import Path

from er_commons.artifact_io import sha256_file
from er_commons.artifact_verification import VerificationBudget
from er_commons.document_parsing.content_parsing import conversion_identity, runtime, sources
from er_commons.document_parsing.content_parsing.config import ContentParsingConfig
from er_commons.document_parsing.content_parsing.conversion_preflight import (
    PreparedContentParsing as PreparedContentParsing,
)
from er_commons.document_parsing.content_parsing.identity import (
    ContentParsingIdentity,
    build_content_parsing_identity,
    code_identity,
    parsing_code_paths,
)
from er_commons.document_parsing.table_reconstruction.pipeline import installed_table_environment


def _conversion_identity(
    config: ContentParsingConfig,
    source: sources.CompleteResolvedSource,
    paths: tuple[Path, Path, Path, Path],
    model_inventory: runtime.ModelInventory,
    budget: VerificationBudget,
) -> ContentParsingIdentity:
    """Select a sealed conversion identity without re-deriving accepted conversion inputs."""
    if config.accepted_conversion_id is not None:
        return ContentParsingIdentity(
            run_id=config.accepted_conversion_id,
            payload={"identity_schema_version": "accepted_conversion_reference.v1"},
        )
    repo_root, source_manifest, source_completion, model_inventory_path = paths
    return conversion_identity.derive_conversion_identity(
        repo_root=repo_root,
        config=config,
        source=source,
        source_manifest_path=source_manifest,
        source_completion_path=source_completion,
        model_inventory_path=model_inventory_path,
        model_inventory=model_inventory,
        budget=budget,
    )


def prepare_content_parsing(
    data_root: Path,
    *,
    config: ContentParsingConfig,
    config_sha256: str,
    budget: VerificationBudget | None = None,
) -> PreparedContentParsing:
    """Verify source/models/runtime and derive the code-bound producer identity."""
    budget = budget or VerificationBudget()
    manifest = sources.load_sealed_manifest(data_root, config)
    source = (
        sources.resolve_complete_source_metadata(data_root, config.source, manifest)
        if config.accepted_conversion_id is not None
        else sources.resolve_complete_source(data_root, config.source, manifest)
    )
    source_manifest_path = (data_root / config.source_manifest_relative_path).resolve()
    source_completion_path = source_manifest_path.parent / "completion_record.json"
    model_inventory_path = (data_root / config.model_inventory_relative_path).resolve()
    model_inventory, models_root = runtime.load_model_inventory_metadata(
        data_root, model_inventory_path
    )
    repo_root = Path(__file__).resolve().parents[4]
    conversion = _conversion_identity(
        config,
        source,
        (repo_root, source_manifest_path, source_completion_path, model_inventory_path),
        model_inventory,
        budget,
    )
    options, format_option = runtime.build_converter_options(
        models_root,
        thread_count=config.thread_count,
        heading_hierarchy_options=conversion_identity.COMMON_HEADING_HIERARCHY,
    )
    runtime_identity = conversion_identity.effective_runtime_identity(
        config, options, format_option
    )
    project_code = code_identity(parsing_code_paths(repo_root), repo_root=repo_root, budget=budget)
    identity = build_content_parsing_identity(
        config=config,
        source=source,
        source_manifest_path=source_manifest_path,
        source_completion_path=source_completion_path,
        table_environment=installed_table_environment(),
        project_code=project_code,
        conversion_id=conversion.run_id,
    )
    return PreparedContentParsing(
        config=config,
        config_sha256=config_sha256,
        source=source,
        source_manifest_path=source_manifest_path,
        models_root=models_root,
        model_inventory_path=model_inventory_path,
        model_inventory=model_inventory,
        model_inventory_sha256=sha256_file(model_inventory_path),
        runtime=runtime_identity,
        conversion_identity=conversion,
        identity=identity,
    )
