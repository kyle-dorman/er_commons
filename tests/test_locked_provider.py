"""Invented native HTTP fixtures for Task 13's shared provider admission boundary."""

from __future__ import annotations

import asyncio
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx2 as httpx
import pytest

from er_commons.locked_dispatch import DispatchStopped, LockedDispatcher
from er_commons.locked_provider import BudgetTransport


@pytest.fixture
def pricing() -> dict[str, Any]:
    """Use invented rates with simple independently computable costs."""
    return {
        provider: {
            "verified": True,
            "model": "fixture-model",
            "count_max_usd": "0.002",
            "input_max_per_million": "2",
            "worst_request_input_tokens": 100000,
            "reserve_input_per_million": "2",
            "reserve_output_per_million": "4",
            "input_per_million": "1",
            "output_per_million": "4",
            "cache_read_per_million": "0.1",
            "cache_write_per_million": "2",
        }
        for provider in ("openai", "anthropic")
    }


class FixtureTransport(httpx.AsyncBaseTransport):
    """Return invented wire responses and measure actual shared network overlap."""

    def __init__(self, status: int = 200, body: dict[str, Any] | None = None) -> None:
        self.status = status
        self.body = body
        self.calls = 0
        self.active = 0
        self.peak = 0

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Yield during the simulated wire operation to expose concurrency bugs."""
        self.calls += 1
        self.active += 1
        self.peak = max(self.peak, self.active)
        await asyncio.sleep(0.005)
        self.active -= 1
        count = request.url.path.endswith(("input_tokens", "count_tokens"))
        body = (
            self.body
            if self.body is not None
            else (
                {"input_tokens": 20}
                if count
                else {
                    "model": "fixture-model",
                    "usage": {"input_tokens": 20, "output_tokens": 10},
                }
            )
        )
        return httpx.Response(self.status, json=body, request=request)


def native(provider: str = "openai", *, count: bool = False) -> httpx.Request:
    """Construct one reference-free invented native request."""
    path = (
        ("responses/input_tokens" if count else "responses")
        if provider == "openai"
        else ("messages/count_tokens" if count else "messages")
    )
    body = {"model": "fixture-model", "input": "Invented fixture"}
    if not count:
        body["max_output_tokens" if provider == "openai" else "max_tokens"] = 100
    return httpx.Request("POST", f"https://api.{provider}.com/v1/{path}", json=body)


def wire(
    dispatcher: LockedDispatcher,
    directory: Path,
    pricing: dict[str, Any],
    fixture: FixtureTransport,
    slot: str = "slot",
) -> BudgetTransport:
    """Attach a mock wire without credentials or a network connection."""
    directory.mkdir(exist_ok=True)
    result = BudgetTransport(dispatcher, slot, directory, "target", pricing)
    result.inner = fixture  # type: ignore[assignment]
    return result


def test_unknown_billing_denies_count_before_wire(tmp_path: Path, pricing: dict[str, Any]) -> None:
    """Unknown counter charges cannot be assumed free even for a first count."""
    pricing["openai"]["count_max_usd"] = None
    fixture = FixtureTransport()

    async def run() -> None:
        with LockedDispatcher(tmp_path / "ledger") as dispatcher:
            transport = wire(dispatcher, tmp_path / "generation", pricing, fixture)
            with pytest.raises(ValueError, match="Unbounded"):
                await transport.handle_async_request(native(count=True))
            assert fixture.calls == 0
            assert dispatcher.snapshot()["counts"] == {"generation": 0, "judge": 0, "count": 0}

    asyncio.run(run())


def test_exact_count_required_before_generation(tmp_path: Path, pricing: dict[str, Any]) -> None:
    """Missing count evidence prevents any paid generation wire operation."""
    fixture = FixtureTransport()

    async def run() -> None:
        with LockedDispatcher(tmp_path / "ledger") as dispatcher:
            transport = wire(dispatcher, tmp_path / "generation", pricing, fixture)
            with pytest.raises(FileNotFoundError):
                await transport.handle_async_request(native())
            assert fixture.calls == 0

    asyncio.run(run())


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_native_usage_and_counter_settlement(
    tmp_path: Path,
    pricing: dict[str, Any],
    provider: str,
) -> None:
    """Every count/generation has a separate exact key and reconciled bounded cost."""
    fixture = FixtureTransport()

    async def run() -> None:
        with LockedDispatcher(tmp_path / "ledger") as dispatcher:
            directory = tmp_path / "generation"
            transport = wire(dispatcher, directory, pricing, fixture)
            count = await transport.handle_async_request(native(provider, count=True))
            (directory / "count_result.json").write_text(json.dumps(count.json()))
            await transport.handle_async_request(native(provider))
            assert dispatcher.snapshot()["counts"] == {"generation": 1, "judge": 0, "count": 1}
            assert dispatcher.liability_usd == Decimal("0.002060")
            reservations = [
                json.loads(p.read_text()) for p in (tmp_path / "ledger").glob("*.reservation.json")
            ]
            from er_commons.artifact_io import sha256_bytes

            assert {r["request_sha256"] for r in reservations} == {
                sha256_bytes(native(provider, count=True).content),
                sha256_bytes(native(provider).content),
            }
            assert (
                next(r for r in reservations if r["kind"] == "count")["parent_key"]
                == "slot/target/generation"
            )
            with pytest.raises(DispatchStopped, match="already attempted"):
                await transport.handle_async_request(native(provider))
            assert fixture.calls == 2

    asyncio.run(run())


def test_count_then_generate_shared_queue_no_deadlock(
    tmp_path: Path,
    pricing: dict[str, Any],
) -> None:
    """A count releases the global slot before its dependent generation acquires it."""
    fixture = FixtureTransport()

    async def run() -> None:
        with LockedDispatcher(tmp_path / "ledger", concurrency=3) as dispatcher:

            async def answer(i: int) -> None:
                directory = tmp_path / str(i)
                transport = wire(dispatcher, directory, pricing, fixture, str(i))
                count = await transport.handle_async_request(native(count=True))
                (directory / "count_result.json").write_text(json.dumps(count.json()))
                await transport.handle_async_request(native())

            await asyncio.wait_for(asyncio.gather(*(answer(i) for i in range(12))), timeout=5)
            assert fixture.peak == 3
            assert fixture.calls == 24
            assert dispatcher.liability_usd == Decimal("0.024720")

    asyncio.run(run())


@pytest.mark.parametrize("status", [429, 500])
def test_http_errors_hold_liability_without_retries(
    tmp_path: Path,
    pricing: dict[str, Any],
    status: int,
) -> None:
    """Returned HTTP errors hold their reservation; 429 also lowers concurrency."""
    fixture = FixtureTransport(status=status, body={"error": "invented"})

    async def run() -> None:
        with LockedDispatcher(tmp_path / "ledger") as dispatcher:
            transport = wire(dispatcher, tmp_path / "generation", pricing, fixture)
            response = await transport.handle_async_request(native(count=True))
            assert response.status_code == status
            assert fixture.calls == 1
            assert dispatcher.liability_usd == Decimal("0.002")
            assert dispatcher.concurrency == (5 if status == 429 else 10)

    asyncio.run(run())


@pytest.mark.parametrize(
    "body",
    [
        {"model": "wrong-model", "usage": {"input_tokens": 20, "output_tokens": 10}},
        {"model": "fixture-model", "usage": {"input_tokens": True, "output_tokens": 10}},
        {"model": "fixture-model", "usage": {"input_tokens": 0, "output_tokens": 10}},
        {"model": "fixture-model", "usage": {"input_tokens": 200001, "output_tokens": 10}},
        {"model": "fixture-model", "usage": {"input_tokens": 20, "output_tokens": -1}},
        {"model": "fixture-model", "usage": {"input_tokens": 20, "output_tokens": 101}},
        {"model": "fixture-model", "usage": {"input_tokens": 20}},
        {
            "model": "fixture-model",
            "usage": {
                "input_tokens": 20,
                "output_tokens": 10,
                "input_tokens_details": {"cached_tokens": 15, "cache_write_tokens": 10},
            },
        },
    ],
    ids=[
        "model",
        "boolean",
        "zero-input",
        "input-cap",
        "negative",
        "output-cap",
        "missing",
        "cache",
    ],
)
def test_unverified_usage_stops_dispatch_and_holds_reserve(
    tmp_path: Path,
    pricing: dict[str, Any],
    body: dict[str, Any],
) -> None:
    """Unverified usage retains the native receipt and full reserve, then stops admission."""
    fixture = FixtureTransport(body=body)

    async def run() -> None:
        with LockedDispatcher(tmp_path / "ledger") as dispatcher:
            directory = tmp_path / "generation"
            transport = wire(dispatcher, directory, pricing, fixture)
            (directory / "count_result.json").write_text('{"input_tokens": 20}')
            await transport.handle_async_request(native())
            assert dispatcher.snapshot()["stop_reason"] == (
                "Unverified model/usage or token cap exceeded"
            )
            assert json.loads((directory / "wire_request_response.body").read_bytes()) == body
            assert dispatcher.liability_usd == Decimal("0.2004")
            assert dispatcher.snapshot()["held_keys"] == ["slot/target/generation"]

    asyncio.run(run())


@pytest.mark.parametrize(
    ("component", "condition", "cap"),
    [
        ("target", "openai_generation", 12288),
        ("target", "anthropic_generation", 12288),
        ("A", "openai_generation", 4096),
        ("G", "openai_generation", 4096),
        ("S", "anthropic_generation", 4096),
        ("C", "openai_generation", 4096),
    ],
)
def test_locked_native_sdk_serializer_offline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    pricing: dict[str, Any],
    component: str,
    condition: str,
    cap: int,
) -> None:
    """Run the real SDK and count hooks through the locked mock-wire budget gate."""
    import time

    from er_commons import locked_provider

    monkeypatch.setenv("OPENAI_API_KEY", "offline-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "offline-test")
    calls: list[str] = []

    class SDKFixture(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            """Count successfully, then return an explicit non-retryable native error."""
            calls.append(str(request.url))
            if request.url.path.endswith(("/input_tokens", "/count_tokens")):
                return httpx.Response(200, json={"input_tokens": 123}, request=request)
            return httpx.Response(
                400,
                json={"error": {"type": "invalid_request_error", "message": "offline boundary"}},
                request=request,
            )

    monkeypatch.setattr(locked_provider.httpx, "AsyncHTTPTransport", lambda **kwargs: SDKFixture())

    async def run() -> None:
        with LockedDispatcher(tmp_path / "ledger") as dispatcher:
            directory = tmp_path / "attempt"
            directory.mkdir()
            result = await locked_provider.execute(
                directory=directory,
                condition=condition,
                component=component,
                prompt="Shared project summary\nFrozen core",
                payload={"question": "offline fixture"},
                deadline=time.monotonic() + 10,
                max_output_tokens=cap,
                dispatcher=dispatcher,
                slot_id="fixture",
                pricing=pricing,
            )
            assert result["count_calls"] == 1 and result["judge_calls"] == 1, result
            assert result["status"] == "execution_error"
            assert len(calls) == 2 and "offline boundary" in result["error"]
            assert (directory / "native_request.json").exists()
            assert (directory / "count_response.body").exists()
            if component == "target":
                from er_commons.artifact_io import stable_json_sha256
                from er_commons.target_generation import REPO

                frozen = json.loads(
                    (REPO / "docs/specs/task11e_frozen_generation_v1.json").read_text()
                )
                payload = json.loads((directory / "native_request.json").read_text())
                target = frozen["targets"]["luna" if condition == "openai_generation" else "haiku"]
                schema = (
                    payload["text"]["format"]
                    if condition == "openai_generation"
                    else payload["output_format"]
                )
                assert payload["model"] == target["model"]
                assert stable_json_sha256(schema) == target["native_schema_sha256"]
            assert dispatcher.snapshot()["counts"]["count"] == 1
            assert len(dispatcher.snapshot()["held_keys"]) == 1

    asyncio.run(run())


def test_native_budget_denial_does_not_report_a_wire_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pricing: dict[str, Any]
) -> None:
    """Prepared hook intents remain distinct from actual remote admissions."""
    from er_commons import locked_provider

    monkeypatch.setenv("OPENAI_API_KEY", "offline-test")
    fixture = FixtureTransport()
    monkeypatch.setattr(locked_provider.httpx, "AsyncHTTPTransport", lambda **kwargs: fixture)

    async def run() -> None:
        with LockedDispatcher(tmp_path / "ledger", cap_usd=Decimal("0.001")) as dispatcher:
            directory = tmp_path / "attempt"
            directory.mkdir()
            result = await locked_provider.execute(
                directory=directory,
                condition="openai_generation",
                component="target",
                prompt="Frozen fixture",
                payload={"question": "Invented fixture"},
                deadline=float("inf"),
                max_output_tokens=12288,
                dispatcher=dispatcher,
                slot_id="fixture",
                pricing=pricing,
            )
            assert result["status"] == "execution_error"
            assert result["count_calls"] == result["judge_calls"] == 0
            assert fixture.calls == 0
            assert dispatcher.liability_usd == Decimal("0")

    asyncio.run(run())


@pytest.mark.parametrize(
    ("provider", "usage"),
    [
        (
            "openai",
            {
                "input_tokens": 100,
                "output_tokens": 10,
                "input_tokens_details": {"cached_tokens": 20, "cache_write_tokens": 30},
            },
        ),
        (
            "anthropic",
            {
                "input_tokens": 50,
                "output_tokens": 10,
                "cache_read_input_tokens": 20,
                "cache_creation_input_tokens": 30,
            },
        ),
    ],
)
def test_native_cache_write_accounting(
    tmp_path: Path, pricing: dict[str, Any], provider: str, usage: dict[str, Any]
) -> None:
    """Both providers bill cache reads/writes separately despite different input totals."""
    fixture = FixtureTransport(body={"model": "fixture-model", "usage": usage})

    async def run() -> None:
        with LockedDispatcher(tmp_path / "ledger") as dispatcher:
            directory = tmp_path / "generation"
            transport = wire(dispatcher, directory, pricing, fixture)
            (directory / "count_result.json").write_text('{"input_tokens": 100}')
            await transport.handle_async_request(native(provider))
            # 50 ordinary * 1 + 20 reads * .1 + 30 writes * 2 + 10 output * 4.
            assert dispatcher.liability_usd == Decimal("0.000152")

    asyncio.run(run())


def test_malformed_native_body_is_preserved_before_cost_parsing(
    tmp_path: Path, pricing: dict[str, Any]
) -> None:
    """Non-JSON success responses retain exact bytes and the full uncertain liability."""
    body = b"upstream returned malformed JSON\x00\xff"

    class MalformedTransport(FixtureTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            """Return uninterpretable bytes with safe and secret-like fixture headers."""
            self.calls += 1
            return httpx.Response(
                200,
                content=body,
                request=request,
                headers={"x-request-id": "fixture-request", "authorization": "must-not-save"},
            )

    async def run() -> None:
        with LockedDispatcher(tmp_path / "ledger") as dispatcher:
            directory = tmp_path / "generation"
            fixture = MalformedTransport()
            transport = wire(dispatcher, directory, pricing, fixture)
            (directory / "count_result.json").write_text('{"input_tokens": 20}')
            with pytest.raises((ValueError, UnicodeDecodeError)):
                await transport.handle_async_request(native())
            assert (directory / "wire_request_response.body").read_bytes() == body
            assert json.loads((directory / "wire_request_response.json").read_text()) == {
                "status_code": 200,
                "request_id": "fixture-request",
            }
            assert fixture.calls == 1
            assert dispatcher.liability_usd == Decimal("0.2004")
            assert dispatcher.snapshot()["held_keys"] == ["slot/target/generation"]

    asyncio.run(run())


def test_accepted_unknown_count_preserves_unknown_actual_and_allows_generation(
    tmp_path: Path, pricing: dict[str, Any]
) -> None:
    """Accepted uncertainty is explicit on wire and ledger receipts, including resume."""
    configured = json.loads(Path("configs/task13_pricing_v1.json").read_text())["openai"]
    pricing["openai"].update(
        verified=False,
        generation_rates_verified=True,
        count_max_usd=None,
        count_fee_exception=configured["count_fee_exception"],
    )
    fixture = FixtureTransport()

    async def run() -> None:
        with LockedDispatcher(tmp_path / "ledger") as dispatcher:
            directory = tmp_path / "generation"
            transport = wire(dispatcher, directory, pricing, fixture)
            count = await transport.handle_async_request(native(count=True))
            (directory / "count_result.json").write_text(json.dumps(count.json()))
            await transport.handle_async_request(native())
            assert dispatcher.liability_usd == Decimal("0.000060")
            assert dispatcher.snapshot()["accepted_unknown_count_keys"] == ["slot/target/count"]
            assert dispatcher.snapshot()["held_keys"] == ["slot/target/count"]
            assert dispatcher.snapshot()["uncertain_keys"] == []
            wire_receipt = json.loads((directory / "wire_count_response.json").read_text())
            assert wire_receipt["count_fee_exception"]["actual_fee_usd"] is None
            settlements = [
                json.loads(p.read_text()) for p in (tmp_path / "ledger").glob("*.settlement.json")
            ]
            assert any(s["actual_cost_usd"] is None for s in settlements)
        with LockedDispatcher(tmp_path / "ledger") as resumed:
            assert resumed.snapshot()["accepted_unknown_count_keys"] == ["slot/target/count"]
            assert resumed.liability_usd == Decimal("0.000060")
            again = wire(resumed, tmp_path / "second", pricing, fixture)
            with pytest.raises(DispatchStopped, match="already attempted"):
                await again.handle_async_request(native(count=True))
            assert fixture.calls == 2

    asyncio.run(run())


@pytest.mark.parametrize(
    "policy, connections",
    [("task13", 1), ("task15s", 16), ("task15t", 16), ("task15v", 16), ("task15w", 16)],
)
def test_execute_forwards_explicit_conclusion_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, policy: str, connections: int
) -> None:
    """Validate opt-in propagation before any provider or budget activity is possible."""
    from types import SimpleNamespace

    from er_commons import adequacy_binary as core
    from er_commons import locked_provider as provider

    captured = {}

    def capture(*args, **kwargs):
        captured.update(kwargs)
        raise ValueError("offline configuration boundary")

    monkeypatch.setattr(provider, "_execution_config", capture)
    version = core.CONCLUSION_STRUCTURED_V6_PROMPT_VERSION
    with pytest.raises(ValueError, match="offline configuration boundary"):
        asyncio.run(
            provider.execute(
                directory=tmp_path,
                condition="openai_generation",
                component="C",
                prompt=core.system_prompt("C", prompt_version=version),
                payload={},
                deadline=1,
                max_output_tokens=4096,
                dispatcher=SimpleNamespace(policy_version=policy),
                slot_id="offline",
                pricing={},
                prompt_version=version,
            )
        )
    assert captured == {
        "prompt_version": version,
        "max_connections": connections,
        "generation_effort": "medium",
    }


def test_generation_attempt_two_requires_recovery_policy(tmp_path: Path, monkeypatch) -> None:
    """Preserve retry identity without allowing historical automatic retries."""
    from types import SimpleNamespace

    from er_commons import locked_provider as provider

    async def fake_execute(**kwargs):
        return {"status": "execution_error", "judge_calls": 1}

    monkeypatch.setattr(provider, "execute", fake_execute)
    args = (
        {"payload": {}},
        tmp_path,
        "openai_generation",
        "prompt",
        1,
        {"run_id": "recovery", "case_id": "C008", "repeat": 1},
    )
    for policy in ("task13", "task15s"):
        with pytest.raises(ValueError, match="recovery policy"):
            asyncio.run(
                provider.generate_one(
                    *args, SimpleNamespace(policy_version=policy), "slot", {}, attempt=2
                )
            )
    result = asyncio.run(
        provider.generate_one(
            *args, SimpleNamespace(policy_version="task15t"), "slot", {}, attempt=2
        )
    )
    assert result["attempt"] == 2
    assert result["generation_calls"] == 1
    assert (tmp_path / "completion.json").exists()


@pytest.mark.parametrize(
    "policy, component, allowed",
    [
        ("task15v", "target", True),
        ("task15t", "target", False),
        ("task15s", "target", False),
        ("task13", "target", False),
        ("task15v", "C", False),
    ],
)
def test_high_effort_requires_explicit_target_policy(
    tmp_path: Path, monkeypatch, policy, component, allowed
) -> None:
    """Deny high judge or historical requests before any native dispatch."""
    from types import SimpleNamespace

    from er_commons import locked_provider as provider

    def capture(*args, **kwargs):
        assert kwargs["generation_effort"] == "high"
        assert kwargs["max_connections"] == 16
        raise ValueError("offline configuration boundary")

    monkeypatch.setattr(provider, "_execution_config", capture)
    with pytest.raises(
        ValueError, match="offline configuration boundary" if allowed else "Task15V target policy"
    ):
        asyncio.run(
            provider.execute(
                directory=tmp_path,
                condition="openai_generation",
                component=component,
                prompt="prompt",
                payload={},
                deadline=1,
                max_output_tokens=12288,
                dispatcher=SimpleNamespace(policy_version=policy),
                slot_id="offline",
                pricing={},
                generation_effort="high",
            )
        )


@pytest.mark.parametrize(
    "policy, condition, effort, tokens, allowed",
    [
        ("task15w", "anthropic_generation", "high", 16384, True),
        ("task15v", "anthropic_generation", "high", 16384, False),
        ("task15w", "openai_generation", "high", 16384, False),
        ("task15w", "anthropic_generation", "medium", 16384, False),
        ("task15w", "anthropic_generation", "high", 12288, False),
    ],
)
def test_16k_native_policy_guard(
    tmp_path, monkeypatch, policy, condition, effort, tokens, allowed
) -> None:
    """Reject broadened provider, effort or output scope before constructing a client."""
    from types import SimpleNamespace

    from er_commons import locked_provider as provider

    def capture(*args, **kwargs):
        assert args[3] == 16384
        assert kwargs["generation_effort"] == "high"
        assert kwargs["max_connections"] == 16
        raise ValueError("offline boundary")

    monkeypatch.setattr(provider, "_execution_config", capture)
    with pytest.raises(ValueError, match="offline boundary" if allowed else "16K target"):
        asyncio.run(
            provider.execute(
                directory=tmp_path,
                condition=condition,
                component="target",
                prompt="prompt",
                payload={},
                deadline=1,
                max_output_tokens=tokens,
                dispatcher=SimpleNamespace(policy_version=policy),
                slot_id="offline",
                pricing={},
                generation_effort=effort,
            )
        )


def test_task15w_attempt_and_output_propagation(tmp_path, monkeypatch) -> None:
    """Require second attempt and carry its explicit limit without changing defaults."""
    from types import SimpleNamespace

    from er_commons import locked_provider as provider

    async def fake_execute(**kwargs):
        assert kwargs["max_output_tokens"] == 16384
        assert kwargs["generation_effort"] == "high"
        return {"status": "execution_error", "judge_calls": 1}

    monkeypatch.setattr(provider, "execute", fake_execute)
    args = (
        {"payload": {}},
        tmp_path,
        "anthropic_generation",
        "prompt",
        1,
        {"run_id": "recovery", "case_id": "C014", "repeat": 1},
        SimpleNamespace(policy_version="task15w"),
        "slot",
        {},
    )
    with pytest.raises(ValueError, match="second attempt"):
        asyncio.run(provider.generate_one(*args, generation_effort="high", max_output_tokens=16384))
    result = asyncio.run(
        provider.generate_one(*args, attempt=2, generation_effort="high", max_output_tokens=16384)
    )
    assert result["attempt"] == 2
    assert result["generation_calls"] == 1
