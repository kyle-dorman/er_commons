"""Thin Inspect execution and explicit diagnostic aggregation for saved grounding."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
from inspect_ai import Task, eval
from inspect_ai.dataset import Sample
from inspect_ai.log import EvalLog
from inspect_ai.model import ModelOutput
from inspect_ai.scorer import Metric, SampleScore, Score, Scorer, Target, metric, scorer
from inspect_ai.solver import Generate, Solver, TaskState, solver

from er_commons.artifact_io import stable_json_sha256
from er_commons.grounding_judge import (
    PROMPT,
    PROMPT_VERSION,
    response_schema,
    validate_completion,
    validate_result,
)
from er_commons.grounding_native import is_transient_error

# Saved external experiment runners import these names from this module.
from er_commons.grounding_records import SavedGroundingSample as SavedGroundingSample
from er_commons.grounding_records import summarize_records as summarize_records
from er_commons.judge_packet_requests import packet_content, prepare_request
from er_commons.judge_qualification import (
    IdentityMismatch,
    call_native_judge,
    check_live_model,
    write_new,
)


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
                        if attempt or not is_transient_error(error):
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
