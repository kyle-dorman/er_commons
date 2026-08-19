"""Resolve document-structure configuration into verified runtime paths."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from er_commons.artifact_io import assert_contained
from er_commons.document_parsing.content_parsing.references import (
    load_document_views,
    resolve_conversion_input,
)
from er_commons.document_records.document_structure.code_inventory import owned_code_paths
from er_commons.document_records.document_structure.config import (
    DocumentStructureConfig,
    load_document_structure_config,
)
from er_commons.document_records.document_structure.construction import (
    DocumentStructureConstructionInputs,
)
from er_commons.document_records.document_structure.inputs import (
    DocumentStructureInputs,
    load_document_structure_inputs,
)

PROJECT_ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class RuntimeContext:
    """Verified values and file locations shared by the materialization lifecycle."""

    data_root: Path
    config_path: Path
    config_identity_path: Path
    config: DocumentStructureConfig
    inputs: DocumentStructureInputs
    task_root: Path
    semantic_schema_path: Path

    @property
    def project_root(self) -> Path:
        """Expose the checked-in root used by identity and schema validation."""
        return PROJECT_ROOT


def load_runtime_context(
    *,
    data_root: Path,
    config_path: Path,
    config_identity_path: Path | None = None,
) -> RuntimeContext:
    """Load configuration and verify sealed inputs before allocating a workspace."""
    config, _ = load_document_structure_config(config_path)
    inputs = load_document_structure_inputs(
        data_root=data_root, project_root=PROJECT_ROOT, config=config
    )
    return RuntimeContext(
        data_root=data_root,
        config_path=config_path.resolve(),
        config_identity_path=(config_identity_path or config_path).resolve(),
        config=config,
        inputs=inputs,
        task_root=assert_contained(data_root, config.artifact_relative_root.as_posix()),
        semantic_schema_path=PROJECT_ROOT / config.semantic_schema_relative_path,
    )


def load_construction_inputs(
    context: RuntimeContext,
    *,
    candidate_id: str,
) -> DocumentStructureConstructionInputs:
    """Load large document views once, only after a fresh candidate is required."""
    config = context.config
    data_root = context.data_root
    baseline_run_root = _producer_run_root(
        data_root, config.baseline_producer_relative_root, config.baseline_producer_run_id
    )
    hierarchy_run_root = _producer_run_root(
        data_root, config.hierarchy_producer_relative_root, config.hierarchy_producer_run_id
    )
    baseline_conversion = resolve_conversion_input(
        data_root, baseline_run_root / "records/conversion_input.json"
    )
    hierarchy_conversion = resolve_conversion_input(
        data_root, hierarchy_run_root / "records/conversion_input.json"
    )
    baseline_document, hierarchy_document = load_document_views(
        baseline_conversion,
        hierarchy_conversion,
        source_id=config.source.source_id,
    )
    return DocumentStructureConstructionInputs(
        baseline_candidate_root=context.inputs.baseline_candidate_root,
        baseline_producer_root=_producer_document_root(baseline_run_root, config.source.source_id),
        baseline_document=baseline_document,
        hierarchy_producer_root=_producer_document_root(
            hierarchy_run_root, config.source.source_id
        ),
        hierarchy_document=hierarchy_document,
        hierarchy_candidate_root=context.inputs.hierarchy_candidate_root,
        baseline_candidate_id=config.baseline_candidate_id,
        candidate_id=candidate_id,
        baseline_producer_run_id=config.baseline_producer_run_id,
        hierarchy_producer_run_id=config.hierarchy_producer_run_id,
        source_id=config.source.source_id,
        page_count=config.source.physical_page_count,
        expectations=(
            config.expectations if config.control_profile == "task03e2d_bounded" else None
        ),
    )


def inherited_warnings(inputs: DocumentStructureInputs) -> list[str]:
    """Carry baseline parser warnings without relabeling accepted limitations."""
    manifest = json.loads(
        (inputs.baseline_candidate_root / "records" / "manifest.json").read_bytes()
    )
    warnings = list(manifest["canonicalization_warnings"])
    if inputs.control_provenance.get("control_kind") != "strict_quality_gate":
        warnings.extend(
            [
                "source semantic disposition: accepted_with_known_limitations",
                "hierarchy inference ambiguities and warnings remain in checksum-pinned "
                "Task 03E.2d evidence",
            ]
        )
    return warnings


def owned_runtime_paths(config_path: Path) -> tuple[Path, ...]:
    """Name every checked-in runtime module bound into candidate identity."""
    return owned_code_paths(PROJECT_ROOT, config_path)


def _producer_run_root(data_root: Path, relative_root: Path, run_id: str) -> Path:
    return assert_contained(data_root, relative_root.as_posix()) / run_id


def _producer_document_root(run_root: Path, source_id: str) -> Path:
    return run_root / "documents" / source_id / "producer"
