"""Inspect-owned answer-only abstention classification, without grounding scores."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from inspect_ai import Task, eval
from inspect_ai.dataset import Sample
from inspect_ai.log import EvalLog
from inspect_ai.model import ModelOutput
from inspect_ai.scorer import Metric, SampleScore, Score, Scorer, Target, metric, scorer
from inspect_ai.solver import Generate, Solver, TaskState, solver

from er_commons import grounding_abstention as abstention
from er_commons.artifact_io import stable_json_sha256
from er_commons.grounding_inspect import SavedGroundingSample, _observed_token_counts
from er_commons.grounding_staged_inspect import Counter, _run_stage
from er_commons.judge_qualification import write_new


def summarize_abstention_records(records: list[dict[str, Any]]) -> dict[str, float | int | None]:
    """Expose classifications and diagnostic denominators without a grounding score."""
    valid = [r for r in records if r["status"] == "classified"]
    eligible = [r for r in valid if r["classification"] != "ambiguous"]
    stages = [s for r in records for s in r["stages"]]
    attempts = [a for s in stages for a in s["attempt_records"]]
    summary: dict[str, float | int | None] = {
        "expected": len(records),
        "attempted": sum(r["attempts"] > 0 for r in records),
        "classified": len(valid),
        "failed": len(records) - len(valid),
        "context_blocked": sum(r["status"].startswith("context_") for r in records),
        "schema_failed": sum(r["status"] == "schema_error" for r in records),
        "output_limit": sum(r["status"] == "output_limit" for r in records),
        "stage_calls": sum(s["attempts"] > 0 for s in stages),
        "stage_attempts": sum(s["attempts"] for s in stages),
        "retries": sum(max(0, s["attempts"] - 1) for s in stages),
        "elapsed_seconds": sum(r["elapsed_seconds"] for r in records),
        "synthetic_comparable": len(eligible),
        "synthetic_agreement": (
            sum(
                (r["classification"] == "clean_abstention") == r["expected_clean"] for r in eligible
            )
            / len(eligible)
            if eligible
            else None
        ),
    }
    for label in ("clean_abstention", "substantive", "ambiguous"):
        summary[label] = sum(r["classification"] == label for r in valid)
    for name, field in (("input", "prompt_eval_count"), ("output", "eval_count")):
        values = _observed_token_counts(attempts, field)
        summary[f"native_{name}_tokens"] = sum(values) if values else None
        summary[f"native_{name}_measured_calls"] = len(values)
    summary["exact_input_parity_calls"] = sum(
        s.get("native", {}).get("output", {}).get("prompt_eval_count")
        == s.get("preflight", {}).get("input_tokens")
        and type(s.get("preflight", {}).get("input_tokens")) is int
        for s in stages
        if isinstance(s.get("native", {}).get("output"), dict)
    )
    return summary


@metric
def abstention_summary() -> Metric:
    """Let Inspect aggregate classification records and explicit error denominators."""

    def compute(scores: list[SampleScore]) -> dict[str, float | int | None]:
        return summarize_abstention_records(
            [(s.score.metadata or {})["abstention_record"] for s in scores]
        )

    return compute


@solver
def saved_answer_text() -> Solver:
    """Record only the supplied answer text without target generation."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        state.output = ModelOutput.from_content("saved-answer", str(state.input))
        return state

    return solve


@scorer(metrics=[abstention_summary()])
def abstention_scorer(
    *,
    settings: dict[str, Any],
    artifact_dir: Path,
    count_tokens: Counter | None = None,
    counter_model_digest: str | None = None,
    fixture_responses: dict[str, dict[str, dict[str, Any]]] | None = None,
) -> Scorer:
    """Run one answer-only classifier call; a disproven counter halts remaining dispatch."""
    halted = False

    async def score(state: TaskState, target: Target) -> Score:
        nonlocal halted
        started = time.monotonic()
        sample = SavedGroundingSample.model_validate(state.metadata["grounding_input"])
        directory = artifact_dir / stable_json_sha256({"sample_id": sample.sample_id})
        directory.mkdir(parents=True, exist_ok=False)
        record: dict[str, Any] = {
            "sample_id": sample.sample_id,
            "case_id": sample.case_id,
            "expected_clean": sample.expected_score is None,
            "classification": None,
            "status": "context_counter_mismatch" if halted else "input_error",
            "stages": [],
            "packet_sha256": stable_json_sha256(sample.packet),
            "sample_sha256": stable_json_sha256(sample.model_dump(mode="json")),
            "settings_sha256": stable_json_sha256(settings),
            "execution_mode": "offline_fixture" if fixture_responses is not None else "native",
        }
        if not halted:
            payload = abstention.abstention_input(sample.packet)
            stage = await _run_stage(
                key="abstention",
                payload=payload,
                prompt=abstention.ABSTENTION_PROMPT,
                version=abstention.ABSTENTION_VERSION,
                schema=abstention.response_schema(),
                validator=abstention.validate_result,
                directory=directory / "abstention",
                settings=settings,
                count_tokens=count_tokens,
                counter_model_digest=counter_model_digest,
                fixture=fixture_responses[sample.sample_id]
                if fixture_responses is not None
                else None,
            )
            record["stages"].append(stage)
            record["status"] = stage["status"]
            if stage["status"] == "validated":
                record.update(status="classified", classification=stage["result"]["classification"])
            halted = stage["status"] == "context_counter_mismatch"
        record["attempts"] = sum(s["attempts"] for s in record["stages"])
        record["elapsed_seconds"] = time.monotonic() - started
        write_new(directory / "abstention_record.json", record)
        write_new(directory / "completion.json", {"record_sha256": stable_json_sha256(record)})
        return Score(
            value={"classification": record["classification"]},
            explanation=record["status"],
            metadata={"abstention_record": record},
        )

    return score


def evaluate_abstention_samples(
    samples: list[SavedGroundingSample],
    *,
    settings: dict[str, Any],
    artifact_dir: Path,
    log_dir: Path,
    count_tokens: Counter | None = None,
    counter_model_digest: str | None = None,
    fixture_responses: dict[str, dict[str, dict[str, Any]]] | None = None,
) -> list[EvalLog]:
    """Run a fresh answer-only panel through Inspect; no point or conclusion calls occur."""
    if artifact_dir.exists() or log_dir.exists():
        raise ValueError("Abstention evaluation requires fresh artifact and log directories")
    if not samples or len({s.sample_id for s in samples}) != len(samples):
        raise ValueError("Require distinct nonempty samples")
    if len({s.scope for s in samples}) != 1:
        raise ValueError("Do not mix fixture and development scopes")
    if fixture_responses is not None:
        if any(s.scope != "invented_fixture" for s in samples):
            raise ValueError("Fixture responses require invented_fixture scope")
        if set(fixture_responses) != {s.sample_id for s in samples}:
            raise ValueError("Fixture identities must match samples")
    dataset = [
        Sample(
            id=s.sample_id,
            input=json.dumps(abstention.abstention_input(s.packet)),
            metadata={"grounding_input": s.model_dump(mode="json")},
        )
        for s in samples
    ]
    task = Task(
        name="task09e_abstention",
        dataset=dataset,
        solver=saved_answer_text(),
        scorer=abstention_scorer(
            settings=settings,
            artifact_dir=artifact_dir,
            count_tokens=count_tokens,
            counter_model_digest=counter_model_digest,
            fixture_responses=fixture_responses,
        ),
    )
    return list(
        eval(
            task,
            model="mockllm/model",
            log_dir=str(log_dir),
            display="none",
            retry_on_error=0,
            fail_on_error=True,
            max_samples=1,
        )
    )
