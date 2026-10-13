"""Invented provider allowance experiments preserve caps without exact-count claims."""

import asyncio
import json
from decimal import Decimal

import pytest
from test_grounding_comparison_inspect import envelopes
from test_grounding_comparison_providers import CONDITIONS
from test_grounding_inspect import sample

from er_commons import grounding_comparison_inspect as runner
from er_commons import grounding_comparison_semantics as semantics
from er_commons.grounding_comparison_safety import RunBudget, provider_allowance_preflight


def condition(provider="fireworks_glm"):
    """Use the explicitly authorized identities with native medium controls."""
    original = CONDITIONS[provider]
    settings = {"reasoning_effort": "medium"}
    if provider in {"fireworks_glm", "fireworks_deepseek"}:
        settings["fireworks_reasoning_mode"] = "prompt_schema"
    return original.model_copy(update={"settings": settings})


def budget():
    """Share reservations across independent stage invocations."""
    return RunBudget("10", 3, 12288, 60)


@pytest.mark.parametrize("provider", ["fireworks_glm", "anthropic_generation"])
def test_larger_output_exception_does_not_expand_other_providers(provider):
    """The new allowance applies only to the pinned DeepSeek identity."""
    with pytest.raises(ValueError, match="authorized medium"):
        runner.require_provider_allowance(
            condition(provider).model_copy(update={"output_cap": 8192})
        )


@pytest.mark.parametrize("output_tokens", [6000, 8193])
def test_deepseek_larger_output_reserves_and_enforces_native_limit(
    tmp_path, monkeypatch, output_tokens
):
    """Reserve the larger cap while rejecting actual usage above that same cap."""
    c = condition("fireworks_deepseek").model_copy(update={"output_cap": 8192})
    fixture = envelopes(c)["fixture"]["P2"]
    fixture["model"] = c.model
    fixture["usage"]["completion_tokens"] = output_tokens

    async def post(*args):
        return fixture

    monkeypatch.setattr(runner, "_post", post)
    monkeypatch.setenv("FIREWORKS_API_KEY", "offline-test-placeholder")
    b = budget()
    result = asyncio.run(
        runner.run_comparison_stage(
            c,
            "point",
            semantics.point_inputs(sample().packet)[0],
            tmp_path / "one",
            b,
            exploratory_provider_allowance=True,
        )
    )
    intent = json.loads((tmp_path / "one" / "intent.json").read_text())
    assert intent["preflight"]["output_reserve"] == 8192
    assert b.output_reserved == 8192
    assert (result["status"] == "validated") == (output_tokens <= 8192)
    assert (b.halt_reason is None) == (output_tokens <= 8192)


def test_allowance_bytes_estimate_and_strict_context_boundary():
    request = {"body": {"text": "é"}}
    base = provider_allowance_preflight(request, {}, context_limit=400000, output_reserve=4096)
    assert base["body_bytes"] == len(
        json.dumps(request["body"], ensure_ascii=False, separators=(",", ":")).encode()
    )
    assert base["input_allowance"] == base["body_bytes"] + 8192
    high = provider_allowance_preflight(
        request, {}, context_limit=400000, output_reserve=4096, estimated_tokens=180000
    )
    assert high["input_allowance"] == 200048
    assert not high["dispatch_allowed"]
    assert high["input_tokens"] is None and high["exact_preflight"] is False


@pytest.mark.parametrize("estimate", [-1, True, 1.5])
def test_invalid_estimate_rejected(estimate):
    with pytest.raises(ValueError):
        provider_allowance_preflight(
            {"body": {}}, {}, context_limit=200000, output_reserve=4096, estimated_tokens=estimate
        )


@pytest.mark.parametrize("provider", ["fireworks_glm", "anthropic_generation"])
def test_positive_reservation_and_bound_counter_receipt(tmp_path, monkeypatch, provider):
    c = condition(provider)
    fixture = envelopes(c)["fixture"]["P2"]
    b = budget()
    result = asyncio.run(
        runner.run_comparison_stage(
            c,
            "point",
            semantics.point_inputs(sample().packet)[0],
            tmp_path / "one",
            b,
            fixture=fixture,
            exploratory_provider_allowance=True,
        )
    )
    assert result["status"] == "validated"
    assert b.currency_reserved > Decimal(0)
    intent = json.loads((tmp_path / "one" / "intent.json").read_text())
    assert intent["preflight"]["input_allowance"] > 8192
    assert intent["preflight"]["exact_preflight"] is False
    if provider == "anthropic_generation":
        assert intent["preflight"]["estimated_count_response"] == {"input_tokens": 100}


def test_native_bound_failure_halts_next_stage_without_transport(tmp_path, monkeypatch):
    c = condition()
    native = envelopes(c)["fixture"]["P2"]
    native["model"] = c.model
    native["usage"]["prompt_tokens"] = 999999
    calls = []

    async def post(*args):
        calls.append(args[0])
        return native

    monkeypatch.setattr(runner, "_post", post)
    monkeypatch.setattr(runner, "_headers", lambda c: {})
    b = budget()

    async def run():
        return [
            await runner.run_comparison_stage(
                c,
                "point",
                semantics.point_inputs(sample().packet)[0],
                tmp_path / name,
                b,
                exploratory_provider_allowance=True,
            )
            for name in ["one", "two"]
        ]

    first, second = asyncio.run(run())
    assert first["status"] == "provider_input_allowance_exceeded"
    assert first["usage"]["input_tokens"] == 999999
    assert second["status"] == "run_halted"
    assert len(calls) == 1 and b.requests_reserved == 1


def test_old_cloud_mode_still_blocks_and_wrong_identity_rejected(tmp_path):
    c = condition()
    payload = semantics.point_inputs(sample().packet)[0]
    assert (
        asyncio.run(runner.run_comparison_stage(c, "point", payload, tmp_path / "old", budget()))[
            "status"
        ]
        == "context_unverified"
    )
    with pytest.raises(ValueError):
        asyncio.run(
            runner.run_comparison_stage(
                c.model_copy(update={"model": "other"}),
                "point",
                payload,
                tmp_path / "wrong",
                budget(),
                exploratory_provider_allowance=True,
            )
        )


def test_anthropic_estimate_is_not_exact_and_usage_includes_cache(tmp_path, monkeypatch):
    c = condition("anthropic_generation")
    native = envelopes(c)["fixture"]["P2"]
    native["model"] = c.model
    native["usage"] = {
        "input_tokens": 90,
        "cache_read_input_tokens": 20,
        "cache_creation_input_tokens": 30,
        "output_tokens": 20,
    }
    calls = []

    async def post(endpoint, body, headers, timeout):
        calls.append((endpoint, body))
        return {"input_tokens": 125} if endpoint.endswith("count_tokens") else native

    monkeypatch.setattr(runner, "_post", post)
    monkeypatch.setattr(runner, "_headers", lambda c: {})
    result = asyncio.run(
        runner.run_comparison_stage(
            c,
            "point",
            semantics.point_inputs(sample().packet)[0],
            tmp_path / "one",
            budget(),
            exploratory_provider_allowance=True,
        )
    )
    assert result["status"] == "validated"
    assert result["usage"]["input_tokens"] == 140
    assert result["estimated_native_delta"] == 15
    assert len(calls) == 2
    intent = json.loads((tmp_path / "one" / "intent.json").read_text())
    counter = intent["preflight"]["estimated_count_request"]
    assert counter["counted_request_sha256"] == result["request_sha256"]
    assert counter["body"]["messages"] == calls[1][1]["messages"]


def test_overflow_and_request_cap_stop_before_counter_or_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "_headers", lambda c: pytest.fail("credential access"))
    c = condition("anthropic_generation")
    payload = semantics.point_inputs(sample().packet)[0]
    b = budget()
    result = asyncio.run(
        runner.run_comparison_stage(
            c,
            "point",
            payload,
            tmp_path / "overflow",
            b,
            exploratory_provider_allowance=True,
            prompt_override="x" * 210000,
        )
    )
    assert result["status"] == "context_allowance_overflow"
    assert b.requests_reserved == 0
    b = budget()
    b.requests_reserved = b.request_cap
    result = asyncio.run(
        runner.run_comparison_stage(
            c, "point", payload, tmp_path / "cap", b, exploratory_provider_allowance=True
        )
    )
    assert result["status"] == "request_cap"


@pytest.mark.parametrize("problem", ["output", "malformed"])
def test_native_output_or_semantic_failure_preserves_usage_and_halts(
    tmp_path, monkeypatch, problem
):
    c = condition()
    native = envelopes(c)["fixture"]["P2"]
    native["model"] = c.model
    if problem == "output":
        native["usage"]["completion_tokens"] = 4097
    else:
        native["choices"][0]["message"]["content"] = "not json"

    async def post(*args):
        return native

    monkeypatch.setattr(runner, "_post", post)
    monkeypatch.setattr(runner, "_headers", lambda c: {})
    b = budget()
    result = asyncio.run(
        runner.run_comparison_stage(
            c,
            "point",
            semantics.point_inputs(sample().packet)[0],
            tmp_path / "one",
            b,
            exploratory_provider_allowance=True,
        )
    )
    assert result["status"] != "validated"
    assert result["usage"]
    assert b.halt_reason == result["status"]
    assert b.currency_reserved > 0


def test_haiku_tier_reservations_cover_full_five_minute_write_price():
    from er_commons.grounding_comparison_safety import provider_allowance_rates, worst_case_cost

    c = condition("anthropic_generation").model_dump(mode="json")
    body = {"system": [{"cache_control": {"type": "ephemeral", "ttl": "5m"}}]}
    low = provider_allowance_rates(c, 100000, body)
    high = provider_allowance_rates(c, 100001, body)
    assert low["cache_write"] == Decimal("0.125")
    assert high["cache_write"] == Decimal("0.625")
    assert high["output"] == Decimal("2.5")
    assert worst_case_cost(100000, 4096, low) == Decimal("0.014548")
    body["system"][0]["cache_control"]["ttl"] = "1h"
    with pytest.raises(ValueError, match="five-minute"):
        provider_allowance_rates(c, 100000, body)
    c["pricing"]["input_per_million"] = 0.2
    with pytest.raises(ValueError, match="reviewed pricing"):
        provider_allowance_rates(c, 100000, {})


def test_transport_total_deadline_is_secret_safe(monkeypatch):
    class SlowClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, *args, **kwargs):
            await asyncio.sleep(1)
            raise AssertionError("deadline should cancel before returning")

    monkeypatch.setattr(runner.httpx, "AsyncClient", SlowClient)
    with pytest.raises(ValueError, match="Transport outcome uncertain"):
        asyncio.run(runner._post("https://example.invalid", {}, {}, 0.001))


@pytest.mark.parametrize("failure", ["timeout", "status", "redirect", "json", "shape"])
def test_transport_errors_are_typed_and_secret_safe(monkeypatch, failure):
    """No remote URL, body, header or exception content leaks into persisted failures."""
    import httpx

    original = httpx.AsyncClient

    def handler(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("SECRET", request=request)
        if failure == "status":
            return httpx.Response(403, text="SECRET")
        if failure == "redirect":
            return httpx.Response(302, headers={"location": "https://SECRET.invalid"})
        if failure == "json":
            return httpx.Response(200, text="SECRET")
        return httpx.Response(200, json=["SECRET"])

    def client(**kwargs):
        return original(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(runner.httpx, "AsyncClient", client)
    with pytest.raises(runner.ProviderTransportError) as error:
        asyncio.run(runner._post("https://example.invalid?key=SECRET", {}, {"x-key": "SECRET"}, 1))
    assert "SECRET" not in str(error.value)
    assert error.value.status == ("credential_error" if failure == "status" else "transport_error")
