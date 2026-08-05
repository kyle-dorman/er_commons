"""Execute six content owners while keeping lineage binding explicit."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from er_commons.canonical_extraction import run_document_canonicalization
from er_commons.corpus_extraction.fresh_lineage import FreshLineageBinder
from er_commons.corpus_extraction.owner_diagnostics import run_owner_stage
from er_commons.corpus_extraction.owner_inputs import OwnerConfigs
from er_commons.corpus_extraction.owner_validation import OwnerCompletions
from er_commons.cross_reference_enrichment import run_cross_reference_enrichment
from er_commons.document_extraction import run_complete_document_producer
from er_commons.hierarchy_correction import run_hierarchy_correction
from er_commons.semantic_materialization import run_semantic_materialization


@dataclass(frozen=True)
class OwnerSequenceResult:
    """Completed owner artifacts, their effective configs, and stage timings."""

    completions: OwnerCompletions
    configs: OwnerConfigs
    timings: dict[str, float]


class OwnerSequence:
    """Run owner stages and bind fresh downstream configs at completion boundaries."""

    def __init__(
        self,
        *,
        data_root: Path,
        project_root: Path,
        source_id: str,
        configs: OwnerConfigs,
        diagnostics_root: Path | None,
        fresh: bool,
    ) -> None:
        self.data_root = data_root
        self.configs = configs
        self.diagnostics_root = diagnostics_root
        self.timings: dict[str, float] = {}
        if fresh and diagnostics_root is None:
            raise ValueError("fresh build requires a retained attempt root")
        self.binder = (
            FreshLineageBinder(
                data_root=data_root,
                project_root=project_root,
                source_id=source_id,
                templates=configs,
                attempt_root=diagnostics_root,
            )
            if fresh and diagnostics_root is not None
            else None
        )

    def run(self) -> OwnerSequenceResult:
        """Execute the full sequence and return its post-run validation inputs."""
        if self.binder:
            baseline_config, hierarchy_config = self.binder.initial_configs()
        else:
            baseline_config = self.configs.baseline_producer
            hierarchy_config = self.configs.hierarchy_producer
        baseline = self._stage(
            "baseline_producer",
            1,
            lambda: run_complete_document_producer(self.data_root, baseline_config),
        )
        hierarchy = self._stage(
            "hierarchy_producer",
            2,
            lambda: run_complete_document_producer(self.data_root, hierarchy_config),
        )
        canonical_config = (
            self.binder.canonical_config(baseline) if self.binder else self.configs.canonical
        )
        canonical = self._stage(
            "canonical",
            3,
            lambda: run_document_canonicalization(
                self.data_root,
                canonical_config,
                config_identity_path=self.configs.canonical if self.binder else None,
            ),
        )
        correction_config = (
            self.binder.correction_config(hierarchy)
            if self.binder
            else self.configs.hierarchy_correction
        )
        correction = self._stage(
            "hierarchy_correction",
            4,
            lambda: run_hierarchy_correction(
                self.data_root,
                correction_config,
                config_identity_path=self.configs.hierarchy_correction if self.binder else None,
            ),
        )
        semantic_config = self._semantic_config(baseline, hierarchy, canonical, correction)
        semantic = self._stage(
            "semantic",
            5,
            lambda: run_semantic_materialization(
                self.data_root,
                semantic_config,
                config_identity_path=self.configs.semantic if self.binder else None,
            ),
        )
        cross_config = (
            self.binder.cross_reference_config(semantic)
            if self.binder
            else self.configs.cross_references
        )
        cross_references = self._stage(
            "cross_references",
            6,
            lambda: run_cross_reference_enrichment(
                self.data_root,
                cross_config,
                config_identity_path=self.configs.cross_references if self.binder else None,
            ),
        )
        completions = OwnerCompletions(
            baseline, hierarchy, canonical, correction, semantic, cross_references
        )
        configs = self.binder.effective_configs() if self.binder else self.configs
        return OwnerSequenceResult(completions, configs, self.timings)

    def _semantic_config(self, *completions: Path) -> Path:
        if not self.binder:
            return self.configs.semantic
        return self.binder.semantic_config(
            baseline_completion=completions[0],
            hierarchy_completion=completions[1],
            canonical_completion=completions[2],
            correction_completion=completions[3],
        )

    def _stage(self, name: str, ordinal: int, operation: Callable[[], Path]) -> Path:
        return run_owner_stage(
            name,
            self.timings,
            operation,
            diagnostics_root=self.diagnostics_root,
            ordinal=ordinal,
            data_root=self.data_root,
        )
