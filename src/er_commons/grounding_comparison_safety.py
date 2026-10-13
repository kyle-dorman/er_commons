"""Fail-closed request qualification, run caps and create-only attempt receipts."""

from __future__ import annotations

import json
import math
import os
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from er_commons.artifact_io import json_bytes, stable_json_sha256


class CounterReceipt(BaseModel):
    """Exact native counts bind all rendered fields and the complete condition."""

    model_config = ConfigDict(strict=True, extra="forbid")
    request_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    condition_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    input_tokens: int = Field(ge=0)
    state_longest_tokens: int | None = Field(default=None, ge=0)
    provenance: str = Field(min_length=1)
    exact: bool


def _integer(value: int, name: str, *, positive: bool = False) -> int:
    """Reject boolean, negative and noninteger token or request quantities."""
    if type(value) is not int or value < (1 if positive else 0):
        raise ValueError(f"Invalid {name}")
    return value


def preflight(
    request: dict[str, Any],
    condition: dict[str, Any],
    receipt: CounterReceipt | None,
    *,
    context_limit: int | None,
    output_reserve: int,
    body_limit: int | None = None,
    state_longest_limit: int | None = None,
    qualified_counter_provenance: str | None = None,
) -> dict[str, Any]:
    """Require adapter-qualified counts; a user-provided receipt alone grants no access.

    The trusted live adapter supplies its known counter provenance only after
    exact endpoint qualification. CLI/config receipt files cannot enable it.
    Body bytes use the compact UTF-8 representation sent by the adapter.
    """
    _integer(output_reserve, "output reserve")
    for name, limit in (
        ("context", context_limit),
        ("body", body_limit),
        ("state plus longest question", state_longest_limit),
    ):
        if limit is not None:
            _integer(limit, name, positive=True)
    body_bytes = len(
        json.dumps(request.get("body", request), ensure_ascii=False, separators=(",", ":")).encode()
    )
    result: dict[str, Any] = {
        "request_sha256": stable_json_sha256(request),
        "condition_sha256": stable_json_sha256(condition),
        "body_bytes": body_bytes,
        "context_limit": context_limit,
        "output_reserve": output_reserve,
        "body_limit": body_limit,
        "state_longest_limit": state_longest_limit,
        "dispatch_allowed": False,
        "status": "context_unverified",
        "counter": receipt.model_dump() if receipt else None,
    }
    if body_limit is not None and body_bytes > body_limit:
        result["status"] = "request_body_overflow"
        return result
    if receipt is None or not qualified_counter_provenance or context_limit is None:
        return result
    if (
        not receipt.exact
        or receipt.provenance != qualified_counter_provenance
        or receipt.request_sha256 != result["request_sha256"]
        or receipt.condition_sha256 != result["condition_sha256"]
    ):
        result["status"] = "counter_binding_mismatch"
        return result
    if state_longest_limit is not None:
        if receipt.state_longest_tokens is None:
            return result
        if receipt.state_longest_tokens > state_longest_limit:
            result["status"] = "state_question_overflow"
            return result
    if receipt.input_tokens + output_reserve > context_limit:
        result["status"] = "context_overflow"
        return result
    result.update(dispatch_allowed=True, status="qualified", input_tokens=receipt.input_tokens)
    return result


def provider_allowance_preflight(
    request: dict[str, Any],
    config: dict[str, Any],
    *,
    context_limit: int,
    output_reserve: int,
    estimated_tokens: int | None = None,
) -> dict[str, Any]:
    """Bound an explicitly authorized provider experiment without claiming exact counts."""
    _integer(context_limit, "context limit", positive=True)
    _integer(output_reserve, "output reserve", positive=True)
    size = len(json.dumps(request["body"], ensure_ascii=False, separators=(",", ":")).encode())
    allowance = size + 8192
    if estimated_tokens is not None:
        _integer(estimated_tokens, "estimated input tokens")
        allowance = max(allowance, (estimated_tokens * 11 + 9) // 10 + 2048)
    limit = min(200000, context_limit // 2)
    allowed = allowance + output_reserve < limit
    return {
        "request_sha256": stable_json_sha256(request),
        "condition_sha256": stable_json_sha256(config),
        "body_bytes": size,
        "input_allowance": allowance,
        "estimated_input_tokens": estimated_tokens,
        "input_tokens": None,
        "output_reserve": output_reserve,
        "allowance_context_limit": limit,
        "exact_preflight": False,
        "counter": None,
        "dispatch_allowed": allowed,
        "status": "exploratory_provider_allowance" if allowed else "context_allowance_overflow",
        "allowance_basis": "utf8_request_bytes_plus_8192_or_estimate_110percent_plus_2048",
    }


def amount(value: Decimal | str | int, *, positive: bool = False) -> Decimal:
    """Parse finite decimal currency without float rounding or boolean coercion."""
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError("Currency must be an exact decimal")
    try:
        parsed = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError("Invalid currency") from error
    if not parsed.is_finite() or parsed < 0 or (positive and parsed == 0):
        raise ValueError("Currency must be finite and positive" if positive else "Invalid currency")
    return parsed


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    rates: Mapping[str, str | int | Decimal],
    *,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> Decimal:
    """Price disjoint input buckets per million tokens; unknown rates fail closed.

    Cache-write rates are the full write price, not a premium to double-count.
    Input tokens include ordinary, cache-read and cache-write tokens.
    """
    for name, value in (
        ("input", input_tokens),
        ("output", output_tokens),
        ("cache read", cache_read_tokens),
        ("cache write", cache_write_tokens),
    ):
        _integer(value, name)
    uncached = input_tokens - cache_read_tokens - cache_write_tokens
    if uncached < 0:
        raise ValueError("Cache buckets exceed total input tokens")
    buckets = {
        "input": uncached,
        "output": output_tokens,
        "cache_read": cache_read_tokens,
        "cache_write": cache_write_tokens,
    }
    total = Decimal(0)
    for key, count in buckets.items():
        if count:
            if key not in rates:
                raise ValueError(f"Missing {key} rate")
            total += count * amount(rates[key]) / Decimal(1_000_000)
    return total


def worst_case_cost(
    input_tokens: int, output_tokens: int, rates: Mapping[str, str | int | Decimal]
) -> Decimal:
    """Reserve the larger complete uncached/write input price before dispatch."""
    selected = dict(rates)
    if "cache_write" in rates:
        selected["input"] = max(amount(rates["input"]), amount(rates["cache_write"]))
    return estimate_cost(input_tokens, output_tokens, selected)


def rates_for_condition(
    pricing: dict[str, Any], *, conservative: bool = True
) -> dict[str, Decimal]:
    """Map dated checked-in per-million prices to exact decimal budget rates.

    JSON numeric prices are converted through their decimal spelling, not binary
    float arithmetic. Missing prices stay absent and fail when a cost needs them.
    Conservative input/output columns already include documented tier premiums.
    """
    rates = {}
    for key in ("input", "output", "cache_read", "cache_write"):
        field = f"{key}_per_million"
        conservative_field = f"conservative_{field}"
        if conservative and conservative_field in pricing:
            field = conservative_field
        value = pricing.get(field)
        if value is not None:
            if isinstance(value, bool):
                raise ValueError("Boolean pricing is invalid")
            rates[key] = amount(str(value))
    return rates


def provider_allowance_rates(
    condition: dict[str, Any], input_tokens: int, body: dict[str, Any]
) -> dict[str, Decimal]:
    """Price only the reviewed Haiku five-minute cache/tier contract; others stay conservative."""
    _integer(input_tokens, "input tokens")
    pricing = condition["pricing"]
    if condition["api"] != "anthropic_messages":
        return rates_for_condition(pricing)
    expected = {"input": "0.1", "cache_read": "0.01", "cache_write": "0.125", "output": "0.5"}
    if condition["model"] != "claude-haiku-5-5" or not pricing.get("verified_date"):
        raise ValueError("Unqualified provider allowance pricing")
    for key, value in expected.items():
        if amount(str(pricing[key + "_per_million"])) != Decimal(value):
            raise ValueError("Haiku allowance rates differ from reviewed pricing")

    def check_cache(value: Any) -> None:
        if isinstance(value, dict):
            if "cache_control" in value and value["cache_control"] != {
                "type": "ephemeral",
                "ttl": "5m",
            }:
                raise ValueError("Haiku allowance requires five-minute cache controls")
            for nested in value.values():
                check_cache(nested)
        elif isinstance(value, list):
            for nested in value:
                check_cache(nested)

    check_cache(body)
    multiplier = 5 if input_tokens > 100000 else 1
    return {key: Decimal(value) * multiplier for key, value in expected.items()}


@dataclass
class RunBudget:
    """Serial run reservations retain worst-case charges, including uncertain attempts."""

    currency_cap: Decimal | str | int
    request_cap: int
    output_cap: int
    wall_seconds: float
    paid: bool = True
    started: float = field(default_factory=time.monotonic)
    halt_reason: str | None = field(default=None, init=False)
    requests_reserved: int = field(default=0, init=False)
    output_reserved: int = field(default=0, init=False)
    currency_reserved: Decimal = field(default=Decimal(0), init=False)

    def __post_init__(self) -> None:
        """Require explicit finite caps before either local or paid execution."""
        self.currency_cap = amount(self.currency_cap, positive=self.paid)
        _integer(self.request_cap, "request cap", positive=True)
        _integer(self.output_cap, "output cap", positive=True)
        if (
            isinstance(self.wall_seconds, bool)
            or not math.isfinite(self.wall_seconds)
            or self.wall_seconds <= 0
        ):
            raise ValueError("Wall-clock cap must be finite and positive")

    def reserve(self, cost: Decimal | str | int, output_tokens: int) -> dict[str, Any]:
        """Atomically check all serial caps before recording an irreversible reservation."""
        if self.halt_reason is not None:
            raise ValueError("run_halted")
        price = amount(cost)
        _integer(output_tokens, "output reservation")
        self.remaining_seconds()
        if self.requests_reserved + 1 > self.request_cap:
            raise ValueError("request_cap")
        if self.output_reserved + output_tokens > self.output_cap:
            raise ValueError("output_cap")
        if self.currency_reserved + price > amount(self.currency_cap):
            raise ValueError("currency_cap")
        self.requests_reserved += 1
        self.output_reserved += output_tokens
        self.currency_reserved += price
        return {
            "request_number": self.requests_reserved,
            "cost_reserved": str(price),
            "output_reserved": output_tokens,
            "total_currency_reserved": str(self.currency_reserved),
        }

    def remaining_seconds(self) -> float:
        """Bound each native timeout by the remaining shared run wall deadline."""
        remaining = self.wall_seconds - (time.monotonic() - self.started)
        if not math.isfinite(remaining) or remaining <= 0:
            raise ValueError("wall_clock_cap")
        return remaining


def _write_new(path: Path, value: dict[str, Any]) -> None:
    """Never replace an earlier attempt artifact, even with identical content."""
    with path.open("xb") as stream:
        stream.write(json_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def begin_attempt(
    directory: Path,
    request: dict[str, Any],
    condition: dict[str, Any],
    diagnostics: dict[str, Any],
    reservation: dict[str, Any],
) -> None:
    """Persist dispatch intent before transport; an unfinished directory forbids replay."""
    if not diagnostics.get("dispatch_allowed"):
        raise ValueError("Unqualified dispatch")
    identities = {
        "request_sha256": stable_json_sha256(request),
        "condition_sha256": stable_json_sha256(condition),
    }
    if any(diagnostics.get(key) != value for key, value in identities.items()):
        raise ValueError("Preflight identity mismatch")
    directory.mkdir(parents=True, exist_ok=False)
    _write_new(
        directory / "intent.json",
        {
            "schema_version": "task09e1.attempt.v1",
            **identities,
            "preflight": diagnostics,
            "reservation": reservation,
        },
    )
    _write_new(directory / "request.json", request)


def complete_attempt(directory: Path, response: dict[str, Any]) -> None:
    """Seal a received native response last; semantic failure does not imply a retry."""
    intent = json.loads((directory / "intent.json").read_text())
    _write_new(directory / "response.json", response)
    _write_new(
        directory / "completion.json",
        {
            "intent_sha256": stable_json_sha256(intent),
            "request_sha256": intent["request_sha256"],
            "condition_sha256": intent["condition_sha256"],
            "response_sha256": stable_json_sha256(response),
        },
    )


class AttemptReceiptError(ValueError):
    """An existing attempt is incomplete or no longer matches its sealed identity."""


def reuse_attempt(
    directory: Path, request: dict[str, Any], condition: dict[str, Any]
) -> dict[str, Any] | None:
    """Return only matching checksum-verified native receipts; never replay uncertain calls."""
    if not directory.exists():
        return None
    if not (directory / "completion.json").is_file():
        raise AttemptReceiptError("Uncertain or incomplete attempt; automatic replay is forbidden")
    try:
        seal = json.loads((directory / "completion.json").read_text())
        intent = json.loads((directory / "intent.json").read_text())
        saved_request = json.loads((directory / "request.json").read_text())
        response = json.loads((directory / "response.json").read_text())
    except (OSError, ValueError) as error:
        raise AttemptReceiptError("Invalid saved attempt receipt") from error
    if any(not isinstance(value, dict) for value in (seal, intent, saved_request, response)):
        raise AttemptReceiptError("Saved attempt receipts must be objects")
    identities = {
        "request_sha256": stable_json_sha256(request),
        "condition_sha256": stable_json_sha256(condition),
    }
    if (
        any(intent.get(key) != value or seal.get(key) != value for key, value in identities.items())
        or stable_json_sha256(saved_request) != identities["request_sha256"]
        or seal.get("intent_sha256") != stable_json_sha256(intent)
        or seal.get("response_sha256") != stable_json_sha256(response)
    ):
        raise AttemptReceiptError("Saved attempt identity or receipt mismatch")
    return response  # type: ignore[no-any-return]
