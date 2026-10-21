"""Locked native execution with a single persistent remote-request budget gate."""

from __future__ import annotations

import asyncio
import json
import time
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import httpx2 as httpx
from inspect_ai.model import ChatMessageSystem, ChatMessageUser

from er_commons import judge_inspect
from er_commons.artifact_io import (
    artifact_inventory,
    publish_bytes_no_clobber,
    sha256_bytes,
    sha256_file,
    stable_json_sha256,
)
from er_commons.context_comparison import (
    MAX_INPUT_TOKENS,
    REQUEST_TIMEOUT_SECONDS,
    TARGET_OUTPUT_TOKENS,
    ReceiptHooks,
    _execution_config,
    _expected_schema,
    delivery,
    expected_delivery,
)
from er_commons.locked_dispatch import Kind, LockedDispatcher, Request
from er_commons.locked_pricing import accepted_count_fee, bounded_or_accepted, count_reservation
from er_commons.target_generation import save, validate_answer


def _generation_cost(
    body: dict[str, Any], provider: str, rates: dict[str, Any], output_limit: int
) -> Decimal | None:
    """Price verified native usage, returning None for model or token-limit mismatches."""
    usage = body.get("usage", {})
    effective = usage.get("input_tokens")
    emitted = usage.get("output_tokens")
    if provider == "openai":
        read = usage.get("input_tokens_details", {}).get("cached_tokens", 0)
        write = usage.get("input_tokens_details", {}).get("cache_write_tokens", 0)
    else:
        read = usage.get("cache_read_input_tokens", 0)
        write = usage.get("cache_creation_input_tokens", 0)
    # Anthropic reports uncached input separately; OpenAI includes cache tokens.
    if provider == "anthropic" and type(effective) is int:
        effective += read + write
    values = (effective, emitted, read, write)
    if (
        body.get("model") != rates["model"]
        or any(type(v) is not int or v < 0 for v in values)
        or not 0 < effective <= MAX_INPUT_TOKENS
        or not emitted <= output_limit
        or read + write > effective
    ):
        return None
    return (
        Decimal(effective - read - write) * Decimal(str(rates["input_per_million"]))
        + Decimal(read) * Decimal(str(rates["cache_read_per_million"]))
        + Decimal(write) * Decimal(str(rates["cache_write_per_million"]))
        + Decimal(emitted) * Decimal(str(rates["output_per_million"]))
    ) / Decimal(1_000_000)


class BudgetTransport(httpx.AsyncBaseTransport):
    """Gate each actual HTTP request after native hooks finish count and parity checks."""

    def __init__(
        self,
        dispatcher: LockedDispatcher,
        slot_id: str,
        directory: Path,
        component: str,
        pricing: dict[str, Any],
        *,
        evaluation_started_at: float | None = None,
    ) -> None:
        """Bind one attempt to the shared ledger; httpx retries are disabled."""
        self.dispatcher = dispatcher
        self.slot_id = slot_id
        self.directory = directory
        self.component = component
        self.pricing = pricing
        self.evaluation_started_at = evaluation_started_at
        self.inner = httpx.AsyncHTTPTransport(retries=0)
        self.dispatched = {"count": 0, "request": 0}
        self.rate_limited = False

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Reserve before wire dispatch and settle only verified bounded usage."""
        native_bytes = await request.aread()
        native = json.loads(native_bytes)
        provider = "openai" if request.url.host == "api.openai.com" else "anthropic"
        if request.url.host not in {"api.openai.com", "api.anthropic.com"}:
            raise ValueError("Unexpected provider endpoint")
        rates = self.pricing[provider]
        if not bounded_or_accepted(provider, rates):
            raise ValueError("Unbounded provider billing: no dispatch permitted")
        is_count = request.url.path.endswith(("/input_tokens", "/count_tokens"))
        unknown_count_fee = is_count and accepted_count_fee(provider, rates)
        if unknown_count_fee and request.url.path != "/v1/responses/input_tokens":
            raise ValueError("Counting-fee exception does not cover this endpoint")
        kind = "count" if is_count else ("generation" if self.component == "target" else "judge")
        key = f"{self.slot_id}/{self.directory.name}/{kind}"
        if self.component == "target":
            key = f"{self.slot_id}/target/{kind}"
        tokens = (
            0
            if is_count
            else json.loads((self.directory / "count_result.json").read_text())["input_tokens"]
        )
        output = 0 if is_count else native.get("max_output_tokens", native.get("max_tokens"))
        reserve = (
            count_reservation(provider, rates)
            if is_count
            else (
                Decimal(rates["worst_request_input_tokens"])
                * Decimal(str(rates["reserve_input_per_million"]))
                + Decimal(output) * Decimal(str(rates["reserve_output_per_million"]))
            )
            / Decimal(1_000_000)
        )
        admission = Request(
            key=key,
            slot_id=self.slot_id,
            kind=cast(Kind, kind),
            maximum_cost_usd=reserve,
            input_tokens=tokens,
            output_tokens=output,
            evaluation_started_at=self.evaluation_started_at,
            parent_key=key.rsplit("/", 1)[0]
            + ("/generation" if self.component == "target" else "/judge")
            if is_count
            else None,
            request_sha256=sha256_bytes(native_bytes),
            accounting_basis="user_accepted_unknown_openai_count_fee"
            if unknown_count_fee
            else None,
        )

        async def operation() -> tuple[httpx.Response, Decimal | None]:
            """Keep the semaphore until the complete body is saved and reconciled."""
            self.dispatched["count" if is_count else "request"] += 1
            response = await self.inner.handle_async_request(request)
            await response.aread()
            prefix = "wire_count" if is_count else "wire_request"
            publish_bytes_no_clobber(self.directory / f"{prefix}_response.body", response.content)
            save(
                self.directory / f"{prefix}_response.json",
                {
                    "status_code": response.status_code,
                    "request_id": response.headers.get("x-request-id")
                    or response.headers.get("request-id"),
                    **(
                        {"count_fee_exception": rates["count_fee_exception"]}
                        if unknown_count_fee
                        else {}
                    ),
                },
            )
            cost = self._response_cost(
                response,
                provider,
                rates,
                is_count=is_count,
                unknown_count_fee=unknown_count_fee,
                output_limit=output,
            )
            return response, cost

        return await self.dispatcher.invoke_async(admission, operation)

    def _response_cost(
        self,
        response: httpx.Response,
        provider: str,
        rates: dict[str, Any],
        *,
        is_count: bool,
        unknown_count_fee: bool,
        output_limit: int,
    ) -> Decimal | None:
        """Reconcile saved responses; failures and unknown fees retain reserved liability."""
        if response.status_code == 429:
            self.rate_limited = True
            self.dispatcher.rate_limit()
        if not response.is_success:
            return None
        if is_count:
            return None if unknown_count_fee else Decimal(str(rates["count_max_usd"]))
        cost = _generation_cost(response.json(), provider, rates, output_limit)
        if cost is None:
            self.dispatcher.stop("Unverified model/usage or token cap exceeded")
        return cost

    async def aclose(self) -> None:
        """Close the underlying connection pool."""
        await self.inner.aclose()


async def execute(
    *,
    directory: Path,
    condition: str,
    component: str,
    prompt: str,
    payload: dict[str, Any],
    deadline: float,
    max_output_tokens: int,
    dispatcher: LockedDispatcher,
    slot_id: str,
    pricing: dict[str, Any],
    evaluation_started_at: float | None = None,
) -> dict[str, Any]:
    """Attempt one native request, count exactly once, retain all failures; never retry."""
    config = _execution_config(condition, component, prompt, max_output_tokens)
    selected = judge_inspect.profile(condition)
    limits = {"max_input_tokens": MAX_INPUT_TOKENS, "max_output_tokens": max_output_tokens}
    expected_schema = _expected_schema(config, selected.provider)
    hooks = ReceiptHooks(
        directory,
        selected.provider,
        selected.model,
        deadline,
        limits,
        expected=expected_delivery(prompt, payload),
        expected_schema=expected_schema,
    )
    result: dict[str, Any] = {
        "status": "execution_error",
        "provider": selected.provider,
        "model": selected.model,
        "component": component,
    }
    client: Any = None
    try:
        if time.monotonic() >= deadline:
            raise ValueError("Global timebox exhausted")
        wire = BudgetTransport(
            dispatcher,
            slot_id,
            directory,
            component,
            pricing,
            evaluation_started_at=evaluation_started_at,
        )
        http_client = httpx.AsyncClient(transport=wire, timeout=REQUEST_TIMEOUT_SECONDS)
        model = judge_inspect.native_model(
            condition, component, prompt, config, streaming=False, http_client=http_client
        )
        client = model.api.client  # type: ignore[attr-defined]
        client.max_retries = 0
        hooks.client = client
        client._client.event_hooks["request"].append(hooks.request)
        client._client.event_hooks["response"].append(hooks.response)
        # Each HTTP attempt owns its timeout. Admission deadlines must not cancel
        # a request already on the wire, including at the six-hour boundary.
        async with asyncio.timeout(2 * REQUEST_TIMEOUT_SECONDS + 60):
            output = await model.generate(
                [
                    ChatMessageSystem(content=prompt),
                    ChatMessageUser(content=json.dumps(payload, ensure_ascii=False)),
                ],
                cache=False,
            )
        save(directory / "inspect_output.json", output.model_dump(mode="json"))
        publish_bytes_no_clobber(directory / "raw_output.txt", output.completion.encode())
        result.update(
            raw_output=output.completion,
            returned_model=output.model,
            response_id=output.response_id,
            usage=output.usage.model_dump(mode="json") if output.usage else None,
        )
        if output.usage is None or output.model != selected.model:
            raise ValueError("Accounting uncertain: returned identity/usage unverified")
        usage = output.usage
        effective = (
            usage.input_tokens
            + (usage.input_tokens_cache_read or 0)
            + (usage.input_tokens_cache_write or 0)
        )
        if (
            not 0 < effective <= MAX_INPUT_TOKENS
            or not 0 <= usage.output_tokens <= max_output_tokens
        ):
            raise ValueError("Accounting uncertain: usage exceeds reserve")
        counted = json.loads((directory / "count_result.json").read_text())["input_tokens"]
        result["accounting"] = {
            "effective_input_tokens": effective,
            "count_input_tokens": counted,
            "count_usage_difference_tokens": effective - counted,
            "actual_count_cost_usd": None,
        }
        result["status"] = "invalid_output" if output.stop_reason != "stop" else "completed"
        if output.stop_reason != "stop":
            result["error"] = f"Noncomplete output: {output.stop_reason}"
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
        causes: list[dict[str, str]] = []
        cause: BaseException | None = error
        while cause is not None and len(causes) < 8:
            causes.append({"type": type(cause).__name__, "message": str(cause)})
            cause = cause.__cause__
        result["failure_causes"] = causes
    finally:
        if client is not None:
            try:
                await client.close()
            except Exception as error:
                # Preserve the request's result and diagnostics even if SDK cleanup fails.
                result["status"] = "execution_error"
                result["cleanup_error"] = f"{type(error).__name__}: {error}"
    counts = wire.dispatched if "wire" in locals() else {"count": 0, "request": 0}
    result.update(count_calls=counts["count"], judge_calls=counts["request"])
    result["prepared_hooks"] = {"count": hooks.count_calls, "request": hooks.judge_calls}
    result["rate_limited"] = wire.rate_limited if "wire" in locals() else False
    return result


async def generate_one(
    record: dict[str, Any],
    directory: Path,
    condition: str,
    prompt: str,
    deadline: float,
    identity: dict[str, Any],
    dispatcher: LockedDispatcher,
    slot_id: str,
    pricing: dict[str, Any],
) -> dict[str, Any]:
    """Validate one candidate while keeping raw output and exact native identity."""
    result = await execute(
        directory=directory,
        condition=condition,
        component="target",
        prompt=prompt,
        payload=record["payload"],
        deadline=deadline,
        max_output_tokens=TARGET_OUTPUT_TOKENS,
        dispatcher=dispatcher,
        slot_id=slot_id,
        pricing=pricing,
    )
    result.update({k: identity[k] for k in ("run_id", "case_id", "repeat")}, attempt=1)
    result["generation_calls"] = result.pop("judge_calls")
    if (directory / "native_request.json").exists():
        result["request_sha256"] = sha256_file(directory / "native_request.json")
        if result["generation_calls"]:
            save(
                directory / "delivery_projection.json",
                delivery(
                    json.loads((directory / "native_request.json").read_text()), result["provider"]
                ),
            )
    if result["status"] == "completed":
        try:
            answer = validate_answer(result["raw_output"], record["payload"])
            save(directory / "candidate.json", answer)
            result.update(
                status="valid", candidate_sha256=sha256_file(directory / "candidate.json")
            )
        except Exception as error:
            result.update(status="invalid_output", error=f"{type(error).__name__}: {error}")
    if "candidate_sha256" not in result and (directory / "raw_output.txt").exists():
        result["candidate_sha256"] = sha256_file(directory / "raw_output.txt")
    result["candidate_id"] = stable_json_sha256(
        {
            k: result.get(k)
            for k in (
                "run_id",
                "case_id",
                "attempt",
                "repeat",
                "request_sha256",
                "candidate_sha256",
            )
        }
    )
    save(directory / "result.json", result)
    save(directory / "completion.json", artifact_inventory(directory, {"completion.json"}))
    return result
