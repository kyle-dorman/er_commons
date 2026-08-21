"""Live subprocess bindings for the production chunk-conversion workflow."""

from __future__ import annotations

import sys
from pathlib import Path

from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.chunked_conversion.runtime.contracts import (
    AggregateWorkerSpec,
    RangeWorkerSpec,
    ResourceLimits,
    ResourceObservation,
)
from er_commons.chunked_conversion.runtime.inputs import (
    behavior_code_identity,
    verify_chunk_inputs,
)
from er_commons.chunked_conversion.runtime.publication import (
    publish_chunked_completion,
)
from er_commons.chunked_conversion.runtime.range_store import ConvertedRangeStore
from er_commons.chunked_conversion.runtime.supervision import ProcessSupervisor
from er_commons.chunked_conversion.runtime.workflow import ChunkedConversionServices, PreAggregate


def live_workflow_services(
    project_root: Path,
    *,
    pre_aggregate: PreAggregate,
) -> ChunkedConversionServices:
    """Bind the coordinator to isolated child processes and maintained stores."""
    supervisor = ProcessSupervisor()
    script = project_root / "scripts/run_chunked_conversion.py"

    def run_range(spec: RangeWorkerSpec, limits: ResourceLimits) -> ResourceObservation:
        spec_path = spec.run_root / "records" / f"worker_{spec.range_id}.json"
        return supervisor.run(
            [sys.executable, str(script), "--worker-spec", str(spec_path)],
            cwd=project_root,
            log_root=spec.run_root / "logs" / spec.range_id,
            limits=limits,
            stage="range_worker",
        )

    def run_aggregate(spec: AggregateWorkerSpec, limits: ResourceLimits) -> ResourceObservation:
        spec_path = spec.run_root / "records/aggregate_spec.json"
        return supervisor.run(
            [sys.executable, str(script), "--aggregate-spec", str(spec_path)],
            cwd=project_root,
            log_root=spec.run_root / "logs/aggregate",
            limits=limits,
            stage="aggregate_worker",
        )

    return ChunkedConversionServices(
        verify_inputs=verify_chunk_inputs,
        code_identity=behavior_code_identity,
        range_store=lambda root, plan: ConvertedRangeStore(root, plan),
        run_range=run_range,
        run_aggregate=run_aggregate,
        publish_completion=_publish_completion,
        pre_aggregate=pre_aggregate,
    )


def _publish_completion(
    run_root: Path,
    run_id: str,
    plan: RangePlan,
    observation: ResourceObservation,
    max_aggregate_rss_bytes: int,
    checkpoint_exists: bool,
) -> Path:
    return publish_chunked_completion(
        run_root=run_root,
        run_id=run_id,
        plan=plan,
        aggregate_observation=observation,
        max_aggregate_rss_bytes=max_aggregate_rss_bytes,
        interruption_checkpoint_exists=checkpoint_exists,
    )


__all__ = ["live_workflow_services"]
