"""Human-owned coordination for restartable chunk conversion."""

from __future__ import annotations

import fcntl
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from er_commons.artifact_io import canonical_json_sha256, read_json_object, write_json_atomic
from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.chunked_conversion.runtime.completion import (
    verify_chunked_completion,
)
from er_commons.chunked_conversion.runtime.contracts import (
    AggregateWorkerSpec,
    ChunkedConversionRequest,
    ExpectedChunkedConversionCompletion,
    RangeWorkerSpec,
    ResourceLimits,
    ResourceObservation,
)
from er_commons.chunked_conversion.runtime.diagnostics import ChunkedConversionError
from er_commons.chunked_conversion.runtime.inputs import (
    RuntimeCodeIdentity,
    VerifiedChunkInputs,
    chunked_run_id,
    chunked_run_identity,
)
from er_commons.chunked_conversion.runtime.range_store import retain_failure
from er_commons.document_parsing.content_parsing.conversion_seal import (
    deep_audit_conversion_bundle,
)


class RangeRepository(Protocol):
    """Range-store surface used by the coordinator and its offline fakes."""

    def final_root(self, range_id: str) -> Path: ...

    def verify(self, range_id: str) -> object: ...


PublishCompletion = Callable[[Path, str, RangePlan, ResourceObservation, int, bool], Path]


@dataclass(frozen=True)
class ChunkedConversionServices:
    """Inject execution and storage seams without weakening workflow policy."""

    verify_inputs: Callable[[Path, Path, Path, RuntimeCodeIdentity], VerifiedChunkInputs]
    code_identity: Callable[[Path], RuntimeCodeIdentity]
    range_store: Callable[[Path, RangePlan], RangeRepository]
    run_range: Callable[[RangeWorkerSpec, ResourceLimits], ResourceObservation]
    run_aggregate: Callable[[AggregateWorkerSpec, ResourceLimits], ResourceObservation]
    publish_completion: PublishCompletion


class ChunkedConversionWorkflow:
    """Resume verified ranges, execute missing work, and publish completion last."""

    def __init__(
        self,
        *,
        project_root: Path,
        services: ChunkedConversionServices | None = None,
    ) -> None:
        self.project_root = project_root
        if services is None:
            from er_commons.chunked_conversion.runtime.execution import (
                live_workflow_services,
            )

            services = live_workflow_services(project_root)
        self.services = services

    def run(self, request: ChunkedConversionRequest) -> Path:
        """Run or reuse one identity-bound chunk conversion."""
        code = self.services.code_identity(self.project_root)
        verified = self.services.verify_inputs(
            request.config_path,
            request.plan_path,
            request.data_root,
            code,
        )
        plan = verified.plan
        identity = chunked_run_identity(
            plan_path=request.plan_path,
            verified=verified,
            code=code,
        )
        run_id = chunked_run_id(identity)
        run_root = request.output_root / "runs" / run_id
        child_root = request.output_root / "plans" / plan.plan_id
        with _coordinator_lock(request.output_root, plan.plan_id):
            completion_path = run_root / "records/completion_record.json"
            if completion_path.is_file():
                self._reuse_completed(
                    run_root,
                    ExpectedChunkedConversionCompletion(run_id=run_id, plan_id=plan.plan_id),
                )
                return completion_path
            self._prepare_run(run_root, child_root, run_id, plan, identity)
            self._record_resource_policy(run_root, request)
            store = self.services.range_store(child_root, plan)
            executed, reused = self._run_ranges(request, run_root, child_root, run_id, plan, store)
            if request.stop_after_ranges is not None and len(executed) >= request.stop_after_ranges:
                return self._write_interruption(run_root, run_id, plan, executed)
            self._validate_resume_checkpoint(run_root, reused)
            self._write_range_report(run_root, run_id, plan, executed, reused)
            aggregate_observation = self._run_aggregate(request, run_root, run_id, plan)
            self._record_aggregate_creation_observation(run_root)
            checkpoint_exists = (run_root / "records/interruption_checkpoint.json").is_file()
            return self.services.publish_completion(
                run_root,
                run_id,
                plan,
                aggregate_observation,
                request.aggregate_limits.max_rss_bytes,
                checkpoint_exists,
            )

    def _prepare_run(
        self,
        run_root: Path,
        child_root: Path,
        run_id: str,
        plan: RangePlan,
        identity: dict[str, Any],
    ) -> None:
        (run_root / "records").mkdir(parents=True, exist_ok=True)
        (child_root / "records/plan_variants").mkdir(parents=True, exist_ok=True)
        (child_root / "ranges").mkdir(exist_ok=True)
        variant = canonical_json_sha256(plan.model_dump(mode="json"))
        write_json_atomic(
            child_root / "records/plan_variants" / f"{variant}.json",
            plan.model_dump(mode="json"),
        )
        range_link = run_root / "ranges"
        if range_link.is_symlink():
            if range_link.resolve() != (child_root / "ranges").resolve():
                raise ValueError(f"run range link differs: {range_link}")
        elif range_link.exists():
            raise ValueError(f"run range path is not the shared child store: {range_link}")
        else:
            range_link.symlink_to(child_root / "ranges", target_is_directory=True)
        write_json_atomic(run_root / "records/range_plan.json", plan.model_dump(mode="json"))
        write_json_atomic(
            run_root / "records/run_identity.json",
            {"run_id": run_id, "identity": identity},
        )

    def _record_resource_policy(
        self,
        run_root: Path,
        request: ChunkedConversionRequest,
    ) -> None:
        policy = {
            "range": request.range_limits.model_dump(mode="json"),
            "aggregate": request.aggregate_limits.model_dump(mode="json"),
        }
        policy_id = canonical_json_sha256(policy)
        write_json_atomic(
            run_root / "records/resource_policies" / f"{policy_id}.json",
            {"policy_id": policy_id, **policy},
        )

    def _reuse_completed(
        self,
        run_root: Path,
        expected: ExpectedChunkedConversionCompletion,
    ) -> None:
        """Verify coordinator evidence and deep-audit its external aggregate target."""
        completion = verify_chunked_completion(run_root, expected)
        reference_path = run_root / "records/aggregate_reference.json"
        reference = read_json_object(reference_path)
        aggregate_id = reference.get("conversion_id")
        aggregate_path = Path(str(reference.get("path")))
        if aggregate_id != completion.aggregate_conversion_id or not aggregate_path.is_absolute():
            raise ChunkedConversionError(
                "aggregate_reference",
                stage="chunked_reuse",
                path=reference_path.as_posix(),
                expected={
                    "conversion_id": completion.aggregate_conversion_id,
                    "absolute_path": True,
                },
                actual={
                    "conversion_id": aggregate_id,
                    "path": aggregate_path.as_posix(),
                },
            )
        deep_audit_conversion_bundle(aggregate_path, completion.aggregate_conversion_id)

    def _run_ranges(
        self,
        request: ChunkedConversionRequest,
        run_root: Path,
        child_root: Path,
        run_id: str,
        plan: RangePlan,
        store: RangeRepository,
    ) -> tuple[list[str], list[str]]:
        executed: list[str] = []
        reused: list[str] = []
        for planned in plan.ranges:
            if store.final_root(planned.range_id).exists():
                store.verify(planned.range_id)
                reused.append(planned.range_id)
                continue
            spec = RangeWorkerSpec(
                run_id=run_id,
                run_root=child_root,
                data_root=request.data_root,
                config_path=request.config_path,
                plan_path=run_root / "records/range_plan.json",
                range_id=planned.range_id,
            )
            spec_path = child_root / "records" / f"worker_{planned.range_id}.json"
            write_json_atomic(spec_path, spec.model_dump(mode="json"))
            try:
                observation = self.services.run_range(spec, request.range_limits)
            except BaseException as error:
                retain_failure(
                    run_root / "attempt_failures" / planned.range_id,
                    error,
                    stage="range_worker",
                )
                raise
            store.verify(planned.range_id)
            write_json_atomic(
                run_root / "records" / f"resource_{planned.range_id}.json",
                {"range_id": planned.range_id, **observation.model_dump(mode="json")},
            )
            executed.append(planned.range_id)
            if request.stop_after_ranges is not None and len(executed) >= request.stop_after_ranges:
                break
        return executed, reused

    def _write_interruption(
        self, run_root: Path, run_id: str, plan: RangePlan, executed: list[str]
    ) -> Path:
        path = run_root / "records/interruption_checkpoint.json"
        write_json_atomic(
            path,
            {
                "schema_version": "er_commons.chunked_conversion_interruption.v1",
                "status": "intentional_stop_after_verified_child",
                "run_id": run_id,
                "verified_range_ids": [
                    item.range_id
                    for item in plan.ranges
                    if (
                        run_root / "ranges" / item.range_id / "records/completion_record.json"
                    ).is_file()
                ],
                "docling_calls_in_this_invocation": len(executed),
            },
        )
        return path

    def _validate_resume_checkpoint(self, run_root: Path, reused: list[str]) -> None:
        checkpoint = run_root / "records/interruption_checkpoint.json"
        if not checkpoint.is_file():
            return
        interrupted = read_json_object(checkpoint).get("verified_range_ids")
        if not isinstance(interrupted, list) or not set(interrupted).issubset(reused):
            raise ValueError("resume did not reuse every child retained at interruption")

    def _write_range_report(
        self,
        run_root: Path,
        run_id: str,
        plan: RangePlan,
        executed: list[str],
        reused: list[str],
    ) -> None:
        observations = []
        for planned in plan.ranges:
            resource_path = run_root / "records" / f"resource_{planned.range_id}.json"
            if resource_path.is_file():
                observations.append(read_json_object(resource_path))
            else:
                observations.append(
                    read_json_object(
                        run_root / "ranges" / planned.range_id / "records/range_observation.json"
                    )
                )
        write_json_atomic(
            run_root / "records/range_execution_report.json",
            {
                "schema_version": "er_commons.chunked_conversion_range_execution.v1",
                "run_id": run_id,
                "execution_order": [item.range_id for item in plan.ranges],
                "executed_range_ids": executed,
                "reused_range_ids": reused,
                "verified_child_count": len(plan.ranges),
                "docling_calls_for_reused_children": 0,
                "observations": observations,
            },
        )

    def _run_aggregate(
        self, request: ChunkedConversionRequest, run_root: Path, run_id: str, plan: RangePlan
    ) -> ResourceObservation:
        spec = AggregateWorkerSpec(
            run_id=run_id,
            run_root=run_root,
            conversion_root=request.conversion_root,
            data_root=request.data_root,
            config_path=request.config_path,
            plan_path=run_root / "records/range_plan.json",
        )
        write_json_atomic(run_root / "records/aggregate_spec.json", spec.model_dump(mode="json"))
        try:
            return self.services.run_aggregate(spec, request.aggregate_limits)
        except BaseException as error:
            retain_failure(
                run_root / "attempt_failures/aggregate",
                error,
                stage="aggregate_worker",
            )
            raise

    def _record_aggregate_creation_observation(self, run_root: Path) -> None:
        """Copy sealed creation resources separately from the reuse subprocess cost."""
        reference = read_json_object(run_root / "records/aggregate_reference.json")
        aggregate_root = Path(str(reference["path"]))
        observation = read_json_object(aggregate_root / "records/aggregate_observation.json")
        write_json_atomic(
            run_root / "records/aggregate_creation_observation.json",
            observation,
        )


@contextmanager
def _coordinator_lock(output_root: Path, plan_id: str) -> Iterator[None]:
    """Fail fast when another coordinator can schedule the same child plan."""
    lock_root = output_root / "coordinator_locks"
    lock_root.mkdir(parents=True, exist_ok=True)
    lock_path = lock_root / f"{plan_id}.lock"
    with lock_path.open("a+b") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ChunkedConversionError(
                "coordinator_locked",
                stage="coordinator",
                path=lock_path.as_posix(),
                expected="one active coordinator per child plan",
                actual="lock already held",
            ) from error
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


__all__ = ["ChunkedConversionWorkflow", "ChunkedConversionServices"]
