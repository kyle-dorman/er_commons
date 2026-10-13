"""Inspect-owned comparison stages with durable receipts and fail-closed dispatch."""

from __future__ import annotations

import asyncio
import json
import os
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
from inspect_ai import Task, eval
from inspect_ai.dataset import Sample
from inspect_ai.log import EvalLog
from inspect_ai.scorer import Metric, SampleScore, Score, Scorer, Target, metric, scorer
from inspect_ai.solver import TaskState

from er_commons import grounding_comparison_semantics as semantics
from er_commons.artifact_io import stable_json_sha256
from er_commons.grounding_abstention import abstention_input, route_result
from er_commons.grounding_comparison_panel import file_binding
from er_commons.grounding_comparison_providers import (
    Condition,
    StageKind,
    count_request,
    estimated_count_request,
    parse_response,
    parse_usage,
    render_request,
)
from er_commons.grounding_comparison_safety import (
    AttemptReceiptError,
    CounterReceipt,
    RunBudget,
    begin_attempt,
    complete_attempt,
    preflight,
    provider_allowance_preflight,
    provider_allowance_rates,
    rates_for_condition,
    reuse_attempt,
    worst_case_cost,
)
from er_commons.grounding_inspect import saved_grounding_answer
from er_commons.grounding_records import SavedGroundingSample
from er_commons.grounding_stages import point_inputs
from er_commons.judge_packet_requests import packet_content
from er_commons.judge_qualification import write_new


@metric
def comparison_summary() -> Metric:
    """Keep coverage and errors separate from numerical scores in Inspect."""

    def compute(scores: list[SampleScore]) -> dict[str, int | float | None]:
        records = [(s.score.metadata or {})["comparison_record"] for s in scores]
        result: dict[str, int | float | None] = {"answers": len(records)}
        for status in {r["status"] for r in records}:
            result[f"status_{status}"] = sum(r["status"] == status for r in records)
        for value in range(3):
            result[f"score_{value}"] = sum(r.get("score") == value for r in records)
        stages = [s for r in records for s in r["stages"]]
        result["stages"] = len(stages)
        result["reused_stages"] = sum(s.get("reused", False) for s in stages)
        result["valid_stages"] = sum(s["status"] == "validated" for s in stages)
        result["elapsed_seconds"] = sum(r["elapsed_seconds"] for r in records)
        result["quote_diagnostic_failures"] = sum(
            s.get("result", {}).get("strict_legacy", {}).get("status") == "schema_error"
            for s in stages
        )
        return result

    return compute


def _headers(condition: Condition) -> dict[str, str]:
    """Read a credential only at dispatch; never return it in a receipt or exception."""
    if condition.credential_env is None:
        return {}
    key = os.environ.get(condition.credential_env)
    if not key or not key.strip():
        raise ValueError(f"Missing credential environment variable {condition.credential_env}")
    if condition.api == "anthropic_messages":
        return {"x-api-key": key, "anthropic-version": "2023-06-01"}
    return {"Authorization": f"Bearer {key}"}


class ProviderTransportError(ValueError):
    """Expose only a fixed transport category and status, never remote error content."""

    def __init__(self, http_status: int | None = None) -> None:
        """An unclassified failure is uncertain; every failure forbids automatic retries."""
        self.http_status = http_status
        self.status = "credential_error" if http_status in {401, 403} else "transport_error"
        message = (
            f"Provider HTTP status {http_status}; no automatic retry"
            if http_status is not None
            else "Transport outcome uncertain; inspect durable intent before reconciliation"
        )
        super().__init__(message)


async def _post(
    endpoint: str, body: dict[str, Any], headers: dict[str, str], timeout: float
) -> dict[str, Any]:
    """Use finite HTTP timeouts and redact URLs, headers and raw response/error content."""
    try:
        async with (
            asyncio.timeout(timeout),
            httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=False,
                trust_env=urlsplit(endpoint).hostname not in {"localhost", "127.0.0.1", "::1"},
            ) as client,
        ):
            response = await client.post(endpoint, json=body, headers=headers)
            if not 200 <= response.status_code < 300:
                raise ProviderTransportError(response.status_code)
            value = response.json()
            if not isinstance(value, dict):
                raise ProviderTransportError()
            return value
    except (httpx.HTTPError, json.JSONDecodeError, TimeoutError):
        raise ProviderTransportError() from None


# These failures invalidate dispatch qualification, regardless of counting mode.
_HALT_STATUSES = frozenset(
    {
        "cancelled",
        "storage_error",
        "receipt_error",
        "transport_error",
        "credential_error",
        "context_counter_mismatch",
        "provider_usage_mismatch",
        "identity_mismatch",
        "provider_truncation",
        "provider_input_allowance_exceeded",
        "request_cap",
        "output_cap",
        "currency_cap",
        "wall_clock_cap",
    }
)


def require_provider_allowance(condition: Condition) -> None:
    """Restrict allowance-based dispatch to the explicitly authorized provider models."""
    identities = {
        "anthropic_generation": (
            "anthropic_messages",
            "claude-haiku-5-5",
            "https://api.anthropic.com/v1/messages",
        ),
        "fireworks_deepseek": (
            "fireworks_chat",
            "accounts/fireworks/models/deepseek-v4p1-flash",
            "https://api.fireworks.ai/inference/v1/chat/completions",
        ),
        "fireworks_glm": (
            "fireworks_chat",
            "accounts/fireworks/models/glm-5p3-flash",
            "https://api.fireworks.ai/inference/v1/chat/completions",
        ),
    }
    if (
        identities.get(condition.id) != (condition.api, condition.model, condition.endpoint)
        or condition.kind != "generation"
        or condition.output_cap
        not in ({4096, 8192} if condition.id == "fireworks_deepseek" else {4096})
        or condition.context_limit is None
        or condition.settings.get("reasoning_effort") != "medium"
        or (
            condition.api == "fireworks_chat"
            and condition.settings.get("fireworks_reasoning_mode") != "prompt_schema"
        )
    ):
        raise ValueError("Provider allowance requires an authorized medium provider configuration")


def _prepare_request(
    condition: Condition,
    kind: StageKind,
    payload: dict[str, Any],
    *,
    fixture: dict[str, Any] | None,
    identity: dict[str, Any] | None,
    exploratory_provider_allowance: bool,
    prompt_override: str | None,
    hide_point_predictions: bool,
    conclusion_only: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate stage options and freeze wire content plus receipt identity before I/O."""
    if prompt_override is not None and (
        condition.kind != "generation"
        or not isinstance(prompt_override, str)
        or not prompt_override.strip()
    ):
        raise ValueError("Prompt override requires nonempty generation instructions")
    if type(conclusion_only) is not bool or (conclusion_only and hide_point_predictions):
        raise ValueError("Conclusion-only mode requires an exclusive Boolean opt-in")
    if type(hide_point_predictions) is not bool:
        raise ValueError("hide_point_predictions must be a Boolean")
    if (hide_point_predictions or conclusion_only) and (
        condition.model != "gpt-6-luna"
        or condition.api != "openai_responses"
        or condition.kind != "generation"
        or kind != "conclusion"
        or prompt_override is not None
    ):
        raise ValueError(
            "Hidden predictions require Luna generation conclusions and the common prompt"
        )
    if type(exploratory_provider_allowance) is not bool:
        raise ValueError("Provider allowance requires an exclusive Boolean opt-in")
    if exploratory_provider_allowance:
        require_provider_allowance(condition)
    config: dict[str, Any] = {
        "condition": condition.model_dump(mode="json"),
        "identity": identity,
        "execution_mode": "invented_fixture" if fixture is not None else "native",
    }
    if exploratory_provider_allowance:
        config["execution_mode"] = "exploratory_provider_allowance"
        config["fixture"] = fixture is not None
    if prompt_override is not None:
        config["prompt_override"] = prompt_override
    # Validate the genuine observations before projecting only their IDs onto the wire.
    schema = (
        semantics.conclusion_only_schema(payload)
        if conclusion_only
        else semantics.stage_schema(kind, payload)
    )
    rendered_payload = payload
    if conclusion_only:
        config["conclusion_only"] = True
        rendered_payload = {
            key: value for key, value in payload.items() if key != "point_assessments"
        }
    if hide_point_predictions:
        config["hide_point_predictions"] = True
        rendered_payload = {
            **payload,
            "point_assessments": [
                {"point_id": row["point_id"]} for row in payload["point_assessments"]
            ],
        }
    request = render_request(
        condition,
        kind,
        rendered_payload,
        semantics.conclusion_only_prompt()
        if conclusion_only
        else prompt_override
        if prompt_override is not None
        else semantics.native_stage_prompt(kind)
        if condition.kind == "decision"
        else semantics.stage_prompt(kind),
        schema,
    )
    return request, config


async def _qualify_request(
    condition: Condition,
    request: dict[str, Any],
    config: dict[str, Any],
    budget: RunBudget,
    *,
    fixture: dict[str, Any] | None,
    exploratory_provider_allowance: bool,
) -> tuple[dict[str, Any], CounterReceipt | None, dict[str, Any] | None]:
    """Count or conservatively bound a rendered request before reserving a generation."""
    receipt: CounterReceipt | None = None
    counter_response: dict[str, Any] | None = None
    if exploratory_provider_allowance:
        budget.remaining_seconds()
        if budget.requests_reserved >= budget.request_cap:
            raise ValueError("request_cap")
        if budget.output_reserved + condition.output_cap > budget.output_cap:
            raise ValueError("output_cap")
        # Check byte headroom before any counter access; estimate can only increase it.
        assert condition.context_limit is not None
        diagnostics = provider_allowance_preflight(
            request,
            config,
            context_limit=condition.context_limit,
            output_reserve=condition.output_cap,
        )
        if diagnostics["dispatch_allowed"] and condition.api == "anthropic_messages":
            count = estimated_count_request(request)
            native_count = (
                {"input_tokens": 100}
                if fixture is not None
                else await _post(
                    count["endpoint"],
                    count["body"],
                    _headers(condition),
                    min(60.0, budget.remaining_seconds()),
                )
            )
            estimated = native_count.get("input_tokens")
            if type(estimated) is not int or estimated < 0:
                raise ValueError("Estimated counter lacks nonnegative integer input_tokens")
            diagnostics = provider_allowance_preflight(
                request,
                config,
                context_limit=condition.context_limit,
                output_reserve=condition.output_cap,
                estimated_tokens=estimated,
            )
            diagnostics["estimated_count_request"] = count
            diagnostics["estimated_count_response"] = native_count
    elif fixture is not None:
        receipt = CounterReceipt(
            request_sha256=stable_json_sha256(request),
            condition_sha256=stable_json_sha256(config),
            input_tokens=100,
            state_longest_tokens=100,
            provenance="invented_fixture",
            exact=True,
        )
        provenance = "invented_fixture"
    else:
        budget.remaining_seconds()
        if budget.requests_reserved >= budget.request_cap:
            raise ValueError("request_cap")
        if budget.output_reserved + condition.output_cap > budget.output_cap:
            raise ValueError("output_cap")
        if condition.api != "openai_responses":
            return {"dispatch_allowed": False, "status": "context_unverified"}, None, None
        headers = _headers(condition)
        count = count_request(request)
        native_count = await _post(
            count["endpoint"], count["body"], headers, min(60.0, budget.remaining_seconds())
        )
        if type(native_count.get("input_tokens")) is not int:
            raise ValueError("Authoritative counter response lacks integer input_tokens")
        provenance = "openai.responses.input_tokens.v1"
        receipt = CounterReceipt(
            request_sha256=stable_json_sha256(request),
            condition_sha256=stable_json_sha256(config),
            input_tokens=native_count["input_tokens"],
            provenance=provenance,
            exact=True,
        )
        counter_response = native_count
    if not exploratory_provider_allowance:
        diagnostics = preflight(
            request,
            config,
            receipt,
            context_limit=(condition.context_limit or 10000)
            if fixture is not None
            else condition.context_limit,
            output_reserve=condition.output_cap,
            body_limit=condition.body_bytes_limit,
            state_longest_limit=condition.state_question_limit,
            qualified_counter_provenance=provenance,
        )
    return diagnostics, receipt, counter_response


async def _dispatch_request(
    condition: Condition,
    request: dict[str, Any],
    config: dict[str, Any],
    diagnostics: dict[str, Any],
    receipt: CounterReceipt | None,
    directory: Path,
    budget: RunBudget,
    *,
    fixture: dict[str, Any] | None,
    exploratory_provider_allowance: bool,
) -> dict[str, Any]:
    """Reserve once and persist intent before sending; incomplete attempts never retry."""
    rates = rates_for_condition(condition.pricing.model_dump(mode="json"))
    if exploratory_provider_allowance:
        rates = provider_allowance_rates(
            condition.model_dump(mode="json"),
            diagnostics["input_allowance"],
            request["body"],
        )
        diagnostics["reservation_rates"] = {key: str(value) for key, value in rates.items()}
    cost = (
        worst_case_cost(diagnostics["input_allowance"], condition.output_cap, rates)
        if exploratory_provider_allowance
        else worst_case_cost(receipt.input_tokens, condition.output_cap, rates)
        if receipt is not None
        else worst_case_cost(0, 0, rates)
    )
    if exploratory_provider_allowance:
        if budget.halt_reason is not None:
            raise ValueError("run_halted")
        if cost <= 0:
            raise ValueError("Provider allowance requires positive cost reservation")
    reservation = budget.reserve(cost, condition.output_cap)
    begin_attempt(directory, request, config, diagnostics, reservation)
    native = (
        fixture
        if fixture is not None
        else await _post(
            request["endpoint"],
            request["body"],
            _headers(condition),
            min(60.0, budget.remaining_seconds()),
        )
    )
    complete_attempt(directory, native)
    return native


def _validate_response(
    condition: Condition,
    kind: StageKind,
    payload: dict[str, Any],
    request: dict[str, Any],
    native: dict[str, Any],
    directory: Path,
    record: dict[str, Any],
    receipt: CounterReceipt | None,
    *,
    fixture: dict[str, Any] | None,
    exploratory_provider_allowance: bool,
    conclusion_only: bool,
) -> dict[str, Any]:
    """Check identity and usage before semantics, retaining usage for invalid judgments."""
    record["native_receipt"] = file_binding(directory / "completion.json")
    try:
        usage = parse_usage(condition, native)
    except ValueError:
        record["status"] = "provider_usage_mismatch"
        return record
    record["usage"] = usage
    # Usage survives malformed decisions; qualification is checked before semantics.
    expected_input = None
    if not exploratory_provider_allowance:
        if record["reused"]:
            saved_intent = json.loads((directory / "intent.json").read_text())
            expected_input = saved_intent["preflight"]["input_tokens"]
        elif receipt is not None:
            expected_input = receipt.input_tokens
    if exploratory_provider_allowance:
        diagnostics = json.loads((directory / "intent.json").read_text())["preflight"]
        record["preflight"] = diagnostics
        actual_input = usage.get("input_tokens")
        record["estimated_native_delta"] = (
            actual_input - diagnostics["estimated_input_tokens"]
            if type(actual_input) is int and diagnostics["estimated_input_tokens"] is not None
            else None
        )
        if type(actual_input) is not int or actual_input > diagnostics["input_allowance"]:
            record["status"] = "provider_input_allowance_exceeded"
            return record
        native_rates = provider_allowance_rates(
            condition.model_dump(mode="json"), actual_input, request["body"]
        )
        record["native_cost_bound"] = str(
            worst_case_cost(actual_input, usage.get("output_tokens", 0), native_rates)
        )
        record["native_rates"] = {key: str(value) for key, value in native_rates.items()}
    if fixture is None:
        if native.get("model") != condition.model:
            record["status"] = "identity_mismatch"
            return record
        if not exploratory_provider_allowance and usage.get("input_tokens") != expected_input:
            record["status"] = "context_counter_mismatch"
            return record
        output_tokens = usage.get("output_tokens")
        if condition.kind == "generation" and (
            type(output_tokens) is not int or output_tokens > condition.output_cap
        ):
            record["status"] = "provider_usage_mismatch"
            return record
    if any(native.get(key) is True for key in ("truncated", "context_truncated")):
        record["status"] = "provider_truncation"
        return record
    parsed = parse_response(condition, kind, payload, native)
    record["probabilities"] = parsed["probabilities"]
    record["result"] = (
        semantics.validate_conclusion_only(json.dumps(parsed["decision"]), payload)
        if conclusion_only
        else semantics.validate_stage(
            kind, json.dumps(parsed["decision"]), payload, native=condition.kind == "decision"
        )
    )
    record["status"] = "validated"
    return record


async def run_comparison_stage(
    condition: Condition,
    kind: StageKind,
    payload: dict[str, Any],
    directory: Path,
    budget: RunBudget,
    *,
    fixture: dict[str, Any] | None = None,
    identity: dict[str, Any] | None = None,
    exploratory_provider_allowance: bool = False,
    prompt_override: str | None = None,
    hide_point_predictions: bool = False,
    conclusion_only: bool = False,
) -> dict[str, Any]:
    """Persist one bounded stage; explicit generation prompt overrides bind its identity."""
    started = time.monotonic()
    record: dict[str, Any] = {"kind": kind, "status": "input_error", "reused": False}
    request, config = _prepare_request(
        condition,
        kind,
        payload,
        fixture=fixture,
        identity=identity,
        exploratory_provider_allowance=exploratory_provider_allowance,
        prompt_override=prompt_override,
        hide_point_predictions=hide_point_predictions,
        conclusion_only=conclusion_only,
    )
    record["request_sha256"] = request["request_sha256"]
    receipt: CounterReceipt | None = None
    try:
        if budget.halt_reason is not None:
            record.update(status="run_halted", halt_reason=budget.halt_reason)
            return record
        saved = reuse_attempt(directory, request, config) if directory.exists() else None
        if saved is not None:
            native = saved
            record["reused"] = True
        else:
            diagnostics, receipt, counter_response = await _qualify_request(
                condition,
                request,
                config,
                budget,
                fixture=fixture,
                exploratory_provider_allowance=exploratory_provider_allowance,
            )
            if counter_response is not None:
                record["counter_response"] = counter_response
            if diagnostics["status"] == "context_unverified":
                record.update(status="context_unverified", blockers=condition.blockers)
                return record
            record["preflight"] = diagnostics
            if not diagnostics["dispatch_allowed"]:
                record["status"] = diagnostics["status"]
                return record
            native = await _dispatch_request(
                condition,
                request,
                config,
                diagnostics,
                receipt,
                directory,
                budget,
                fixture=fixture,
                exploratory_provider_allowance=exploratory_provider_allowance,
            )
        _validate_response(
            condition,
            kind,
            payload,
            request,
            native,
            directory,
            record,
            receipt,
            fixture=fixture,
            exploratory_provider_allowance=exploratory_provider_allowance,
            conclusion_only=conclusion_only,
        )
    except asyncio.CancelledError:
        record["status"] = "cancelled"
        raise
    except OSError as error:
        record.update(status="storage_error", error=type(error).__name__)
    except AttemptReceiptError as error:
        record.update(status="receipt_error", error=str(error))
    except ProviderTransportError as error:
        record.update(
            status=error.status,
            error=str(error),
            http_status=error.http_status,
            possibly_billed=True,
            automatic_retry=False,
        )
    except (ValueError, KeyError) as error:
        record.update(status="stage_error", error=str(error))
        if str(error) in {
            "request_cap",
            "output_cap",
            "currency_cap",
            "wall_clock_cap",
            "run_halted",
        }:
            record["status"] = str(error)
    finally:
        if record["status"] in _HALT_STATUSES or (
            exploratory_provider_allowance and record["status"] != "validated"
        ):
            budget.halt_reason = budget.halt_reason or record["status"]
        record["elapsed_seconds"] = time.monotonic() - started
    return record


def resolve_stage_prompts(
    condition: Condition, overrides: Mapping[StageKind, str] | None
) -> dict[StageKind, str]:
    """Copy explicit generation overrides and reject invalid maps before scheduling."""
    if overrides is None:
        return {}
    if not isinstance(overrides, Mapping) or condition.kind != "generation":
        raise ValueError("Stage prompts require a generation condition and mapping")
    if any(
        key not in {"abstention", "point", "conclusion"}
        or not isinstance(value, str)
        or not value.strip()
        for key, value in overrides.items()
    ):
        raise ValueError("Stage prompts require known stages and nonempty strings")
    return dict(overrides)


@scorer(metrics=[comparison_summary()])
def comparison_scorer(
    condition: Condition,
    output: Path,
    budget: RunBudget,
    *,
    fixtures: dict[str, dict[str, dict[str, Any]]] | None = None,
    identity: dict[str, Any] | None = None,
    protocol: str = "run",
    exploratory_provider_allowance: bool = False,
    stage_prompts: Mapping[StageKind, str] | None = None,
) -> Scorer:
    """Own the original gate/point/review graph inside Inspect with serial bounded stages."""
    if protocol not in {"run", "smoke", "cache"}:
        raise ValueError("Unknown comparison protocol")
    prompts = resolve_stage_prompts(condition, stage_prompts)
    halted: list[str] = []

    async def score(state: TaskState, target: Target) -> Score:
        started = time.monotonic()
        sample = SavedGroundingSample.model_validate(state.metadata["grounding_input"])
        directory = output / stable_json_sha256({"sample_id": sample.sample_id})
        directory.mkdir(parents=True, exist_ok=True)
        record: dict[str, Any] = {
            "sample_id": sample.sample_id,
            "case_id": sample.case_id,
            "status": "input_error",
            "score": None,
            "stages": [],
        }

        async def stage(kind: StageKind, key: str, payload: dict[str, Any]) -> dict[str, Any]:
            if halted:
                result: dict[str, Any] = {"kind": kind, "status": "run_halted", "reason": halted[0]}
            else:
                fixture = fixtures[sample.sample_id].get(key, {}) if fixtures is not None else None
                result = await run_comparison_stage(
                    condition,
                    kind,
                    payload,
                    directory / stable_json_sha256({"stage": key}),
                    budget,
                    fixture=fixture,
                    identity=identity,
                    exploratory_provider_allowance=exploratory_provider_allowance,
                    prompt_override=prompts.get(kind),
                )
            result["key"] = key
            record["stages"].append(result)
            if result["status"] in _HALT_STATUSES:
                halted.append(result["status"])
            return result

        if protocol != "run":
            inputs = point_inputs(sample.packet)
            if protocol == "cache" and inputs:
                probe = await stage("point", inputs[0]["point"]["point_id"], inputs[0])
            else:
                probe = await stage("abstention", "abstention", abstention_input(sample.packet))
            record["status"] = (
                "protocol_complete" if probe["status"] == "validated" else probe["status"]
            )
            record["evaluation_denominator"] = False
            record["elapsed_seconds"] = time.monotonic() - started
            index = len(list(directory.glob("result_*.json"))) + 1
            write_new(directory / f"result_{index:04d}.json", record)
            return Score(
                value={"grounding": None},
                explanation=record["status"],
                metadata={"comparison_record": record},
            )
        gate = await stage("abstention", "abstention", abstention_input(sample.packet))
        if gate["status"] == "validated":
            record["status"] = route_result(gate["result"]["decision"]["classification"])
        else:
            record["status"] = gate["status"]
        if record["status"] == "continue":
            predictions = []
            for value in point_inputs(sample.packet):
                result = await stage("point", value["point"]["point_id"], value)
                if result["status"] == "validated":
                    predictions.append(result["result"]["decision"])
                else:
                    record["status"] = result["status"]
            if record["status"] == "continue":
                value = semantics.conclusion_input(sample.packet, predictions)
                conclusion = await stage("conclusion", "conclusion", value)
                if conclusion["status"] == "validated":
                    record.update(
                        semantics.aggregate(predictions, conclusion["result"]["decision"])
                    )
                else:
                    record["status"] = conclusion["status"]
        record["elapsed_seconds"] = time.monotonic() - started
        # Each resume creates a new Inspect log and immutable observation of reused receipts.
        index = len(list(directory.glob("result_*.json"))) + 1
        write_new(directory / f"result_{index:04d}.json", record)
        return Score(
            value={"grounding": record["score"]},
            explanation=record["status"],
            metadata={"comparison_record": record},
        )

    return score


def evaluate_comparison(
    samples: list[SavedGroundingSample],
    condition: Condition,
    output: Path,
    budget: RunBudget,
    *,
    fixtures: dict[str, dict[str, dict[str, Any]]] | None = None,
    identity: dict[str, Any] | None = None,
    protocol: str = "run",
    exploratory_provider_allowance: bool = False,
    stage_prompts: Mapping[StageKind, str] | None = None,
) -> list[EvalLog]:
    """Run one condition through Inspect; fixture inference cannot consume development samples."""
    if protocol not in {"run", "smoke", "cache"}:
        raise ValueError("Unknown comparison protocol")
    prompts = resolve_stage_prompts(condition, stage_prompts)
    if type(exploratory_provider_allowance) is not bool:
        raise ValueError("Provider allowance requires an exclusive Boolean opt-in")
    if exploratory_provider_allowance:
        require_provider_allowance(condition)
    if not samples or len({s.sample_id for s in samples}) != len(samples):
        raise ValueError("Require distinct nonempty samples")
    if fixtures is not None and (
        any(s.scope != "invented_fixture" for s in samples)
        or set(fixtures) != {s.sample_id for s in samples}
    ):
        raise ValueError("Offline responses require matching invented fixtures")
    if fixtures is None and (output / "requests").exists():
        raise ValueError(
            "Live continuation requires a fresh namespace; caps cannot reset on resume"
        )
    task = Task(
        name="task09e1_comparison" if protocol == "run" else f"task09e1_{protocol}_probe",
        dataset=[
            Sample(
                id=s.sample_id,
                input=packet_content(s.packet),
                metadata={"grounding_input": s.model_dump(mode="json")},
            )
            for s in samples
        ],
        solver=saved_grounding_answer(),
        scorer=comparison_scorer(
            condition,
            output / "requests",
            budget,
            fixtures=fixtures,
            identity=identity,
            protocol=protocol,
            exploratory_provider_allowance=exploratory_provider_allowance,
            stage_prompts=prompts if stage_prompts is not None else None,
        ),
    )
    return list(
        eval(
            task,
            model="mockllm/model",
            log_dir=str(output / "inspect"),
            display="none",
            retry_on_error=0,
            fail_on_error=True,
            max_samples=1,
        )
    )
