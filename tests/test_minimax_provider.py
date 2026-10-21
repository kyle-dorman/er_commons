"""Offline native fixtures for the separately scoped MiniMax condition."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import httpx2 as httpx
import pytest

from er_commons import minimax_provider as provider
from er_commons.context_comparison import expected_delivery
from er_commons.locked_dispatch import LockedDispatcher
from er_commons.target_generation import output_schema


def answer() -> dict[str, Any]:
    """An invented valid abstention with no evidence or semantic repair."""
    return {
        "status": "abstained",
        "conclusion": {
            "point_id": "C1",
            "text": "Insufficient evidence.",
            "citation_ids": [],
            "applies_to": [],
        },
        "supporting_points": [],
        "qualifications": [],
        "optional_context": [],
    }


def response(content: str | None = None, **changes: Any) -> dict[str, Any]:
    """Build independently controlled provider identity, usage and completion fields."""
    return {
        "id": "fixture-response",
        "object": "chat.completion",
        "created": 1,
        "model": provider.MODEL,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content or json.dumps(answer())},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 30, "completion_tokens": 25, "total_tokens": 55},
        **changes,
    }


def execute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: dict[str, Any], status: int = 200
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Run the actual Inspect path through a fake wire and a real persistent ledger."""
    requests: list[dict[str, Any]] = []

    async def fake(request: httpx.Request) -> httpx.Response:
        """Capture the actual body while returning no real remote response."""
        requests.append(json.loads(request.content))
        return httpx.Response(status, json=body, request=request)

    monkeypatch.setenv("OLLAMA_API_KEY", "credential-must-not-appear")
    monkeypatch.setattr(provider, "PROMOTION_END", time.time() + 3600)
    monkeypatch.setattr(httpx, "AsyncHTTPTransport", lambda **kwargs: httpx.MockTransport(fake))

    async def run() -> tuple[dict[str, Any], dict[str, Any]]:
        """Execute one slot under the same gate used by production generation."""
        directory = tmp_path / "generation"
        directory.mkdir()
        with LockedDispatcher(tmp_path / "ledger") as dispatcher:
            result = await provider.generate_one(
                {"payload": {"question": "Invented question", "passages": []}},
                directory,
                "minimax_cloud",
                "Frozen instruction",
                time.monotonic() + 60,
                {"run_id": "fixture", "case_id": "C041", "repeat": 1},
                dispatcher,
                "fixture-slot",
                {},
            )
            return result, dispatcher.snapshot()

    result, snapshot = asyncio.run(run())
    for path in tmp_path.rglob("*"):
        if path.is_file():
            assert "credential-must-not-appear" not in path.read_text()
    return result, requests, snapshot


def test_native_schema_and_delivery(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Inspect emits exact schema/messages and settlement follows verified usage."""
    result, requests, ledger = execute(tmp_path, monkeypatch, response())
    assert result["status"] == "valid"
    assert result["generation_calls"] == 1 and result["count_calls"] == 0
    assert len(requests) == 1
    assert requests[0]["response_format"]["json_schema"]["schema"] == output_schema()
    assert requests[0]["reasoning_effort"] == "medium"
    assert requests[0]["max_tokens"] == 12288
    assert "temperature" not in requests[0]
    delivered = json.loads((tmp_path / "generation/delivery_projection.json").read_text())
    assert delivered == expected_delivery(
        "Frozen instruction", {"question": "Invented question", "passages": []}
    )
    assert ledger["liability_usd"] == "0"
    assert result["candidate_id"] and (tmp_path / "generation/completion.json").exists()


@pytest.mark.parametrize("status", [400, 429, 500])
def test_no_http_retries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: int) -> None:
    """SDK errors retain one full reservation and never trigger another wire attempt."""
    result, requests, ledger = execute(
        tmp_path, monkeypatch, {"error": {"message": "fixture", "type": "fixture"}}, status
    )
    assert len(requests) == result["generation_calls"] == 1
    assert result["status"] == "execution_error"
    assert ledger["liability_usd"] == str(provider.RESERVE_USD)
    assert bool(ledger["stop_reason"]) == (status != 429)
    assert result["rate_limited"] == (status == 429)


@pytest.mark.parametrize(
    "changes",
    [
        {"model": "wrong-model"},
        {"usage": {"prompt_tokens": 100001, "completion_tokens": 1, "total_tokens": 100002}},
        {"usage": {"prompt_tokens": 1, "completion_tokens": 12289, "total_tokens": 12290}},
        {"usage": {"prompt_tokens": True, "completion_tokens": 1, "total_tokens": 2}},
    ],
)
def test_usage_and_identity_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changes: dict[str, Any]
) -> None:
    """Wrong identity or invalid native usage cannot settle as free promotional usage."""
    result, requests, ledger = execute(tmp_path, monkeypatch, response(**changes))
    assert len(requests) == 1
    assert result["status"] == "execution_error"
    assert ledger["liability_usd"] == str(provider.RESERVE_USD)
    assert ledger["stop_reason"]


def test_markdown_is_not_repaired(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A schema-shaped JSON fence remains invalid and raw output is preserved."""
    raw = "```json\n" + json.dumps(answer()) + "\n```"
    result, _, ledger = execute(tmp_path, monkeypatch, response(raw))
    assert result["status"] == "invalid_output"
    assert (tmp_path / "generation/raw_output.txt").read_text() == raw
    assert not (tmp_path / "generation/candidate.json").exists()
    assert ledger["liability_usd"] == "0"


@pytest.mark.parametrize("change", ["prompt", "schema", "sampling", "expiry", "input_bound"])
def test_pre_wire_drift_rejected(
    tmp_path: Path, change: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Native drift, expiry and oversized input are denied before budget admission."""

    async def run() -> None:
        """Exercise the transport's controls independently of Inspect's serializer."""
        with LockedDispatcher(tmp_path / "ledger") as dispatcher:
            wire = provider.BudgetTransport(
                dispatcher, tmp_path, "slot", "instruction", {}, time.monotonic() + 60
            )
            calls = []

            async def fake(request: httpx.Request) -> httpx.Response:
                """Record any forbidden wire call."""
                calls.append(request)
                return httpx.Response(200, json=response(), request=request)

            wire.inner = httpx.MockTransport(fake)
            native: dict[str, Any] = {
                "model": provider.MODEL,
                "max_tokens": 12288,
                "reasoning_effort": "medium",
                "messages": [
                    {"role": "system", "content": "instruction"},
                    {"role": "user", "content": "{}"},
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": provider.SCHEMA_NAME,
                        "schema": output_schema(),
                        "description": None,
                        "strict": None,
                    },
                },
            }
            monkeypatch.setattr(provider, "PROMOTION_END", time.time() + 3600)
            if change == "prompt":
                native["messages"][0]["content"] = "changed"
            elif change == "schema":
                native["response_format"]["json_schema"]["schema"] = {}
            elif change == "sampling":
                native["temperature"] = 0
            elif change == "expiry":
                monkeypatch.setattr(provider, "PROMOTION_END", time.time() + 899)
            else:
                native["messages"][0]["content"] = "x" * 100000
                wire.expected = expected_delivery("x" * 100000, {})
            with pytest.raises(ValueError):
                await wire.handle_async_request(
                    httpx.Request("POST", provider.ENDPOINT, json=native)
                )
            assert not calls
            assert dispatcher.snapshot()["counts"]["generation"] == 0
            await wire.aclose()

    asyncio.run(run())
