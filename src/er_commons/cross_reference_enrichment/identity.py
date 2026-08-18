"""Expanded, non-circular identity for the human-owned v3 candidate."""

from __future__ import annotations

from pathlib import Path

from er_commons.canonical_extraction.candidate_identity import owned_code_digest
from er_commons.canonical_extraction.identity import extraction_identity_sha256
from er_commons.cross_reference_enrichment.config import RuntimeContext
from er_commons.cross_reference_enrichment.storage import sha256_file
from er_commons.cross_reference_enrichment.types import JsonObject


def build_candidate_identity(context: RuntimeContext) -> JsonObject:
    """Bind accepted inputs, contract, configuration, and all production owners."""
    owned_paths = _owned_paths(context)
    extension: JsonObject = {
        "schema_version": "er_commons.cross_reference_identity_extension.v3",
        "upstream_candidate_id": context.config.upstream_candidate_id,
        "upstream_completion_sha256": context.config.upstream_completion_sha256,
        "upstream_inventory_sha256": context.config.upstream_inventory_sha256,
        "specification": _artifact_ref(
            context.project_root, context.config.specification_relative_path
        ),
        "schema": _artifact_ref(context.project_root, context.config.schema_relative_path),
        "config": {
            "path": context.config_identity_path.relative_to(context.project_root).as_posix(),
            "sha256": sha256_file(context.config_identity_path),
        },
        "corpus_manifest": {
            "path": context.config.source_manifest_relative_path.as_posix(),
            "sha256": context.config.source_manifest_sha256,
        },
        "source_family_catalog": {
            "path": context.source_family_catalog_path.relative_to(context.data_root).as_posix(),
            "sha256": context.source_family_catalog_sha256,
        },
        "owned_code_inventory": [
            {
                "path": path.relative_to(context.project_root).as_posix(),
                "sha256": sha256_file(path),
            }
            for path in owned_paths
        ],
        "owned_code_bundle_sha256": owned_code_digest(context.project_root, owned_paths),
        "pattern_version": "cross_reference_patterns_v3",
        "resolver_policy_version": "cross_document_resolution_v2",
        "table_page_window": 10,
        "allowed_difference_categories": [
            "identity_and_schema",
            "cross_reference_records",
            "verified_table_alias_extension",
            "cross_reference_support",
            "terminal_artifacts",
        ],
    }
    identity: JsonObject = {
        "schema_version": "er_commons.extraction_identity.v3",
        "extraction_version_name": context.config.candidate_version_name,
        "upstream_candidate_id": context.config.upstream_candidate_id,
        "cross_reference_contract": extension,
    }
    digest = extraction_identity_sha256(identity)
    identity["extraction_id"] = f"exv1-{digest}"
    identity["identity_sha256"] = digest
    return identity


def _owned_paths(context: RuntimeContext) -> tuple[Path, ...]:
    package = context.project_root / "src" / "er_commons" / "cross_reference_enrichment"
    paths = [*package.glob("*.py")]
    paths.extend(
        [
            context.project_root / "src" / "er_commons" / "source_family_catalog.py",
            context.project_root / "src" / "er_commons" / "cli.py",
            context.project_root / "pyproject.toml",
            context.project_root / "uv.lock",
            context.config_identity_path,
        ]
    )
    return tuple(sorted(path.resolve() for path in paths))


def _artifact_ref(project_root: Path, relative_path: Path) -> JsonObject:
    return {
        "path": relative_path.as_posix(),
        "sha256": sha256_file(project_root / relative_path),
    }
