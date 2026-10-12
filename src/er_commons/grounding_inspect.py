"""Thin Inspect execution and explicit diagnostic aggregation for saved grounding."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

import httpx
from inspect_ai import Task, eval
from inspect_ai.dataset import Sample
from inspect_ai.log import EvalLog
from inspect_ai.model import ModelOutput
from inspect_ai.scorer import Metric, SampleScore, Score, Scorer, Target, metric, scorer
from inspect_ai.solver import Generate, Solver, TaskState, solver
from pydantic import BaseModel, ConfigDict, Field

from er_commons.artifact_io import stable_json_sha256
from er_commons.grounding_judge import (
    PROMPT,
    PROMPT_VERSION,
    response_schema,
    validate_completion,
    validate_result,
)
from er_commons.judge_packet_requests import packet_content, prepare_request
from er_commons.judge_qualification import (
    IdentityMismatch,
    call_native_judge,
    check_live_model,
    write_new,
)


class SavedGroundingSample(BaseModel):
    """A saved packet with labels restricted to analysis rather than grader input."""

    model_config = ConfigDict(strict=True, extra="forbid")
    sample_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    scope: Literal["invented_fixture", "development"]
    packet: dict[str, Any]
    expected_score: int | None = Field(ge=0, le=2)
    category: str = Field(min_length=1)
    control: bool = False
    stage_expectations: dict[str, Any] | None = None


def _observed_token_counts(records: list[dict[str, Any]], field: str) -> list[int]:
    """Retain only observed nonnegative integer measurements from native objects."""
    counts = []
    for record in records:
        if record.get("reused"):
            continue
        native = record.get("native")
        output = native.get("output") if isinstance(native, dict) else None
        value = output.get(field) if isinstance(output, dict) else None
        if type(value) is int and value >= 0:
            counts.append(value)
    return counts


def summarize_records(records: list[dict[str, Any]]) -> dict[str, float | int | None]:
    """Expose all denominators; numeric confusion excludes failures and N/A."""
    scored = [r for r in records if r["status"] == "scored"]
    na = [r for r in records if r["status"] == "not_applicable"]
    comparable = [r for r in scored if r["expected_score"] is not None]
    valid = scored + na
    expected_na = [r for r in valid if r["expected_score"] is None]
    proposed_errors = [r for r in scored if r["expected_score"] in (0, 1)]
    controls = [r for r in valid if r["control"]]
    count = len(scored)
    input_counts = _observed_token_counts(records, "prompt_eval_count")
    output_counts = _observed_token_counts(records, "eval_count")
    summary: dict[str, float | int | None] = {
        "expected": len(records),
        "attempted": sum(r["attempts"] > 0 for r in records),
        "new": sum(r["attempts"] > 0 for r in records),
        "reused": sum(r.get("reused", False) for r in records),
        "scored": count,
        "not_applicable": len(na),
        "failed": len(records) - len(valid),
        "context_blocked": sum(r["status"].startswith("context_") for r in records),
        "schema_failed": sum(r["status"] == "schema_error" for r in records),
        "retries": sum(max(0, r["attempts"] - 1) for r in records),
        "valid_findings": len(valid),
        "grounding_mean": sum(r["score"] for r in scored) / count if count else None,
        "synthetic_numeric_comparable": len(comparable),
        "synthetic_exact_agreement": (
            sum(r["score"] == r["expected_score"] for r in comparable) / len(comparable)
            if comparable
            else None
        ),
        "synthetic_ordinal_absolute_error": (
            sum(abs(r["score"] - r["expected_score"]) for r in comparable) / len(comparable)
            if comparable
            else None
        ),
        "expected_na_valid": len(expected_na),
        "unexpected_na": sum(r["expected_score"] is not None for r in na),
        "numeric_expected_valid_denominator": sum(r["expected_score"] is not None for r in valid),
        "native_input_tokens": sum(input_counts) if input_counts else None,
        "native_input_measured_samples": len(input_counts),
        "native_output_tokens": sum(output_counts) if output_counts else None,
        "native_output_measured_samples": len(output_counts),
        "na_agreement": (
            sum(r["status"] == "not_applicable" for r in expected_na) / len(expected_na)
            if expected_na
            else None
        ),
        "false_supported_count": sum(r["score"] == 2 for r in proposed_errors),
        "false_supported_denominator": len(proposed_errors),
        "control_rejected_count": sum(r["score"] != 2 for r in controls),
        "control_valid_denominator": len(controls),
        "control_scored_denominator": sum(r["status"] == "scored" for r in controls),
        "elapsed_seconds": sum(r["elapsed_seconds"] for r in records),
    }
    for score in range(3):
        summary[f"score_{score}"] = sum(r["score"] == score for r in scored)
        for expected in range(3):
            summary[f"confusion_expected_{expected}_judge_{score}"] = sum(
                r["score"] == score and r["expected_score"] == expected for r in comparable
            )
    question_means = []
    for case_id in sorted({r["case_id"] for r in scored}):
        rows = [r for r in scored if r["case_id"] == case_id]
        question_means.append(sum(r["score"] for r in rows) / len(rows))
    summary["question_balanced_grounding_mean"] = (
        sum(question_means) / len(question_means) if question_means else None
    )
    question_rates = []
    for case_id in sorted({r["case_id"] for r in records}):
        rows = [r for r in comparable if r["case_id"] == case_id]
        if rows:
            question_rates.append(sum(r["score"] == r["expected_score"] for r in rows) / len(rows))
    summary["question_balanced_agreement"] = (
        sum(question_rates) / len(question_rates) if question_rates else None
    )
    summary["question_agreement_denominator"] = len(question_rates)
    for field in ("case_id", "category"):
        for label in sorted({r.get(field, "unspecified") for r in records}):
            rows = [r for r in records if r.get(field, "unspecified") == label]
            eligible = [r for r in rows if r["status"] == "scored"]
            prefix = f"by_{field}_{label}"
            summary[f"{prefix}_expected"] = len(rows)
            summary[f"{prefix}_scored"] = len(eligible)
            summary[f"{prefix}_mean"] = (
                sum(r["score"] for r in eligible) / len(eligible) if eligible else None
            )
    return summary


@metric
def grounding_summary() -> Metric:
    """Let Inspect aggregate the complete records rather than error sentinel values."""

    def compute(scores: list[SampleScore]) -> dict[str, float | int | None]:
        """Recover explicitly eligible records retained on every Inspect score."""
        return summarize_records([(s.score.metadata or {})["grounding_record"] for s in scores])

    return compute


@solver
def saved_grounding_answer() -> Solver:
    """Keep the exact saved answer in Inspect's trace with zero target generation."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        """Read only the validated model-visible payload, never the target."""
        payload = json.loads(str(state.input))
        state.output = ModelOutput.from_content("saved-answer", json.dumps(payload["answer"]))
        return state

    return solve


def _transient(error: Exception) -> bool:
    """Retry only transient network or rate/server failures, never schema outcomes."""
    return isinstance(error, (httpx.TimeoutException, httpx.NetworkError)) or (
        isinstance(error, httpx.HTTPStatusError)
        and (error.response.status_code in {408, 429} or error.response.status_code >= 500)
    )


@scorer(metrics=[grounding_summary()])
def grounding_scorer(
    *,
    settings: dict[str, Any],
    artifact_dir: Path,
    count_tokens: Callable[[dict[str, Any]], int] | None = None,
    counter_model_digest: str | None = None,
    fixture_responses: dict[str, dict[str, Any]] | None = None,
) -> Scorer:
    """Use validated packet requests and native transport inside Inspect execution."""

    async def score(state: TaskState, target: Target) -> Score:
        """Persist preflight and each raw attempt before parsing source-linked results."""
        started = time.monotonic()
        sample = SavedGroundingSample.model_validate(state.metadata["grounding_input"])
        schema = response_schema(sample.packet)
        # Hash IDs for filesystem safety; raw sample identity remains in the receipt.
        directory = artifact_dir / stable_json_sha256({"sample_id": sample.sample_id})
        record: dict[str, Any] = {
            "sample_id": sample.sample_id,
            "case_id": sample.case_id,
            "expected_score": sample.expected_score,
            "category": sample.category,
            "control": sample.control,
            "status": "input_error",
            "score": None,
            "attempts": 0,
            "elapsed_seconds": 0.0,
            "prompt_version": PROMPT_VERSION,
            "prompt_sha256": stable_json_sha256(PROMPT),
            "schema_sha256": stable_json_sha256(schema),
            "settings_sha256": stable_json_sha256(settings),
            "packet_sha256": stable_json_sha256(sample.packet),
            "sample_sha256": stable_json_sha256(sample.model_dump(mode="json")),
            "reused": False,
            "execution_mode": "offline_fixture" if fixture_responses is not None else "native",
        }
        if directory.exists():
            previous = json.loads((directory / "grounding_record.json").read_text())
            seal = json.loads((directory / "completion.json").read_text())
            if seal.get("record_sha256") != stable_json_sha256(previous):
                raise ValueError("Existing grounding result checksum differs")
            current_request = prepare_request(
                sample.packet,
                system_prompt=PROMPT,
                response_schema=schema,
                settings=settings,
            )
            if (
                previous.get("preflight", {}).get("request_sha256")
                != current_request["diagnostics"]["request_sha256"]
            ):
                raise ValueError("Existing full native request identity differs")
            bindings = (
                "prompt_sha256",
                "schema_sha256",
                "settings_sha256",
                "packet_sha256",
                "sample_sha256",
                "execution_mode",
            )
            if any(previous.get(key) != record[key] for key in bindings):
                raise ValueError(
                    "Existing grounding result identity differs; use a fresh run directory"
                )
            if previous["status"] not in {"scored", "not_applicable"}:
                raise ValueError("Only completed valid exact-identity results may resume")
            validated = validate_result(json.dumps(previous["result"]), sample.packet)
            expected_status = "not_applicable" if validated.score is None else "scored"
            if previous["score"] != validated.score or previous["status"] != expected_status:
                raise ValueError("Existing score/status differs from its validated result")
            if not previous["preflight"]["dispatch_allowed"]:
                raise ValueError("Existing result lacks a dispatch-authorizing exact preflight")
            previous.update(
                reused=True, original_attempts=previous["attempts"], attempts=0, elapsed_seconds=0.0
            )
            return Score(
                value={"grounding": previous["score"]},
                explanation=previous["status"],
                metadata={"grounding_record": previous},
            )
        directory.mkdir(parents=True, exist_ok=False)
        try:
            prepared = prepare_request(
                sample.packet,
                system_prompt=PROMPT,
                response_schema=schema,
                settings=settings,
                count_tokens=count_tokens,
                counter_model_digest=counter_model_digest,
            )
            write_new(directory / "preflight.json", prepared)
            record["preflight"] = prepared["diagnostics"]
            if not prepared["diagnostics"]["dispatch_allowed"]:
                record["status"] = prepared["diagnostics"]["status"]
            else:
                transport_request = {
                    "settings": settings,
                    "messages": prepared["request"]["messages"],
                    "schema": prepared["request"]["format"],
                }
                captured: dict[str, Any] = {}
                for attempt in range(2):
                    attempt_dir = directory / f"attempt_{attempt + 1}"
                    attempt_dir.mkdir()
                    write_new(attempt_dir / "native_request.json", prepared["request"])
                    record["attempts"] += 1
                    try:
                        if fixture_responses is not None:
                            if sample.scope != "invented_fixture":
                                raise ValueError(
                                    "Fixture transport requires invented_fixture scope"
                                )
                            output = fixture_responses[sample.sample_id]
                            write_new(attempt_dir / "fixture_response.json", output)
                            captured = {"output": output, **validate_completion(output, settings)}
                        else:
                            await asyncio.to_thread(check_live_model, settings, attempt_dir)
                            await call_native_judge(
                                transport_request,
                                attempt_dir,
                                captured,
                                output_validator=validate_completion,
                            )
                        break
                    except (
                        httpx.HTTPError,
                        OSError,
                        IdentityMismatch,
                        json.JSONDecodeError,
                    ) as error:
                        captured = {"status": "runtime_error", "error": repr(error)}
                        write_new(attempt_dir / "failure.json", captured)
                        if attempt or not _transient(error):
                            break
                record["status"] = captured["status"]
                record["native"] = captured
                if (
                    captured["status"] == "complete"
                    and captured["output"]["prompt_eval_count"]
                    != prepared["diagnostics"]["input_tokens"]
                ):
                    record.update(
                        status="context_counter_mismatch",
                        error="Observed native input count differs from exact preflight",
                    )
                elif captured["status"] == "complete":
                    try:
                        result = validate_result(captured["raw_judgment"], sample.packet)
                    except ValueError as error:
                        record.update(status="schema_error", error=str(error))
                    else:
                        record.update(
                            status="not_applicable" if result.score is None else "scored",
                            score=result.score,
                            result=result.model_dump(mode="json"),
                        )
        except (ValueError, KeyError) as error:
            record.update(status="input_error", error=str(error))
        record["elapsed_seconds"] = time.monotonic() - started
        write_new(directory / "grounding_record.json", record)
        if record["status"] in {"scored", "not_applicable"}:
            write_new(directory / "completion.json", {"record_sha256": stable_json_sha256(record)})
        return Score(
            value={"grounding": record["score"]},
            explanation=record["status"],
            metadata={"grounding_record": record},
        )

    return score


def grounding_task(
    samples: list[SavedGroundingSample],
    *,
    settings: dict[str, Any],
    artifact_dir: Path,
    count_tokens: Callable[[dict[str, Any]], int] | None = None,
    counter_model_digest: str | None = None,
    fixture_responses: dict[str, dict[str, Any]] | None = None,
) -> Task:
    """Build one explicit saved panel; never discover partitions or generate answers."""
    if not samples or len({s.sample_id for s in samples}) != len(samples):
        raise ValueError("Require nonempty samples with distinct sample IDs")
    if len({s.scope for s in samples}) != 1:
        raise ValueError("Do not mix fixture and development scopes")
    if fixture_responses is not None and any(s.scope != "invented_fixture" for s in samples):
        raise ValueError("Fixture responses cannot be used with development samples")
    for sample in samples:
        if sample.packet.get("dimension") != "grounding":
            raise ValueError("Require reference-blind grounding packets")
        packet_content(sample.packet)
    return Task(
        name="task09e_grounding",
        dataset=[
            Sample(
                id=s.sample_id,
                input=packet_content(s.packet),
                metadata={"grounding_input": s.model_dump(mode="json")},
            )
            for s in samples
        ],
        solver=saved_grounding_answer(),
        scorer=grounding_scorer(
            settings=settings,
            artifact_dir=artifact_dir,
            count_tokens=count_tokens,
            counter_model_digest=counter_model_digest,
            fixture_responses=fixture_responses,
        ),
    )


def evaluate_grounding_samples(
    samples: list[SavedGroundingSample],
    *,
    settings: dict[str, Any],
    artifact_dir: Path,
    log_dir: Path,
    count_tokens: Callable[[dict[str, Any]], int] | None = None,
    counter_model_digest: str | None = None,
    fixture_responses: dict[str, dict[str, Any]] | None = None,
) -> list[EvalLog]:
    """Delegate execution and aggregation to Inspect with its automatic retries disabled."""
    return list(
        eval(
            grounding_task(
                samples,
                settings=settings,
                artifact_dir=artifact_dir,
                count_tokens=count_tokens,
                counter_model_digest=counter_model_digest,
                fixture_responses=fixture_responses,
            ),
            model="mockllm/model",
            log_dir=str(log_dir),
            display="none",
            retry_on_error=0,
            fail_on_error=True,
            max_samples=1,
        )
    )
