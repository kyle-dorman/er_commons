"""Bounded saved-candidate evaluation with native Inspect transport and sealed replay."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from er_commons import development_evaluation_inputs as inputs
from er_commons import development_evaluation_provider as provider
from er_commons.artifact_io import (
    artifact_inventory,
    publish_bytes_no_clobber,
    sha256_bytes,
    sha256_file,
    stable_json_sha256,
)
from er_commons.target_generation import REPO, save


def evaluation_limits(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Allow bounded operational overrides without changing frozen per-call policy."""
    caps = {
        "max_judge_calls": 72,
        "max_count_calls": 72,
        "max_spend_usd": 24.0,
        "max_elapsed_seconds": 1800,
        "max_input_tokens": 100000,
        "count_cost_allowance_usd": 0.30,
    }
    overrides = overrides or {}
    if set(overrides) - set(caps):
        raise ValueError("Only operational run limits may change")
    for key, value in overrides.items():
        expected = (int, float) if key in {"max_spend_usd", "count_cost_allowance_usd"} else (int,)
        if type(value) not in expected:
            raise ValueError(f"Invalid operational limit: {key}")
        valid_value = (
            0 <= value <= caps[key] if key == "count_cost_allowance_usd" else 0 < value <= caps[key]
        )
        if not valid_value:
            raise ValueError(f"Invalid operational limit: {key}")
    return {**provider.LIMITS, **overrides}


def run_manifest(
    plans: list[dict[str, Any]], limits: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Record worst-case fanout, semantic bindings and accounting before dispatch."""
    limits = evaluation_limits(limits)
    count = sum(sum(item["status"] == "not_run" for item in plan["items"]) for plan in plans)
    if count > min(limits["max_judge_calls"], limits["max_count_calls"]):
        raise ValueError("Judge fanout exceeds declared call limit")
    reserve = count * (
        limits["count_cost_allowance_usd"]
        + (
            limits["max_input_tokens"] * limits["reserve_input_per_million"]
            + limits["max_output_tokens"] * limits["reserve_output_per_million"]
        )
        / 1_000_000
    )
    if reserve > limits["max_spend_usd"]:
        raise ValueError("Prospective liability exceeds spending ceiling")
    configs = {}
    for component in ("A", "G", "S", "C"):
        condition, prompt, config = provider.component_settings(component)
        configs[component] = {
            "condition": condition,
            "prompt_sha256": sha256_bytes(prompt.encode()),
            "frozen_config": config.model_dump(mode="json", exclude_none=True),
            "execution_overrides": {"max_retries": 0, "max_connections": 1},
        }
    return {
        "schema_version": "task11c.run.v1",
        "limits": limits,
        "prospective_calls": count,
        "reserved_usd": reserve,
        "plans_sha256": stable_json_sha256(plans),
        "components": configs,
        "target_generation_calls": 0,
        "input_bindings": {
            name: sha256_file(REPO / name)
            for name in (
                "docs/specs/task11b_final_result.json",
                "docs/specs/task11a_development_panels_v1.json",
                "docs/specs/task09g_judge_freeze_v1.json",
                "docs/specs/task09f_question_publication_v2_result.json",
                "uv.lock",
                "src/er_commons/no_answer.py",
                "src/er_commons/point_grounding.py",
                "src/er_commons/adequacy_binary.py",
                "src/er_commons/judge_inspect.py",
                "configs/judges_selected_v1.json",
                "configs/judge_models_v1.json",
                "src/er_commons/no_answer_inspect.py",
                "src/er_commons/point_grounding_inspect.py",
                "src/er_commons/adequacy_inspect.py",
            )
        },
        "implementation": {
            name: sha256_file(Path(__file__).with_name(name))
            for name in (
                "development_evaluation.py",
                "development_evaluation_inputs.py",
                "development_evaluation_provider.py",
                "development_evaluation_run.py",
            )
        },
    }


def replay_run(
    output: Path,
    plans: list[dict[str, Any]],
    manifest: dict[str, Any],
    *,
    allow_source_change: bool,
) -> dict[str, Any]:
    """Verify sealed receipts and rebuild reports without constructing a provider."""
    from er_commons.development_evaluation import build_report

    if json.loads((output / "completion.json").read_text()) != artifact_inventory(
        output, {"completion.json"}
    ):
        raise ValueError("Evaluation inventory changed")
    execution_manifest = json.loads((output / "manifest.json").read_text())
    ignored = {"implementation"} if allow_source_change else set()
    if {k: v for k, v in execution_manifest.items() if k not in ignored} != {
        k: v for k, v in manifest.items() if k not in ignored
    }:
        raise ValueError("Evaluation inputs/configuration changed")
    judgments = json.loads((output / "judgments.json").read_text())
    known = {item["sample_id"]: plan["identity"] for plan in plans for item in plan["items"]}
    seen = set()
    for judgment in judgments:
        sample = judgment["sample_id"]
        if sample in seen or sample not in known or judgment["identity"] != known[sample]:
            raise ValueError("Duplicate, orphan or cross-answer judgment")
        seen.add(sample)
    reports = [
        build_report(plan, [j for j in judgments if j["identity"] == plan["identity"]])
        for plan in plans
    ]
    if stable_json_sha256(reports) != stable_json_sha256(
        json.loads((output / "reports.json").read_text())
    ):
        raise ValueError("Report replay differs")
    return {
        "replay": "verified",
        "new_calls": 0,
        "reports": reports,
        "source_change_allowed": allow_source_change,
        "execution_implementation": execution_manifest["implementation"],
        "replay_implementation": manifest["implementation"],
    }


async def run(
    data_root: Path,
    output: Path,
    *,
    replay: bool = False,
    allow_replay_source_change: bool = False,
    generation_run: Path | None = None,
    limits: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate a fresh namespace, or verify and replay its sealed saved judgments."""
    from er_commons.development_evaluation import build_report, pending_items, readable_report

    if not data_root.is_dir() or not output.resolve().is_relative_to(data_root.resolve()):
        raise ValueError("Output must be under configured external root")
    if allow_replay_source_change and not replay:
        raise ValueError("Source-change allowance requires replay")
    plans = (
        inputs.load_plans(data_root)
        if generation_run is None
        else inputs.load_plans(data_root, generation_run)
    )
    manifest = run_manifest(plans) if limits is None else run_manifest(plans, limits)
    if generation_run is not None:
        manifest["generation_run"] = {
            "namespace": str(generation_run.resolve().relative_to(data_root.resolve())),
            "completion_sha256": sha256_file(generation_run / "completion.json"),
        }
    if replay:
        return replay_run(output, plans, manifest, allow_source_change=allow_replay_source_change)
    if output.exists():
        raise ValueError("Existing/interrupted namespace: accounting unknown; redispatch forbidden")
    output.mkdir(parents=True, exist_ok=False)
    save(output / "manifest.json", manifest)
    save(output / "plans.json", plans)
    deadline = time.monotonic() + manifest["limits"]["max_elapsed_seconds"]
    judgments = []
    reports = []
    stopped = False
    for plan in plans:
        case_judgments: list[dict[str, Any]] = []
        while not stopped and (items := pending_items(plan, case_judgments)):
            for item in items:
                directory = output / "judgments" / item["sample_id"]
                directory.mkdir(parents=True, exist_ok=False)
                result = await provider.execute_item(
                    item, plan["identity"], directory, deadline, manifest["limits"]
                )
                case_judgments.append(result)
                stopped = result["status"] == "execution_error"
                if stopped:
                    break
        judgments.extend(case_judgments)
        report = build_report(plan, case_judgments)
        save(output / "questions" / f"{plan['identity']['case_id']}.json", report)
        publish_bytes_no_clobber(
            output / "questions" / f"{plan['identity']['case_id']}.md",
            readable_report(report).encode(),
        )
        reports.append(report)
    save(output / "judgments.json", judgments)
    save(output / "reports.json", reports)
    summary = {
        "case_ids": [plan["identity"]["case_id"] for plan in plans],
        "judge_calls": sum(j["judge_calls"] for j in judgments),
        "count_calls": sum(j["count_calls"] for j in judgments),
        "execution_errors": sum(j["status"] == "execution_error" for j in judgments),
        "reserved_usd": manifest["reserved_usd"],
        "actual_count_cost_usd": None,
        "target_generation_calls": 0,
    }
    save(output / "summary.json", summary)
    save(output / "completion.json", artifact_inventory(output, {"completion.json"}))
    return summary


def main() -> None:
    """Expose bounded fixed-panel evaluation and no-network sealed replay commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--generation-run", type=Path)
    parser.add_argument("--limits-config", type=Path)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--allow-replay-source-change", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    root = os.environ.get("ER_COMMONS_DATA_ROOT")
    if not root:
        raise ValueError("ER_COMMONS_DATA_ROOT required")
    logging.info(
        "Evaluation result: %s",
        asyncio.run(
            run(
                Path(root),
                args.output,
                replay=args.replay,
                generation_run=args.generation_run,
                limits=json.loads(args.limits_config.read_text()) if args.limits_config else None,
                allow_replay_source_change=args.allow_replay_source_change,
            )
        ),
    )


if __name__ == "__main__":
    main()
