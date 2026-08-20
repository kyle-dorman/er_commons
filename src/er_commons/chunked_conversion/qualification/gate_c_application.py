"""Application entrypoints for Gate C coordinator and private workers."""

from __future__ import annotations

from pathlib import Path

from er_commons.chunked_conversion.qualification.aggregation import AggregatePublisher
from er_commons.chunked_conversion.qualification.contracts import (
    AggregateWorkerSpec,
    GateCRequest,
    RangeWorkerSpec,
)
from er_commons.chunked_conversion.qualification.gate_c_worker import RangeWorker
from er_commons.chunked_conversion.qualification.gate_c_workflow import GateCWorkflow


def run_gate_c(request: GateCRequest, *, project_root: Path) -> Path:
    """Run the public Gate C workflow and return its completion or checkpoint."""
    return GateCWorkflow(project_root=project_root).run(request)


def run_range_worker(spec_path: Path) -> None:
    """Validate and execute one private range-worker file protocol."""
    spec = RangeWorkerSpec.model_validate_json(spec_path.read_bytes())
    RangeWorker().run(spec)


def run_aggregate_worker(spec_path: Path) -> None:
    """Validate and execute one private aggregate-worker file protocol."""
    spec = AggregateWorkerSpec.model_validate_json(spec_path.read_bytes())
    AggregatePublisher().run(spec)


__all__ = ["run_aggregate_worker", "run_gate_c", "run_range_worker"]
