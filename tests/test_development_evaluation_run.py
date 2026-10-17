"""Offline transport guards for saved-candidate evaluation; never call providers."""

import asyncio
import json
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

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

    async def execute(item: Any, identity: Any, directory: Path, deadline: float) -> Any:
        """Produce an offline receipt with an auditable call count."""
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
def test_native_sdk_serialization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, component: str
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
                200, json={"input_tokens": 100, "object": "response.input_tokens"}
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
                    "usage": {"input_tokens": 100, "output_tokens": 10},
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
                "usage": {"input_tokens": 100, "output_tokens": 10, "total_tokens": 110},
            },
        )

    def client(**kwargs: Any) -> Any:
        """Keep production hooks and replace network transport alone."""
        return DefaultAsyncHttpxClient(transport=httpx2.MockTransport(handle), **kwargs)

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
    result = asyncio.run(provider.execute_item(item, {}, tmp_path, time.monotonic() + 30))
    assert result["status"] == "completed", result
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
