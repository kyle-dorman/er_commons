"""Repository code inventory bound into hierarchy-correction identity."""

from __future__ import annotations

from pathlib import Path

OWNED_CODE_RELATIVE_PATHS = (
    "pyproject.toml",
    "src/er_commons/cli.py",
    "src/er_commons/hierarchy_correction/__init__.py",
    "src/er_commons/hierarchy_correction/application.py",
    "src/er_commons/hierarchy_correction/bundle.py",
    "src/er_commons/hierarchy_correction/candidate_identity.py",
    "src/er_commons/hierarchy_correction/candidate_publication.py",
    "src/er_commons/hierarchy_correction/candidate_records.py",
    "src/er_commons/hierarchy_correction/checks.py",
    "src/er_commons/hierarchy_correction/code_inventory.py",
    "src/er_commons/hierarchy_correction/configuration.py",
    "src/er_commons/hierarchy_correction/constants.py",
    "src/er_commons/hierarchy_correction/correction_policy.py",
    "src/er_commons/hierarchy_correction/decision_builder.py",
    "src/er_commons/hierarchy_correction/decisions.py",
    "src/er_commons/hierarchy_correction/digests.py",
    "src/er_commons/hierarchy_correction/errors.py",
    "src/er_commons/hierarchy_correction/evaluation.py",
    "src/er_commons/hierarchy_correction/failures.py",
    "src/er_commons/hierarchy_correction/features.py",
    "src/er_commons/hierarchy_correction/hierarchy.py",
    "src/er_commons/hierarchy_correction/hierarchy_builder.py",
    "src/er_commons/hierarchy_correction/hierarchy_projection.py",
    "src/er_commons/hierarchy_correction/identity.py",
    "src/er_commons/hierarchy_correction/inputs.py",
    "src/er_commons/hierarchy_correction/level_evidence.py",
    "src/er_commons/hierarchy_correction/numbering_scopes.py",
    "src/er_commons/hierarchy_correction/pdf_observations.py",
    "src/er_commons/hierarchy_correction/preflight.py",
    "src/er_commons/hierarchy_correction/preservation.py",
    "src/er_commons/hierarchy_correction/publication.py",
    "src/er_commons/hierarchy_correction/quality_acceptance.py",
    "src/er_commons/hierarchy_correction/quality_config.py",
    "src/er_commons/hierarchy_correction/quality_evidence.py",
    "src/er_commons/hierarchy_correction/quality_evaluation.py",
    "src/er_commons/hierarchy_correction/quality_gate.py",
    "src/er_commons/hierarchy_correction/quality_reports.py",
    "src/er_commons/hierarchy_correction/quality_workflow.py",
    "src/er_commons/hierarchy_correction/regime_builder.py",
    "src/er_commons/hierarchy_correction/regimes.py",
    "src/er_commons/hierarchy_correction/repeat_builds.py",
    "src/er_commons/hierarchy_correction/review.py",
    "src/er_commons/hierarchy_correction/review_evaluation.py",
    "src/er_commons/hierarchy_correction/review_preparation.py",
    "src/er_commons/hierarchy_correction/review_sealing.py",
    "src/er_commons/hierarchy_correction/rewrite_equivalence.py",
    "src/er_commons/hierarchy_correction/rule_applications.py",
    "src/er_commons/hierarchy_correction/rule_context.py",
    "src/er_commons/hierarchy_correction/rules.py",
    "src/er_commons/hierarchy_correction/scope_lifecycle.py",
    "src/er_commons/hierarchy_correction/semantic_types.py",
    "src/er_commons/hierarchy_correction/single_build.py",
    "src/er_commons/hierarchy_correction/source_features.py",
    "src/er_commons/hierarchy_correction/text_evidence.py",
    "src/er_commons/hierarchy_correction/toc.py",
    "src/er_commons/hierarchy_correction/toc_analysis.py",
    "src/er_commons/hierarchy_correction/toc_builder.py",
    "src/er_commons/hierarchy_correction/toc_reconciliation.py",
    "src/er_commons/hierarchy_correction/toc_regions.py",
    "src/er_commons/hierarchy_correction/toc_rows.py",
    "src/er_commons/hierarchy_correction/toc_text.py",
    "src/er_commons/hierarchy_correction/validation.py",
)


def owned_code_paths(project_root: Path) -> tuple[Path, ...]:
    """Resolve the complete, explicit code bundle used by candidate identity."""
    paths = tuple(project_root / relative for relative in OWNED_CODE_RELATIVE_PATHS)
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise ValueError(f"hierarchy-correction owned code path is missing: {missing[0]}")
    return tuple(sorted(paths))
