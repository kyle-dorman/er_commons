"""Inspect/native Ollama adapters for packets; no judge prompt or scorer is defined."""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from er_commons.artifact_io import stable_json_sha256
from er_commons.judge_packets import (
    CONTEXT_TOKENS,
    OUTPUT_RESERVE,
    SCHEMA_VERSION,
    serialize_payload,
)
from er_commons.judge_qualification import native_request, validate_settings

if TYPE_CHECKING:
    from inspect_ai.dataset import Sample


def packet_content(packet: dict[str, Any]) -> str:
    """Accept this version only and cross the model boundary through validated payloads."""
    if packet.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported judge packet version")
    content = serialize_payload(packet["payload"], packet["dimension"])
    expected = packet.get("diagnostics", {}).get("payload_sha256")
    if expected != stable_json_sha256(packet["payload"]):
        raise ValueError(
            "Packet payload changed or its integrity hash is missing; rebuild the packet"
        )
    return content


def inspect_sample(packet: dict[str, Any]) -> Sample:
    """Create a plain Inspect sample with no target, labels, identity or provenance.

    Later Tasks supply saved-answer solvers and independent scorers. This function
    neither registers a task nor performs evaluation.
    """
    from inspect_ai.dataset import Sample

    return Sample(input=packet_content(packet))


def prepare_request(
    packet: dict[str, Any],
    *,
    system_prompt: str,
    response_schema: dict[str, Any],
    settings: dict[str, Any],
    count_tokens: Callable[[dict[str, Any]], int] | None = None,
    counter_model_digest: str | None = None,
) -> dict[str, Any]:
    """Preflight a complete request using a caller-supplied exact runtime counter.

    The counter must apply the pinned model's actual chat template, including any
    model-visible schema and special tokens. No character heuristic substitutes
    for it. Unknown counts and overflows are explicit non-dispatch results.
    09E/09F own the future prompt, scoring and runtime counter integration.
    """
    validate_settings(settings)
    if settings["context"] != CONTEXT_TOKENS or settings["max_tokens"] != OUTPUT_RESERVE:
        raise ValueError("09C requires measured 48K allocation and 1500-token output reserve")
    if not system_prompt.strip():
        raise ValueError("The consuming judge must supply its own system prompt")
    request = native_request(
        {
            "settings": settings,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": packet_content(packet)},
            ],
            "schema": copy.deepcopy(response_schema),
        }
    )
    diagnostic: dict[str, Any] = {
        "status": "context_unverified",
        "request_sha256": stable_json_sha256(request),
        "model_digest": settings["identity"]["digest"],
        "context_tokens": CONTEXT_TOKENS,
        "output_reserve": OUTPUT_RESERVE,
        "input_budget": CONTEXT_TOKENS - OUTPUT_RESERVE,
        "input_tokens": None,
        "overflow_tokens": None,
        "dispatch_allowed": False,
    }
    if count_tokens is not None:
        if counter_model_digest != diagnostic["model_digest"]:
            raise ValueError("Token counter must be bound to the selected model digest")
        count = count_tokens(copy.deepcopy(request))
        if type(count) is not int or count <= 0:
            raise ValueError("Exact full-request token count must be a positive integer")
        overflow = max(0, count + OUTPUT_RESERVE - CONTEXT_TOKENS)
        diagnostic.update(
            status="context_overflow" if overflow else "ready",
            input_tokens=count,
            overflow_tokens=overflow,
            dispatch_allowed=not overflow,
        )
    return {"request": request, "diagnostics": diagnostic}
