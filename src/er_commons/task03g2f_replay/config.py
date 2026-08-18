"""Reviewable paths and source configuration for the bounded Task 03G.2f replay."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_RETAINED_SCOPE_ID = (
    "scopev1-2096b371305552b6ec927bda3d5f6ff8285dd40bd5e9b168747f39cad21b6a95"
)
SOURCE_CONFIG_SLUGS = {
    "deir_main": "main",
    "deir_appendix_d": "appendix_d",
    "deir_appendix_p": "appendix_p",
}


@dataclass(frozen=True)
class ReplayPaths:
    """All filesystem policy for one replay, derived from two explicit roots."""

    project_root: Path
    data_root: Path
    retained_scope_id: str = DEFAULT_RETAINED_SCOPE_ID

    @property
    def pilot_root(self) -> Path:
        """Return the retained pilot artifact root."""
        return self.data_root / "pipelines/brisbane_baylands/task_03g2_representative_pilot"

    @property
    def retained_bundle(self) -> Path:
        """Return the immutable pre-repair contract bundle."""
        return self.pilot_root / "scopes" / self.retained_scope_id / "contract_bundle.json"

    @property
    def document_spec(self) -> Path:
        """Return the checked document-run specification."""
        return self.project_root / "configs/brisbane_baylands_2025_deir_task03g2_document_v1.json"

    @property
    def scope_spec(self) -> Path:
        """Return the checked scope-run specification."""
        return self.project_root / "configs/brisbane_baylands_2025_deir_task03g2_scope_v1.json"

    @property
    def source_family_catalog(self) -> Path:
        """Return the checked shared source-family catalog."""
        return (
            self.project_root
            / "configs/brisbane_baylands_2025_deir_task03g2_source_family_catalog_v1.json"
        )

    def cross_reference_template(self, source_id: str) -> Path:
        """Return one source's reviewed cross-reference configuration template."""
        slug = SOURCE_CONFIG_SLUGS[source_id]
        return (
            self.project_root
            / f"configs/brisbane_baylands_2025_deir_task03g2_{slug}_cross_references_v1.json"
        )

    def effective_cross_reference_config(self, source_id: str) -> Path:
        """Return the immutable replay-specific effective config location."""
        return (
            self.pilot_root
            / "review_cache/task_03g2f/controls"
            / f"{source_id}_cross_references.json"
        )

    def replay_report(self, scope_id: str) -> Path:
        """Return the scope-qualified candidate-neutral report location."""
        return (
            self.pilot_root
            / "review_cache/task_03g2f"
            / scope_id
            / "candidate_neutral_replay_report.json"
        )

    @property
    def forbidden_attempt_roots(self) -> dict[str, Path]:
        """Return attempt namespaces that downstream replay must not change."""
        pipelines = self.data_root / "pipelines/brisbane_baylands"
        return {
            "document_producers": pipelines / "task_03g2_document_producers/attempts",
            "canonical_records": pipelines / "task_03g2_canonical_records/attempts",
            "hierarchy_correction": pipelines / "task_03g2_hierarchy_correction/attempts",
            "document_attempts": self.pilot_root / "attempts",
        }
