"""Resolve checked-in configuration into verified Task 03E.4 runtime paths."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from er_commons.semantic_materialization.config import (
    SemanticMaterializationConfig,
    load_semantic_materialization_config,
)
from er_commons.semantic_materialization.construction import SemanticConstructionInputs
from er_commons.semantic_materialization.errors import SemanticMaterializationInvariantError
from er_commons.semantic_materialization.inputs import (
    SemanticMaterializationInputs,
    load_semantic_materialization_inputs,
)
from er_commons.source_freeze import assert_contained

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PLACEHOLDER_ID = "exv1-" + "0" * 64


@dataclass(frozen=True)
class RuntimeContext:
    """Verified values and file locations shared by the materialization lifecycle."""

    data_root: Path
    config_path: Path
    config: SemanticMaterializationConfig
    inputs: SemanticMaterializationInputs
    construction_inputs: SemanticConstructionInputs
    task_root: Path
    source_pdf: Path

    @property
    def project_root(self) -> Path:
        """Expose the checked-in root used by identity and schema validation."""
        return PROJECT_ROOT


@dataclass(frozen=True)
class CandidateLocations:
    """The immutable reference and derived candidate paths for one run."""

    candidate_root: Path
    candidate_review_root: Path
    reference_root: Path
    reference_review_root: Path
    comparison_root: Path


def load_runtime_context(*, data_root: Path, config_path: Path) -> RuntimeContext:
    """Load configuration and verify sealed inputs before allocating a workspace."""
    config, _ = load_semantic_materialization_config(config_path)
    inputs = load_semantic_materialization_inputs(
        data_root=data_root, project_root=PROJECT_ROOT, config=config
    )
    construction_inputs = SemanticConstructionInputs(
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
    )
    return RuntimeContext(
        data_root=data_root,
        config_path=config_path.resolve(),
        config=config,
        inputs=inputs,
        construction_inputs=construction_inputs,
        task_root=assert_contained(data_root, config.artifact_relative_root.as_posix()),
        source_pdf=_source_pdf(data_root, config),
    )


def candidate_locations(context: RuntimeContext, candidate_id: str) -> CandidateLocations:
    """Return every location needed to compare and publish one candidate ID."""
    review_root = assert_contained(
        context.data_root, context.config.review_cache_relative_root.as_posix()
    )
    return CandidateLocations(
        candidate_root=context.task_root / candidate_id,
        candidate_review_root=review_root / candidate_id,
        reference_root=context.task_root / context.config.mvp_reference_candidate_id,
        reference_review_root=review_root / context.config.mvp_reference_candidate_id,
        comparison_root=assert_contained(
            context.data_root, context.config.rewrite_review_relative_root.as_posix()
        ),
    )


def inherited_warnings(inputs: SemanticMaterializationInputs) -> list[str]:
    """Carry baseline parser warnings without relabeling accepted limitations."""
    manifest = json.loads(
        (inputs.baseline_candidate_root / "records" / "manifest.json").read_bytes()
    )
    return [
        *manifest["canonicalization_warnings"],
        "source semantic disposition: accepted_with_known_limitations",
        "hierarchy correction ambiguities and warnings remain in checksum-pinned "
        "Task 03E.2d evidence",
    ]


def owned_runtime_paths(config_path: Path) -> tuple[Path, ...]:
    """Name every checked-in runtime module bound into candidate identity."""
    runtime_packages = (
        PROJECT_ROOT / "src" / "er_commons" / "semantic_materialization",
        PROJECT_ROOT / "src" / "er_commons" / "semantic_structure",
        PROJECT_ROOT / "src" / "er_commons" / "canonical_extraction",
        PROJECT_ROOT / "src" / "er_commons" / "document_extraction",
    )
    runtime_paths = {
        path.resolve() for package in runtime_packages for path in package.rglob("*.py")
    }
    runtime_paths.update(
        {
            (PROJECT_ROOT / "src" / "er_commons" / "source_freeze.py").resolve(),
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


def _source_pdf(data_root: Path, config: SemanticMaterializationConfig) -> Path:
    manifest = json.loads((data_root / config.source_manifest_relative_path).read_bytes())
    selected = [
        item for item in manifest["sources"] if item["source_id"] == config.source.source_id
    ]
    if len(selected) != 1:
        raise SemanticMaterializationInvariantError(
            stage="review input",
            invariant="source manifest selects one Appendix P PDF",
            expected=1,
            observed=len(selected),
            subject=config.source_manifest_relative_path.as_posix(),
        )
    source_path = assert_contained(data_root, selected[0]["local_path"])
    manifest_sha256 = selected[0]["sha256"]
    if manifest_sha256 != config.source.source_sha256:
        raise SemanticMaterializationInvariantError(
            stage="review input",
            invariant="source manifest checksum matches the frozen configuration",
            expected=config.source.source_sha256,
            observed=manifest_sha256,
            subject=config.source_manifest_relative_path.as_posix(),
        )
    if source_path.stat().st_size != selected[0]["byte_size"]:
        raise SemanticMaterializationInvariantError(
            stage="review input",
            invariant="source PDF byte size matches the source manifest",
            expected=selected[0]["byte_size"],
            observed=source_path.stat().st_size,
            subject=source_path.as_posix(),
        )
    with source_path.open("rb") as source_stream:
        actual_sha256 = hashlib.file_digest(source_stream, "sha256").hexdigest()
    if actual_sha256 != manifest_sha256:
        raise SemanticMaterializationInvariantError(
            stage="review input",
            invariant="source PDF checksum matches the source manifest and configuration",
            expected=manifest_sha256,
            observed=actual_sha256,
            subject=source_path.as_posix(),
        )
    return source_path
