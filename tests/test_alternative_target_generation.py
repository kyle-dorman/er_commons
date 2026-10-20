"""Native Inspect/SDK integration with invented payloads and no network."""

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import httpx2
import pytest
from test_target_generation import answer, packet

from er_commons import alternative_target_generation as alt


def install(
    monkeypatch: pytest.MonkeyPatch,
    condition: str,
    *,
    status: int = 200,
    tokens: int = 100,
    text: str | None = None,
    cached: int = 0,
    alias: bool = False,
    hidden_message: bool = False,
    close_error: bool = False,
) -> list[dict[str, Any]]:
    """Replace transport only; preserve native provider serialization and hooks."""
    original = alt.judge_inspect.native_model
    calls = []
    models = []

    async def handle(request: httpx2.Request) -> httpx2.Response:
        assert models[0].api.client.max_retries == 0
        body = json.loads(request.content)
        calls.append(body)
        if request.url.path.endswith("/count_tokens"):
            return httpx2.Response(200, json={"input_tokens": tokens})
        if status != 200:
            return httpx2.Response(
                status, json={"error": {"message": "fixture", "type": "api_error"}}
            )
        content = json.dumps(answer()) if text is None else text
        if condition == "anthropic_generation":
            return httpx2.Response(
                200,
                json={
                    "id": "msg_fixture",
                    "type": "message",
                    "role": "assistant",
                    "model": "claude-haiku-5-5",
                    "content": [{"type": "text", "text": content}],
                    "stop_reason": "end_turn",
                    "stop_sequence": None,
                    "usage": {"input_tokens": tokens, "output_tokens": 50},
                },
            )
        return httpx2.Response(
            200,
            json={
                "id": "chat_fixture",
                "object": "chat.completion",
                "created": 1,
                "model": alt.MODELS[condition][1].rsplit("/", 1)[-1]
                if alias
                else alt.MODELS[condition][1],
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": tokens,
                    "prompt_tokens_details": {"cached_tokens": cached},
                    "completion_tokens": 50,
                    "total_tokens": tokens + 50,
                },
            },
        )

    def model(*args: Any, **kwargs: Any) -> Any:
        instance = original(*args, **kwargs)
        models.append(instance)
        if hidden_message:

            async def mutate(request: httpx2.Request) -> None:
                body = json.loads(request.content)
                body["messages"].append({"role": "assistant", "content": "evaluator feedback"})
                request._content = json.dumps(body).encode()

            instance.api.client._client.event_hooks["request"].append(mutate)
        instance.api.client._client._transport = httpx2.MockTransport(handle)
        instance.api.client._client._mounts = {}
        if close_error:
            original_close = instance.api.client.close

            async def fail_close() -> None:
                await original_close()
                raise RuntimeError("fixture close failure")

            instance.api.client.close = fail_close
        return instance

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture")
    monkeypatch.setenv("FIREWORKS_API_KEY", "fixture")
    monkeypatch.setattr(alt.judge_inspect, "native_model", model)
    return calls


def run(tmp_path: Path, condition: str) -> tuple[dict[str, Any], Path]:
    """Create one fresh synthetic attempt with a bound run identity."""
    alt.save(tmp_path / "manifest.json", {"run_id": "fixture_run"})
    directory = tmp_path / "C041"
    directory.mkdir()
    result = asyncio.run(
        alt.generate_one(
            packet(),
            directory,
            condition,
            alt.generation_prompt("Use evidence only.", condition),
            {
                "max_input_tokens": 100000,
                "max_output_tokens": 4096,
                "max_retries": 0,
                "timeout_seconds": 60,
            },
            time.monotonic() + 60,
        )
    )
    return result, directory


@pytest.mark.parametrize("condition", list(alt.MODELS))
def test_native_roundtrip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, condition: str) -> None:
    calls = install(monkeypatch, condition)
    result, directory = run(tmp_path, condition)
    assert result["status"] == "valid", result
    assert result["generation_calls"] == 1
    assert result["count_calls"] == (condition == "anthropic_generation")
    assert len(calls) == 1 + result["count_calls"]
    native = json.loads((directory / "native_request.json").read_text())
    delivery = alt.canonical_delivery(native, result["provider"])
    assert json.loads(delivery["input"][1]["content"][0]["text"]) == packet()["payload"]
    assert delivery == json.loads((directory / "delivery_projection.json").read_text())
    if condition == "fireworks_glm":
        assert "response_format" not in native
        assert "JSON Schema" in native["messages"][0]["content"]


@pytest.mark.parametrize("condition", list(alt.MODELS))
def test_no_sdk_or_inspect_retry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, condition: str
) -> None:
    calls = install(monkeypatch, condition, status=500)
    result, directory = run(tmp_path, condition)
    assert result["status"] == "failed"
    assert result["failure_class"] == "provider_failure"
    assert len(calls) == 1 + result["count_calls"]
    assert (directory / "generation_response.body").exists()


@pytest.mark.parametrize("condition", list(alt.MODELS))
def test_invalid_answer_retains_usage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, condition: str
) -> None:
    install(monkeypatch, condition, text="invalid JSON")
    result, directory = run(tmp_path, condition)
    assert result["failure_class"] == "invalid_output"
    assert result["usage"] is not None
    assert (directory / "raw_answer.txt").read_text() == "invalid JSON"


@pytest.mark.parametrize("tokens,valid", [(100000, True), (100001, False)])
@pytest.mark.parametrize("condition", list(alt.MODELS))
def test_input_boundary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, condition: str, tokens: int, valid: bool
) -> None:
    install(monkeypatch, condition, tokens=tokens)
    result, _ = run(tmp_path, condition)
    assert (result["status"] == "valid") is valid, result
    if not valid:
        assert result["generation_calls"] == (condition == "fireworks_glm")
        assert result["failure_class"] == "provider_failure"


def test_projection_rejects_hidden_message() -> None:
    with pytest.raises(ValueError):
        alt.canonical_delivery(
            {
                "messages": [
                    {"role": "system", "content": "Prompt"},
                    {"role": "user", "content": "{}"},
                    {"role": "assistant", "content": "Feedback"},
                ]
            },
            "fireworks",
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("max_retries", 1),
        ("max_input_tokens", 100001),
        ("max_output_tokens", 4097),
        ("timeout_seconds", 901),
    ],
)
def test_config_policy(key: str, value: int) -> None:
    config = {
        "max_input_tokens": 100000,
        "max_output_tokens": 4096,
        "max_retries": 0,
        "timeout_seconds": 60,
    }
    config[key] = value
    with pytest.raises(ValueError):
        alt.validate_config(config)


@pytest.mark.parametrize("size,allowed", [(200000 - 8192, True), (200001 - 8192, False)])
def test_glm_byte_allowance(tmp_path: Path, size: int, allowed: bool) -> None:
    payload = {"question": "fixture", "passages": []}
    hook = alt.ReceiptHooks(tmp_path, "fireworks_glm", "prompt", payload, time.monotonic() + 60)
    native = {
        "model": alt.MODELS["fireworks_glm"][1],
        "max_tokens": 4096,
        "messages": [
            {"role": "system", "content": "prompt"},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        "temperature": 0,
        "top_p": 1,
        "seed": 0,
        "reasoning_effort": "medium",
        "context_length_exceeded_behavior": "error",
    }
    encoded = json.dumps(native).encode()
    body = encoded + b" " * (size - len(encoded))
    request = httpx2.Request(
        "POST", "https://api.fireworks.ai/inference/v1/chat/completions", content=body
    )
    if allowed:
        asyncio.run(hook.request(request))
        assert hook.generation_calls == 1 and hook.count_calls == 0
    else:
        with pytest.raises(ValueError, match="allowance"):
            asyncio.run(hook.request(request))
        assert hook.generation_calls == 0


def test_native_feedback_rejected_before_wire(tmp_path: Path) -> None:
    hook = alt.ReceiptHooks(tmp_path, "fireworks_glm", "expected", {}, time.monotonic() + 60)
    native = {
        "messages": [
            {"role": "system", "content": "unexpected feedback"},
            {"role": "user", "content": "{}"},
        ]
    }
    with pytest.raises(alt.IntegrityError, match="prompt/evidence"):
        asyncio.run(
            hook.request(
                httpx2.Request(
                    "POST", "https://api.fireworks.ai/inference/v1/chat/completions", json=native
                )
            )
        )
    assert hook.generation_calls == 0


def test_glm_alias_cache_usage(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    install(monkeypatch, "fireworks_glm", tokens=100000, cached=90000, alias=True)
    result, _ = run(tmp_path, "fireworks_glm")
    assert result["status"] == "valid", result
    assert result["effective_input_tokens"] == 100000
    assert result["usage"]["input_tokens"] == 10000
    assert result["usage"]["input_tokens_cache_read"] == 90000


def test_zero_glm_usage_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    install(monkeypatch, "fireworks_glm", tokens=0)
    result, _ = run(tmp_path, "fireworks_glm")
    assert result["failure_class"] == "provider_failure"


def test_shape_isolation_stops_globally(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = install(monkeypatch, "fireworks_glm", hidden_message=True)
    result, _ = run(tmp_path, "fireworks_glm")
    assert result["failure_class"] == "integrity_failure", result
    assert result["generation_calls"] == 0
    assert calls == []


@pytest.mark.parametrize("condition", list(alt.MODELS))
@pytest.mark.parametrize("text", [None, "invalid JSON"])
def test_cleanup_failure_preserves_attempt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, condition: str, text: str | None
) -> None:
    """Closing transport cannot discard output, usage, seals or an earlier failure."""
    calls = install(monkeypatch, condition, text=text, close_error=True)
    result, directory = run(tmp_path, condition)
    assert result["status"] == "failed"
    assert result["cleanup_error"] == {"type": "RuntimeError", "message": "fixture close failure"}
    assert result["failure_class"] == ("provider_failure" if text is None else "invalid_output")
    if text is None:
        assert result["failure"] == "fixture close failure"
        assert (directory / "candidate.json").exists()
    else:
        assert result["failure"] != "fixture close failure"
        assert result["failure_causes"]
    assert result["usage"] is not None
    assert (directory / "raw_answer.txt").exists()
    assert json.loads((directory / "result.json").read_text()) == result
    assert (directory / "completion.json").exists()
    assert len(calls) == 1 + result["count_calls"]
