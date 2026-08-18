"""Repository code inventory bound into hierarchy-inference identity."""

from __future__ import annotations

from pathlib import Path

OWNED_CODE_RELATIVE_PATHS = (
    "pyproject.toml",
    "src/er_commons/cli.py",
    "src/er_commons/document_parsing/heading_evidence_parsing/document.py",
    "src/er_commons/document_parsing/heading_evidence_parsing/errors.py",
    "src/er_commons/document_parsing/heading_evidence_parsing/pdf_observations.py",
    "src/er_commons/document_parsing/heading_evidence_parsing/source_features.py",
    "src/er_commons/document_parsing/heading_evidence_parsing/text_evidence.py",
    "src/er_commons/document_parsing/heading_evidence_parsing/types.py",
    "src/er_commons/hierarchy_inference/__init__.py",
    "src/er_commons/hierarchy_inference/application.py",
    "src/er_commons/hierarchy_inference/bounded_acceptance.py",
    "src/er_commons/hierarchy_inference/bundle.py",
    "src/er_commons/hierarchy_inference/candidate_identity.py",
    "src/er_commons/hierarchy_inference/candidate_publication.py",
    "src/er_commons/hierarchy_inference/candidate_records.py",
    "src/er_commons/hierarchy_inference/checks.py",
    "src/er_commons/hierarchy_inference/code_inventory.py",
    "src/er_commons/hierarchy_inference/configuration.py",
    "src/er_commons/hierarchy_inference/constants.py",
    "src/er_commons/hierarchy_inference/correction_policy.py",
    "src/er_commons/hierarchy_inference/decisions.py",
    "src/er_commons/hierarchy_inference/digests.py",
    "src/er_commons/hierarchy_inference/errors.py",
    "src/er_commons/hierarchy_inference/failures.py",
    "src/er_commons/hierarchy_inference/hierarchy.py",
    "src/er_commons/hierarchy_inference/hierarchy_projection.py",
    "src/er_commons/hierarchy_inference/identity.py",
    "src/er_commons/hierarchy_inference/inputs.py",
    "src/er_commons/hierarchy_inference/level_evidence.py",
    "src/er_commons/hierarchy_inference/numbering_scopes.py",
    "src/er_commons/hierarchy_inference/preflight.py",
    "src/er_commons/hierarchy_inference/publication.py",
    "src/er_commons/hierarchy_inference/publication_authorization.py",
    "src/er_commons/hierarchy_inference/regimes.py",
    "src/er_commons/hierarchy_inference/rule_applications.py",
    "src/er_commons/hierarchy_inference/rule_context.py",
    "src/er_commons/hierarchy_inference/rules.py",
    "src/er_commons/hierarchy_inference/scope_lifecycle.py",
    "src/er_commons/hierarchy_inference/semantic_types.py",
    "src/er_commons/hierarchy_inference/single_build.py",
    "src/er_commons/hierarchy_inference/toc.py",
    "src/er_commons/hierarchy_inference/toc_analysis.py",
    "src/er_commons/hierarchy_inference/toc_reconciliation.py",
    "src/er_commons/hierarchy_inference/toc_regions.py",
    "src/er_commons/hierarchy_inference/toc_rows.py",
    "src/er_commons/hierarchy_inference/toc_text.py",
    "src/er_commons/hierarchy_inference/validation.py",
)


def owned_code_paths(project_root: Path) -> tuple[Path, ...]:
    """Resolve the complete, explicit code bundle used by candidate identity."""
    paths = tuple(project_root / relative for relative in OWNED_CODE_RELATIVE_PATHS)
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise ValueError(f"hierarchy-inference owned code path is missing: {missing[0]}")
    return tuple(sorted(paths))
