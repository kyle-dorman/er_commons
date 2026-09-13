"""Execute six document transformations with explicit lineage binding."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

from er_commons.authority_reference import AuthorityReference
from er_commons.document_parsing.content_parsing.configured_application import (
    run_configured_document_parsing,
)
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

if TYPE_CHECKING:
    from er_commons.task06g.staged_process_configs import Task06GProcessConfigResolver


@dataclass(frozen=True)
class ProcessSequenceResult:
    """Completed products, effective configs, and process timings."""

    completions: ProcessCompletions
    configs: ProcessConfigs
    timings: dict[str, float]
    resolved_process_config_refs: dict[str, AuthorityReference] | None = None


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
        resume_stage: str = "content_parsing",
        reused_completions: dict[str, Path] | None = None,
        run_spec_path: Path | None = None,
        task06g_v4: bool = False,
    ) -> None:
        self.data_root = data_root
        self.configs = configs
        self.diagnostics_root = diagnostics_root
        self.timings: dict[str, float] = {}
        self.resume_stage = resume_stage
        self.reused_completions = reused_completions or {}
        stage_order = (
            "content_parsing",
            "heading_evidence_parsing",
            "record_mapping",
            "hierarchy_inference",
            "document_structure",
            "document_reference_linking",
        )
        expected = set(stage_order[: stage_order.index(resume_stage)])
        if set(self.reused_completions) != expected:
            raise ValueError(
                "resume-stage completions differ from the exact skipped prefix: "
                f"stage={resume_stage}, expected={sorted(expected)}, "
                f"observed={sorted(self.reused_completions)}"
            )
        if fresh and diagnostics_root is None:
            raise ValueError("fresh build requires a retained attempt root")
        self.task06g_resolver = None
        if task06g_v4:
            if run_spec_path is None:
                raise ValueError("Task 06G v4 execution requires its resolved run-spec path")
            from er_commons.task06g.staged_process_configs import task06g_resolver

            self.task06g_resolver = task06g_resolver(
                data_root=data_root,
                project_root=project_root,
                source_id=source_id,
                templates=configs,
                run_spec_path=run_spec_path,
                reused_completions=self.reused_completions,
            )
        self.binder = (
            FreshLineageBinder(
                data_root=data_root,
                project_root=project_root,
                source_id=source_id,
                templates=configs,
                attempt_root=diagnostics_root,
            )
            if fresh and diagnostics_root is not None and self.task06g_resolver is None
            else None
        )

    def run(self) -> ProcessSequenceResult:
        """Execute the full sequence and return its post-run validation inputs."""
        baseline_config = self._config("content_parsing")
        hierarchy_config = self._config("heading_evidence_parsing")
        baseline = self._run_or_reuse(
            "content_parsing",
            1,
            lambda: run_configured_document_parsing(
                self.data_root,
                baseline_config,
                policy_path=self.configs.content_parsing.with_name("chunked_conversion.json"),
            ),
        )
        self._record_checkpoint("content_parsing", baseline)
        hierarchy = self._run_or_reuse(
            "heading_evidence_parsing",
            2,
            lambda: run_configured_document_parsing(
                self.data_root,
                hierarchy_config,
                policy_path=self.configs.heading_evidence_parsing.with_name(
                    "chunked_conversion.json"
                ),
            ),
        )
        self._record_checkpoint("heading_evidence_parsing", hierarchy)
        canonical_config = self._mapping_config(baseline)
        record_mapping = self._run_or_reuse(
            "record_mapping",
            3,
            lambda: map_document_records(
                self.data_root,
                canonical_config,
                config_identity_path=self._identity_config("record_mapping"),
            ),
        )
        self._record_checkpoint("record_mapping", record_mapping)
        correction_config = self._correction_config(hierarchy)
        correction = self._run_or_reuse(
            "hierarchy_inference",
            4,
            lambda: infer_document_hierarchy(
                self.data_root,
                correction_config,
                config_identity_path=self._identity_config("hierarchy_inference"),
            ),
        )
        self._record_checkpoint("hierarchy_inference", correction)
        semantic_config = self._semantic_config(baseline, hierarchy, record_mapping, correction)
        document_structure = self._stage(
            "document_structure",
            5,
            lambda: map_document_structure(
                self.data_root,
                semantic_config,
                config_identity_path=self._identity_config("document_structure"),
            ),
        )
        self._record_checkpoint("document_structure", document_structure)
        resolver = self._task06g()
        cross_config = (
            resolver.config_for("document_reference_linking")
            if resolver
            else (
                self.binder.cross_reference_config(document_structure)
                if self.binder
                else self.configs.document_reference_linking
            )
        )
        document_reference_linking = self._stage(
            "document_reference_linking",
            6,
            lambda: link_document_references(
                self.data_root,
                cross_config,
                config_identity_path=self._identity_config("document_reference_linking"),
            ),
        )
        self._record_checkpoint("document_reference_linking", document_reference_linking)
        completions = ProcessCompletions(
            baseline,
            hierarchy,
            record_mapping,
            correction,
            document_structure,
            document_reference_linking,
        )
        resolver = self._task06g()
        configs = (
            resolver.effective_configs()
            if resolver
            else (self.binder.effective_configs() if self.binder else self.configs)
        )
        config_refs = None
        if resolver:
            config_refs = {
                role: AuthorityReference.model_validate(item)
                for role, item in resolver.config_references().items()
            }
        return ProcessSequenceResult(completions, configs, self.timings, config_refs)

    def _config(self, role: str) -> Path:
        """Materialize a producer template whether its owner runs or is reused."""
        resolver = self._task06g()
        if resolver:
            return resolver.config_for(role)
        if not self.binder:
            return self.configs.as_dict()[role]
        reused = self._reused_completions().get(role)
        if reused is not None:
            return self.binder.reused_config(role, reused)
        initial_config = getattr(self.binder, "initial_config", None)
        if initial_config is not None:
            return cast(Path, initial_config(role))
        baseline, hierarchy = self.binder.initial_configs()
        return {
            "content_parsing": baseline,
            "heading_evidence_parsing": hierarchy,
        }[role]

    def _run_or_reuse(self, name: str, ordinal: int, operation: Callable[[], Path]) -> Path:
        """Return one verified predecessor completion or invoke its owning stage."""
        reused = self._reused_completions().get(name)
        if reused is not None:
            # PipelineResult requires a closed six-owner timing map. A zero records
            # that this owner was deliberately not invoked during the current run.
            self.timings[name] = 0.0
            return reused
        return self._stage(name, ordinal, operation)

    def _reused_completions(self) -> dict[str, Path]:
        """Default legacy in-memory sequences to a full run without relaxing config validation."""
        return getattr(self, "reused_completions", {})

    def _mapping_config(self, baseline: Path) -> Path:
        resolver = self._task06g()
        if resolver:
            return resolver.config_for("record_mapping")
        if not self.binder:
            return self.configs.record_mapping
        reused = self._reused_completions().get("record_mapping")
        return (
            self.binder.reused_config(
                "record_mapping",
                reused,
                updates={"producer_run_id": baseline.parents[1].name},
                upstreams={"content_parsing": baseline},
            )
            if reused is not None
            else self.binder.canonical_config(baseline)
        )

    def _correction_config(self, hierarchy: Path) -> Path:
        resolver = self._task06g()
        if resolver:
            return resolver.config_for("hierarchy_inference")
        if not self.binder:
            return self.configs.hierarchy_inference
        reused = self._reused_completions().get("hierarchy_inference")
        return (
            self.binder.reused_config(
                "hierarchy_inference",
                reused,
                updates={"producer_run_id": hierarchy.parents[1].name},
                upstreams={"heading_evidence_parsing": hierarchy},
            )
            if reused is not None
            else self.binder.correction_config(hierarchy)
        )

    def _semantic_config(self, *completions: Path) -> Path:
        resolver = self._task06g()
        if resolver:
            return resolver.config_for("document_structure")
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

    def _record_checkpoint(self, role: str, completion: Path) -> None:
        """Seal each Task 06G process result before any dependent config resolves."""
        resolver = self._task06g()
        if resolver and role not in self.reused_completions:
            resolver.record_completion(role, completion)

    def _identity_config(self, role: str) -> Path | None:
        """Keep legacy owners' code inventories repository-contained."""
        if self.binder or self._task06g():
            return self.configs.as_dict()[role]
        return None

    def _task06g(self) -> Task06GProcessConfigResolver | None:
        """Return the optional resolver while tolerating historical synthetic fixtures."""
        return getattr(self, "task06g_resolver", None)
