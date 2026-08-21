"""Production entrypoints for restartable chunk conversion and private workers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from er_commons.artifact_io import read_json_object
from er_commons.chunked_conversion.runtime.aggregate import AggregatePublisher
from er_commons.chunked_conversion.runtime.contracts import (
    AggregateWorkerSpec,
    ChunkedConversionRequest,
    PreAggregateContext,
    RangeWorkerSpec,
)
from er_commons.chunked_conversion.runtime.worker import RangeWorker
from er_commons.chunked_conversion.runtime.workflow import ChunkedConversionWorkflow
from er_commons.document_parsing.content_parsing.conversion_seal import (
    SealedConversion,
    deep_audit_conversion_bundle,
)


def run_chunked_conversion(
    request: ChunkedConversionRequest,
    *,
    project_root: Path,
    pre_aggregate: Callable[[PreAggregateContext], Path],
) -> Path:
    """Run the public workflow and return its completion or interruption checkpoint."""
    from er_commons.chunked_conversion.runtime.execution import live_workflow_services

    return ChunkedConversionWorkflow(
        project_root=project_root,
        services=live_workflow_services(project_root, pre_aggregate=pre_aggregate),
    ).run(request)


def ensure_chunked_conversion_bundle(
    request: ChunkedConversionRequest,
    *,
    project_root: Path,
    pre_aggregate: Callable[[PreAggregateContext], Path],
) -> SealedConversion:
    """Run/reuse chunking and return the ordinary sealed-conversion interface."""
    completion_path = run_chunked_conversion(
        request, project_root=project_root, pre_aggregate=pre_aggregate
    )
    completion = read_json_object(completion_path)
    if completion.get("status") != "complete":
        raise RuntimeError(f"chunk conversion stopped before completion: {completion_path}")
    reference = read_json_object(completion_path.parent / "aggregate_reference.json")
    conversion_id = str(reference["conversion_id"])
    return deep_audit_conversion_bundle(Path(str(reference["path"])), conversion_id)


def run_range_worker(spec_path: Path) -> None:
    """Validate and execute one private range-worker file protocol."""
    spec = RangeWorkerSpec.model_validate_json(spec_path.read_bytes())
    RangeWorker().run(spec)


def run_aggregate_worker(spec_path: Path) -> None:
    """Validate and execute one private aggregate-worker file protocol."""
    spec = AggregateWorkerSpec.model_validate_json(spec_path.read_bytes())
    AggregatePublisher().run(spec)


__all__ = [
    "ensure_chunked_conversion_bundle",
    "run_aggregate_worker",
    "run_chunked_conversion",
    "run_range_worker",
]
