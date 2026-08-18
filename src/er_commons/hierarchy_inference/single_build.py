"""Fresh-process semantic build entrypoint for hierarchy inference."""

from __future__ import annotations

import argparse
import resource
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.document_parsing.heading_evidence_parsing.pdf_observations import (
    read_native_heading_observations,
    read_pdf_observations,
)
from er_commons.document_parsing.heading_evidence_parsing.source_features import (
    build_feature_seeds,
    document_index_text_pointers,
)
from er_commons.hierarchy_inference.candidate_records import stable_json_bytes
from er_commons.hierarchy_inference.config import load_hierarchy_inference_config
from er_commons.hierarchy_inference.correction_policy import build_rule_decisions
from er_commons.hierarchy_inference.hierarchy_projection import build_corrected_hierarchy
from er_commons.hierarchy_inference.inputs import (
    HierarchyInferenceInputs,
    load_hierarchy_inference_inputs,
)
from er_commons.hierarchy_inference.numbering_scopes import build_numbering_regimes
from er_commons.hierarchy_inference.toc_analysis import build_visible_toc

JsonRecord = dict[str, Any]


@dataclass(frozen=True)
class SingleBuildResult:
    """Deterministic semantic records plus process-local resource observations."""

    semantic: JsonRecord
    wall_seconds: float
    stage_wall_time_seconds: JsonRecord
    peak_rss_bytes: int

    def as_record(self) -> JsonRecord:
        """Return the subprocess interchange shape."""
        return {
            "semantic": self.semantic,
            "wall_seconds": self.wall_seconds,
            "stage_wall_time_seconds": self.stage_wall_time_seconds,
            "peak_rss_bytes": self.peak_rss_bytes,
        }


def build_single_semantic_candidate(
    inputs: HierarchyInferenceInputs,
) -> SingleBuildResult:
    """Run every deterministic semantic stage once in the current process."""
    total_start = time.perf_counter()

    started = time.perf_counter()
    pdf_observations = read_pdf_observations(inputs.selected_source.source_path)
    outline_observations = pdf_observations.outline_observations
    features = build_feature_seeds(
        inputs.document,
        inputs.conversion_pages,
        outline_observations=outline_observations,
    )
    native_heading_observations = read_native_heading_observations(
        inputs.selected_source.source_path, features
    )
    feature_seconds = time.perf_counter() - started

    started = time.perf_counter()
    toc = build_visible_toc(
        features,
        outline_observations,
        native_heading_observations=native_heading_observations,
        document_index_text_refs=document_index_text_pointers(inputs.document),
    )
    toc_seconds = time.perf_counter() - started

    started = time.perf_counter()
    regime_result = build_numbering_regimes(list(toc.features), outline_observations)
    decisions = build_rule_decisions(
        features=regime_result.features,
        toc_entries=toc.entries,
        reconciliations=toc.reconciliations,
        regimes=regime_result.regimes,
    )
    rule_seconds = time.perf_counter() - started

    started = time.perf_counter()
    hierarchy = build_corrected_hierarchy(
        features=regime_result.features,
        decisions=decisions.decisions,
        regimes=regime_result.regimes,
    )
    hierarchy_seconds = time.perf_counter() - started

    semantic: JsonRecord = {
        "features": list(regime_result.features),
        "toc_entries": list(toc.entries),
        "reconciliations": list(toc.reconciliations),
        "regimes": list(regime_result.regimes),
        "decisions": list(decisions.decisions),
        "hierarchy": hierarchy.hierarchy,
        "ambiguities": list(decisions.ambiguities),
        "warnings": sorted(
            [*pdf_observations.diagnostics, *toc.diagnostics, *hierarchy.warnings],
            key=lambda item: (
                -1 if item["reading_order_index"] is None else item["reading_order_index"],
                "" if item["stable_item_key"] is None else item["stable_item_key"],
                item["code"],
            ),
        ),
    }
    started = time.perf_counter()
    stable_json_bytes(semantic)
    publication_seconds = time.perf_counter() - started
    total_seconds = time.perf_counter() - total_start
    return SingleBuildResult(
        semantic=semantic,
        wall_seconds=total_seconds,
        stage_wall_time_seconds={
            "features": feature_seconds,
            "toc_reconciliation": toc_seconds,
            "rules": rule_seconds,
            "hierarchy": hierarchy_seconds,
            # This measurement covers deterministic semantic serialization;
            # aggregate validation and completion sealing follow in application.
            "publication": publication_seconds,
        },
        peak_rss_bytes=_peak_rss_bytes(),
    )


def _peak_rss_bytes() -> int:
    """Normalize ru_maxrss to bytes on macOS and Linux."""
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def main() -> None:
    """Load verified inputs, run one build, and write one deterministic result."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    config, _config_sha256 = load_hierarchy_inference_config(arguments.config)
    inputs = load_hierarchy_inference_inputs(arguments.data_root, config)
    result = build_single_semantic_candidate(inputs)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(stable_json_bytes(result.as_record()))


if __name__ == "__main__":
    main()
