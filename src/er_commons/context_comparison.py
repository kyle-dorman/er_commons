"""Bounded native execution for the explicitly versioned shared-context condition."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

from inspect_ai.model import ChatMessageSystem, ChatMessageUser, GenerateConfig
from inspect_ai.util._json import (
    JSON_SCHEMA_EXTENDED_FIELDS,
    json_schema_dump,
    set_additional_properties_false,
)

from er_commons import adequacy_binary, adequacy_inspect, judge_inspect
from er_commons.alternative_target_generation import canonical_delivery
from er_commons.artifact_io import (
    artifact_inventory,
    publish_bytes_no_clobber,
    sha256_file,
    stable_json_sha256,
)
from er_commons.development_evaluation_provider import ReceiptHooks as FrozenHooks
from er_commons.development_evaluation_provider import component_settings
from er_commons.target_generation import output_schema, save, validate_answer

# These are the registered comparison condition, not tunable per-request defaults.
TARGET_OUTPUT_TOKENS = 12_288
JUDGE_OUTPUT_TOKENS = 4_096
MAX_INPUT_TOKENS = 100_000
REQUEST_TIMEOUT_SECONDS = 900


def delivery(native: dict[str, Any], provider: str) -> dict[str, Any]:
    """Extract the actual native messages without substituting intended input."""
    if provider == "anthropic":
        return canonical_delivery(native, provider)
    if provider != "openai" or not isinstance(native.get("input"), list):
        raise ValueError("Unsupported native delivery")
    return {"input": native["input"]}


def expected_delivery(prompt: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Bind exactly one instruction and one user payload across providers."""
    return {
        "input": [
            {"type": "message", "role": role, "content": [{"type": "input_text", "text": text}]}
            for role, text in (
                ("developer", prompt),
                ("user", json.dumps(payload, ensure_ascii=False)),
            )
        ]
    }


class ReceiptHooks(FrozenHooks):
    """Add exact shared-context isolation to existing native counter/receipt checks."""

    def __init__(
        self, *args: Any, expected: dict[str, Any], expected_schema: dict[str, Any], **kwargs: Any
    ) -> None:
        """Bind expected messages before any client can be constructed."""
        super().__init__(*args, **kwargs)
        self.expected = expected
        self.expected_schema = expected_schema

    def _validate_native_controls(self, native: dict[str, Any]) -> None:
        """Reject prompt, payload, model and reasoning drift before counting."""
        super()._validate_native_controls(native)
        if delivery(native, self.provider) != self.expected:
            raise ValueError("Native context isolation mismatch")
        actual_schema = (
            native.get("text", {}).get("format", {}).get("schema")
            if self.provider == "openai"
            else native.get("output_format", native.get("output_config", {}).get("format", {})).get(
                "schema"
            )
        )
        if actual_schema != self.expected_schema:
            raise ValueError("Native output schema changed")
        if native.get("stream", False):
            raise ValueError("Streaming forbidden")
        if self.provider == "anthropic" and (
            native.get("thinking", {}).get("type") != "adaptive"
            or native.get("output_config", {}).get("effort") != self.expected_reasoning_effort
            or any(k in native for k in ("temperature", "top_p", "top_k", "stop_sequences"))
        ):
            raise ValueError("Frozen Anthropic reasoning changed")


def _execution_config(
    condition: str,
    component: str,
    prompt: str,
    max_output_tokens: int,
    *,
    prompt_version: str | None = None,
    max_connections: int = 1,
    generation_effort: str = "medium",
) -> GenerateConfig:
    """Validate the registered condition before constructing native execution settings."""
    if generation_effort not in ("medium", "high") or (
        generation_effort != "medium" and component != "target"
    ):
        raise ValueError("High reasoning is registered only for target generation")
    if type(max_connections) is not int or max_connections not in (1, 16):
        raise ValueError("Unregistered native connection limit")
    if prompt_version is not None:
        if (
            component != "C"
            or condition != "openai_generation"
            or prompt_version != adequacy_binary.CONCLUSION_STRUCTURED_V6_PROMPT_VERSION
            or max_output_tokens not in (JUDGE_OUTPUT_TOKENS, 6144)
        ):
            raise ValueError("Unregistered versioned judge condition")
        if prompt != adequacy_binary.system_prompt("C", prompt_version=prompt_version):
            raise ValueError("Versioned conclusion prompt changed or context duplicated")
        config = adequacy_inspect.generation_config(condition, "C", prompt_version=prompt_version)
    elif component == "target":
        if condition not in {"openai_generation", "anthropic_generation"} or (
            max_output_tokens != TARGET_OUTPUT_TOKENS
            and not (
                max_output_tokens == 16384
                and condition == "anthropic_generation"
                and generation_effort == "high"
            )
        ):
            raise ValueError("Unregistered target condition")
        config = judge_inspect.generation_config(
            condition, component, prompt, output_schema(), "task11d8_answer_v1"
        )
    else:
        frozen_condition, _, config = component_settings(component)
        if condition != frozen_condition or max_output_tokens != JUDGE_OUTPUT_TOKENS:
            raise ValueError("Frozen judge condition changed")
    if component == "target":
        config = config.model_copy(update={"reasoning_effort": generation_effort})
    config = config.model_copy(
        update={
            "max_tokens": max_output_tokens,
            "max_retries": 0,
            "max_connections": max_connections,
            "timeout": REQUEST_TIMEOUT_SECONDS,
            "attempt_timeout": REQUEST_TIMEOUT_SECONDS,
        }
    )
    return config


def _expected_schema(config: GenerateConfig, provider: str) -> dict[str, Any]:
    """Mirror native provider schema serialization without mutating the configuration."""
    assert config.response_schema is not None
    schema = config.response_schema.json_schema.model_copy(deep=True)
    if provider == "anthropic":
        set_additional_properties_false(schema)
    return dict(
        json_schema_dump(
            schema,
            exclude=JSON_SCHEMA_EXTENDED_FIELDS if provider == "anthropic" else set(),
        )
    )


async def execute(
    *,
    directory: Path,
    condition: str,
    component: str,
    prompt: str,
    payload: dict[str, Any],
    deadline: float,
    max_output_tokens: int,
    prompt_version: str | None = None,
) -> dict[str, Any]:
    """Attempt one native request, count exactly once, retain all failures; never retry."""
    config = _execution_config(
        condition, component, prompt, max_output_tokens, prompt_version=prompt_version
    )
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
        model = judge_inspect.native_model(condition, component, prompt, config, streaming=False)
        client = model.api.client  # type: ignore[attr-defined]
        client.max_retries = 0
        hooks.client = client
        client._client.event_hooks["request"].append(hooks.request)
        client._client.event_hooks["response"].append(hooks.response)
        async with asyncio.timeout(
            min(REQUEST_TIMEOUT_SECONDS, max(0.001, deadline - time.monotonic()))
        ):
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
    result.update(count_calls=hooks.count_calls, judge_calls=hooks.judge_calls)
    return result


async def generate_one(
    record: dict[str, Any],
    directory: Path,
    condition: str,
    prompt: str,
    deadline: float,
    identity: dict[str, Any],
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
