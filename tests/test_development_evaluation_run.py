"""Offline transport guards for saved-candidate evaluation; never call providers."""

import asyncio
import json
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from er_commons.artifact_io import artifact_inventory
from er_commons.development_evaluation_provider import (
    LIMITS,
    ReceiptHooks,
    component_settings,
    count_projection,
)


class Request:
    """Minimal native request fixture with exact serialized body."""

    def __init__(self, provider: str, body: dict[str, Any], *, count: bool = False) -> None:
        """Choose the provider's generation or count endpoint."""
        path = "/responses" if provider == "openai" else "/messages"
        if count:
            path += "/input_tokens" if provider == "openai" else "/count_tokens"
        self.url = SimpleNamespace(host=f"api.{provider}.com", path=path)
        self.body = json.dumps(body).encode()
        self.headers = {}

    async def aread(self) -> bytes:
        """Return unchanged fixture request bytes."""
        return self.body


@pytest.mark.parametrize("component", list("AGSC"))
def test_frozen_settings(component: str) -> None:
    """Current native semantic configuration must match the 09G seal."""
    _, _, config = component_settings(component)
    assert config.max_tokens == 4096
    assert config.max_retries == 2


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_exact_count_schema_parity_and_no_retry(tmp_path: Path, provider: str) -> None:
    """Counter sees every model input/schema field before one permitted dispatch."""
    native = (
        {
            "model": "fixture",
            "input": [{"role": "user", "content": "body"}],
            "text": {"format": {"schema": {"type": "object"}}},
            "max_output_tokens": 4096,
            "truncation": "disabled",
            "reasoning": {"effort": "medium"},
            "store": False,
        }
        if provider == "openai"
        else {
            "model": "fixture",
            "messages": [{"role": "user", "content": "body"}],
            "system": "prompt",
            "output_config": {"format": {"schema": {"type": "object"}}},
            "max_tokens": 4096,
        }
    )
    hooks = ReceiptHooks(tmp_path, provider, "fixture", time.monotonic() + 60)

    async def count(**projection: Any) -> Any:
        """Emulate SDK counter and invoke its actual audit hook."""
        extra = projection.pop("extra_body", {})
        projection.pop("extra_headers", None)
        projection.update(extra)
        assert projection == count_projection(provider, native)
        await hooks.request(Request(provider, projection, count=True))
        return SimpleNamespace(input_tokens=100, model_dump=lambda **_: {"input_tokens": 100})

    hooks.client = SimpleNamespace(
        responses=SimpleNamespace(input_tokens=SimpleNamespace(count=count)),
        messages=SimpleNamespace(count_tokens=count),
    )
    asyncio.run(hooks.request(Request(provider, native)))
    assert hooks.count_calls == hooks.judge_calls == 1
    assert (tmp_path / "dispatch.json").exists()
    with pytest.raises(ValueError, match="retry"):
        asyncio.run(hooks.request(Request(provider, native)))
    assert hooks.count_calls == hooks.judge_calls == 1


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_unknown_fields_block_before_count(provider: str) -> None:
    """Uncounted novel provider features cannot silently pass context preflight."""
    with pytest.raises(ValueError, match="unknown"):
        count_projection(provider, {"model": "fixture", "new_schema": {}})


def test_count_parity_blocks_changed_schema(tmp_path: Path) -> None:
    """A count projection with missing structured schema is not accepted."""
    (tmp_path / "count_projection.json").write_text(
        json.dumps({"model": "fixture", "text": {"schema": {}}})
    )
    hooks = ReceiptHooks(tmp_path, "openai", "fixture", time.monotonic() + 60)
    with pytest.raises(ValueError, match="parity"):
        asyncio.run(hooks.request(Request("openai", {"model": "fixture"}, count=True)))
    assert hooks.count_calls == hooks.judge_calls == 0


def test_timebox_and_accounting_limits(tmp_path: Path) -> None:
    """Expired runs cannot dispatch; maximum declared liability fits budget."""
    hooks = ReceiptHooks(tmp_path, "openai", "fixture", time.monotonic() - 1)
    with pytest.raises(ValueError, match="timebox"):
        asyncio.run(hooks.request(Request("openai", {})))
    liability = (
        LIMITS["max_count_calls"] * LIMITS["count_cost_allowance_usd"]
        + LIMITS["max_judge_calls"]
        * (
            LIMITS["max_input_tokens"] * LIMITS["reserve_input_per_million"]
            + LIMITS["max_output_tokens"] * LIMITS["reserve_output_per_million"]
        )
        / 1e6
    )
    assert liability <= LIMITS["max_spend_usd"]
    assert LIMITS["max_retries"] == 0


def test_offline_run_and_replay(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A fresh fixture run replays without transport and rejects foreign judgments."""
    from er_commons import development_evaluation as core
    from er_commons import development_evaluation_run as runner
    from er_commons.artifact_io import artifact_inventory, json_bytes

    identity = {"case_id": "C041", "candidate_id": "fixture"}
    item = {
        "sample_id": "sample",
        "component": "A",
        "point_id": None,
        "payload_sha256": "payload",
        "status": "not_run",
    }
    plans = [{"identity": identity, "items": [item]}]
    monkeypatch.setattr(runner.inputs, "load_plans", lambda _: plans)
    monkeypatch.setattr(core, "pending_items", lambda plan, rows: [] if rows else [item])
    monkeypatch.setattr(
        core,
        "build_report",
        lambda plan, rows: {"identity": identity, "rows": rows, "citation_ids": ("P1", "P2")},
    )
    monkeypatch.setattr(core, "readable_report", lambda report: json.dumps(report))
    calls = []

    async def execute(
        item: Any, identity: Any, directory: Path, deadline: float, limits: dict[str, Any]
    ) -> Any:
        """Produce an offline receipt with an auditable call count."""
        assert limits == LIMITS
        calls.append(item)
        return {
            **item,
            "identity": identity,
            "status": "completed",
            "judge_calls": 1,
            "count_calls": 1,
        }

    monkeypatch.setattr(runner.provider, "execute_item", execute)
    output = tmp_path / "run"
    result = asyncio.run(runner.run(tmp_path, output))
    assert result["judge_calls"] == 1
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["prospective_calls"] == 1
    assert manifest["reserved_usd"] == pytest.approx(0.311264)
    replay = asyncio.run(runner.run(tmp_path, output, replay=True))
    assert replay["new_calls"] == 0 and len(calls) == 1
    assert replay["reports"][0]["citation_ids"] == ("P1", "P2")
    assert json.loads((output / "reports.json").read_text())[0]["citation_ids"] == ["P1", "P2"]
    original_manifest = runner.run_manifest

    def changed_manifest(plans: Any) -> dict[str, Any]:
        """Simulate a new replay implementation without changing accepted inputs."""
        value = original_manifest(plans)
        value["implementation"]["development_evaluation_run.py"] = "changed"
        return value

    monkeypatch.setattr(runner, "run_manifest", changed_manifest)
    with pytest.raises(ValueError, match="inputs/configuration"):
        asyncio.run(runner.run(tmp_path, output, replay=True))
    changed = asyncio.run(
        runner.run(tmp_path, output, replay=True, allow_replay_source_change=True)
    )
    assert changed["execution_implementation"] != changed["replay_implementation"]
    assert changed["new_calls"] == 0 and len(calls) == 1

    def changed_input(plans: Any) -> dict[str, Any]:
        """Input drift stays forbidden even with explicit replay source allowance."""
        value = changed_manifest(plans)
        value["plans_sha256"] = "changed"
        return value

    monkeypatch.setattr(runner, "run_manifest", changed_input)
    with pytest.raises(ValueError, match="inputs/configuration"):
        asyncio.run(runner.run(tmp_path, output, replay=True, allow_replay_source_change=True))
    with pytest.raises(ValueError, match="requires replay"):
        asyncio.run(runner.run(tmp_path, output, allow_replay_source_change=True))
    monkeypatch.setattr(runner, "run_manifest", original_manifest)
    with pytest.raises(ValueError, match="redispatch forbidden"):
        asyncio.run(runner.run(tmp_path, output))
    rows = json.loads((output / "judgments.json").read_text())
    rows.append({**rows[0], "sample_id": "foreign"})
    (output / "judgments.json").write_bytes(json_bytes(rows))
    (output / "completion.json").write_bytes(
        json_bytes(artifact_inventory(output, {"completion.json"}))
    )
    with pytest.raises(ValueError, match="orphan"):
        asyncio.run(runner.run(tmp_path, output, replay=True))


@pytest.mark.parametrize("component", ["A", "S"])
@pytest.mark.parametrize("input_tokens", [100, 100000, 100001])
@pytest.mark.parametrize("close_error", [False, True])
def test_native_sdk_serialization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    component: str,
    input_tokens: int,
    close_error: bool,
) -> None:
    """Exercise real Inspect and both SDK serializers using network-only replacement."""
    import httpx2
    from openai import DefaultAsyncHttpxClient

    from er_commons import development_evaluation_provider as provider

    condition, _, _ = component_settings(component)
    selected = provider.judge_inspect.profile(condition)
    calls = []

    async def handle(request: httpx2.Request) -> httpx2.Response:
        """Return native provider-shaped fixtures after capturing the actual wire body."""
        body = json.loads(request.content)
        calls.append(body)
        if request.url.path.endswith(("/input_tokens", "/count_tokens")):
            return httpx2.Response(
                200, json={"input_tokens": input_tokens, "object": "response.input_tokens"}
            )
        if component == "S":
            return httpx2.Response(
                200,
                json={
                    "id": "msg_fixture",
                    "type": "message",
                    "role": "assistant",
                    "model": selected.model,
                    "content": [{"type": "text", "text": "{}"}],
                    "stop_reason": "end_turn",
                    "stop_sequence": None,
                    "usage": {"input_tokens": input_tokens, "output_tokens": 10},
                },
            )
        return httpx2.Response(
            200,
            json={
                "id": "resp_fixture",
                "object": "response",
                "created_at": 1,
                "model": selected.model,
                "status": "completed",
                "output": [
                    {
                        "id": "msg_fixture",
                        "type": "message",
                        "role": "assistant",
                        "status": "completed",
                        "content": [{"type": "output_text", "text": "{}", "annotations": []}],
                    }
                ],
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": 10,
                    "total_tokens": input_tokens + 10,
                },
            },
        )

    def client(**kwargs: Any) -> Any:
        """Keep production hooks and replace network transport alone."""
        transport = DefaultAsyncHttpxClient(transport=httpx2.MockTransport(handle), **kwargs)
        if close_error:
            original_close = transport.aclose

            async def failed_close() -> None:
                """Simulate cleanup failure after releasing the fixture transport."""
                await original_close()
                raise RuntimeError("fixture close failure")

            transport.aclose = failed_close
        return transport

    monkeypatch.setenv("OPENAI_API_KEY", "fixture-key-not-real")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture-key-not-real")
    monkeypatch.setattr(provider, "DefaultAsyncHttpxClient", client)
    item = {
        "sample_id": "fixture",
        "component": component,
        "point_id": None,
        "packet": {"fixture": "invented"},
        "payload_sha256": "fixture",
    }
    limits = {**LIMITS, "max_input_tokens": 100000, "count_cost_allowance_usd": 0.0}
    result = asyncio.run(provider.execute_item(item, {}, tmp_path, time.monotonic() + 30, limits))
    if close_error:
        assert result["status"] == "execution_error"
        assert result["cleanup_error"] == "RuntimeError: fixture close failure"
        assert json.loads((tmp_path / "judgment.json").read_text()) == result
        assert json.loads((tmp_path / "completion.json").read_text()) == artifact_inventory(
            tmp_path, {"completion.json"}
        )
    if input_tokens > 100000:
        assert result["status"] == "execution_error"
        assert any("context_overflow" in cause for cause in result["failure_causes"])
        assert result["count_calls"] == 1 and result["judge_calls"] == 0
        assert len(calls) == 1
        return
    assert result["accounting"]["count_cost_allowance_usd"] == 0.0
    assert result["accounting"]["actual_count_cost_usd"] is None
    assert result["status"] == ("execution_error" if close_error else "completed"), result
    assert len(calls) == 2
    assert calls[0] == count_projection(selected.provider, calls[1])
    assert (tmp_path / "judge_response.body").exists()
    assert json.loads((tmp_path / "count_headers.json").read_text()) == json.loads(
        (tmp_path / "native_headers.json").read_text()
    )
    assert result["count_calls"] == result["judge_calls"] == 1


def test_manifest_binds_every_evaluation_module() -> None:
    """Extracted source owners remain part of strict replay implementation identity."""
    from er_commons.development_evaluation_run import run_manifest

    assert set(run_manifest([])["implementation"]) == {
        "development_evaluation.py",
        "development_evaluation_inputs.py",
        "development_evaluation_provider.py",
        "development_evaluation_run.py",
    }


def test_operational_caps_preserve_judge_policy() -> None:
    """Six-panel budgets increase capacity without changing judge semantics or retries."""
    from er_commons.development_evaluation_run import evaluation_limits, run_manifest

    limits = {"max_judge_calls": 72, "max_count_calls": 72, "max_spend_usd": 24.0}
    plans = [{"items": [{"status": "not_run"}] * 72}]
    manifest = run_manifest(plans, limits)
    assert manifest["prospective_calls"] == 72
    resumed = run_manifest(
        plans, {**limits, "max_input_tokens": 100000, "count_cost_allowance_usd": 0}
    )
    assert resumed["reserved_usd"] == pytest.approx(72 * 0.028072)
    assert resumed["limits"]["actual_count_cost_usd"] is None
    assert LIMITS["max_input_tokens"] == 32768
    assert LIMITS["count_cost_allowance_usd"] == 0.30
    assert manifest["limits"]["max_output_tokens"] == 4096
    assert manifest["limits"]["max_retries"] == 0
    for invalid in (
        {"max_input_tokens": 100001},
        {"max_input_tokens": True},
        {"count_cost_allowance_usd": -0.01},
        {"count_cost_allowance_usd": True},
        {"count_cost_allowance_usd": 0.31},
        {"reserve_input_per_million": 0},
        {"max_judge_calls": 73},
        {"max_output_tokens": 8192},
        {"max_retries": 1},
        {"max_elapsed_seconds": 1801},
        {"max_count_calls": True},
    ):
        with pytest.raises(ValueError):
            evaluation_limits(invalid)
    with pytest.raises(ValueError, match="fanout"):
        run_manifest(plans)
    with pytest.raises(ValueError, match="fanout"):
        run_manifest(plans, {**limits, "max_count_calls": 71})
    with pytest.raises(ValueError, match="liability"):
        run_manifest(plans, {**limits, "max_spend_usd": 1})


@pytest.mark.parametrize("panel", ["initial_three", "expanded_six"])
def test_explicit_generation_run_panel_and_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, panel: str
) -> None:
    """Only sealed complete panels with bound run/repeat/candidate identities load."""
    from er_commons import development_evaluation_inputs as inputs
    from er_commons.artifact_io import artifact_inventory, json_bytes, stable_json_sha256
    from er_commons.target_generation import panel_case_ids

    source = tmp_path / "run"
    source.mkdir()
    cases = panel_case_ids(panel)
    records = [{"case_id": case} for case in cases]
    bindings = {"fixture": "bound"}
    monkeypatch.setattr(inputs, "load_smoke", lambda root, **kw: (records, bindings))
    run_id = stable_json_sha256("run")
    manifest = {
        "case_ids": cases,
        "bindings": bindings,
        "namespace": "run",
        "run_id": run_id,
        "repeat": 2,
        "attempts_per_case": 1,
    }
    rows = []
    for case in cases:
        identity = {
            "run_id": run_id,
            "case_id": case,
            "attempt": 1,
            "repeat": 2,
            "request_sha256": "request",
            "candidate_sha256": "answer",
        }
        rows.append(
            {
                **identity,
                "candidate_id": stable_json_sha256(identity),
                "status": "valid",
                "generation_calls": 1,
                "count_calls": 1,
            }
        )
    summary = {"case_ids": cases, "results": rows}

    def seal() -> None:
        """Publish synthetic seal after each deliberately changed metadata fixture."""
        (source / "manifest.json").write_bytes(json_bytes(manifest))
        (source / "summary.json").write_bytes(json_bytes(summary))
        (source / "completion.json").write_bytes(
            json_bytes(artifact_inventory(source, {"completion.json"}))
        )

    seal()
    assert inputs._load_panel_run(tmp_path, source)[1] == rows
    rows[0]["repeat"] = 1
    seal()
    with pytest.raises(ValueError, match="receipt"):
        inputs._load_panel_run(tmp_path, source)
    rows[0]["repeat"] = 2
    rows[0]["candidate_id"] = "foreign"
    seal()
    with pytest.raises(ValueError, match="Candidate identity"):
        inputs._load_panel_run(tmp_path, source)
    manifest["case_ids"] = [*cases, "C999"]
    seal()
    with pytest.raises(ValueError, match="fixed three/six"):
        inputs._load_panel_run(tmp_path, source)
