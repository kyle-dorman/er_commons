"""Opt-in Task 11D.4 native providers; immutable receipts and explicit count limits."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from inspect_ai.model import ChatMessageSystem, ChatMessageUser, GenerateConfig, ResponseSchema
from inspect_ai.util._json import (
    JSON_SCHEMA_EXTENDED_FIELDS,
    json_schema_dump,
    set_additional_properties_false,
)

from er_commons import judge_inspect
from er_commons.artifact_io import (
    artifact_inventory,
    publish_bytes_no_clobber,
    sha256_bytes,
    sha256_file,
    stable_json_sha256,
)
from er_commons.development_evaluation_provider import count_projection
from er_commons.target_generation import (
    EXPANDED,
    output_schema,
    readable,
    save,
    validate_answer,
    validate_record,
)

MODELS = {
    "anthropic_generation": ("anthropic", "claude-haiku-5-5", 1_000_000),
    "fireworks_glm": ("fireworks", "accounts/fireworks/models/glm-5p3-flash", 1_040_000),
}


class IntegrityError(ValueError):
    """Native request drift must stop all provider scheduling."""


def generation_prompt(prompt: str, providercondition: str) -> str:
    """Append the fixed explicit JSON contract only for the GLM condition."""
    if providercondition not in MODELS:
        raise ValueError("Unregistered alternative provider")
    if providercondition == "anthropic_generation":
        return prompt
    return prompt + (
        "\n\nReturn only one valid JSON object matching the following JSON Schema. "
        "Do not include Markdown fences, commentary, or text outside the JSON object.\n"
        + json.dumps(output_schema(), ensure_ascii=False, sort_keys=True)
        + "\n"
    )


def _text(content: Any) -> str:
    """Accept only plain text blocks, preserving every character and its order."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list) or len(content) != 1:
        raise ValueError("Unexpected native text block inventory")
    block = content[0]
    if set(block) - {"type", "text", "cache_control"} or block.get("type") != "text":
        raise ValueError("Nontext native content")
    if not isinstance(block.get("text"), str):
        raise ValueError("Missing native text")
    return str(block["text"])


def canonical_delivery(native: dict[str, Any], provider: str) -> dict[str, Any]:
    """Derive evaluator delivery from native bytes; this is not a native request."""
    messages = native.get("messages")
    if not isinstance(messages, list):
        raise ValueError("Missing native messages")
    if provider == "anthropic":
        if len(messages) != 1 or set(messages[0]) != {"role", "content"}:
            raise ValueError("Unexpected Anthropic messages")
        system, user = _text(native.get("system")), messages[0]
    elif provider == "fireworks":
        if len(messages) != 2 or any(set(m) != {"role", "content"} for m in messages):
            raise ValueError("Unexpected Fireworks messages")
        if messages[0]["role"] != "system":
            raise ValueError("Missing system instruction")
        system, user = _text(messages[0]["content"]), messages[1]
    else:
        raise ValueError("Unsupported native provider")
    if user["role"] != "user":
        raise ValueError("Missing user payload")
    return {
        "input": [
            {"type": "message", "role": role, "content": [{"type": "input_text", "text": text}]}
            for role, text in (("developer", system), ("user", _text(user["content"])))
        ]
    }


def native_answer_schema() -> dict[str, Any]:
    """Apply installed Inspect Anthropic serialization to the registered schema."""
    schema = ResponseSchema.model_validate(
        {"name": "task11d4_answer_v1", "json_schema": output_schema(), "strict": True}
    ).json_schema
    set_additional_properties_false(schema)
    return dict(json_schema_dump(schema, exclude=JSON_SCHEMA_EXTENDED_FIELDS))


def validate_config(config: dict[str, Any]) -> None:
    """Reject operational expansion before constructing a provider."""
    for key, expected in (
        ("max_input_tokens", 100000),
        ("max_output_tokens", 4096),
        ("max_retries", 0),
    ):
        if type(config.get(key)) is not int or config[key] != expected:
            raise ValueError(f"Unregistered limit: {key}")
    if not 0 < config["timeout_seconds"] <= 900:
        raise ValueError("Generation timeout exceeds contract")
    if config.get("max_preflight_tokens", 200000) != 200000:
        raise ValueError("Preflight allowance changed")


class ReceiptHooks:
    """Capture actual SDK traffic; one dispatch, no retries and no invented counts."""

    def __init__(
        self, directory: Path, condition: str, prompt: str, payload: dict[str, Any], deadline: float
    ) -> None:
        """Bind expected prompt and evidence before any native request."""
        self.directory, self.deadline = directory, deadline
        self.provider, self.model, self.context = MODELS[condition]
        self.expected = {
            "input": [
                {"type": "message", "role": role, "content": [{"type": "input_text", "text": text}]}
                for role, text in (
                    ("developer", prompt),
                    ("user", json.dumps(payload, ensure_ascii=False)),
                )
            ]
        }
        self.client: Any = None
        self.count_calls = self.generation_calls = 0
        self.seen = False

    async def request(self, request: Any) -> None:
        """Validate native settings, retain preflight and gate the actual wire send."""
        if time.monotonic() >= self.deadline:
            raise ValueError("Run timebox exhausted")
        host = "api.anthropic.com" if self.provider == "anthropic" else "api.fireworks.ai"
        if request.url.host != host:
            raise IntegrityError("Provider endpoint drift")
        body = await request.aread()
        try:
            native = json.loads(body)
            if not isinstance(native, dict):
                raise ValueError("Native request must be an object")
        except (ValueError, TypeError) as error:
            raise IntegrityError("Malformed native request") from error
        if request.url.path.endswith("/messages/count_tokens"):
            if self.provider != "anthropic" or self.count_calls:
                raise IntegrityError("Unexpected count or forbidden retry")
            if native != json.loads((self.directory / "count_projection.json").read_text()):
                raise IntegrityError("Count projection mismatch")
            save(
                self.directory / "count_headers.json",
                {"anthropic-beta": request.headers.get("anthropic-beta")},
            )
            self.count_calls += 1
            publish_bytes_no_clobber(self.directory / "count_request.json", body)
            save(
                self.directory / "count_dispatch.json",
                {
                    "actual_cost_usd": None,
                    "reserved_cost_usd": 0,
                    "request_sha256": sha256_bytes(body),
                },
            )
            return
        endpoint = "/messages" if self.provider == "anthropic" else "/chat/completions"
        if not request.url.path.endswith(endpoint) or self.seen:
            raise IntegrityError("Unexpected endpoint or forbidden retry")
        self.seen = True
        publish_bytes_no_clobber(self.directory / "native_request.json", body)
        save(
            self.directory / "native_headers.json",
            {"anthropic-beta": request.headers.get("anthropic-beta")},
        )
        try:
            delivery = canonical_delivery(native, self.provider)
        except (ValueError, TypeError, KeyError) as error:
            raise IntegrityError("Native message isolation failed") from error
        if delivery != self.expected:
            raise IntegrityError("Native prompt/evidence differs")
        if native.get("model") != self.model or native.get("max_tokens") != 4096:
            raise IntegrityError("Native model/output cap differs")
        if native.get("stream", False) or native.get("tools"):
            raise IntegrityError("Streaming/tools forbidden")
        if self.provider == "anthropic":
            if native.get("thinking", {}).get("type") != "adaptive" or any(
                key in native for key in ("temperature", "top_p", "top_k", "stop_sequences")
            ):
                raise IntegrityError("Native adaptive thinking/sampling differs")
            projection = count_projection(self.provider, native)
            format_value = native.get(
                "output_format", native.get("output_config", {}).get("format")
            )
            if not format_value or format_value.get("schema") != native_answer_schema():
                raise IntegrityError("Native answer schema differs")
            if native.get("output_config", {}).get("effort") != "medium":
                raise IntegrityError("Native effort differs")
            save(self.directory / "count_projection.json", projection)
            arguments = {k: v for k, v in projection.items() if k != "output_format"}
            count = await self.client.messages.count_tokens(
                **arguments,
                extra_body={"output_format": projection["output_format"]}
                if "output_format" in projection
                else {},
                extra_headers={"anthropic-beta": request.headers["anthropic-beta"]}
                if "anthropic-beta" in request.headers
                else None,
            )
            save(self.directory / "count_result.json", count.model_dump(mode="json"))
            tokens = count.input_tokens
            if type(tokens) is not int or not 0 < tokens <= 100000:
                raise ValueError("Native count exceeds input ceiling or is invalid")
            method = "anthropic_native_count"
        else:
            allowed = {
                "model",
                "messages",
                "max_tokens",
                "temperature",
                "top_p",
                "seed",
                "reasoning_effort",
                "context_length_exceeded_behavior",
                "prompt_cache_key",
                "user",
                "stream",
            }
            if set(native) - allowed or native.get("context_length_exceeded_behavior") != "error":
                raise IntegrityError("Unknown native control or truncation policy")
            if (
                native.get("reasoning_effort"),
                native.get("temperature"),
                native.get("top_p"),
                native.get("seed"),
            ) != ("medium", 0, 1, 0):
                raise IntegrityError("Native sampling/effort differs")
            tokens = len(body) + 8192
            if tokens > 200000 or tokens + 4096 > self.context:
                raise ValueError("Exploratory byte allowance exceeds ceiling")
            method = "utf8_request_bytes_plus_8192_assumption_not_exact"
        save(self.directory / "delivery_projection.json", delivery)
        save(
            self.directory / "delivery_projection_manifest.json",
            {
                "provider": self.provider,
                "native_request_sha256": sha256_bytes(body),
                "projection_sha256": sha256_file(self.directory / "delivery_projection.json"),
                "schema_version": "task11d4.delivery_projection.v1",
            },
        )
        preflight = {
            "method": method,
            "input_allowance": tokens,
            "native_request_sha256": sha256_bytes(body),
            "output_reserve": 4096,
            "native_input_ceiling": 100000,
            "actual_count_cost_usd": None,
            "reserved_generation_cost_usd": (200000 * 0.25 + 4096 * 0.75) / 1000000,
        }
        save(self.directory / "preflight.json", preflight)
        if time.monotonic() >= self.deadline:
            raise ValueError("Run timebox exhausted after preflight")
        save(self.directory / "dispatch.json", preflight)
        self.generation_calls += 1

    async def response(self, response: Any) -> None:
        """Retain successful and failed raw responses without secret headers."""
        prefix = "count" if response.request.url.path.endswith("/count_tokens") else "generation"
        publish_bytes_no_clobber(self.directory / f"{prefix}_response.body", await response.aread())
        save(
            self.directory / f"{prefix}_response.json",
            {
                "status_code": response.status_code,
                "request_id": response.headers.get("x-request-id")
                or response.headers.get("request-id"),
            },
        )


async def generate_one(
    record: dict[str, Any],
    directory: Path,
    providercondition: str,
    prompt: str,
    config: dict[str, Any],
    deadline: float,
    *,
    repeat: int = 1,
) -> dict[str, Any]:
    """Attempt one immutable native generation; retain invalid answers and usage."""
    validate_config(config)
    validate_record(record)
    if record["case_id"] not in EXPANDED or repeat not in (1, 2):
        raise ValueError("Unregistered case/repeat")
    if providercondition not in MODELS:
        raise ValueError("Unregistered provider")
    hooks = ReceiptHooks(directory, providercondition, prompt, record["payload"], deadline)
    settings = judge_inspect.generation_config(
        providercondition, "target", prompt, output_schema(), "task11d4_answer_v1"
    )
    settings = settings.model_copy(
        update={
            "max_retries": 0,
            "max_connections": 1,
            "timeout": config["timeout_seconds"],
            "attempt_timeout": config["timeout_seconds"],
        }
    )
    result: dict[str, Any] = {
        "case_id": record["case_id"],
        "attempt": 1,
        "repeat": repeat,
        "provider": hooks.provider,
        "providercondition": providercondition,
    }
    return await execute_generation(
        record, directory, providercondition, prompt, settings, hooks, result, output_cap=4096
    )


async def execute_generation(
    record: dict[str, Any],
    directory: Path,
    providercondition: str,
    prompt: str,
    settings: GenerateConfig,
    hooks: ReceiptHooks,
    result: dict[str, Any],
    *,
    output_cap: int,
) -> dict[str, Any]:
    """Execute and seal one attempt using the caller's version-specific request gates.

    This lifecycle preserves raw outputs, usage, failures and candidate identities;
    provider settings and authorized caps remain owned by each public entrypoint.
    """
    client: Any = None
    failure_class = "provider_failure"
    try:
        model = judge_inspect.native_model(
            providercondition,
            "target",
            prompt,
            settings,
            **({"streaming": False} if hooks.provider == "anthropic" else {}),
        )
        client = model.api.client  # type: ignore[attr-defined]
        client.max_retries = 0
        hooks.client = client
        http = client._client
        http.event_hooks["request"].append(hooks.request)
        http.event_hooks["response"].append(hooks.response)
        output = await model.generate(
            [
                ChatMessageSystem(content=prompt),
                ChatMessageUser(content=json.dumps(record["payload"], ensure_ascii=False)),
            ],
            cache=False,
        )
        save(directory / "inspect_output.json", output.model_dump(mode="json"))
        publish_bytes_no_clobber(directory / "raw_answer.txt", output.completion.encode())
        result.update(
            returned_model=output.model,
            response_id=output.response_id,
            usage=output.usage.model_dump(mode="json") if output.usage else None,
        )
        if output.usage is None:
            raise ValueError("accounting_uncertain: missing native usage")
        usage = output.usage
        total = (
            usage.input_tokens
            + (usage.input_tokens_cache_read or 0)
            + (usage.input_tokens_cache_write or 0)
        )
        result["effective_input_tokens"] = total
        if (
            not 0 < total <= 100000
            or not 0 <= usage.output_tokens <= output_cap
            or any(
                value < 0
                for value in (
                    usage.input_tokens,
                    usage.input_tokens_cache_read or 0,
                    usage.input_tokens_cache_write or 0,
                )
            )
        ):
            raise ValueError("accounting_limit: native usage exceeds ceiling")
        if output.model not in {hooks.model, hooks.model.rsplit("/", 1)[-1]}:
            raise IntegrityError("Returned model identity differs")
        failure_class = "invalid_output"
        if output.stop_reason != "stop":
            raise ValueError(f"Noncomplete output: {output.stop_reason}")
        answer = validate_answer(output.completion, record["payload"])
        save(directory / "candidate.json", answer)
        publish_bytes_no_clobber(
            directory / "candidate.md", readable(answer, record["payload"]).encode()
        )
        result.update(status="valid", candidate_sha256=sha256_file(directory / "candidate.json"))
    except Exception as error:
        causes: list[dict[str, str]] = []
        cause: BaseException | None = error
        while cause is not None and len(causes) < 8:
            causes.append({"type": type(cause).__name__, "message": str(cause)})
            cause = cause.__cause__
        if any(c["type"] == "IntegrityError" for c in causes):
            failure_class = "integrity_failure"
        result["failure_causes"] = causes
        result.update(
            status="failed",
            failure_type=type(error).__name__,
            failure=str(error),
            failure_class=failure_class,
        )
    finally:
        if client is not None:
            try:
                await client.close()
            except Exception as error:
                # Cleanup must not discard a completed response or its original failure.
                result["cleanup_error"] = {"type": type(error).__name__, "message": str(error)}
                if result.get("status") != "failed":
                    result.update(
                        status="failed",
                        failure_type=type(error).__name__,
                        failure=str(error),
                        failure_class="provider_failure",
                    )
    result.update(count_calls=hooks.count_calls, generation_calls=hooks.generation_calls)
    result["run_id"] = json.loads((directory.parent / "manifest.json").read_text())["run_id"]
    if (directory / "native_request.json").exists():
        result["request_sha256"] = sha256_file(directory / "native_request.json")
    if (directory / "delivery_projection.json").exists():
        result["delivery_projection_sha256"] = sha256_file(directory / "delivery_projection.json")
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
