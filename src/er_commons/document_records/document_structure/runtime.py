"""Resolve document-structure configuration into verified runtime paths."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from er_commons.artifact_io import assert_contained
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
PLACEHOLDER_ID = "exv1-" + "0" * 64


@dataclass(frozen=True)
class RuntimeContext:
    """Verified values and file locations shared by the materialization lifecycle."""

    data_root: Path
    config_path: Path
    config_identity_path: Path
    config: DocumentStructureConfig
    inputs: DocumentStructureInputs
    construction_inputs: DocumentStructureConstructionInputs
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
    construction_inputs = DocumentStructureConstructionInputs(
        baseline_candidate_root=inputs.baseline_candidate_root,
        baseline_producer_root=_producer_document_root(
            data_root,
            config.baseline_producer_relative_root,
            config.baseline_producer_run_id,
            config.source.source_id,
        ),
        hierarchy_producer_root=_producer_document_root(
            data_root,
            config.hierarchy_producer_relative_root,
            config.hierarchy_producer_run_id,
            config.source.source_id,
        ),
        hierarchy_candidate_root=inputs.hierarchy_candidate_root,
        baseline_candidate_id=config.baseline_candidate_id,
        candidate_id=PLACEHOLDER_ID,
        baseline_producer_run_id=config.baseline_producer_run_id,
        hierarchy_producer_run_id=config.hierarchy_producer_run_id,
        source_id=config.source.source_id,
        page_count=config.source.physical_page_count,
        expectations=(
            config.expectations if config.control_profile == "task03e2d_bounded" else None
        ),
    )
    return RuntimeContext(
        data_root=data_root,
        config_path=config_path.resolve(),
        config_identity_path=(config_identity_path or config_path).resolve(),
        config=config,
        inputs=inputs,
        construction_inputs=construction_inputs,
        task_root=assert_contained(data_root, config.artifact_relative_root.as_posix()),
        semantic_schema_path=PROJECT_ROOT / config.semantic_schema_relative_path,
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
    runtime_packages = (
        PROJECT_ROOT / "src" / "er_commons" / "document_records",
        PROJECT_ROOT / "src" / "er_commons" / "document_parsing",
    )
    runtime_paths = {
        path.resolve() for package in runtime_packages for path in package.rglob("*.py")
    }
    runtime_paths.update(
        path.resolve()
        for path in (PROJECT_ROOT / "src" / "er_commons" / "source_release").rglob("*.py")
    )
    runtime_paths.update(
        {
            (PROJECT_ROOT / "src" / "er_commons" / "artifact_io.py").resolve(),
            (PROJECT_ROOT / "src" / "er_commons" / "settings.py").resolve(),
            (PROJECT_ROOT / "src" / "er_commons" / "cli.py").resolve(),
        }
    )
    contract_paths = (
        PROJECT_ROOT / "pyproject.toml",
        PROJECT_ROOT / "uv.lock",
        PROJECT_ROOT / "docs" / "specs" / "semantic_structure_v2.md",
        PROJECT_ROOT
        / "benchmarks"
        / "er_bench"
        / "schemas"
        / "canonical_extraction"
        / "v2"
        / "semantic_structure.schema.json",
        config_path.resolve(),
    )
    return tuple(sorted(runtime_paths)) + contract_paths


def _producer_document_root(
    data_root: Path, relative_root: Path, run_id: str, source_id: str
) -> Path:
    return (
        assert_contained(data_root, relative_root.as_posix())
        / run_id
        / "documents"
        / source_id
        / "producer"
    )
