"""Execute six document transformations with explicit lineage binding."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from er_commons.document_parsing import run_document_parsing
from er_commons.document_publication.fresh_lineage import FreshLineageBinder
from er_commons.document_publication.process_diagnostics import run_process_stage
from er_commons.document_publication.process_inputs import ProcessConfigs
from er_commons.document_publication.process_validation import ProcessCompletions
from er_commons.document_records import (
    link_document_references,
    map_document_records,
    map_document_structure,
)
from er_commons.hierarchy_inference import infer_document_hierarchy


@dataclass(frozen=True)
class ProcessSequenceResult:
    """Completed products, effective configs, and process timings."""

    completions: ProcessCompletions
    configs: ProcessConfigs
    timings: dict[str, float]


class DocumentProcessSequence:
    """Run processes and bind downstream configs at completion boundaries."""

    def __init__(
        self,
        *,
        data_root: Path,
        project_root: Path,
        source_id: str,
        configs: ProcessConfigs,
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

    def run(self) -> ProcessSequenceResult:
        """Execute the full sequence and return its post-run validation inputs."""
        if self.binder:
            baseline_config, hierarchy_config = self.binder.initial_configs()
        else:
            baseline_config = self.configs.content_parsing
            hierarchy_config = self.configs.heading_evidence_parsing
        baseline = self._stage(
            "content_parsing",
            1,
            lambda: run_document_parsing(self.data_root, baseline_config),
        )
        hierarchy = self._stage(
            "heading_evidence_parsing",
            2,
            lambda: run_document_parsing(self.data_root, hierarchy_config),
        )
        canonical_config = (
            self.binder.canonical_config(baseline) if self.binder else self.configs.record_mapping
        )
        record_mapping = self._stage(
            "record_mapping",
            3,
            lambda: map_document_records(
                self.data_root,
                canonical_config,
                config_identity_path=self.configs.record_mapping if self.binder else None,
            ),
        )
        correction_config = (
            self.binder.correction_config(hierarchy)
            if self.binder
            else self.configs.hierarchy_inference
        )
        correction = self._stage(
            "hierarchy_inference",
            4,
            lambda: infer_document_hierarchy(
                self.data_root,
                correction_config,
                config_identity_path=self.configs.hierarchy_inference if self.binder else None,
            ),
        )
        semantic_config = self._semantic_config(baseline, hierarchy, record_mapping, correction)
        document_structure = self._stage(
            "document_structure",
            5,
            lambda: map_document_structure(
                self.data_root,
                semantic_config,
                config_identity_path=self.configs.document_structure if self.binder else None,
            ),
        )
        cross_config = (
            self.binder.cross_reference_config(document_structure)
            if self.binder
            else self.configs.document_reference_linking
        )
        document_reference_linking = self._stage(
            "document_reference_linking",
            6,
            lambda: link_document_references(
                self.data_root,
                cross_config,
                config_identity_path=self.configs.document_reference_linking
                if self.binder
                else None,
            ),
        )
        completions = ProcessCompletions(
            baseline,
            hierarchy,
            record_mapping,
            correction,
            document_structure,
            document_reference_linking,
        )
        configs = self.binder.effective_configs() if self.binder else self.configs
        return ProcessSequenceResult(completions, configs, self.timings)

    def _semantic_config(self, *completions: Path) -> Path:
        if not self.binder:
            return self.configs.document_structure
        return self.binder.semantic_config(
            baseline_completion=completions[0],
            hierarchy_completion=completions[1],
            canonical_completion=completions[2],
            correction_completion=completions[3],
        )

    def _stage(self, name: str, ordinal: int, operation: Callable[[], Path]) -> Path:
        return run_process_stage(
            name,
            self.timings,
            operation,
            diagnostics_root=self.diagnostics_root,
            ordinal=ordinal,
            data_root=self.data_root,
        )
