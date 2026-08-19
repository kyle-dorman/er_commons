"""Deterministic in-process semantic build for hierarchy inference."""

from __future__ import annotations

import logging
import resource
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar, cast

from er_commons.document_parsing.heading_evidence_parsing.pdf_observations import (
    PdfObservations,
    read_native_heading_observations,
    read_pdf_observations,
)
from er_commons.document_parsing.heading_evidence_parsing.source_features import (
    apply_outline_observations,
    build_feature_seeds,
    document_index_text_pointers,
)
from er_commons.document_parsing.heading_evidence_parsing.types import ObservedItem
from er_commons.hierarchy_inference.correction_policy import (
    DecisionBuildResult,
    build_rule_decisions,
)
from er_commons.hierarchy_inference.hierarchy_projection import (
    HierarchyBuildResult,
    build_corrected_hierarchy,
)
from er_commons.hierarchy_inference.inputs import (
    HierarchyInferenceInputs,
)
from er_commons.hierarchy_inference.numbering_scopes import (
    NumberingScopeAnalysis,
    build_numbering_regimes,
)
from er_commons.hierarchy_inference.semantic_types import SemanticCandidate
from er_commons.hierarchy_inference.toc_analysis import TocBuildResult, build_visible_toc

JsonRecord = dict[str, Any]
LOGGER = logging.getLogger(__name__)
StageResult = TypeVar("StageResult")

_STAGE_UNITS = {
    "feature_indexing": "pages",
    "outline_observations": "features",
    "outline_overlay": "features",
    "visible_toc": "features",
    "numbering_scopes": "features",
    "rule_decisions": "features",
    "hierarchy_projection": "features",
}


@dataclass(frozen=True)
class SingleBuildResult:
    """Deterministic semantic records plus process-local resource observations."""

    semantic: SemanticCandidate
    wall_seconds: float
    stage_wall_time_seconds: JsonRecord
    peak_rss_bytes: int


@dataclass
class SemanticStageRunner:
    """Own the fixed semantic stage order and its per-stage telemetry."""

    inputs: HierarchyInferenceInputs
    stage_wall_time_seconds: dict[str, float] = field(default_factory=dict)

    def run(self) -> SemanticCandidate:
        """Run the seven semantic stages once and assemble their typed result."""
        preliminary_features = self._feature_indexing()
        pdf_observations = self._outline_observations(preliminary_features)
        features, native_headings = self._outline_overlay(
            preliminary_features,
            pdf_observations.outline_observations,
        )
        toc = self._visible_toc(
            features,
            pdf_observations.outline_observations,
            native_headings,
        )
        scopes = self._numbering_scopes(toc, pdf_observations.outline_observations)
        decisions = self._rule_decisions(toc, scopes)
        hierarchy = self._hierarchy_projection(scopes, decisions)
        return _assemble_semantic_candidate(
            pdf_observations=pdf_observations,
            toc=toc,
            scopes=scopes,
            decisions=decisions,
            hierarchy=hierarchy,
        )

    def _feature_indexing(self) -> list[ObservedItem]:
        return self._run_stage(
            "feature_indexing",
            len(self.inputs.alignment_pages),
            lambda: build_feature_seeds(self.inputs.document, self.inputs.alignment_pages),
        )

    def _outline_observations(self, preliminary_features: list[ObservedItem]) -> PdfObservations:
        return self._run_stage(
            "outline_observations",
            len(preliminary_features),
            lambda: read_pdf_observations(
                self.inputs.selected_source.source_path,
                heading_features=preliminary_features,
            ),
        )

    def _outline_overlay(
        self,
        preliminary_features: list[ObservedItem],
        outline_observations: tuple[JsonRecord, ...],
    ) -> tuple[list[ObservedItem], dict[str, JsonRecord]]:
        def overlay() -> tuple[list[ObservedItem], dict[str, JsonRecord]]:
            features = apply_outline_observations(preliminary_features, outline_observations)
            native_headings = read_native_heading_observations(
                self.inputs.selected_source.source_path, features
            )
            return features, native_headings

        return self._run_stage(
            "outline_overlay",
            len(preliminary_features),
            overlay,
            processed_units=lambda result: len(result[0]),
        )

    def _visible_toc(
        self,
        features: list[ObservedItem],
        outline_observations: tuple[JsonRecord, ...],
        native_headings: dict[str, JsonRecord],
    ) -> TocBuildResult:
        return self._run_stage(
            "visible_toc",
            len(features),
            lambda: build_visible_toc(
                features,
                outline_observations,
                native_heading_observations=native_headings,
                document_index_text_refs=document_index_text_pointers(self.inputs.document),
            ),
        )

    def _numbering_scopes(
        self,
        toc: TocBuildResult,
        outline_observations: tuple[JsonRecord, ...],
    ) -> NumberingScopeAnalysis:
        return self._run_stage(
            "numbering_scopes",
            len(toc.features),
            lambda: build_numbering_regimes(list(toc.features), outline_observations),
        )

    def _rule_decisions(
        self, toc: TocBuildResult, scopes: NumberingScopeAnalysis
    ) -> DecisionBuildResult:
        return self._run_stage(
            "rule_decisions",
            len(scopes.features),
            lambda: build_rule_decisions(
                features=scopes.features,
                toc_entries=toc.entries,
                reconciliations=toc.reconciliations,
                regimes=scopes.regimes,
            ),
        )

    def _hierarchy_projection(
        self,
        scopes: NumberingScopeAnalysis,
        decisions: DecisionBuildResult,
    ) -> HierarchyBuildResult:
        return self._run_stage(
            "hierarchy_projection",
            len(scopes.features),
            lambda: build_corrected_hierarchy(
                features=scopes.features,
                decisions=decisions.decisions,
                regimes=scopes.regimes,
            ),
        )

    def _run_stage(
        self,
        stage: str,
        total_units: int,
        operation: Callable[[], StageResult],
        *,
        processed_units: Callable[[StageResult], int] | None = None,
    ) -> StageResult:
        """Run one operation between the existing start/completion telemetry calls."""
        started = start_stage(stage, total_units)
        result = operation()
        completed_units = processed_units(result) if processed_units else total_units
        self.stage_wall_time_seconds[stage] = complete_stage(stage, started, completed_units)
        return result


def build_single_semantic_candidate(
    inputs: HierarchyInferenceInputs,
) -> SingleBuildResult:
    """Run every deterministic semantic stage once in the current process."""
    total_start = time.perf_counter()
    runner = SemanticStageRunner(inputs)
    semantic = runner.run()
    return SingleBuildResult(
        semantic=semantic,
        wall_seconds=time.perf_counter() - total_start,
        stage_wall_time_seconds=runner.stage_wall_time_seconds,
        peak_rss_bytes=_peak_rss_bytes(),
    )


def _assemble_semantic_candidate(
    *,
    pdf_observations: PdfObservations,
    toc: TocBuildResult,
    scopes: NumberingScopeAnalysis,
    decisions: DecisionBuildResult,
    hierarchy: HierarchyBuildResult,
) -> SemanticCandidate:
    """Assemble the complete semantic payload from typed stage results."""
    return SemanticCandidate(
        features=cast(tuple[JsonRecord, ...], scopes.features),
        toc_entries=tuple(toc.entries),
        reconciliations=tuple(toc.reconciliations),
        regimes=cast(tuple[JsonRecord, ...], scopes.regimes),
        decisions=cast(tuple[JsonRecord, ...], decisions.decisions),
        hierarchy=cast(JsonRecord, hierarchy.hierarchy),
        ambiguities=cast(tuple[JsonRecord, ...], decisions.ambiguities),
        warnings=tuple(
            sorted(
                [
                    *pdf_observations.diagnostics,
                    *toc.diagnostics,
                    *cast(tuple[JsonRecord, ...], hierarchy.warnings),
                ],
                key=lambda item: (
                    -1 if item["reading_order_index"] is None else item["reading_order_index"],
                    "" if item["stable_item_key"] is None else item["stable_item_key"],
                    item["code"],
                ),
            )
        ),
    )


def start_stage(stage: str, total_units: int) -> float:
    """Log one named stage boundary before potentially expensive work."""
    LOGGER.info(
        "Hierarchy stage started stage=%s total_units=%d unit=%s",
        stage,
        total_units,
        _STAGE_UNITS[stage],
    )
    return time.perf_counter()


def complete_stage(stage: str, started: float, processed_units: int) -> float:
    """Log elapsed time and throughput for one completed semantic stage."""
    elapsed = time.perf_counter() - started
    throughput = processed_units / elapsed if elapsed else 0.0
    LOGGER.info(
        "Hierarchy stage completed stage=%s processed_units=%d unit=%s "
        "elapsed_seconds=%.3f throughput_units_per_second=%.3f peak_rss_bytes=%d",
        stage,
        processed_units,
        _STAGE_UNITS[stage],
        elapsed,
        throughput,
        _peak_rss_bytes(),
    )
    return elapsed


def _peak_rss_bytes() -> int:
    """Normalize ru_maxrss to bytes on macOS and Linux."""
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)
