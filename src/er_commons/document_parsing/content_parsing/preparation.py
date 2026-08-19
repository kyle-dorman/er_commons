"""Prepare verified content-parsing inputs and deterministic identities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.artifact_io import sha256_file
from er_commons.document_parsing.content_parsing.config import ContentParsingConfig
from er_commons.document_parsing.content_parsing.conversion_identity import (
    COMMON_HEADING_HIERARCHY,
    derive_conversion_identity,
    effective_runtime_identity,
)
from er_commons.document_parsing.content_parsing.conversion_preflight import PreparedConversion
from er_commons.document_parsing.content_parsing.identity import (
    ContentParsingIdentity,
    build_content_parsing_identity,
    code_identity,
    parsing_code_paths,
)
from er_commons.document_parsing.content_parsing.runtime import (
    build_converter_options,
    load_model_inventory_metadata,
)
from er_commons.document_parsing.content_parsing.sources import (
    load_sealed_manifest,
    resolve_complete_source,
)
from er_commons.document_parsing.table_reconstruction.pipeline import installed_table_environment


@dataclass(frozen=True)
class PreparedContentParsing(PreparedConversion):
    """Verified inputs and constructed runtime required before staging begins."""

    config_sha256: str
    identity: ContentParsingIdentity


def prepare_content_parsing(
    data_root: Path,
    *,
    config: ContentParsingConfig,
    config_sha256: str,
) -> PreparedContentParsing:
    """Verify source/models/runtime and derive the code-bound producer identity."""
    manifest = load_sealed_manifest(data_root, config)
    source = resolve_complete_source(data_root, config.source, manifest)
    source_manifest_path = (data_root / config.source_manifest_relative_path).resolve()
    source_completion_path = source_manifest_path.parent / "completion_record.json"
    model_inventory_path = (data_root / config.model_inventory_relative_path).resolve()
    model_inventory, models_root = load_model_inventory_metadata(data_root, model_inventory_path)
    repo_root = Path(__file__).resolve().parents[4]
    conversion_identity = derive_conversion_identity(
        repo_root=repo_root,
        config=config,
        source=source,
        source_manifest_path=source_manifest_path,
        source_completion_path=source_completion_path,
        model_inventory_path=model_inventory_path,
        model_inventory=model_inventory,
    )
    options, format_option = build_converter_options(
        models_root,
        thread_count=config.thread_count,
        heading_hierarchy_options=COMMON_HEADING_HIERARCHY,
    )
    runtime = effective_runtime_identity(config, options, format_option)
    project_code = code_identity(parsing_code_paths(repo_root), repo_root=repo_root)
    identity = build_content_parsing_identity(
        config=config,
        source=source,
        source_manifest_path=source_manifest_path,
        source_completion_path=source_completion_path,
        table_environment=installed_table_environment(),
        project_code=project_code,
        conversion_id=conversion_identity.run_id,
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
        runtime=runtime,
        conversion_identity=conversion_identity,
        identity=identity,
    )
