"""Close future production recipes over declared code and proposed artifact bytes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from er_commons.artifact_verification import VerificationBudget
from er_commons.document_publication.identity import canonical_digest

from .shared import GenerationSpec, json_bytes, json_sha256


def production_identity(
    spec: GenerationSpec,
    sources: list[dict[str, Any]],
    proposed: dict[Path, dict[str, Any]],
    process_paths: dict[str, dict[str, str]],
    scope: dict[str, Any],
    budget: VerificationBudget,
) -> dict[str, Any]:
    """Bind current dependencies without writing or re-deriving a historical recipe."""
    document_artifacts = [Path(path) for paths in process_paths.values() for path in paths.values()]
    document_artifacts.extend(
        path.relative_to(spec.repository_root) for path in spec.chunked_policy_paths(sources)
    )
    preimage = {
        "schema_version": "er_commons.document_publication_identity_preimage.v2",
        "contract_revision": "document_generation_v1",
        "extraction_version_name": spec.name_prefix,
        "production_scope": scope,
        "document_process_contract": _contract(
            spec,
            "document_generation_v1",
            [*document_artifacts, *spec.document_contracts],
            spec.document_code,
            proposed,
            budget,
        ),
        "collection_process_contract": _contract(
            spec,
            "collection_generation_v1",
            [
                spec.catalog_output,
                spec.collection_spec_output,
                spec.target_policy,
                spec.resolution_policy,
                *spec.collection_contracts,
            ],
            spec.collection_code,
            proposed,
            budget,
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


def _contract(
    spec: GenerationSpec,
    version: str,
    artifacts: list[Path],
    code: tuple[Path, ...],
    proposed: dict[Path, dict[str, Any]],
    budget: VerificationBudget,
) -> dict[str, Any]:
    """Use explicit finite inventories and new-output digests, with no package glob."""
    return {
        "version": version,
        "artifacts": [
            _reference(spec, path, proposed, budget, "config") for path in sorted(set(artifacts))
        ],
        "owned_code": [
            _reference(spec, path, proposed, budget, "code") for path in sorted(set(code))
        ],
    }


def _reference(
    spec: GenerationSpec,
    relative: Path,
    proposed: dict[Path, dict[str, Any]],
    budget: VerificationBudget,
    role: str,
) -> dict[str, Any]:
    """Reference proposed bytes directly or bounded current dependency files."""
    path = spec.project_path(relative)
    if path in proposed:
        digest, size = json_sha256(proposed[path]), len(json_bytes(proposed[path]))
    else:
        digest = budget.hash_file(
            path, root=spec.repository_root, role=role, source_id="generation"
        )
        size = path.stat().st_size
    return {"path": relative.as_posix(), "sha256": digest, "byte_size": size}
