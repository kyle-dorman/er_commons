"""Offline public-API tests for the human-owned Gate C workflow."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from er_commons.artifact_io import write_json_atomic
from er_commons.chunked_conversion.qualification import gate_c_inputs
from er_commons.chunked_conversion.qualification.contracts import (
    GateCRequest,
    ResourceLimits,
    ResourceObservation,
)
from er_commons.chunked_conversion.qualification.diagnostics import QualificationError
from er_commons.chunked_conversion.qualification.docling_adapter import DoclingAdapter
from er_commons.chunked_conversion.qualification.g1_profile import G1CodeIdentity
from er_commons.chunked_conversion.qualification.gate_c_inputs import VerifiedG1Inputs
from er_commons.chunked_conversion.qualification.gate_c_reporting import select_concurrency
from er_commons.chunked_conversion.qualification.gate_c_workflow import (
    GateCWorkflow,
    GateCWorkflowServices,
)
from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.document_parsing.content_parsing.preparation import PreparedContentParsing


def _observation() -> ResourceObservation:
    return ResourceObservation(
        process_tree_peak_rss_bytes=6 * 1024**3,
        wall_seconds=1.0,
        minimum_system_available_bytes=8 * 1024**3,
        swap_delta_bytes=0,
        stdout="stdout.log",
        stderr="stderr.log",
    )


def test_concurrency_stays_one_when_two_peaks_exceed_ceiling() -> None:
    gib = 1024**3
    selection = select_concurrency(
        [{"process_tree_peak_rss_bytes": 6 * gib}],
        _observation(),
        max_aggregate_rss_bytes=10 * gib,
    )
    assert selection["selected_workers"] == 1
    assert selection["projected_two_worker_peak_rss_bytes"] == 12 * gib


def test_behavior_identity_excludes_cli_workflow_and_reporting(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    package = tmp_path / "src/er_commons/chunked_conversion"
    package.mkdir(parents=True)
    observed: list[tuple[str, ...]] = []

    def fake_code_identity(paths: list[Path], *, repo_root: Path) -> dict[str, str]:
        assert repo_root == tmp_path
        relative = tuple(path.relative_to(package).as_posix() for path in paths)
        observed.append(relative)
        return {"sha256": "|".join(relative)}

    monkeypatch.setattr(gate_c_inputs, "code_identity", fake_code_identity)
    identity = gate_c_inputs.behavior_code_identity(tmp_path)

    flattened = {path for group in observed for path in group}
    assert "qualification/gate_c_workflow.py" not in flattened
    assert "qualification/gate_c_reporting.py" not in flattened
    assert all(not path.startswith("scripts/") for path in flattened)
    assert identity.range_conversion != identity.aggregate


def test_docling_backend_unload_failure_is_not_swallowed() -> None:
    class FailingBackend:
        def unload(self) -> None:
            raise RuntimeError("cannot release mapped PDF")

    input_document = SimpleNamespace(_backend=FailingBackend())

    with pytest.raises(QualificationError, match="backend_unload") as caught:
        DoclingAdapter().release_backend(input_document)

    assert caught.value.path == "input_document._backend"
    assert caught.value.actual == "cannot release mapped PDF"


class _FakeStore:
    def __init__(self, root: Path, plan: Any, states: dict[str, str]) -> None:
        self.root = root
        self.plan = plan
        self.states = states

    def final_root(self, range_id: str) -> Path:
        return self.root / "ranges" / range_id

    def verify(self, range_id: str) -> object:
        state = self.states.get(range_id)
        if state != self.plan.plan_id:
            raise QualificationError(
                "child_identity",
                stage="range_reuse",
                path=self.final_root(range_id).as_posix(),
                expected=self.plan.plan_id,
                actual=state,
            )
        return object()


def _request(tmp_path: Path, *, stop_after_ranges: int | None = None) -> GateCRequest:
    data_root = (tmp_path / "data").resolve()
    source_root = (tmp_path / "source").resolve()
    output_root = (tmp_path / "output").resolve()
    config = (tmp_path / "config.json").resolve()
    (source_root / "records").mkdir(parents=True, exist_ok=True)
    (source_root / "records/artifact_inventory.json").write_text("{}\n")
    config.write_text("{}\n")
    limits = ResourceLimits(max_rss_bytes=10 * 1024**3, max_wall_seconds=60.0)
    return GateCRequest(
        data_root=data_root,
        source_root=source_root,
        output_root=output_root,
        config_path=config,
        stop_after_ranges=stop_after_ranges,
        range_limits=limits,
        aggregate_limits=limits,
    )


def _services(
    states: dict[str, str], calls: list[str], *, fail_aggregate_once: list[bool] | None = None
) -> GateCWorkflowServices:
    sealed = {
        "conversion_id": "dconv1-" + "a" * 64,
        "identity": {
            "source": {
                "source_id": "deir_appendix_g1",
                "sha256": "b" * 64,
                "byte_size": 123,
            },
            "sealed_release": {},
            "package_versions": {},
            "model_inventory": {},
        },
    }
    prepared = cast(
        PreparedContentParsing,
        SimpleNamespace(
            conversion_identity=SimpleNamespace(run_id="dconv1-" + "a" * 64),
            runtime={},
        ),
    )

    def run_range(spec: Any, _limits: ResourceLimits) -> ResourceObservation:
        calls.append(f"range:{spec.range_id}")
        loaded = RangePlan.model_validate_json(spec.plan_path.read_bytes())
        states[spec.range_id] = loaded.plan_id
        completion = spec.run_root / "ranges" / spec.range_id / "records/completion_record.json"
        completion.parent.mkdir(parents=True)
        completion.write_text("{}\n")
        return _observation()

    def run_aggregate(spec: Any, _limits: ResourceLimits) -> ResourceObservation:
        calls.append("aggregate")
        if fail_aggregate_once and fail_aggregate_once.pop(0):
            raise QualificationError("aggregate_failed", stage="aggregate", path=str(spec.run_root))
        write_json_atomic(
            spec.run_root / "records/aggregate_reference.json",
            {"conversion_id": "dconv1-" + "c" * 64, "path": "aggregate"},
        )
        return _observation()

    def publish(
        root: Path,
        _run_id: str,
        _source: Path,
        _plan: Any,
        _observation_value: ResourceObservation,
        _limit: int,
        _checkpoint: bool,
    ) -> Path:
        calls.append("publish")
        path = root / "records/completion_record.json"
        path.write_text("{}\n")
        return path

    return GateCWorkflowServices(
        verify_inputs=lambda _source, _config, _data: VerifiedG1Inputs(sealed, prepared),
        code_identity=lambda _root: G1CodeIdentity("page", "range", "plan", "aggregate"),
        range_store=lambda root, plan: _FakeStore(root, plan, states),
        run_range=run_range,
        run_aggregate=run_aggregate,
        publish_completion=publish,
    )


@pytest.mark.parametrize("foreign_state", ["corrupt", "transplanted-plan"])
def test_resume_rejects_corrupt_or_transplanted_child(tmp_path: Path, foreign_state: str) -> None:
    states: dict[str, str] = {}
    calls: list[str] = []
    services = _services(states, calls)
    workflow = GateCWorkflow(project_root=tmp_path, services=services)
    checkpoint = workflow.run(_request(tmp_path, stop_after_ranges=1))
    first_range = next(iter(states))
    states[first_range] = foreign_state

    with pytest.raises(QualificationError, match="child_identity") as caught:
        workflow.run(_request(tmp_path))

    assert str(checkpoint.parents[1] / "ranges" / first_range) in str(caught.value)


def test_aggregate_retry_reuses_all_ranges_and_publishes_without_range_execution(
    tmp_path: Path,
) -> None:
    states: dict[str, str] = {}
    calls: list[str] = []
    fail_once = [True]
    services = _services(states, calls, fail_aggregate_once=fail_once)
    workflow = GateCWorkflow(project_root=tmp_path, services=services)

    with pytest.raises(QualificationError, match="aggregate_failed"):
        workflow.run(_request(tmp_path))
    initial_range_calls = [call for call in calls if call.startswith("range:")]
    assert len(initial_range_calls) == 12
    retained = list(
        (tmp_path / "output/runs").glob("*/attempt_failures/aggregate/records/failure.json")
    )
    assert len(retained) == 1

    calls.clear()
    completion = workflow.run(_request(tmp_path))

    assert calls == ["aggregate", "publish"]
    assert completion.name == "completion_record.json"
