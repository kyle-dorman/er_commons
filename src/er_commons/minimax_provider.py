"""Task 13A's narrow, zero-retry Ollama Cloud generation boundary."""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx2 as httpx
from inspect_ai.model import (
    ChatMessageSystem,
    ChatMessageUser,
    GenerateConfig,
    ResponseSchema,
    get_model,
)

from er_commons.artifact_io import (
    artifact_inventory,
    publish_bytes_no_clobber,
    sha256_bytes,
    sha256_file,
    stable_json_sha256,
)
from er_commons.context_comparison import expected_delivery
from er_commons.locked_dispatch import LockedDispatcher, Request
from er_commons.target_generation import output_schema, save, validate_answer

MODEL = "minimax-m3.1-flash"
ENDPOINT = "https://ollama.com/v1/chat/completions"
PROMOTION_END = datetime(2026, 10, 22, 23, 59, tzinfo=UTC).timestamp()
INPUT_LIMIT = 100_000
OUTPUT_LIMIT = 12_288
TIMEOUT = 900
RESERVE_USD = Decimal("0.0223728")
SCHEMA_NAME = "compatibility"


def delivery(native: dict[str, Any], provider: str = "ollama") -> dict[str, Any]:
    """Project actual chat messages into the unchanged evaluator delivery contract."""
    if provider != "ollama":
        raise ValueError("Unsupported delivery provider")
    messages = native.get("messages")
    if (
        not isinstance(messages, list)
        or len(messages) != 2
        or [message.get("role") for message in messages] != ["system", "user"]
        or any(set(message) != {"role", "content"} for message in messages)
        or any(not isinstance(message["content"], str) for message in messages)
    ):
        raise ValueError("Unexpected native message shape")
    return {
        "input": [
            {
                "type": "message",
                "role": "developer" if message["role"] == "system" else "user",
                "content": [{"type": "input_text", "text": message["content"]}],
            }
            for message in messages
        ]
    }


class BudgetTransport(httpx.AsyncBaseTransport):
    """Reserve every native request through the runner's shared durable ledger."""

    def __init__(
        self,
        dispatcher: LockedDispatcher,
        directory: Path,
        slot_id: str,
        prompt: str,
        payload: dict[str, Any],
        deadline: float,
    ) -> None:
        """Bind exact messages/schema and a per-run monotonic admission deadline."""
        self.dispatcher = dispatcher
        self.directory = directory
        self.slot_id = slot_id
        self.expected = expected_delivery(prompt, payload)
        self.deadline = deadline
        self.inner: httpx.AsyncBaseTransport = httpx.AsyncHTTPTransport(retries=0)
        self.calls = 0
        self.verified_usage = False
        self.rate_limited = False
        self.accounting: dict[str, Any] = {}

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Reject drift before admission; hold uncertain native requests at full reserve."""
        if request.method != "POST" or str(request.url) != ENDPOINT:
            raise ValueError("Unexpected provider endpoint")
        if time.monotonic() >= self.deadline or time.time() >= PROMOTION_END - TIMEOUT:
            raise ValueError("Dispatch or promotional timebox exhausted")
        body = await request.aread()
        native = json.loads(body)
        controls = {
            "model": MODEL,
            "max_tokens": OUTPUT_LIMIT,
            "reasoning_effort": "medium",
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": SCHEMA_NAME,
                    "schema": output_schema(),
                    "description": None,
                    "strict": None,
                },
            },
        }
        if set(native) != {*controls, "messages"} or any(
            native.get(key) != value for key, value in controls.items()
        ):
            raise ValueError("Frozen native controls or output schema changed")
        if delivery(native) != self.expected:
            raise ValueError("Frozen prompt or payload changed")
        bound = len(body) + 4096
        if bound > INPUT_LIMIT:
            raise ValueError("Conservative input bound exceeded")
        publish_bytes_no_clobber(self.directory / "native_request.json", body)
        save(self.directory / "delivery_projection.json", delivery(native))
        self.accounting = {
            "input_bound": bound,
            "input_bound_basis": "serialized_utf8_bytes_plus_4096_template_allowance",
            "exact_preflight_token_count": None,
            "reserved_input_tokens": INPUT_LIMIT,
            "ordinary_input_per_million_usd": "0.15",
            "ordinary_output_per_million_usd": "0.60",
            "maximum_cost_usd": str(RESERVE_USD),
            "promotion_end_epoch": PROMOTION_END,
        }
        save(self.directory / "input_bound.json", self.accounting)
        admission = Request(
            key=f"{self.slot_id}/target/generation",
            slot_id=self.slot_id,
            kind="generation",
            maximum_cost_usd=RESERVE_USD,
            input_tokens=INPUT_LIMIT,
            output_tokens=OUTPUT_LIMIT,
            request_sha256=sha256_bytes(body),
            accounting_basis="ollama_promotion_with_ordinary_price_reservation",
        )

        async def operation() -> tuple[httpx.Response, Decimal | None]:
            """Preserve the complete response before settling verified promotional usage."""
            self.calls += 1
            response = await self.inner.handle_async_request(request)
            await response.aread()
            publish_bytes_no_clobber(
                self.directory / "wire_request_response.body", response.content
            )
            save(
                self.directory / "wire_request_response.json",
                {
                    "status_code": response.status_code,
                    "request_id": response.headers.get("x-request-id")
                    or response.headers.get("request-id"),
                },
            )
            if response.status_code == 429:
                self.rate_limited = True
                self.dispatcher.rate_limit()
            elif not response.is_success:
                self.dispatcher.stop("Ollama generation returned non-success HTTP status")
            cost = None
            if response.is_success:
                value = response.json()
                usage = value.get("usage", {})
                incoming, outgoing = usage.get("prompt_tokens"), usage.get("completion_tokens")
                self.verified_usage = (
                    value.get("model") == MODEL
                    and type(incoming) is int
                    and 0 < incoming <= INPUT_LIMIT
                    and type(outgoing) is int
                    and 0 <= outgoing <= OUTPUT_LIMIT
                    and time.time() < PROMOTION_END
                )
                if self.verified_usage:
                    cost = Decimal("0")
                    self.accounting.update(
                        effective_input_tokens=incoming,
                        output_tokens=outgoing,
                        actual_cost_usd="0",
                        accounting_basis="verified_promotional_usage",
                    )
                else:
                    self.dispatcher.stop("Unverified Ollama identity, usage or promotional window")
            return response, cost

        return await self.dispatcher.invoke_async(admission, operation)

    async def aclose(self) -> None:
        """Close the underlying no-retry HTTP transport."""
        await self.inner.aclose()


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
    """Attempt one native-schema answer, retaining failures without parsing repairs."""
    if condition != "minimax_cloud":
        raise ValueError("Unregistered MiniMax condition")
    # Rates are module-frozen; the shared runner pricing argument cannot widen them.
    result: dict[str, Any] = {
        "status": "execution_error",
        "provider": "ollama",
        "model": MODEL,
        "component": "target",
        **{key: identity[key] for key in ("run_id", "case_id", "repeat")},
        "attempt": 1,
    }
    wire = BudgetTransport(dispatcher, directory, slot_id, prompt, record["payload"], deadline)
    config = GenerateConfig(
        max_tokens=OUTPUT_LIMIT,
        max_retries=0,
        max_connections=10,
        adaptive_connections=False,
        timeout=TIMEOUT,
        attempt_timeout=TIMEOUT,
        reasoning_effort="medium",
        response_schema=ResponseSchema.model_validate(
            {"name": SCHEMA_NAME, "json_schema": output_schema()}
        ),
    )
    try:
        async with httpx.AsyncClient(transport=wire, timeout=TIMEOUT) as client:
            model = get_model(
                f"openai-api/ollama/{MODEL}",
                memoize=False,
                base_url="https://ollama.com/v1",
                api_key=os.environ["OLLAMA_API_KEY"],
                config=config,
                http_client=client,
                stream=False,
                max_retries=0,
                client_timeout=TIMEOUT,
            )
            output = await model.generate(
                [
                    ChatMessageSystem(content=prompt),
                    ChatMessageUser(content=json.dumps(record["payload"], ensure_ascii=False)),
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
            if not wire.verified_usage or output.model != MODEL or output.usage is None:
                raise ValueError("Unverified returned identity or usage")
            result["status"] = "invalid_output"
            if output.stop_reason == "stop":
                answer = validate_answer(output.completion, record["payload"])
                save(directory / "candidate.json", answer)
                result.update(
                    status="valid", candidate_sha256=sha256_file(directory / "candidate.json")
                )
    except Exception as error:
        # SDK exception text can echo credentials; native bodies are already preserved.
        result["error_type"] = type(error).__name__
        if wire.calls and result["status"] == "execution_error" and not wire.rate_limited:
            dispatcher.stop("Uncertain MiniMax execution; no automatic replay")
    finally:
        await wire.aclose()
    result.update(
        generation_calls=wire.calls,
        count_calls=0,
        rate_limited=wire.rate_limited,
        accounting=wire.accounting,
    )
    if (directory / "native_request.json").exists():
        result["request_sha256"] = sha256_file(directory / "native_request.json")
    if "candidate_sha256" not in result and (directory / "raw_output.txt").exists():
        result["candidate_sha256"] = sha256_file(directory / "raw_output.txt")
    result["candidate_id"] = stable_json_sha256(
        {
            key: result.get(key)
            for key in (
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
