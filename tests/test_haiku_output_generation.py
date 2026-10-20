"""Offline native Haiku cap-only intervention fixtures, including frozen parity."""

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import httpx2
import pytest
from test_target_generation import answer, packet

from er_commons import alternative_target_generation as old
from er_commons import haiku_output_generation as new


def fixture_run(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    tokens: int = 100,
    output_tokens: int = 12288,
    cache: int = 0,
    status: int = 200,
    text: str | None = None,
    drift: bool = False,
    stop_reason: str = "end_turn",
) -> tuple[dict[str, Any], list[Any], Path]:
    """Generate a native old baseline offline, then exercise new native transport."""
    native_model = old.judge_inspect.native_model
    calls: list[Any] = []
    phase = "old"
    models: list[Any] = []

    async def handle(request: httpx2.Request) -> httpx2.Response:
        assert models[-1].api.client.max_retries == 0
        calls.append(json.loads(request.content))
        if request.url.path.endswith("/count_tokens"):
            return httpx2.Response(200, json={"input_tokens": tokens if phase == "new" else 100})
        if phase == "new" and status != 200:
            return httpx2.Response(
                status, json={"error": {"message": "fixture", "type": "api_error"}}
            )
        return httpx2.Response(
            200,
            json={
                "id": "msg_fixture",
                "type": "message",
                "role": "assistant",
                "model": "claude-haiku-5-5",
                "content": [
                    {"type": "thinking", "thinking": "fixture reasoning", "signature": "fixture"},
                    {"type": "text", "text": json.dumps(answer()) if text is None else text},
                ],
                "stop_reason": stop_reason if phase == "new" else "end_turn",
                "stop_sequence": None,
                "usage": {
                    "input_tokens": tokens - cache if phase == "new" else 100,
                    "cache_read_input_tokens": cache if phase == "new" else 0,
                    "output_tokens": output_tokens if phase == "new" else 50,
                },
            },
        )

    def construct(*args: Any, **kwargs: Any) -> Any:
        model = native_model(*args, **kwargs)
        models.append(model)
        model.api.client._client._transport = httpx2.MockTransport(handle)
        model.api.client._client._mounts = {}
        if drift and phase == "new":

            async def mutate(request: httpx2.Request) -> None:
                body = json.loads(request.content)
                body["output_config"]["effort"] = "high"
                request._content = json.dumps(body).encode()

            model.api.client._client.event_hooks["request"].append(mutate)
        return model

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture")
    monkeypatch.setattr(old.judge_inspect, "native_model", construct)
    config = {
        "max_input_tokens": 100000,
        "max_output_tokens": 4096,
        "max_retries": 0,
        "timeout_seconds": 60,
    }
    baseline = tmp_path / "old" / "C041"
    baseline.mkdir(parents=True)
    old.save(baseline.parent / "manifest.json", {"run_id": "old_fixture"})
    baseline_result = asyncio.run(
        old.generate_one(
            packet(),
            baseline,
            "anthropic_generation",
            "Use exact evidence.",
            config,
            time.monotonic() + 60,
        )
    )
    assert baseline_result["status"] == "valid", baseline_result
    phase = "new"
    calls.clear()
    current = tmp_path / "new" / "C041"
    current.mkdir(parents=True)
    new.save(current.parent / "manifest.json", {"run_id": "new_fixture"})
    config.update(
        max_output_tokens=12288, baseline_native_request_path=str(baseline / "native_request.json")
    )
    result = asyncio.run(
        new.generate_one(
            packet(),
            current,
            "anthropic_generation",
            "Use exact evidence.",
            config,
            time.monotonic() + 60,
        )
    )
    return result, calls, current


def test_native_cap_only_parity(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    result, calls, current = fixture_run(monkeypatch, tmp_path)
    assert result["status"] == "valid", result
    assert result["usage"]["output_tokens"] == 12288
    assert len(calls) == 2
    native = json.loads((current / "native_request.json").read_text())
    baseline = json.loads((tmp_path / "old/C041/native_request.json").read_text())
    new.validate_native_delta(native, baseline)
    assert native["max_tokens"] == 12288
    assert calls[0] == json.loads((current / "count_projection.json").read_text())
    assert calls[1] == native
    preflight = json.loads((current / "preflight.json").read_text())
    assert preflight["output_reserve"] == 12288
    assert preflight["context_tokens"] == 1000000
    assert preflight["reserved_generation_cost_usd"] == pytest.approx(0.034216)
    assert (
        result["candidate_id"]
        != json.loads((tmp_path / "old/C041/result.json").read_text())["candidate_id"]
    )


@pytest.mark.parametrize(
    "tokens,output,valid", [(100000, 12288, True), (100001, 12288, False), (100, 12289, False)]
)
def test_native_usage_limits(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, tokens: int, output: int, valid: bool
) -> None:
    result, calls, _ = fixture_run(monkeypatch, tmp_path, tokens=tokens, output_tokens=output)
    assert (result["status"] == "valid") is valid, result
    assert len(calls) == (1 if tokens > 100000 else 2)


def test_cache_inclusive_input(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    result, _, _ = fixture_run(monkeypatch, tmp_path, tokens=100000, cache=99900)
    assert result["status"] == "valid", result
    assert result["effective_input_tokens"] == 100000
    assert result["usage"]["input_tokens"] == 100


def test_native_drift_no_dispatch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    result, calls, _ = fixture_run(monkeypatch, tmp_path, drift=True)
    assert result["failure_class"] == "integrity_failure", result
    assert calls == []
    assert result["count_calls"] == 0 and result["generation_calls"] == 0


def test_transport_no_retry(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    result, calls, path = fixture_run(monkeypatch, tmp_path, status=500)
    assert result["failure_class"] == "provider_failure", result
    assert len(calls) == 2
    assert (path / "generation_response.body").exists()


def test_output_limit_retained(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    result, _, path = fixture_run(monkeypatch, tmp_path, stop_reason="max_tokens")
    assert result["failure_class"] == "invalid_output"
    assert result["usage"]["output_tokens"] == 12288
    assert (path / "raw_answer.txt").exists()


@pytest.mark.parametrize("cap", [4096, 12287, 12289])
def test_only_registered_output_cap(cap: int) -> None:
    with pytest.raises(ValueError):
        new.validate_config(
            {
                "max_input_tokens": 100000,
                "max_output_tokens": cap,
                "max_retries": 0,
                "timeout_seconds": 60,
                "baseline_native_request_path": "fixture",
            }
        )


def test_count_plus_output_must_fit_context(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class SmallContextHooks(new.ReceiptHooks):
        """Exercise the context gate at an invented lower context boundary."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.context = 112287

    monkeypatch.setattr(new, "ReceiptHooks", SmallContextHooks)
    result, calls, _ = fixture_run(monkeypatch, tmp_path, tokens=100000)
    assert result["failure_class"] == "provider_failure", result
    assert result["generation_calls"] == 0
    assert len(calls) == 1


def test_frozen_judge_caps_remain_4096() -> None:
    from er_commons.development_evaluation_provider import component_settings

    for component in ("A", "G", "S", "C"):
        assert component_settings(component)[2].max_tokens == 4096
