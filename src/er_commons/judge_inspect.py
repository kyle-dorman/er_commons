"""Shared native Inspect provider settings for the independent A/G/S/C judges.

Inspect owns transport, retries, concurrency and logs. Local Ollama profiles are
integration diagnostics; their compute costs and context qualification are unknown.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Literal

from inspect_ai.model import (
    GenerateConfig,
    Model,
    ModelCost,
    ResponseSchema,
    get_model,
    set_model_cost,
)
from inspect_ai.util._json import resolve_schema_references
from pydantic import BaseModel, ConfigDict, Field

from er_commons.artifact_io import stable_json_sha256

REPO = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO / "configs/judge_models_v1.json"
SELECTION_PATH = REPO / "configs/judges_selected_v1.json"
PROVIDERS = {
    "openai_generation": "openai",
    "anthropic_generation": "anthropic",
    "fireworks_glm": "fireworks",
    "ollama_small": "ollama",
    "ollama_9b": "ollama",
}


class Pricing(BaseModel):
    """Dated prices per million tokens; local compute is deliberately unpriced."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    input_per_million: float = Field(ge=0, allow_inf_nan=False)
    output_per_million: float = Field(ge=0, allow_inf_nan=False)
    cache_read_per_million: float = Field(ge=0, allow_inf_nan=False)
    cache_write_per_million: float = Field(ge=0, allow_inf_nan=False)
    verified_date: str
    source: str


class Profile(BaseModel):
    """Only options actually consumed by the native provider runtime."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    provider: Literal["openai", "anthropic", "fireworks", "ollama"]
    model: str = Field(min_length=1)
    pricing: Pricing | None


def profile(condition_id: str) -> Profile:
    """Reject unknown profiles before constructing any native provider client."""
    if condition_id not in PROVIDERS:
        raise ValueError("Unknown judge provider")
    document = json.loads(CONFIG_PATH.read_text())
    if set(document) != {"version", "profiles"} or document["version"] != "judge.native_models.v1":
        raise ValueError("Unsupported native provider configuration")
    if set(document["profiles"]) != set(PROVIDERS):
        raise ValueError("Native provider profile inventory differs")
    result = Profile.model_validate(document["profiles"][condition_id])
    if result.provider != PROVIDERS[condition_id] or (result.pricing is None) != (
        result.provider == "ollama"
    ):
        raise ValueError("Native provider identity or pricing differs")
    return result


def _schema(schema: dict[str, Any], provider: str) -> dict[str, Any]:
    """Translate provider-supported constraints without changing local validation."""
    value = copy.deepcopy(resolve_schema_references(schema))

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            if provider == "openai":
                for key in ("default", "minLength", "maxLength"):
                    node.pop(key, None)
                if "const" in node:
                    node["enum"] = [node.pop("const")]
                if node.get("type") == "object":
                    node["additionalProperties"] = False
                    node["required"] = list(node.get("properties", {}))
            elif provider == "anthropic":
                removed = {
                    key: node.pop(key)
                    for key in ("minLength", "maxLength", "minimum", "maximum", "maxItems")
                    if key in node
                }
                if node.get("minItems", 0) > 1:
                    removed["minItems"] = node.pop("minItems")
                if removed:
                    encoded = json.dumps(
                        removed, ensure_ascii=False, separators=(",", ":"), allow_nan=False
                    )
                    node["description"] = (
                        node.get("description", "") + " Constraints: " + encoded
                    ).strip()
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return value


def affinity(condition_id: str, component: str, prompt: str) -> str:
    """Preserve the accepted model/component/prompt cache isolation identity."""
    return stable_json_sha256(
        {"model": profile(condition_id).model, "component": component, "prompt": prompt}
    )


def generation_config(
    condition_id: str, component: str, prompt: str, schema: dict[str, Any], schema_name: str
) -> GenerateConfig:
    """Use shared bounded native settings; provider exceptions remain explicit."""
    selected = profile(condition_id)
    common: dict[str, Any] = {
        "max_retries": 2,
        "timeout": 120,
        "attempt_timeout": 45,
        "max_connections": 4,
        "adaptive_connections": False,
        "max_tokens": 4096,
        "cache": False,
    }
    if selected.provider in {"openai", "anthropic", "ollama"}:
        common["response_schema"] = ResponseSchema.model_validate(
            {"name": schema_name, "json_schema": _schema(schema, selected.provider), "strict": True}
        )
    if selected.provider == "openai":
        common.update(
            reasoning_effort="medium",
            reasoning_summary="none",
            extra_body={"store": False, "truncation": "disabled"},
        )
    elif selected.provider == "anthropic":
        common.update(cache_prompt=True, reasoning_effort="medium")
    elif selected.provider == "fireworks":
        key = affinity(condition_id, component, prompt)
        common.update(
            extra_headers={"x-session-affinity": key},
            temperature=0,
            top_p=1,
            seed=0,
            reasoning_effort="medium",
            extra_body={
                "context_length_exceeded_behavior": "error",
                "prompt_cache_key": key,
                "user": key,
            },
        )
    else:
        # Historical 48K aliases are diagnostic conveniences, not verified model
        # identities. Native compatible requests do not use the legacy token counter.
        common.update(temperature=0, top_p=1, seed=0, max_connections=1)
    return GenerateConfig(**common)


def native_model(
    condition_id: str, component: str, prompt: str, config: GenerateConfig, **model_args: Any
) -> Model:
    """Construct only Inspect providers and register explicit cloud token prices."""
    selected = profile(condition_id)
    if selected.provider == "openai":
        model_args.update(
            responses_api=True,
            responses_store=False,
            max_retries=0,
            prompt_cache_key=affinity(condition_id, component, prompt),
        )
    elif selected.provider == "anthropic":
        model_args.update(max_retries=0, cache_ttl="5m")
    model = get_model(
        f"{selected.provider}/{selected.model}", config=config, memoize=False, **model_args
    )
    pricing = selected.pricing
    if pricing is not None:
        cost = ModelCost(
            input=pricing.input_per_million,
            output=pricing.output_per_million,
            input_cache_write=pricing.cache_write_per_million,
            input_cache_read=pricing.cache_read_per_million,
        )
        set_model_cost(f"{selected.provider}/{selected.model}", cost)
        if selected.provider == "fireworks":
            set_model_cost(f"fireworks/{selected.model.rsplit('/', 1)[-1]}", cost)
    return model


def selected_condition(
    component: str, prompt_version: str, prompt: str, schema: dict[str, Any]
) -> str:
    """Reject selected model or semantic drift before any provider is instantiated."""
    document = json.loads(SELECTION_PATH.read_text())
    if (
        document["version"] != "judge.selected.v1"
        or set(document["components"]) != {"A", "G", "S", "C"}
        or document["provider_config_sha256"]
        != stable_json_sha256(json.loads(CONFIG_PATH.read_text()))
    ):
        raise ValueError("Selected provider configuration changed; version the selection")
    selected = document["components"][component]
    condition_id = str(selected["condition_id"])
    if (
        profile(condition_id).model != selected["model"]
        or prompt_version != selected["prompt_version"]
        or stable_json_sha256(prompt) != selected["prompt_sha256"]
        or stable_json_sha256(schema) != selected["schema_sha256"]
    ):
        raise ValueError("Selected judge model, prompt or schema changed; version the selection")
    return condition_id


def validate_samples(samples: list[dict[str, Any]], labels: dict[str, Any], epochs: int) -> None:
    """Require one exact target per unique sample before any provider construction."""
    if type(epochs) is not int or epochs < 1:
        raise ValueError("epochs must be a positive integer")
    ids = [sample["sample_id"] for sample in samples]
    if (
        not ids
        or any(not isinstance(value, str) or not value.strip() for value in ids)
        or len(set(ids)) != len(ids)
        or set(ids) != set(labels)
    ):
        raise ValueError("Samples must be nonempty, unique and match label identities exactly")


def task_metadata(
    component: str, prompt_version: str, prompt: str, schema: dict[str, Any]
) -> dict[str, Any]:
    """Bind the common production identity without inserting it into judge messages."""
    return {
        "component": component,
        "prompt_version": prompt_version,
        "prompt_sha256": stable_json_sha256(prompt),
        "schema_sha256": stable_json_sha256(schema),
        "provider_config_sha256": stable_json_sha256(json.loads(CONFIG_PATH.read_text())),
    }
