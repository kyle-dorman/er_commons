"""Non-circular identity for schema-v3 cross-reference candidates."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import rfc8785

from er_commons.canonical_extraction.candidate_identity import owned_code_digest
from er_commons.canonical_extraction.identity import extraction_identity_sha256
from er_commons.cross_reference_materialization.config import CrossReferenceConfig
from er_commons.cross_reference_materialization.io import sha256_file

JsonObject = dict[str, Any]


def owned_paths(project_root: Path, config_path: Path) -> tuple[Path, ...]:
    """Return every runtime and contract file bound into candidate identity."""
    package = project_root / "src" / "er_commons" / "cross_reference_materialization"
    paths = [*package.glob("*.py")]
    paths.extend(
        [
            project_root / "src" / "er_commons" / "cross_reference_contract" / "validation.py",
            project_root / "src" / "er_commons" / "cross_reference_contract" / "errors.py",
            project_root / "src" / "er_commons" / "cli.py",
            project_root / "pyproject.toml",
            project_root / "uv.lock",
            config_path,
        ]
    )
    return tuple(sorted(path.resolve() for path in paths))


def build_identity(
    *, project_root: Path, config_path: Path, config: CrossReferenceConfig
) -> JsonObject:
    """Bind the accepted v2 handoff, v3 contract, config, and owned code."""
    code_paths = owned_paths(project_root, config_path)
    inventory = [
        {
            "path": path.relative_to(project_root).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in code_paths
    ]
    extension: JsonObject = {
        "schema_version": "er_commons.cross_reference_identity_extension.v3",
        "upstream_candidate_id": config.upstream_candidate_id,
        "upstream_completion_sha256": config.upstream_completion_sha256,
        "upstream_inventory_sha256": config.upstream_inventory_sha256,
        "specification": {
            "path": config.specification_relative_path.as_posix(),
            "sha256": sha256_file(project_root / config.specification_relative_path),
        },
        "schema": {
            "path": config.schema_relative_path.as_posix(),
            "sha256": sha256_file(project_root / config.schema_relative_path),
        },
        "config": {
            "path": config_path.relative_to(project_root).as_posix(),
            "sha256": sha256_file(config_path),
        },
        "owned_code_inventory": inventory,
        "owned_code_bundle_sha256": owned_code_digest(project_root, code_paths),
        "pattern_version": "cross_reference_patterns_v1",
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
        "extraction_version_name": "appendix_p_cross_references_v3",
        "upstream_candidate_id": config.upstream_candidate_id,
        "cross_reference_contract": extension,
    }
    digest = extraction_identity_sha256(identity)
    identity["extraction_id"] = f"exv1-{digest}"
    identity["identity_sha256"] = digest
    return identity


def normalized_payload_sha256(value: Any, candidate_id: str) -> str:
    """Hash a candidate-independent payload preimage for comparison evidence."""

    def normalize(item: Any) -> Any:
        if isinstance(item, str):
            return item.replace(candidate_id, "<EXTRACTION_ID>")
        if isinstance(item, list):
            return [normalize(child) for child in item]
        if isinstance(item, dict):
            return {key: normalize(child) for key, child in item.items()}
        return item

    return hashlib.sha256(rfc8785.dumps(normalize(value))).hexdigest()
