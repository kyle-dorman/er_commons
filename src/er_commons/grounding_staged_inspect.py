"""Serial staged grounding calls owned by Inspect, with immutable per-call evidence."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from inspect_ai import Task, eval
from inspect_ai.dataset import Sample
from inspect_ai.log import EvalLog
from inspect_ai.scorer import Metric, SampleScore, Score, Scorer, Target, metric, scorer
from inspect_ai.solver import TaskState

from er_commons import grounding_abstention as abstention
from er_commons import grounding_stages as stages
from er_commons.artifact_io import stable_json_sha256
from er_commons.grounding_inspect import saved_grounding_answer
from er_commons.grounding_records import (
    SavedGroundingSample,
    observed_token_counts,
    summarize_records,
)
from er_commons.grounding_stage_runtime import Counter, run_stage
from er_commons.judge_packet_requests import packet_content
from er_commons.judge_qualification import write_new


def _stage_diagnostics(records: list[dict[str, Any]]) -> dict[str, float | int | None]:
    """Compare restricted proposals only to validated stages; missing calls stay uncovered."""
    if not any(r.get("stage_expectations") is not None for r in records):
        return {}
    eligible = {name: 0 for name in ("abstention", "point", "conclusion")}
    pairs: dict[str, list[tuple[bool, bool]]] = {name: [] for name in eligible}
    ambiguous = 0
    for record in records:
        expected = record.get("stage_expectations")
        if expected is None:
            continue
        valid = {s["key"]: s["result"] for s in record["stages"] if s["status"] == "validated"}
        clean = expected.get("clean_abstention")
        if type(clean) is bool:
            eligible["abstention"] += 1
            classification = valid.get("abstention", {}).get("classification")
            if classification in {"clean_abstention", "substantive"}:
                pairs["abstention"].append((clean, classification == "clean_abstention"))
            ambiguous += classification == "ambiguous"
        for point in expected.get("point_expectations", []):
            target = point.get("supported")
            if type(target) is bool:
                eligible["point"] += 1
                prediction = valid.get(point["point_id"], {}).get("supported")
                if type(prediction) is bool:
                    pairs["point"].append((target, prediction))
        target = expected.get("conclusion_supported")
        if type(target) is bool:
            eligible["conclusion"] += 1
            prediction = valid.get("conclusion", {}).get("conclusion_supported")
            if type(prediction) is bool:
                pairs["conclusion"].append((target, prediction))
    result: dict[str, float | int | None] = {"stage_diagnostic_abstention_ambiguous": ambiguous}
    for name, count in eligible.items():
        prefix = f"stage_diagnostic_{name}"
        observed = pairs[name]
        agreements = sum(target == prediction for target, prediction in observed)
        result.update(
            {
                f"{prefix}_eligible": count,
                f"{prefix}_predictions": len(observed),
                f"{prefix}_coverage": len(observed) / count if count else None,
                f"{prefix}_agreements": agreements,
                f"{prefix}_agreement": agreements / len(observed) if observed else None,
            }
        )
        for target in (False, True):
            for prediction in (False, True):
                result[
                    f"{prefix}_expected_{str(target).lower()}_predicted_{str(prediction).lower()}"
                ] = sum(pair == (target, prediction) for pair in observed)
    return result


def summarize_staged_records(records: list[dict[str, Any]]) -> dict[str, float | int | None]:
    """Reuse eligible answer metrics while measuring calls and retries at stage granularity."""
    points_only = bool(records) and all(r.get("points_only", False) for r in records)
    if any(r.get("points_only", False) for r in records) and not points_only:
        raise ValueError("Cannot aggregate points-only and complete-judge runs together")
    summary = (
        {
            "expected": len(records),
            "attempted": sum(r["attempts"] > 0 for r in records),
            "points_complete": sum(r["status"] == "points_complete" for r in records),
            "no_points": sum(r.get("no_points", False) for r in records),
            "elapsed_seconds": sum(r["elapsed_seconds"] for r in records),
        }
        if points_only
        else summarize_records(records)
    )
    calls = [stage for record in records for stage in record["stages"]]
    validated_points = [s for s in calls if s["kind"] == "point" and s["status"] == "validated"]
    summary.update(
        point_supported=sum(s["result"]["supported"] is True for s in validated_points),
        point_unsupported=sum(s["result"]["supported"] is False for s in validated_points),
        unresolved_abstention=sum(r["status"] == "unresolved_abstention" for r in records),
        abstention_calls=sum(s["attempts"] > 0 and s["kind"] == "abstention" for s in calls),
        unresolved_disagreement=sum(r["status"] == "unresolved_disagreement" for r in records),
        stage_calls=sum(s["attempts"] > 0 for s in calls),
        point_calls=sum(s["attempts"] > 0 and s["kind"] == "point" for s in calls),
        conclusion_calls=sum(s["attempts"] > 0 and s["kind"] == "conclusion" for s in calls),
        point_failed=sum(s["status"] != "validated" and s["kind"] == "point" for s in calls),
        conclusion_failed=sum(
            s["status"] != "validated" and s["kind"] == "conclusion" for s in calls
        ),
        stage_attempts=sum(s["attempts"] for s in calls),
        retries=sum(max(0, s["attempts"] - 1) for s in calls),
        stage_validated=sum(s["status"] == "validated" for s in calls),
        stage_expected=sum(r["stage_expected"] for r in records),
        stage_failed=sum(s["status"] != "validated" for s in calls),
        conclusion_skipped=sum("conclusion_skipped" in r for r in records),
        runtime_failed=sum(
            r["status"] in {"runtime_error", "identity_changed", "malformed"} for r in records
        ),
    )
    summary["failed"] = sum(
        r["status"]
        not in {
            "scored",
            "not_applicable",
            "unresolved_disagreement",
            "unresolved_abstention",
            "points_complete",
        }
        for r in records
    )
    summary["evaluation_failed"] = summary["failed"]
    attempts = [a for stage in calls for a in stage["attempt_records"]]
    for name, field in (("input", "prompt_eval_count"), ("output", "eval_count")):
        observations = observed_token_counts(attempts, field)
        summary[f"native_{name}_tokens"] = sum(observations) if observations else None
        summary[f"native_{name}_measured_samples"] = len(observations)
    summary.update(_stage_diagnostics(records))
    return summary


@metric
def staged_grounding_summary() -> Metric:
    """Aggregate durable staged records within Inspect."""

    def compute(scores: list[SampleScore]) -> dict[str, float | int | None]:
        return summarize_staged_records(
            [(s.score.metadata or {})["grounding_record"] for s in scores]
        )

    return compute


@scorer(metrics=[staged_grounding_summary()])
def staged_grounding_scorer(
    *,
    settings: dict[str, Any],
    artifact_dir: Path,
    count_tokens: Counter | None = None,
    counter_model_digest: str | None = None,
    fixture_responses: dict[str, dict[str, dict[str, Any]]] | None = None,
    check_abstention: bool = False,
    points_only: bool = False,
) -> Scorer:
    """Evaluate each point before a conclusion; missing predictions never become false."""

    if points_only and check_abstention:
        raise ValueError("Points-only mode cannot run an abstention gate")
    halted: dict[str, str] = {}

    async def score(state: TaskState, target: Target) -> Score:
        started = time.monotonic()
        sample = SavedGroundingSample.model_validate(state.metadata["grounding_input"])
        directory = artifact_dir / stable_json_sha256({"sample_id": sample.sample_id})
        directory.mkdir(parents=True, exist_ok=False)
        record: dict[str, Any] = {
            "sample_id": sample.sample_id,
            "case_id": sample.case_id,
            "category": sample.category,
            "control": sample.control,
            "expected_score": sample.expected_score,
            "stage_expectations": sample.stage_expectations,
            "abstention_gate_enabled": check_abstention,
            "points_only": points_only,
            "status": "input_error",
            "score": None,
            "attempts": 0,
            "elapsed_seconds": 0.0,
            "reused": False,
            "stages": [],
            "packet_sha256": stable_json_sha256(sample.packet),
            "sample_sha256": stable_json_sha256(sample.model_dump(mode="json")),
            "settings_sha256": stable_json_sha256(settings),
            "execution_mode": "offline_fixture" if fixture_responses is not None else "native",
        }
        fixture = fixture_responses[sample.sample_id] if fixture_responses is not None else None
        common: dict[str, Any] = dict(
            settings=settings,
            count_tokens=count_tokens,
            counter_model_digest=counter_model_digest,
            fixture=fixture,
        )
        predictions = []
        inputs = stages.point_inputs(sample.packet)
        record["stage_expected"] = len(inputs) + int(not points_only) + int(check_abstention)
        record["no_points"] = not inputs
        if halted:
            record.update(status="context_counter_mismatch", conclusion_skipped=halted["reason"])
            return _finish_record(record, directory, started)
        if check_abstention:
            gate = await run_stage(
                key="abstention",
                payload=abstention.abstention_input(sample.packet),
                prompt=abstention.ABSTENTION_PROMPT,
                version=abstention.ABSTENTION_VERSION,
                schema=abstention.response_schema(),
                validator=abstention.validate_result,
                directory=directory / "abstention",
                **common,
            )
            record["stages"].append(gate)
            if gate["status"] != "validated":
                record.update(status=gate["status"], conclusion_skipped="Abstention gate failed")
                if gate["status"] == "context_counter_mismatch":
                    halted["reason"] = "Exact counter disproven; remaining run calls blocked"
                return _finish_record(record, directory, started)
            route = abstention.route_result(gate["result"]["classification"])
            if route != "continue":
                record.update(status=route, conclusion_skipped="Abstention gate routing")
                return _finish_record(record, directory, started)
        for payload in inputs:
            key = payload["point"]["point_id"]
            stage = await run_stage(
                key=key,
                payload=payload,
                prompt=stages.POINT_PROMPT,
                version=stages.POINT_VERSION,
                schema=stages.point_schema(payload),
                validator=stages.validate_point,
                directory=directory / stable_json_sha256({"stage": key}),
                **common,
            )
            record["stages"].append(stage)
            if stage["status"] == "context_counter_mismatch":
                halted["reason"] = "Exact counter disproven; remaining run calls blocked"
                break
            if stage["status"] == "validated":
                predictions.append(stage["result"])
        failed = [s for s in record["stages"] if s["status"] != "validated"]
        if failed:
            record.update(status=failed[0]["status"], conclusion_skipped="Point stage failed")
        elif points_only:
            record.update(status="points_complete", conclusion_skipped="Points-only mode")
        else:
            payload = stages.conclusion_input(sample.packet, predictions)
            stage = await run_stage(
                key="conclusion",
                payload=payload,
                prompt=stages.CONCLUSION_PROMPT,
                version=stages.CONCLUSION_VERSION,
                schema=stages.conclusion_schema(payload),
                validator=stages.validate_conclusion,
                directory=directory / "conclusion",
                **common,
            )
            record["stages"].append(stage)
            if stage["status"] == "validated":
                record.update(stages.aggregate(predictions, stage["result"]))
            else:
                record["status"] = stage["status"]
                if stage["status"] == "context_counter_mismatch":
                    halted["reason"] = "Exact counter disproven; remaining run calls blocked"
        return _finish_record(record, directory, started)

    return score


def _finish_record(record: dict[str, Any], directory: Path, started: float) -> Score:
    """Persist every terminal sample status, including operationally blocked samples."""
    record["attempts"] = sum(s["attempts"] for s in record["stages"])
    record["elapsed_seconds"] = time.monotonic() - started
    write_new(directory / "grounding_record.json", record)
    write_new(directory / "completion.json", {"record_sha256": stable_json_sha256(record)})
    return Score(
        value={"grounding": record["score"]},
        explanation=record["status"],
        metadata={"grounding_record": record},
    )


def evaluate_staged_samples(
    samples: list[SavedGroundingSample],
    *,
    settings: dict[str, Any],
    artifact_dir: Path,
    log_dir: Path,
    count_tokens: Counter | None = None,
    counter_model_digest: str | None = None,
    fixture_responses: dict[str, dict[str, dict[str, Any]]] | None = None,
    check_abstention: bool = False,
    points_only: bool = False,
) -> list[EvalLog]:
    """Execute a fresh immutable panel in Inspect; existing artifacts require a new namespace."""
    if points_only and check_abstention:
        raise ValueError("Points-only mode cannot run an abstention gate")
    if artifact_dir.exists() or log_dir.exists():
        raise ValueError("Staged evaluation requires fresh artifact and log directories; no resume")
    if not samples or len({s.sample_id for s in samples}) != len(samples):
        raise ValueError("Require distinct nonempty samples")
    if len({s.scope for s in samples}) != 1:
        raise ValueError("Do not mix fixture and development scopes")
    if fixture_responses is not None:
        if any(s.scope != "invented_fixture" for s in samples):
            raise ValueError("Fixture responses require invented_fixture scope")
        if set(fixture_responses) != {s.sample_id for s in samples}:
            raise ValueError("Fixture response identities must match samples")
    for sample in samples:
        packet_content(sample.packet)
        stages.point_inputs(sample.packet)
    task = Task(
        name="task09e_staged_grounding",
        dataset=[
            Sample(
                id=s.sample_id,
                input=packet_content(s.packet),
                metadata={"grounding_input": s.model_dump(mode="json")},
            )
            for s in samples
        ],
        solver=saved_grounding_answer(),
        scorer=staged_grounding_scorer(
            settings=settings,
            artifact_dir=artifact_dir,
            count_tokens=count_tokens,
            counter_model_digest=counter_model_digest,
            fixture_responses=fixture_responses,
            check_abstention=check_abstention,
            points_only=points_only,
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
