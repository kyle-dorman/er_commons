"""Offline recovery tests for the source-neutral chunk runtime."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from er_commons.artifact_io import write_json_atomic
from er_commons.chunked_conversion.range_contract import (
    OverlapOwner,
    OverlapPolicy,
    PageInterval,
    RangeDefinition,
    RangePlan,
    RangePlanInputs,
    SourceIdentity,
    build_range_plan,
)
from er_commons.chunked_conversion.runtime import inputs
from er_commons.chunked_conversion.runtime import workflow as workflow_module
from er_commons.chunked_conversion.runtime.contracts import (
    ChunkedConversionRequest,
    ExpectedChunkedConversionCompletion,
    ResourceLimits,
    ResourceObservation,
)
from er_commons.chunked_conversion.runtime.diagnostics import ChunkedConversionError
from er_commons.chunked_conversion.runtime.docling_adapter import DoclingAdapter
from er_commons.chunked_conversion.runtime.inputs import (
    RuntimeCodeIdentity,
    VerifiedChunkInputs,
)
from er_commons.chunked_conversion.runtime.workflow import (
    ChunkedConversionServices,
    ChunkedConversionWorkflow,
    _coordinator_lock,
)
from er_commons.document_parsing.content_parsing.configured_application import (
    _persist_plan_variant,
)
from er_commons.document_parsing.content_parsing.preparation import PreparedContentParsing


def _plan(*, aggregate_identity: str = "aggregate", global_policy: str = "global") -> RangePlan:
    first = PageInterval(start=1, end=2)
    second = PageInterval(start=3, end=4)
    return build_range_plan(
        RangePlanInputs(
            source=SourceIdentity(
                source_id="example",
                sha256="a" * 64,
                byte_size=123,
                physical_page_count=4,
            ),
            sealed_source_release_identity="release",
            converter_identity="converter",
            package_identity="packages",
            model_identity="models",
            adapter_identity="adapter",
            page_evidence_contract_identity="page-evidence",
            range_conversion_identity="range-conversion",
            range_planner_identity="planner",
            aggregate_merge_identity=aggregate_identity,
            target_range_size=2,
            hard_maximum=2,
            overlap_policy=OverlapPolicy(max_left_pages=1, max_right_pages=1),
            ranges=(
                RangeDefinition(
                    core=first,
                    read=PageInterval(start=1, end=3),
                    overlap_owners=(OverlapOwner(page=3, owner_core=second),),
                ),
                RangeDefinition(
                    core=second,
                    read=PageInterval(start=2, end=4),
                    overlap_owners=(OverlapOwner(page=2, owner_core=first),),
                ),
            ),
            aggregate_output_schema_identity="outputs",
            global_interpretation_policy_identity=global_policy,
        )
    )


def _observation() -> ResourceObservation:
    return ResourceObservation(
        process_tree_peak_rss_bytes=6 * 1024**3,
        wall_seconds=1.0,
        minimum_system_available_bytes=8 * 1024**3,
        swap_delta_bytes=0,
        stdout="stdout.log",
        stderr="stderr.log",
    )


def test_behavior_identity_separates_coordinator_from_child_and_aggregate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "src/er_commons/chunked_conversion").mkdir(parents=True)
    observed: list[tuple[str, ...]] = []

    def fake_code_identity(paths: list[Path], *, repo_root: Path) -> dict[str, str]:
        assert repo_root == tmp_path
        relative = tuple(path.relative_to(tmp_path).as_posix() for path in paths)
        observed.append(relative)
        return {"sha256": "|".join(relative)}

    monkeypatch.setattr(inputs, "code_identity", fake_code_identity)
    identity = inputs.behavior_code_identity(tmp_path)

    flattened = {path for group in observed for path in group}
    assert all(not path.startswith("scripts/") for path in flattened)
    assert identity.range_conversion != identity.aggregate
    assert "src/er_commons/chunked_conversion/runtime/workflow.py" not in identity.range_conversion
    assert "src/er_commons/chunked_conversion/runtime/workflow.py" not in identity.aggregate
    assert "src/er_commons/chunked_conversion/runtime/workflow.py" in identity.coordinator
    assert "src/er_commons/chunked_conversion/runtime/application.py" in identity.coordinator
    assert (
        "src/er_commons/document_parsing/content_parsing/pdfium_backend.py"
        in identity.range_conversion
    )
    assert (
        "src/er_commons/document_parsing/content_parsing/routing_geometry.py" in identity.aggregate
    )
    assert (
        "src/er_commons/document_parsing/content_parsing/ordering_projection_records.py"
        in identity.aggregate
    )
    assert (
        "src/er_commons/document_parsing/content_parsing/table_stage_reference.py"
        in identity.aggregate
    )


def test_docling_backend_unload_failure_is_not_swallowed() -> None:
    class FailingBackend:
        def unload(self) -> None:
            raise RuntimeError("cannot release mapped PDF")

    input_document = SimpleNamespace(_backend=FailingBackend())
    with pytest.raises(ChunkedConversionError, match="backend_unload") as caught:
        DoclingAdapter().release_backend(input_document)
    assert caught.value.path == "input_document._backend"
    assert caught.value.actual == "cannot release mapped PDF"


class _FakeStore:
    def __init__(self, root: Path, plan: RangePlan, states: dict[str, str]) -> None:
        self.root = root
        self.plan = plan
        self.states = states

    def final_root(self, range_id: str) -> Path:
        return self.root / "ranges" / range_id

    def verify(self, range_id: str) -> object:
        state = self.states.get(range_id)
        if state != self.plan.plan_id:
            raise ChunkedConversionError(
                "child_identity",
                stage="range_reuse",
                path=self.final_root(range_id).as_posix(),
                expected=self.plan.plan_id,
                actual=state,
            )
        return object()


def _request(
    tmp_path: Path,
    *,
    stop_after_ranges: int | None = None,
    plan: RangePlan | None = None,
) -> ChunkedConversionRequest:
    data_root = (tmp_path / "data").resolve()
    output_root = (tmp_path / "output").resolve()
    conversion_root = (tmp_path / "conversions").resolve()
    config = (tmp_path / "config.json").resolve()
    plan_path = (tmp_path / "plan.json").resolve()
    data_root.mkdir(exist_ok=True)
    config.write_text("{}\n")
    write_json_atomic(plan_path, (plan or _plan()).model_dump(mode="json"))
    limits = ResourceLimits(max_rss_bytes=10 * 1024**3, max_wall_seconds=60.0)
    return ChunkedConversionRequest(
        data_root=data_root,
        output_root=output_root,
        conversion_root=conversion_root,
        config_path=config,
        plan_path=plan_path,
        stop_after_ranges=stop_after_ranges,
        range_limits=limits,
        aggregate_limits=limits,
    )


def _services(
    states: dict[str, str], calls: list[str], *, fail_aggregate_once: list[bool] | None = None
) -> ChunkedConversionServices:
    plan = _plan()
    prepared = cast(
        PreparedContentParsing,
        SimpleNamespace(conversion_identity=SimpleNamespace(run_id="dconv1-" + "a" * 64)),
    )

    def run_range(spec: Any, _limits: ResourceLimits) -> ResourceObservation:
        calls.append(f"range:{spec.range_id}")
        loaded = RangePlan.model_validate_json(spec.plan_path.read_bytes())
        states[spec.range_id] = loaded.plan_id
        completion = spec.run_root / "ranges" / spec.range_id / "records/completion_record.json"
        completion.parent.mkdir(parents=True)
        completion.write_text("{}\n")
        write_json_atomic(
            completion.parent / "range_observation.json",
            {"range_id": spec.range_id, "peak_worker_rss_bytes": 5},
        )
        return _observation()

    def run_aggregate(spec: Any, _limits: ResourceLimits) -> ResourceObservation:
        calls.append("aggregate")
        if fail_aggregate_once and fail_aggregate_once.pop(0):
            raise ChunkedConversionError(
                "aggregate_failed", stage="aggregate", path=str(spec.run_root)
            )
        aggregate_root = spec.conversion_root / ("dconv1-" + "c" * 64)
        write_json_atomic(
            aggregate_root / "records/aggregate_observation.json",
            {"aggregate_id": "dconv1-" + "c" * 64, "peak_worker_rss_bytes": 9},
        )
        write_json_atomic(
            spec.run_root / "records/aggregate_reference.json",
            {"conversion_id": "dconv1-" + "c" * 64, "path": aggregate_root.as_posix()},
        )
        return _observation()

    def publish(
        root: Path,
        _run_id: str,
        _plan_value: RangePlan,
        _observation_value: ResourceObservation,
        _limit: int,
        _checkpoint: bool,
    ) -> Path:
        calls.append("publish")
        write_json_atomic(
            root / "records/aggregate_resource_observation.json",
            _observation_value.model_dump(mode="json"),
        )
        path = root / "records/completion_record.json"
        path.write_text("{}\n")
        return path

    def pre_aggregate(context: Any) -> Path:
        calls.append("pre_aggregate")
        path = context.child_root / "records/ordering_projection.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        write_json_atomic(path, {"pages": []})
        return path

    return ChunkedConversionServices(
        verify_inputs=lambda _config, _plan_path, _data, _code: VerifiedChunkInputs(prepared, plan),
        code_identity=lambda _root: RuntimeCodeIdentity(
            "page", "range", "plan", "aggregate", "coordinator"
        ),
        range_store=lambda root, selected: _FakeStore(root, selected, states),
        run_range=run_range,
        run_aggregate=run_aggregate,
        publish_completion=publish,
        pre_aggregate=pre_aggregate,
    )


@pytest.mark.parametrize("foreign_state", ["corrupt", "transplanted-plan"])
def test_resume_rejects_corrupt_or_transplanted_child(tmp_path: Path, foreign_state: str) -> None:
    states: dict[str, str] = {}
    calls: list[str] = []
    workflow = ChunkedConversionWorkflow(project_root=tmp_path, services=_services(states, calls))
    workflow.run(_request(tmp_path, stop_after_ranges=1))
    first_range = next(iter(states))
    states[first_range] = foreign_state

    with pytest.raises(ChunkedConversionError, match="child_identity") as caught:
        workflow.run(_request(tmp_path))
    child = tmp_path / "output/plans" / _plan().plan_id / "ranges" / first_range
    assert str(child) in str(caught.value)


def test_live_workflow_requires_pre_aggregate_callback(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="pre-aggregate projection callback"):
        ChunkedConversionWorkflow(project_root=tmp_path)


def test_aggregate_retry_reuses_all_ranges_without_range_execution(tmp_path: Path) -> None:
    states: dict[str, str] = {}
    calls: list[str] = []
    workflow = ChunkedConversionWorkflow(
        project_root=tmp_path,
        services=_services(states, calls, fail_aggregate_once=[True]),
    )
    with pytest.raises(ChunkedConversionError, match="aggregate_failed"):
        workflow.run(_request(tmp_path))
    assert len([call for call in calls if call.startswith("range:")]) == 2
    retained = (tmp_path / "output/runs").glob("*/attempt_failures/aggregate/records/failure.json")
    assert len(list(retained)) == 1

    calls.clear()
    completion = workflow.run(_request(tmp_path))
    assert calls == ["pre_aggregate", "aggregate", "publish"]
    assert completion.name == "completion_record.json"


def test_coordinator_lock_rejects_duplicate_child_scheduler(tmp_path: Path) -> None:
    with _coordinator_lock(tmp_path, "dplan1-test"):
        with pytest.raises(ChunkedConversionError) as raised:
            with _coordinator_lock(tmp_path, "dplan1-test"):
                pass
    assert raised.value.code == "coordinator_locked"


def test_aggregate_only_variant_reuses_shared_children(tmp_path: Path) -> None:
    states: dict[str, str] = {}
    first_calls: list[str] = []
    first = ChunkedConversionWorkflow(
        project_root=tmp_path,
        services=_services(states, first_calls, fail_aggregate_once=[True]),
    )
    with pytest.raises(ChunkedConversionError, match="aggregate_failed"):
        first.run(_request(tmp_path))

    second_plan = _plan(aggregate_identity="aggregate-v2", global_policy="global-v2")
    write_json_atomic(tmp_path / "plan.json", second_plan.model_dump(mode="json"))
    second_calls: list[str] = []
    prepared = cast(
        PreparedContentParsing,
        SimpleNamespace(conversion_identity=SimpleNamespace(run_id="dconv1-" + "a" * 64)),
    )
    second_services = _services(states, second_calls)
    second_services = ChunkedConversionServices(
        verify_inputs=lambda _config, _plan_path, _data, _code: VerifiedChunkInputs(
            prepared, second_plan
        ),
        code_identity=lambda _root: RuntimeCodeIdentity(
            "page", "range", "plan", "aggregate-v2", "coordinator-v2"
        ),
        range_store=second_services.range_store,
        run_range=second_services.run_range,
        run_aggregate=second_services.run_aggregate,
        publish_completion=second_services.publish_completion,
        pre_aggregate=second_services.pre_aggregate,
    )

    completion = ChunkedConversionWorkflow(project_root=tmp_path, services=second_services).run(
        _request(tmp_path, plan=second_plan)
    )

    assert second_plan.plan_id == _plan().plan_id
    assert second_plan.ranges == _plan().ranges
    assert second_calls == ["pre_aggregate", "aggregate", "publish"]
    assert completion.name == "completion_record.json"
    variants = tmp_path / "output/plans" / second_plan.plan_id / "records/plan_variants"
    assert len(list(variants.glob("*.json"))) == 2


def test_missing_coordinator_resource_recovers_from_sealed_child(tmp_path: Path) -> None:
    states: dict[str, str] = {}
    calls: list[str] = []
    workflow = ChunkedConversionWorkflow(
        project_root=tmp_path,
        services=_services(states, calls, fail_aggregate_once=[True]),
    )
    with pytest.raises(ChunkedConversionError, match="aggregate_failed"):
        workflow.run(_request(tmp_path))
    run_root = next((tmp_path / "output/runs").iterdir())
    for resource in (run_root / "records").glob("resource_drange1-*.json"):
        resource.unlink()

    completion = workflow.run(_request(tmp_path))

    report = json.loads((run_root / "records/range_execution_report.json").read_text())
    assert completion.name == "completion_record.json"
    assert {row["peak_worker_rss_bytes"] for row in report["observations"]} == {5}


def test_creation_and_reuse_process_resources_remain_separate(tmp_path: Path) -> None:
    states: dict[str, str] = {}
    workflow = ChunkedConversionWorkflow(
        project_root=tmp_path,
        services=_services(states, []),
    )
    completion = workflow.run(_request(tmp_path))
    records = completion.parent

    creation = json.loads((records / "aggregate_creation_observation.json").read_text())
    subprocess_observation = json.loads(
        (records / "aggregate_resource_observation.json").read_text()
    )
    assert creation["peak_worker_rss_bytes"] == 9
    assert subprocess_observation["process_tree_peak_rss_bytes"] == 6 * 1024**3


def test_plan_storage_allows_safe_aggregate_variants(tmp_path: Path) -> None:
    first = _plan()
    second = _plan(aggregate_identity="aggregate-v2", global_policy="global-v2")

    first_path = _persist_plan_variant(tmp_path, first)
    second_path = _persist_plan_variant(tmp_path, second)

    assert first.plan_id == second.plan_id
    assert first.ranges == second.ranges
    assert first_path != second_path
    assert RangePlan.model_validate_json(first_path.read_bytes()) == first
    assert RangePlan.model_validate_json(second_path.read_bytes()) == second


def test_completed_shortcut_deep_audits_external_aggregate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    run_root = tmp_path / "run"
    aggregate_root = tmp_path / "conversions/dconv1-complete"
    write_json_atomic(
        run_root / "records/aggregate_reference.json",
        {"conversion_id": "dconv1-complete", "path": aggregate_root.as_posix()},
    )
    monkeypatch.setattr(
        workflow_module,
        "verify_chunked_completion",
        lambda _root, _expected: SimpleNamespace(aggregate_conversion_id="dconv1-complete"),
    )
    audited: list[tuple[Path, str]] = []
    monkeypatch.setattr(
        workflow_module,
        "deep_audit_conversion_bundle",
        lambda root, conversion_id: audited.append((root, conversion_id)),
    )
    workflow = ChunkedConversionWorkflow(
        project_root=tmp_path,
        services=_services({}, []),
    )

    workflow._reuse_completed(
        run_root,
        ExpectedChunkedConversionCompletion(run_id="chunk1-run", plan_id=_plan().plan_id),
    )

    assert audited == [(aggregate_root, "dconv1-complete")]


def test_coordinator_change_invalidates_run_without_changing_child_plan(tmp_path: Path) -> None:
    plan = _plan()
    plan_path = tmp_path / "plan.json"
    write_json_atomic(plan_path, plan.model_dump(mode="json"))
    prepared = cast(
        PreparedContentParsing,
        SimpleNamespace(conversion_identity=SimpleNamespace(run_id="dconv1-source")),
    )
    verified = VerifiedChunkInputs(prepared, plan)
    first = inputs.chunked_run_identity(
        plan_path=plan_path,
        verified=verified,
        code=RuntimeCodeIdentity("page", "range", "plan", "aggregate", "coordinator-v1"),
    )
    second = inputs.chunked_run_identity(
        plan_path=plan_path,
        verified=verified,
        code=RuntimeCodeIdentity("page", "range", "plan", "aggregate", "coordinator-v2"),
    )

    assert inputs.chunked_run_id(first) != inputs.chunked_run_id(second)
    assert plan.plan_id == _plan().plan_id
    assert plan.ranges == _plan().ranges
