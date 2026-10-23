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


def test_v6_configuration_is_explicit_and_context_exact() -> None:
    """Only the opted-in C route changes schema, with its overview included once."""
    from er_commons import adequacy_binary as core

    version = core.CONCLUSION_STRUCTURED_V6_PROMPT_VERSION
    prompt = core.system_prompt("C", prompt_version=version)
    config = cc._execution_config("openai_generation", "C", prompt, 4096, prompt_version=version)
    schema = cc._expected_schema(config, "openai")
    assert "internal_contradictions" in schema["properties"]
    assert "internal_contradictions" in schema["required"]
    for component, condition, text, selected in (
        ("S", "openai_generation", prompt, version),
        ("C", "anthropic_generation", prompt, version),
        ("C", "openai_generation", "extra context" + prompt, version),
        ("C", "openai_generation", prompt, "unknown"),
    ):
        with pytest.raises(ValueError):
            cc._execution_config(condition, component, text, 4096, prompt_version=selected)
    old = cc._execution_config("openai_generation", "C", "historical prompt", 4096)
    assert "internal_contradictions" not in cc._expected_schema(old, "openai")["properties"]


def test_task15s_native_limit_is_transport_only() -> None:
    """Explicit native concurrency changes no prompt, schema or reasoning setting."""
    from er_commons import adequacy_binary as core
    from er_commons.development_evaluation_provider import component_settings

    version = core.CONCLUSION_STRUCTURED_V6_PROMPT_VERSION
    for condition, component, prompt, limit, selected in [
        ("openai_generation", "target", "prompt", 12288, None),
        ("anthropic_generation", "target", "prompt", 12288, None),
        *[(component_settings(c)[0], c, component_settings(c)[1], 4096, None) for c in "AGS"],
        ("openai_generation", "C", core.system_prompt("C", prompt_version=version), 4096, version),
    ]:
        base = cc._execution_config(condition, component, prompt, limit, prompt_version=selected)
        expanded = cc._execution_config(
            condition, component, prompt, limit, prompt_version=selected, max_connections=16
        )
        assert base.max_connections == 1 and expanded.max_connections == 16
        assert base.model_dump(exclude={"max_connections"}) == expanded.model_dump(
            exclude={"max_connections"}
        )
    with pytest.raises(ValueError, match="connection limit"):
        cc._execution_config("openai_generation", "target", "prompt", 12288, max_connections=32)


def test_task15t_larger_output_is_only_explicit_v6_c() -> None:
    """Recovery expands only the registered C output allowance, not its reasoning."""
    from er_commons import adequacy_binary as core

    version = core.CONCLUSION_STRUCTURED_V6_PROMPT_VERSION
    prompt = core.system_prompt("C", prompt_version=version)
    base = cc._execution_config("openai_generation", "C", prompt, 4096, prompt_version=version)
    larger = cc._execution_config("openai_generation", "C", prompt, 6144, prompt_version=version)
    assert larger.model_dump(exclude={"max_tokens"}) == base.model_dump(exclude={"max_tokens"})
    assert larger.max_tokens == 6144
    for component in "AGSC":
        with pytest.raises(ValueError):
            cc._execution_config("openai_generation", component, prompt, 6144)
    for limit in (6145, 8192):
        with pytest.raises(ValueError):
            cc._execution_config("openai_generation", "C", prompt, limit, prompt_version=version)


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_explicit_high_effort_native_guard(tmp_path: Path, provider: str) -> None:
    """Explicit high controls must match exactly without relaxing other native guards."""
    hook = cc.ReceiptHooks(
        tmp_path,
        provider,
        "m",
        time.monotonic() + 10,
        {"max_output_tokens": 12288},
        expected=cc.expected_delivery("summary+prompt", {"question": "q"}),
        expected_schema={"type": "object"},
        expected_reasoning_effort="high",
    )
    request = native(provider)
    with pytest.raises(ValueError, match="changed"):
        hook._validate_native_controls(request)
    key = "reasoning" if provider == "openai" else "output_config"
    request[key]["effort"] = "high"
    hook._validate_native_controls(request)
    request["tools"] = [{"type": "web_search"}]
    with pytest.raises(ValueError, match="Tools"):
        hook._validate_native_controls(request)


def test_high_effort_config_is_only_target_opt_in() -> None:
    """Keep historical targets and all judges medium while high targets change only effort."""
    for condition in ("openai_generation", "anthropic_generation"):
        base = cc._execution_config(condition, "target", "prompt", 12288)
        high = cc._execution_config(condition, "target", "prompt", 12288, generation_effort="high")
        assert base.reasoning_effort == "medium"
        assert high.reasoning_effort == "high"
        assert base.model_dump(exclude={"reasoning_effort"}) == high.model_dump(
            exclude={"reasoning_effort"}
        )
    for component in ("A", "G", "S", "C"):
        with pytest.raises(ValueError, match="only for target"):
            cc._execution_config(
                "openai_generation", component, "prompt", 4096, generation_effort="high"
            )


def test_16k_target_requires_high_anthropic() -> None:
    """The enlarged target budget is registered only for high Anthropic generation."""
    high = cc._execution_config(
        "anthropic_generation", "target", "prompt", 16384, generation_effort="high"
    )
    assert high.max_tokens == 16384
    for condition, effort, tokens in (
        ("openai_generation", "high", 16384),
        ("anthropic_generation", "medium", 16384),
        ("anthropic_generation", "high", 16385),
    ):
        with pytest.raises(ValueError, match="Unregistered target"):
            cc._execution_config(condition, "target", "prompt", tokens, generation_effort=effort)
