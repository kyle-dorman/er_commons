"""Live subprocess bindings for the Gate C workflow service seams."""

from __future__ import annotations

import sys
from pathlib import Path

from er_commons.chunked_conversion.qualification.contracts import (
    AggregateWorkerSpec,
    RangeWorkerSpec,
    ResourceLimits,
    ResourceObservation,
)
from er_commons.chunked_conversion.qualification.converted_range_store import ConvertedRangeStore
from er_commons.chunked_conversion.qualification.gate_c_inputs import (
    behavior_code_identity,
    verify_g1_inputs,
)
from er_commons.chunked_conversion.qualification.gate_c_reporting import (
    publish_gate_c_completion,
)
from er_commons.chunked_conversion.qualification.gate_c_workflow import GateCWorkflowServices
from er_commons.chunked_conversion.qualification.process_supervision import ProcessSupervisor
from er_commons.chunked_conversion.range_contract import RangePlan


def live_workflow_services(project_root: Path) -> GateCWorkflowServices:
    """Bind the coordinator to isolated child processes and maintained stores."""
    supervisor = ProcessSupervisor()
    script = project_root / "scripts/run_task03h2_gate_c.py"

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

    return GateCWorkflowServices(
        verify_inputs=verify_g1_inputs,
        code_identity=behavior_code_identity,
        range_store=lambda root, plan: ConvertedRangeStore(root, plan),
        run_range=run_range,
        run_aggregate=run_aggregate,
        publish_completion=_publish_completion,
    )


def _publish_completion(
    run_root: Path,
    run_id: str,
    source_root: Path,
    plan: RangePlan,
    observation: ResourceObservation,
    max_aggregate_rss_bytes: int,
    checkpoint_exists: bool,
) -> Path:
    return publish_gate_c_completion(
        run_root=run_root,
        run_id=run_id,
        source_root=source_root,
        plan=plan,
        aggregate_observation=observation,
        max_aggregate_rss_bytes=max_aggregate_rss_bytes,
        interruption_checkpoint_exists=checkpoint_exists,
    )


__all__ = ["live_workflow_services"]
