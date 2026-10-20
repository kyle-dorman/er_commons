"""Haiku-only Task 11D.5 output intervention, preserving the sealed 11D.4 adapter.

Only max_tokens may differ from a caller-verified sealed 11D.4 native request.
Version-specific request gates retain the original experiment contract; the
attempt lifecycle and immutable receipt helpers are shared with the base adapter.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from er_commons import judge_inspect
from er_commons.alternative_target_generation import (
    IntegrityError,
    canonical_delivery,
    execute_generation,
    native_answer_schema,
)
from er_commons.alternative_target_generation import (
    ReceiptHooks as OriginalReceiptHooks,
)
from er_commons.alternative_target_generation import (
    generation_prompt as generation_prompt,
)
from er_commons.artifact_io import (
    publish_bytes_no_clobber,
    sha256_bytes,
    sha256_file,
)
from er_commons.development_evaluation_provider import count_projection
from er_commons.target_generation import (
    EXPANDED,
    output_schema,
    save,
    validate_record,
)

OUTPUT_CAP = 12288


def validate_config(config: dict[str, Any]) -> None:
    """Allow exactly the registered Haiku output intervention and baseline binding."""
    for key, expected in (
        ("max_input_tokens", 100000),
        ("max_output_tokens", OUTPUT_CAP),
        ("max_retries", 0),
    ):
        if type(config.get(key)) is not int or config[key] != expected:
            raise ValueError(f"Unregistered limit: {key}")
    if not 0 < config["timeout_seconds"] <= 900:
        raise ValueError("Generation timeout exceeds contract")
    if not isinstance(config.get("baseline_native_request_path"), str):
        raise ValueError("A sealed baseline native request path is required")


def validate_native_delta(native: dict[str, Any], baseline: dict[str, Any]) -> None:
    """Require the saved native request to change only its output cap."""
    if baseline.get("model") != "claude-haiku-5-5" or baseline.get("max_tokens") != 4096:
        raise IntegrityError("Baseline is not the registered 11D.4 Haiku request")
    if native != {**baseline, "max_tokens": OUTPUT_CAP}:
        raise IntegrityError("Native request differs beyond authorized output cap")


class ReceiptHooks(OriginalReceiptHooks):
    """Reuse immutable receipt capture; independently gate the larger Haiku request."""

    def __init__(
        self,
        directory: Path,
        condition: str,
        prompt: str,
        payload: dict[str, Any],
        deadline: float,
        *,
        baseline_path: Path,
    ) -> None:
        """Read baseline bytes once; caller must verify its owning completion seal."""
        if condition != "anthropic_generation":
            raise ValueError("Only Haiku is authorized")
        super().__init__(directory, condition, prompt, payload, deadline)
        baseline_bytes = baseline_path.read_bytes()
        self.baseline_native = json.loads(baseline_bytes)
        if not isinstance(self.baseline_native, dict):
            raise IntegrityError("Malformed native baseline")
        self.baseline_sha256 = sha256_bytes(baseline_bytes)

    async def request(self, request: Any) -> None:
        """Validate native settings, retain preflight and gate the actual wire send."""
        if time.monotonic() >= self.deadline:
            raise ValueError("Run timebox exhausted")
        host = "api.anthropic.com"
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
        endpoint = "/messages"
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
        validate_native_delta(native, self.baseline_native)
        if native.get("model") != self.model or native.get("max_tokens") != OUTPUT_CAP:
            raise IntegrityError("Native model/output cap differs")
        if native.get("stream", False) or native.get("tools"):
            raise IntegrityError("Streaming/tools forbidden")
        if native.get("thinking", {}).get("type") != "adaptive" or any(
            key in native for key in ("temperature", "top_p", "top_k", "stop_sequences")
        ):
            raise IntegrityError("Native adaptive thinking/sampling differs")
        projection = count_projection(self.provider, native)
        format_value = native.get("output_format", native.get("output_config", {}).get("format"))
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
        if tokens + OUTPUT_CAP > self.context:
            raise ValueError("Count plus output reserve exceeds native context")
        method = "anthropic_native_count"
        save(self.directory / "delivery_projection.json", delivery)
        save(
            self.directory / "delivery_projection_manifest.json",
            {
                "provider": self.provider,
                "native_request_sha256": sha256_bytes(body),
                "projection_sha256": sha256_file(self.directory / "delivery_projection.json"),
                "schema_version": "task11d5.delivery_projection.v1",
            },
        )
        preflight = {
            "method": method,
            "baseline_native_request_sha256": self.baseline_sha256,
            "context_tokens": self.context,
            "input_allowance": tokens,
            "native_request_sha256": sha256_bytes(body),
            "output_reserve": OUTPUT_CAP,
            "native_input_ceiling": 100000,
            "actual_count_cost_usd": None,
            "reserved_generation_cost_usd": (100000 * 0.25 + OUTPUT_CAP * 0.75) / 1000000,
        }
        save(self.directory / "preflight.json", preflight)
        if time.monotonic() >= self.deadline:
            raise ValueError("Run timebox exhausted after preflight")
        save(self.directory / "dispatch.json", preflight)
        self.generation_calls += 1


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
    if providercondition != "anthropic_generation":
        raise ValueError("Unregistered provider")
    hooks = ReceiptHooks(
        directory,
        providercondition,
        prompt,
        record["payload"],
        deadline,
        baseline_path=Path(config["baseline_native_request_path"]),
    )
    settings = judge_inspect.generation_config(
        providercondition, "target", prompt, output_schema(), "task11d4_answer_v1"
    )
    settings = settings.model_copy(
        update={
            "max_tokens": OUTPUT_CAP,
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
        "baseline_native_request_sha256": hooks.baseline_sha256,
    }
    return await execute_generation(
        record, directory, providercondition, prompt, settings, hooks, result, output_cap=OUTPUT_CAP
    )
