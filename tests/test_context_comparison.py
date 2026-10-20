"""Native isolation and immutable failure handling for shared-context comparisons."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from er_commons import context_comparison as cc
from er_commons import judge_inspect


def native(provider: str) -> dict:
    """Provide minimal native controls with a known exact message/schema binding."""
    if provider == "openai":
        return {
            "model": "m",
            "max_output_tokens": 12288,
            "truncation": "disabled",
            "reasoning": {"effort": "medium"},
            "store": False,
            "input": cc.expected_delivery("summary+prompt", {"question": "q"})["input"],
            "text": {"format": {"schema": {"type": "object"}}},
        }
    return {
        "model": "m",
        "max_tokens": 12288,
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "medium"},
        "output_format": {"schema": {"type": "object"}},
        "system": "summary+prompt",
        "messages": [{"role": "user", "content": json.dumps({"question": "q"})}],
    }


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_native_parity_and_schema(tmp_path: Path, provider: str) -> None:
    """Reject changed instructions, payloads and schemas before provider counting."""
    hook = cc.ReceiptHooks(
        tmp_path,
        provider,
        "m",
        time.monotonic() + 10,
        {"max_output_tokens": 12288},
        expected=cc.expected_delivery("summary+prompt", {"question": "q"}),
        expected_schema={"type": "object"},
    )
    request = native(provider)
    hook._validate_native_controls(request)
    changed = json.loads(json.dumps(request))
    if provider == "openai":
        changed["input"][1]["content"][0]["text"] = "{}"
    else:
        changed["messages"][0]["content"] = "{}"
    with pytest.raises(ValueError, match="isolation"):
        hook._validate_native_controls(changed)
    changed = json.loads(json.dumps(request))
    if provider == "openai":
        changed["text"]["format"]["schema"] = {}
    else:
        changed["output_format"]["schema"] = {}
    with pytest.raises(ValueError, match="schema"):
        hook._validate_native_controls(changed)


def test_generation_preserves_invalid_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Bad JSON is retained as one invalid attempt, never repaired or retried."""
    import asyncio

    fake = AsyncMock(
        return_value={
            "status": "completed",
            "raw_output": "not json",
            "provider": "openai",
            "count_calls": 1,
            "judge_calls": 0,
        }
    )
    monkeypatch.setattr(cc, "execute", fake)
    result = asyncio.run(
        cc.generate_one(
            {"payload": {}},
            tmp_path,
            "openai_generation",
            "p",
            time.monotonic() + 10,
            {"run_id": "r", "case_id": "C014", "repeat": 1},
        )
    )
    assert result["status"] == "invalid_output" and fake.await_count == 1
    assert json.loads((tmp_path / "result.json").read_text())["raw_output"] == "not json"
    assert not (tmp_path / "candidate.json").exists()


@pytest.mark.parametrize(
    "component,condition,cap",
    [
        ("target", "fireworks_glm", 12288),
        ("target", "openai_generation", 4096),
        ("C", "anthropic_generation", 4096),
        ("G", "openai_generation", 12288),
    ],
)
def test_unregistered_dispatch_rejected(
    tmp_path: Path, component: str, condition: str, cap: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Invalid model/output combinations cannot construct a provider client."""
    import asyncio

    mock = AsyncMock()
    monkeypatch.setattr(judge_inspect, "native_model", mock)
    with pytest.raises(ValueError):
        asyncio.run(
            cc.execute(
                directory=tmp_path,
                condition=condition,
                component=component,
                prompt="p",
                payload={},
                deadline=time.monotonic() + 10,
                max_output_tokens=cap,
            )
        )
    mock.assert_not_called()


@pytest.mark.parametrize(
    "component,condition,cap",
    [
        ("target", "openai_generation", 12288),
        ("target", "anthropic_generation", 12288),
        ("A", "openai_generation", 4096),
        ("G", "openai_generation", 4096),
        ("S", "anthropic_generation", 4096),
        ("C", "openai_generation", 4096),
    ],
)
def test_real_native_serializer_offline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, component: str, condition: str, cap: int
) -> None:
    """Exercise real Inspect/SDK serialization and count hooks against mock HTTP only."""
    import asyncio

    import httpx2 as httpx
    from openai import DefaultAsyncHttpxClient

    monkeypatch.setenv("OPENAI_API_KEY", "offline-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "offline-test")
    calls = []

    async def response(request: httpx.Request) -> httpx.Response:
        """Return count success and one explicit generation error without network."""
        calls.append(str(request.url))
        if request.url.path.endswith(("/input_tokens", "/count_tokens")):
            return httpx.Response(200, json={"input_tokens": 123}, request=request)
        return httpx.Response(
            400,
            json={"error": {"type": "invalid_request_error", "message": "offline boundary"}},
            request=request,
        )

    original = judge_inspect.native_model

    def model(*args, **kwargs):
        """Install HTTP mock before constructing the native SDK client."""
        kwargs["http_client"] = DefaultAsyncHttpxClient(transport=httpx.MockTransport(response))
        return original(*args, **kwargs)

    monkeypatch.setattr(judge_inspect, "native_model", model)
    result = asyncio.run(
        cc.execute(
            directory=tmp_path,
            condition=condition,
            component=component,
            prompt="Shared project summary\nFrozen core",
            payload={"question": "offline fixture"},
            deadline=time.monotonic() + 10,
            max_output_tokens=cap,
        )
    )
    assert result["count_calls"] == 1 and result["judge_calls"] == 1, result
    assert result["status"] == "execution_error"
    assert len(calls) == 2 and "offline boundary" in result["error"]
    assert (tmp_path / "native_request.json").exists() and (
        tmp_path / "count_response.body"
    ).exists()


@pytest.mark.parametrize("generation_fails", [False, True])
def test_client_close_failure_preserves_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, generation_fails: bool
) -> None:
    """Seal completed output or original execution diagnostics despite failed cleanup."""
    import asyncio
    from types import SimpleNamespace

    selected = judge_inspect.profile("openai_generation")
    usage = SimpleNamespace(
        input_tokens=123,
        input_tokens_cache_read=0,
        input_tokens_cache_write=0,
        output_tokens=10,
        model_dump=lambda **kwargs: {"input_tokens": 123, "output_tokens": 10},
    )
    output = SimpleNamespace(
        completion="retained output",
        model=selected.model,
        response_id="offline-response",
        usage=usage,
        stop_reason="stop",
        model_dump=lambda **kwargs: {"model": selected.model, "completion": "retained output"},
    )
    client = SimpleNamespace(
        _client=SimpleNamespace(event_hooks={"request": [], "response": []}),
        close=AsyncMock(side_effect=RuntimeError("close failed")),
    )
    generate = AsyncMock(
        return_value=output,
        side_effect=ValueError("generation failed") if generation_fails else None,
    )
    model = SimpleNamespace(api=SimpleNamespace(client=client), generate=generate)
    monkeypatch.setattr(judge_inspect, "native_model", lambda *args, **kwargs: model)
    cc.save(tmp_path / "count_result.json", {"input_tokens": 123})
    result = asyncio.run(
        cc.generate_one(
            {"payload": {}},
            tmp_path,
            "openai_generation",
            "p",
            time.monotonic() + 10,
            {"run_id": "r", "case_id": "C014", "repeat": 1},
        )
    )
    assert result["status"] == "execution_error"
    assert result["cleanup_error"] == "RuntimeError: close failed"
    if generation_fails:
        assert result["error"] == "ValueError: generation failed"
        assert result["failure_causes"] == [{"type": "ValueError", "message": "generation failed"}]
    else:
        assert result["raw_output"] == "retained output"
        assert result["accounting"]["effective_input_tokens"] == 123
        assert (tmp_path / "raw_output.txt").read_text() == "retained output"
    assert json.loads((tmp_path / "result.json").read_text()) == result
    assert (tmp_path / "completion.json").exists()
    assert not (tmp_path / "candidate.json").exists()
    generate.assert_awaited_once()
    client.close.assert_awaited_once()
