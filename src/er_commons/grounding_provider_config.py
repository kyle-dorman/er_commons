"""Explicit provider configuration, independent of wire rendering and Inspect."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

StageKind = Literal["abstention", "point", "conclusion"]
ProviderAPI = Literal[
    "openai_responses", "anthropic_messages", "fireworks_chat", "openai_decisions", "systemone"
]
CONDITION_IDS = {
    "openai_generation",
    "anthropic_generation",
    "fireworks_glm",
    "fireworks_deepseek",
    "openai_decisions",
    "typesafe_jev",
}


class StrictConfig(BaseModel):
    """Reject implicit coercion and unknown provider settings."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class Pricing(StrictConfig):
    """Dated USD rates and maximum documented tier rates for conservative reservation."""

    verified_date: str
    input_per_million: float = Field(ge=0, allow_inf_nan=False)
    cache_read_per_million: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    cache_write_per_million: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    output_per_million: float = Field(ge=0, allow_inf_nan=False)
    conservative_input_per_million: float = Field(ge=0, allow_inf_nan=False)
    conservative_output_per_million: float = Field(ge=0, allow_inf_nan=False)
    source: str
    caveat: str


class CachePolicy(StrictConfig):
    """Documented cache capabilities; unknown thresholds remain null."""

    supported: bool | None
    minimum_tokens: int | None = Field(default=None, gt=0)
    ttl: str | None = None
    controls: list[str]
    native_fields: list[str]
    source: str


class Condition(StrictConfig):
    """One exact model/API condition, including live qualification blockers."""

    id: str
    kind: Literal["generation", "decision"]
    api: ProviderAPI
    model: str = Field(min_length=1)
    endpoint: str
    credential_env: str | None
    context_limit: int | None = Field(default=None, gt=0)
    output_cap: int = Field(ge=0)
    body_bytes_limit: int | None = Field(default=None, gt=0)
    state_question_limit: int | None = Field(default=None, gt=0)
    blockers: list[str]
    pricing: Pricing
    cache: CachePolicy
    settings: dict[str, Any]

    @model_validator(mode="after")
    def check_contract(self) -> Condition:
        """Keep decision controls and endpoint families consistent with declared identities."""
        if self.id not in CONDITION_IDS:
            raise ValueError("Unknown Task 09E.1 condition")
        if (self.kind == "decision") != (self.api in {"openai_decisions", "systemone"}):
            raise ValueError("Condition kind does not match endpoint API")
        if self.kind == "decision" and self.output_cap != 0:
            raise ValueError("Decision endpoints do not support generation output caps")
        if self.kind == "generation" and self.output_cap <= 0:
            raise ValueError("Generation requires a positive output cap")
        if "evidence_cache_breakpoint" in self.settings:
            enabled = self.settings["evidence_cache_breakpoint"]
            options = self.settings.get("prompt_cache_options")
            if type(enabled) is not bool:
                raise ValueError("Evidence cache breakpoint requires a boolean")
            if enabled and (
                self.api != "openai_responses"
                or self.model != "gpt-6-luna"
                or not isinstance(options, dict)
                or options.get("mode") not in ("implicit", "explicit")
                or options.get("ttl") != "30m"
            ):
                raise ValueError(
                    "Evidence cache breakpoint requires Luna Responses with 30m caching"
                )
        if "anthropic_evidence_cache_breakpoint" in self.settings:
            enabled = self.settings["anthropic_evidence_cache_breakpoint"]
            if (
                type(enabled) is not bool
                or enabled
                and (self.api != "anthropic_messages" or self.model != "claude-haiku-5-5")
            ):
                raise ValueError("Anthropic evidence breakpoint requires Haiku 5.5 and a boolean")
        if "fireworks_reasoning_mode" in self.settings and (
            self.api != "fireworks_chat"
            or self.model
            not in {
                "accounts/fireworks/models/glm-5p3-flash",
                "accounts/fireworks/models/deepseek-v4p1-flash",
            }
            or self.settings["fireworks_reasoning_mode"] != "prompt_schema"
            or self.settings.get("reasoning_effort") != "medium"
        ):
            raise ValueError(
                "Fireworks prompt-schema reasoning requires pinned Flash models with medium effort"
            )
        if "fireworks_evidence_cache_prefix" in self.settings:
            enabled = self.settings["fireworks_evidence_cache_prefix"]
            if type(enabled) is not bool or (
                enabled
                and (
                    self.api != "fireworks_chat"
                    or self.model
                    not in {
                        "accounts/fireworks/models/glm-5p3-flash",
                        "accounts/fireworks/models/deepseek-v4p1-flash",
                    }
                    or self.settings.get("fireworks_reasoning_mode") != "prompt_schema"
                    or self.settings.get("reasoning_effort") != "medium"
                )
            ):
                raise ValueError(
                    "Fireworks evidence prefix requires pinned medium prompt-schema mode"
                )
        if "fireworks_cache_isolation_key" in self.settings:
            isolation = self.settings["fireworks_cache_isolation_key"]
            if (
                self.api != "fireworks_chat"
                or self.model
                not in {
                    "accounts/fireworks/models/glm-5p3-flash",
                    "accounts/fireworks/models/deepseek-v4p1-flash",
                }
                or self.settings.get("fireworks_reasoning_mode") != "prompt_schema"
                or self.settings.get("reasoning_effort") != "medium"
                or not isinstance(isolation, str)
                or not isolation.strip()
                or len(isolation) > 64
                or any(ord(character) < 32 for character in isolation)
            ):
                raise ValueError(
                    "Fireworks isolation requires pinned medium prompt-schema mode and a short key"
                )
        if "prompt_cache_retention" in self.settings and (
            self.api != "openai_responses"
            or self.settings["prompt_cache_retention"] not in ("in_memory", "24h")
        ):
            raise ValueError("Invalid OpenAI prompt cache retention")
        if "prompt_cache_key" in self.settings:
            cache_key = self.settings["prompt_cache_key"]
            if (
                self.api != "openai_responses"
                or not isinstance(cache_key, str)
                or not cache_key.strip()
                or len(cache_key) > 64
            ):
                raise ValueError("Invalid OpenAI prompt cache key")
        if (
            self.model == "gpt-6-luna"
            and self.settings.get("reasoning_effort") != "none"
            and any(name in self.settings for name in ("temperature", "top_p"))
        ):
            raise ValueError("Luna sampling settings require reasoning effort none")
        for name, maximum in (("temperature", 2), ("top_p", 1)):
            if name not in self.settings:
                continue
            value = self.settings[name]
            if (
                self.api != "openai_responses"
                or type(value) not in {int, float}
                or not math.isfinite(value)
                or not 0 <= value <= maximum
                or name == "top_p"
                and value == 0
            ):
                raise ValueError(f"Invalid explicit OpenAI sampling setting: {name}")
        self._check_provider_settings()
        return self

    def _check_provider_settings(self) -> None:
        """Reject ignored settings and mismatched endpoint families before rendering."""
        families = {
            "openai_generation": ("openai_responses", "https://api.openai.com/v1/responses"),
            "openai_decisions": ("openai_decisions", "https://api.openai.com/v1/decisions"),
            "anthropic_generation": ("anthropic_messages", "https://api.anthropic.com/v1/messages"),
            "fireworks_glm": (
                "fireworks_chat",
                "https://api.fireworks.ai/inference/v1/chat/completions",
            ),
            "fireworks_deepseek": (
                "fireworks_chat",
                "https://api.fireworks.ai/inference/v1/chat/completions",
            ),
            "typesafe_jev": ("systemone", "https://api.typesafe.ai/v1/systemone"),
        }
        if (self.api, self.endpoint) != families[self.id]:
            raise ValueError("Condition identity, API and endpoint must agree")
        if not self.credential_env or not self.credential_env.isidentifier():
            raise ValueError("Cloud conditions require a credential environment variable name")
        allowed = {
            "openai_responses": {
                "reasoning_effort",
                "temperature",
                "top_p",
                "prompt_cache_options",
                "prompt_cache_retention",
                "prompt_cache_key",
                "evidence_cache_breakpoint",
            },
            "anthropic_messages": {"reasoning_effort", "anthropic_evidence_cache_breakpoint"},
            "fireworks_chat": {
                "reasoning_effort",
                "reasoning_output",
                "fireworks_reasoning_mode",
                "fireworks_evidence_cache_prefix",
                "fireworks_cache_isolation_key",
            },
            "openai_decisions": set(),
            "systemone": set(),
        }
        disabled_flags = {
            key
            for key in (
                "evidence_cache_breakpoint",
                "anthropic_evidence_cache_breakpoint",
                "fireworks_evidence_cache_prefix",
            )
            if self.settings.get(key) is False
        }
        if set(self.settings) - allowed[self.api] - disabled_flags:
            raise ValueError("Unknown provider settings")
        if self.api in {"openai_responses", "anthropic_messages"}:
            efforts = (
                {"none", "low", "medium", "high", "xhigh", "max"}
                if self.api == "openai_responses"
                else {"low", "medium", "high", "max"}
            )
            effort = self.settings.get("reasoning_effort")
            if not isinstance(effort, str) or effort not in efforts:
                raise ValueError("Require a supported explicit reasoning effort")
        if "prompt_cache_options" in self.settings:
            options = self.settings["prompt_cache_options"]
            if (
                self.model != "gpt-6-luna"
                or not isinstance(options, dict)
                or set(options) != {"mode", "ttl"}
                or options.get("mode") not in ("implicit", "explicit")
                or options.get("ttl") != "30m"
            ):
                raise ValueError("Luna cache options require explicit mode and 30m ttl")
        if self.api == "fireworks_chat":
            if (
                "reasoning_output" in self.settings
                and self.settings["reasoning_output"] != "disabled_by_json_schema"
            ):
                raise ValueError("Unknown Fireworks reasoning output policy")
            if (
                "reasoning_effort" in self.settings
                and self.settings.get("fireworks_reasoning_mode") != "prompt_schema"
            ):
                raise ValueError("Fireworks reasoning effort requires prompt-schema mode")


def load_conditions(path: Path) -> dict[str, Condition]:
    """Load a nonempty supported subset; reject duplicates and retired configurations."""
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or set(data) != {"version", "conditions"}:
        raise ValueError("Invalid condition configuration envelope")
    if data["version"] not in {"task09e1.conditions.v1", "grounding.conditions.v2"}:
        raise ValueError("Unknown condition configuration version")
    if not isinstance(data["conditions"], list) or not data["conditions"]:
        raise ValueError("Require a nonempty condition list")
    result = [Condition.model_validate(item) for item in data["conditions"]]
    if len({item.id for item in result}) != len(result):
        raise ValueError("Condition IDs must be distinct")
    return {item.id: item for item in result}
