"""Frozen judge transport, exact token counting, limits and immutable receipts."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, TypedDict, cast

from inspect_ai.model import ChatMessageSystem, ChatMessageUser, ContentText, GenerateConfig
from openai import DefaultAsyncHttpxClient

from er_commons import (
    adequacy_binary,
    adequacy_inspect,
    judge_inspect,
    no_answer,
    no_answer_inspect,
    point_grounding,
    point_grounding_inspect,
)
from er_commons.artifact_io import (
    artifact_inventory,
    publish_bytes_no_clobber,
    sha256_bytes,
    stable_json_sha256,
)
from er_commons.target_generation import COUNT_FIELDS, REPO, save


class EvaluationLimits(TypedDict):
    """Fixed run budget recorded before dispatch; counting charges remain unknown."""

    max_judge_calls: int
    max_count_calls: int
    max_retries: int
    max_input_tokens: int
    max_output_tokens: int
    max_spend_usd: float
    max_elapsed_seconds: int
    reserve_input_per_million: float
    reserve_output_per_million: float
    count_cost_allowance_usd: float
    actual_count_cost_usd: None
    provider_enforced_total_spend_cap: bool


LIMITS: EvaluationLimits = {
    "max_judge_calls": 36,
    "max_count_calls": 36,
    "max_retries": 0,
    "max_input_tokens": 32768,
    "max_output_tokens": 4096,
    "max_spend_usd": 12.0,
    "max_elapsed_seconds": 1800,
    "reserve_input_per_million": 0.25,
    "reserve_output_per_million": 0.75,
    "count_cost_allowance_usd": 0.30,
    "actual_count_cost_usd": None,
    "provider_enforced_total_spend_cap": False,
}
ANTHROPIC_COUNT_FIELDS = {
    "model",
    "messages",
    "system",
    "tools",
    "tool_choice",
    "thinking",
    "output_config",
    "output_format",
    "cache_control",
    "speed",
    "user_profile_id",
    "workspace_id",
}


def component_settings(component: str) -> tuple[str, str, GenerateConfig]:
    """Validate frozen semantic settings before explicit transport-only overrides."""
    if component == "A":
        condition = no_answer_inspect.selected_condition()
        prompt = no_answer.system_prompt()
        config = no_answer_inspect.generation_config(condition)
    elif component == "G":
        condition = point_grounding_inspect.selected_condition()
        prompt = point_grounding.system_prompt()
        config = point_grounding_inspect.generation_config(condition)
    elif component in {"S", "C"}:
        component = cast(adequacy_binary.Component, component)
        condition = adequacy_inspect.selected_condition(component)
        prompt = adequacy_binary.system_prompt(
            component, prompt_version=adequacy_inspect.VERSIONS[component]
        )
        config = adequacy_inspect.generation_config(condition, component)
    else:
        raise ValueError("Unknown component")
    freeze = json.loads((REPO / "docs/specs/task09g_judge_freeze_v1.json").read_text())
    if (
        stable_json_sha256(config.model_dump(mode="json", exclude_none=True))
        != freeze["components"][component]["generation_config_sha256"]
    ):
        raise ValueError("Frozen generation configuration changed")
    return condition, prompt, config


def count_projection(provider: str, native: dict[str, Any]) -> dict[str, Any]:
    """Project exact native input including structured output schema; reject unknowns."""
    if provider == "openai":
        fields = COUNT_FIELDS
        controls = {
            "max_output_tokens",
            "store",
            "service_tier",
            "include",
            "background",
            "prompt_cache_key",
            "stream",
        }
    elif provider == "anthropic":
        fields = ANTHROPIC_COUNT_FIELDS
        controls = {
            "max_tokens",
            "stream",
            "metadata",
            "temperature",
            "top_p",
            "top_k",
            "stop_sequences",
            "service_tier",
        }
    else:
        raise ValueError("Unsupported frozen provider")
    if set(native) - fields - controls:
        raise ValueError("context_unverified: unknown native request fields")
    return {key: value for key, value in native.items() if key in fields}


class ReceiptHooks:
    """One exact count and one generation dispatch, without retry or credential logging."""

    def __init__(self, directory: Path, provider: str, model: str, deadline: float) -> None:
        """Bind a fresh request directory and immutable runtime limits."""
        self.directory, self.provider, self.model = directory, provider, model
        self.deadline = deadline
        self.client: Any = None
        self.count_calls = 0
        self.judge_calls = 0
        self.seen_generation = False

    async def request(self, request: Any) -> None:
        """Count the exact on-wire input before allowing a generation request."""
        if time.monotonic() >= self.deadline:
            raise ValueError("Run timebox exhausted")
        expected_host = "api.openai.com" if self.provider == "openai" else "api.anthropic.com"
        if request.url.host != expected_host:
            raise ValueError("Unexpected provider endpoint")
        body = await request.aread()
        is_count = request.url.path.endswith(("/input_tokens", "/count_tokens"))
        if is_count:
            self._record_count_request(request, body)
            return
        if not request.url.path.endswith(("/responses", "/messages")) or self.seen_generation:
            raise ValueError("Unexpected endpoint or forbidden retry")
        self.seen_generation = True
        publish_bytes_no_clobber(self.directory / "native_request.json", body)
        save(
            self.directory / "native_headers.json",
            {"anthropic-beta": request.headers.get("anthropic-beta")},
        )
        native = json.loads(body)
        self._validate_native_controls(native)
        projection = count_projection(self.provider, native)
        save(self.directory / "count_projection.json", projection)
        count = await self._count_input(projection, request.headers)
        tokens = count.input_tokens
        save(self.directory / "count_result.json", count.model_dump(mode="json"))
        if type(tokens) is not int or not 0 < tokens <= LIMITS["max_input_tokens"]:
            raise ValueError("context_overflow_or_unverified")
        if time.monotonic() >= self.deadline:
            raise ValueError("Run timebox exhausted after count")
        save(
            self.directory / "dispatch.json",
            {
                "input_tokens": tokens,
                "request_sha256": sha256_bytes(body),
                "max_output_tokens": LIMITS["max_output_tokens"],
            },
        )
        self.judge_calls += 1

    async def _count_input(self, projection: dict[str, Any], headers: Any) -> Any:
        """Use the provider SDK without changing the exact structured-output schema."""
        if self.provider == "openai":
            return await self.client.responses.input_tokens.count(**projection)
        else:
            # Native Inspect uses the beta structured-output field; retain it
            # verbatim rather than converting it to another semantic schema.
            arguments = {k: v for k, v in projection.items() if k != "output_format"}
            extra = (
                {"output_format": projection["output_format"]}
                if "output_format" in projection
                else {}
            )
            return await self.client.messages.count_tokens(
                **arguments,
                extra_body=extra,
                extra_headers={"anthropic-beta": headers["anthropic-beta"]}
                if "anthropic-beta" in headers
                else None,
            )

    def _validate_native_controls(self, native: dict[str, Any]) -> None:
        """Reject model, output, tool or premium-tier drift before counting."""
        cap = "max_output_tokens" if self.provider == "openai" else "max_tokens"
        if native["model"] != self.model or native.get(cap) != LIMITS["max_output_tokens"]:
            raise ValueError("Native model/output cap changed")
        if native.get("tools") or native.get("service_tier", "default") not in {"default", "auto"}:
            raise ValueError("Tools or premium service tier forbidden")
        if self.provider == "openai" and (
            native.get("truncation") != "disabled"
            or native.get("reasoning") != {"effort": "medium"}
            or native.get("store") is not False
        ):
            raise ValueError("Frozen native controls changed")

    def _record_count_request(self, request: Any, body: bytes) -> None:
        """Check exact counter parity before recording the sole count attempt."""
        if self.count_calls:
            raise ValueError("Counter retry forbidden")
        if json.loads(body) != json.loads((self.directory / "count_projection.json").read_text()):
            raise ValueError("Native count input parity failure")
        save(
            self.directory / "count_headers.json",
            {"anthropic-beta": request.headers.get("anthropic-beta")},
        )
        self.count_calls += 1
        publish_bytes_no_clobber(self.directory / "count_request.json", body)

    async def response(self, response: Any) -> None:
        """Retain complete native response bytes and nonsecret response identifiers."""
        prefix = (
            "count"
            if response.request.url.path.endswith(("/input_tokens", "/count_tokens"))
            else "judge"
        )
        publish_bytes_no_clobber(self.directory / f"{prefix}_response.body", await response.aread())
        save(
            self.directory / f"{prefix}_response.json",
            {
                "status_code": response.status_code,
                "request_id": response.headers.get("x-request-id")
                or response.headers.get("request-id"),
            },
        )


async def execute_item(
    item: dict[str, Any], identity: dict[str, Any], directory: Path, deadline: float
) -> dict[str, Any]:
    """Attempt one frozen judgment; preserve errors and never replace an answer."""
    condition, prompt, frozen = component_settings(item["component"])
    selected = judge_inspect.profile(condition)
    config = frozen.model_copy(update={"max_retries": 0, "max_connections": 1})
    hooks = ReceiptHooks(directory, selected.provider, selected.model, deadline)
    client = DefaultAsyncHttpxClient(
        event_hooks={"request": [hooks.request], "response": [hooks.response]}
    )
    judgment = {key: item[key] for key in ("sample_id", "component", "point_id", "payload_sha256")}
    judgment.update(identity=identity, status="execution_error")
    save(directory / "item.json", item)
    try:
        model = judge_inspect.native_model(
            condition, item["component"], prompt, config, http_client=client, streaming=False
        )
        hooks.client = model.api.client  # type: ignore[attr-defined]
        output = await model.generate(
            [
                ChatMessageSystem(
                    content=[ContentText(text=prompt, cache_breakpoint=True)]
                    if selected.provider == "anthropic"
                    else prompt
                ),
                ChatMessageUser(
                    content=json.dumps(item["packet"], ensure_ascii=False, separators=(",", ":"))
                ),
            ],
            cache=False,
        )
        save(directory / "inspect_output.json", output.model_dump(mode="json"))
        publish_bytes_no_clobber(directory / "raw_output.txt", output.completion.encode())
        judgment.update(
            raw_output=output.completion,
            returned_model=output.model,
            response_id=output.response_id,
            usage=output.usage.model_dump(mode="json") if output.usage else None,
        )
        if output.stop_reason != "stop":
            raise ValueError(f"Noncomplete output: {output.stop_reason}")
        if output.model != selected.model or output.usage is None:
            raise ValueError("Returned model or usage unverified; accounting uncertain")
        if output.usage.output_tokens > LIMITS["max_output_tokens"]:
            raise ValueError("Output usage exceeds reserve; accounting uncertain")
        effective_input = (
            output.usage.input_tokens
            + (output.usage.input_tokens_cache_read or 0)
            + (output.usage.input_tokens_cache_write or 0)
        )
        judgment["accounting"] = {
            "effective_input_tokens": effective_input,
            "count_input_tokens": json.loads((directory / "count_result.json").read_text())[
                "input_tokens"
            ],
            "actual_count_cost_usd": None,
            "count_cost_allowance_usd": LIMITS["count_cost_allowance_usd"],
        }
        judgment["accounting"]["count_usage_difference_tokens"] = (
            effective_input - judgment["accounting"]["count_input_tokens"]
        )
        judgment["accounting"]["count_usage_match"] = (
            judgment["accounting"]["count_usage_difference_tokens"] == 0
        )
        if effective_input > LIMITS["max_input_tokens"]:
            raise ValueError("Input usage exceeds reserve; accounting uncertain")
        judgment["status"] = "completed"
    except Exception as error:
        causes: list[str] = []
        cause: BaseException | None = error
        while cause is not None and len(causes) < 8:
            causes.append(f"{type(cause).__name__}: {cause}")
            cause = cause.__cause__
        judgment.update(error=f"{type(error).__name__}: {error}", failure_causes=causes)
    finally:
        await client.aclose()
    judgment.update(judge_calls=hooks.judge_calls, count_calls=hooks.count_calls)
    save(directory / "judgment.json", judgment)
    save(directory / "completion.json", artifact_inventory(directory, {"completion.json"}))
    return judgment
