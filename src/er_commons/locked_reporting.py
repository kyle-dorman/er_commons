"""Replay a sealed Task 13 run and publish its complete test-only reporting roster."""

from __future__ import annotations

import tempfile
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from er_commons import development_evaluation as evaluation
from er_commons.artifact_io import sha256_bytes, sha256_file, stable_json_sha256
from er_commons.context_comparison import delivery
from er_commons.locked_inputs import planned_slots
from er_commons.reporting import answer_tables, citation_tables, complexity_tables
from er_commons.reporting_counts import citation_complexity
from er_commons.reporting_inputs import SealedInputs, _json, _same
from er_commons.reporting_judges import build_historical_judge_tables
from er_commons.reporting_review import export_review
from er_commons.reporting_run import _binding, _csv, _implementation
from er_commons.reporting_run import _json as encode_json


def _replay_judgments(
    sealed: SealedInputs,
    relative: str,
    plan: dict[str, Any],
    frozen: dict[str, Any],
) -> list[dict[str, Any]]:
    """Verify saved judgments in order against their plan and frozen judge context."""
    saved_judgments = sorted(
        name
        for name in sealed.files
        if name.startswith(f"{relative}/judgments/") and name.endswith("/judgment.json")
    )
    judgments = [sealed.json(name) for name in saved_judgments]
    if f"{relative}/judgments.json" in sealed.files:
        declared = sealed.json(f"{relative}/judgments.json")
        _same(
            sorted(judgments, key=lambda j: j["sample_id"]),
            sorted(declared, key=lambda j: j["sample_id"]),
            "judgment inventory",
        )
    seen = set()
    for judgment in judgments:
        sample = judgment["sample_id"]
        if sample in seen:
            raise ValueError("Duplicate judgment")
        seen.add(sample)
        item = next((item for item in plan["items"] if item["sample_id"] == sample), None)
        if item is None or judgment["component"] != item["component"]:
            raise ValueError("Orphan or cross-component judgment")
        component = judgment["component"]
        model = frozen["targets"]["haiku" if component == "S" else "luna"]["model"]
        if judgment["model"] != model or judgment.get("returned_model") not in (None, model):
            raise ValueError("Frozen judge identity mismatch")
        folder = f"{relative}/judgments/{sample}"
        _same(judgment, sealed.json(f"{folder}/judgment.json"), "raw judgment")
        _same(item, sealed.json(f"{folder}/item.json"), "judge item")
        context = sealed.json(f"{folder}/context_envelope.json")
        context_id = stable_json_sha256({k: v for k, v in context.items() if k != "context_id"})
        if (
            context["context_id"] != context_id
            or judgment["context_id"] != context_id
            or context["parent_sample_id"] != sample
            or stable_json_sha256(context["prompt"])
            != frozen["effective_prompts_sha256"]["all19"]["judges"][component]
        ):
            raise ValueError("Frozen judge context mismatch")
        _same(context["payload"], item["packet"], "judge payload")
    return judgments


def _observation(
    sealed: SealedInputs,
    slot: dict[str, Any],
    data: dict[str, Any],
    frozen: dict[str, Any],
    preflight: dict[str, Any],
    summary_override: dict[str, Any] | None = None,
    *,
    delivery_fn: Callable[[dict[str, Any], str], dict[str, Any]] = delivery,
) -> dict[str, Any]:
    """Replay every present evaluation, including incomplete and failed observations."""
    relative = f"observations/{slot['model']}_repeat{slot['repeat']}/{slot['case_id']}"
    identity = {**slot, "run_id": stable_json_sha256({"slot": slot, "preflight": preflight})}
    if f"{relative}/manifest.json" in sealed.files:
        _same(sealed.json(f"{relative}/manifest.json"), identity, "slot manifest")
    if f"{relative}/summary.json" in sealed.files:
        summary = sealed.json(f"{relative}/summary.json")
    elif f"{relative}/interruption.json" in sealed.files:
        summary = sealed.json(f"{relative}/interruption.json")
    elif summary_override is not None:
        summary = summary_override
    else:
        raise ValueError("Missing slot outcome")
    _same({key: summary[key] for key in identity}, identity, "slot summary")
    row = {
        **slot,
        "split": "test",
        "exposure_group": "test_30",
        "identity": identity,
        "model_id": frozen["targets"][slot["model"]]["model"],
        "source_path": relative,
        "status": summary["status"],
        "candidate": None,
        "plan": None,
        "report": None,
        "judgments": [],
        "complexity": None,
        "unavailable_reason": summary.get("reason", summary["status"]),
    }
    generation_path = f"{relative}/generation/result.json"
    if generation_path not in sealed.files:
        if summary["status"] == "completed":
            raise ValueError("Completed slot has no generation")
        return row
    generation = sealed.json(generation_path)
    if any(generation.get(k) != identity[k] for k in ("case_id", "repeat", "run_id")):
        raise ValueError("Cross-slot generation identity")
    if generation.get("model") != row["model_id"]:
        raise ValueError("Frozen target model mismatch")
    if generation["status"] not in {"valid", "invalid_output"}:
        if summary["status"] == "completed":
            raise ValueError("Execution failure has completed evaluation")
        return row
    if generation.get("returned_model") != row["model_id"]:
        raise ValueError("Returned target model mismatch")
    candidate_name = "candidate.json" if generation["status"] == "valid" else "raw_output.txt"
    candidate = sealed.read(f"{relative}/generation/{candidate_name}")
    if sha256_bytes(candidate) != generation["candidate_sha256"]:
        raise ValueError("Candidate digest mismatch")
    native = sealed.read(f"{relative}/generation/native_request.json")
    if sha256_bytes(native) != generation["request_sha256"]:
        raise ValueError("Native request digest mismatch")
    actual_delivery = delivery_fn(_json(native), generation["provider"])
    _same(
        actual_delivery, sealed.json(f"{relative}/generation/delivery_projection.json"), "delivery"
    )
    _same(sealed.json(f"{relative}/generation/packet.json"), data["record"], "packet")
    plan = evaluation.prepare_candidate(
        candidate,
        generation,
        data["record"],
        data["mapping"],
        actual_delivery,
        data["reference"],
        expected_split="test",
    )
    if plan["automatic"].get("schema") != "invalid":
        row["candidate"] = _json(candidate)
    if f"{relative}/plan.json" in sealed.files:
        _same(plan, sealed.json(f"{relative}/plan.json"), "plan")
    elif summary["status"] == "completed":
        raise ValueError("Completed slot lacks evaluation plan")
    if f"{relative}/mapping.json" in sealed.files:
        _same(sealed.json(f"{relative}/mapping.json"), data["mapping"], "mapping")
    judgments = _replay_judgments(sealed, relative, plan, frozen)
    report = evaluation.build_report(plan, judgments)
    if f"{relative}/report.json" in sealed.files:
        _same(report, sealed.json(f"{relative}/report.json"), "report")
    elif summary["status"] == "completed":
        raise ValueError("Completed slot lacks saved report")
    if summary["status"] == "completed" and not report["coverage_complete"]:
        raise ValueError("Completed slot has incomplete evaluation")
    row.update(
        identity=plan["identity"],
        plan=plan,
        report=report,
        judgments=judgments,
        complexity=citation_complexity(report["automatic"], data["mapping"]),
    )
    return row


def load_run(repo: Path, source: Path, completion_sha256: str) -> dict[str, Any]:
    """Verify the complete seal and exactly 180 planned slots without development loading."""
    seal_bytes = (source / "completion.json").read_bytes()
    if sha256_bytes(seal_bytes) != completion_sha256:
        raise ValueError("Locked completion digest mismatch")
    sealed = SealedInputs(source, _json(seal_bytes))
    for name in sealed.files:
        sealed.read(name)
    frozen_bytes = (repo / "docs/specs/task11e_frozen_generation_v1.json").read_bytes()
    if sealed.read("frozen_configuration.json") != frozen_bytes:
        raise ValueError("Frozen configuration changed")
    frozen = _json(frozen_bytes)
    data = sealed.json("inputs.json")
    preflight = sealed.json("preflight.json")
    expected = planned_slots(list(data))
    slots = preflight["slots"]
    if sorted(slots, key=stable_json_sha256) != sorted(expected, key=stable_json_sha256):
        raise ValueError("Missing, duplicate or non-test planned slots")
    outcomes = {}
    if "slot_results.json" in sealed.files:
        for outcome in sealed.json("slot_results.json"):
            key = (outcome["model"], outcome["repeat"], outcome["case_id"])
            if key in outcomes:
                raise ValueError("Duplicate slot outcome")
            outcomes[key] = outcome
        if set(outcomes) != {(s["model"], s["repeat"], s["case_id"]) for s in slots}:
            raise ValueError("Slot outcome roster mismatch")
    rows = [
        _observation(
            sealed,
            slot,
            data[slot["case_id"]],
            frozen,
            preflight,
            outcomes.get((slot["model"], slot["repeat"], slot["case_id"])),
        )
        for slot in slots
    ]
    return {
        "rows": rows,
        "configuration": frozen,
        "preflight": preflight,
        "stop_reason": (
            sealed.json("accounting.json").get("stop_reason")
            if "accounting.json" in sealed.files
            else None
        ),
        "source_completion_sha256": completion_sha256,
        "source_files": list(sealed.consumed.values()),
    }


def publish(
    repo: Path,
    data_root: Path,
    source: Path,
    output: Path,
    review_output: Path,
    completion_sha256: str,
) -> dict[str, Any]:
    """Publish a create-only sealed test report and separate final gallery offline."""
    repo, data_root = repo.resolve(), data_root.resolve()
    source, output, review_output = source.resolve(), output.resolve(), review_output.resolve()
    task_root = data_root / "pipelines/brisbane_baylands/task_13"
    for path in (source, output, review_output):
        if not path.is_relative_to(task_root) or path.is_relative_to(repo):
            raise ValueError("Task 13 artifacts must remain under the external task namespace")
    if output.exists() or review_output.exists():
        raise ValueError("Select fresh report and review destinations")
    if any(
        a.is_relative_to(b)
        for a, b in (
            (output, source),
            (source, output),
            (review_output, source),
            (source, review_output),
            (review_output, output),
            (output, review_output),
        )
    ):
        raise ValueError("Run, report and gallery must be separate")
    loaded = load_run(repo, source, completion_sha256)
    tables = answer_tables(loaded["rows"])
    tables["execution_status"] = [
        {
            "model": model,
            "planned": 90,
            "stop_reason": loaded["stop_reason"],
            **dict(Counter(row["status"] for row in loaded["rows"] if row["model"] == model)),
        }
        for model in ("luna", "haiku")
    ]
    tables["citation_results"] = citation_tables(tables["answers"])
    tables["complexity"] = complexity_tables(tables["answers"])
    tables.update(build_historical_judge_tables(repo))
    manifest = {
        "schema_version": "task13.reporting.v1",
        "scope": "test_only",
        "planned_answers": 180,
        "questions": 30,
        "new_calls": 0,
        "source": str(source),
        "source_completion_sha256": completion_sha256,
        "source_files": loaded["source_files"],
        "configuration": loaded["configuration"],
        "implementation": _implementation(repo),
        "historical_judge_sources": tables["judge_sources"],
        "recomputed_answers": sum(row["report"] is not None for row in loaded["rows"]),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".task13-report-", dir=output.parent) as temporary:
        staging = Path(temporary) / "report"
        staging.mkdir()
        for name, rows in tables.items():
            (staging / f"{name}.json").write_bytes(encode_json(rows))
            (staging / f"{name}.csv").write_bytes(_csv(rows))
        (staging / "manifest.json").write_bytes(encode_json(manifest))
        seal = {
            "schema_version": "task13.reporting.completion.v1",
            "files": [_binding(path, path.name) for path in sorted(staging.iterdir())],
        }
        (staging / "completion.json").write_bytes(encode_json(seal))
        if output.exists():
            raise ValueError("Report destination appeared during publication")
        staging.rename(output)
    export_review(output, review_output, sha256_file(output / "completion.json"))
    return manifest


def main() -> None:
    """Expose replay and final gallery publication without any remote execution path."""
    import argparse
    import logging
    import os

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--completion-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review-output", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    result = publish(
        Path(__file__).resolve().parents[2],
        Path(os.environ["ER_COMMONS_DATA_ROOT"]),
        args.source,
        args.output,
        args.review_output,
        args.completion_sha256,
    )
    logging.info("locked_reporting_complete planned=%s", result["planned_answers"])


if __name__ == "__main__":
    main()
