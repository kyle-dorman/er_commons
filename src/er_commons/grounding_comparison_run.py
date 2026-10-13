"""Prepare or explicitly launch the bounded Task 09E.1 comparison through Inspect.

Default mode is offline. Credentials alone never enable paid calls. Qualified
cloud dispatch additionally requires --execute-paid and all positive run caps.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from er_commons.artifact_io import stable_json_sha256
from er_commons.grounding_comparison_audit import prepare_audit
from er_commons.grounding_comparison_inspect import (
    evaluate_comparison,
    require_provider_allowance,
    resolve_stage_prompts,
)
from er_commons.grounding_comparison_panel import (
    PANEL_RELATIVE,
    file_binding,
    implementation_identity,
    load_dev3,
    load_development_panel,
)
from er_commons.grounding_comparison_providers import CONDITION_IDS, load_conditions
from er_commons.grounding_comparison_safety import RunBudget, rates_for_condition, worst_case_cost
from er_commons.grounding_records import SavedGroundingSample
from er_commons.grounding_stages import point_inputs
from er_commons.judge_qualification import write_new

LOGGER = logging.getLogger(__name__)
DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "configs/grounding_judges_v1.json"


def _protocol_samples(samples: list[SavedGroundingSample], mode: str) -> list[SavedGroundingSample]:
    """Use original saved inputs for probes, excluding probe samples from evaluation results."""
    if not samples:
        raise ValueError("Require a nonempty development panel")
    if mode == "run":
        return samples
    if mode == "smoke":
        return samples[:1]
    with_points = [sample for sample in samples if point_inputs(sample.packet)]
    if not with_points:
        raise ValueError("Cache probe requires a panel with at least one claim")
    first = with_points[0]
    first_evidence = point_inputs(first.packet)[0]["evidence"]
    shared = next(
        (
            sample
            for sample in with_points[1:]
            if point_inputs(sample.packet)[0]["evidence"] == first_evidence
        ),
        None,
    )
    if shared is None:
        raise ValueError("No original shared-evidence point pair available for cache probe")
    return [
        first.model_copy(update={"sample_id": f"{first.sample_id}__probe_{i}"}) for i in (1, 2)
    ] + [shared]


def _receipt_summary(directory: Path, pricing: dict[str, Any]) -> dict[str, Any]:
    """Expose measured probe usage without assuming coldness or charging reused receipts twice."""
    rows = []
    for path in sorted((directory / "requests").glob("*/result_*.json")):
        record = json.loads(path.read_text())
        for stage in record["stages"]:
            usage = stage.get("usage", {})
            input_tokens, output_tokens = usage.get("input_tokens"), usage.get("output_tokens")
            ceiling = None
            if type(input_tokens) is int and type(output_tokens) is int and not stage.get("reused"):
                ceiling = str(
                    worst_case_cost(input_tokens, output_tokens, rates_for_condition(pricing))
                )
            rows.append(
                {
                    "sample_id": record["sample_id"],
                    "stage": stage.get("key"),
                    "status": stage["status"],
                    "native_usage": usage,
                    "reused_saved_receipt": stage.get("reused", False),
                    "conservative_measured_token_cost_usd": ceiling,
                    "elapsed_seconds": stage.get("elapsed_seconds"),
                }
            )
    return {
        "observations": rows,
        "billed_cost_usd": None,
        "first_request_cold": "not assumed; inspect native cache read fields",
        "cache_savings": "unverified unless native receipt fields establish reads/writes",
    }


def launch(args: argparse.Namespace) -> dict[str, Any]:
    """Freeze the configuration before scheduling; incomplete runs require explicit inspection."""
    conditions = load_conditions(args.config)
    selected = (
        conditions
        if args.condition == "all"
        else {
            key: condition
            for key, condition in conditions.items()
            if key == args.condition or args.condition == "all-cloud"
        }
    )
    if not selected:
        raise ValueError("No selected condition")
    if args.manifest is None:
        root = os.environ.get("ER_COMMONS_DATA_ROOT")
        if not root:
            raise ValueError("Set ER_COMMONS_DATA_ROOT or pass --manifest")
        manifest_path = Path(root) / PANEL_RELATIVE
    else:
        manifest_path = args.manifest
    panel = getattr(args, "panel", "dev3")
    expected_sha256 = getattr(args, "manifest_sha256", None)
    if expected_sha256 is not None:
        samples, bindings = load_development_panel(manifest_path, panel, expected_sha256)
    elif panel == "dev3":
        samples, bindings = load_dev3(manifest_path)
    else:
        raise ValueError("An explicit development panel requires --manifest-sha256")
    counting_mode = getattr(args, "counting_mode", "exact")
    if counting_mode not in {"exact", "provider-allowance"}:
        raise ValueError("Unknown counting mode")
    stage_prompts_path = getattr(args, "stage_prompts", None)
    stage_prompts = None
    if stage_prompts_path is not None:
        stage_prompts = json.loads(stage_prompts_path.read_text())
        for condition in selected.values():
            resolve_stage_prompts(condition, stage_prompts)
    if args.mode == "prepare":
        return prepare_audit(
            samples,
            bindings,
            selected,
            args.output,
            args.config,
            stage_prompts=stage_prompts,
            stage_prompts_path=stage_prompts_path,
        )
    if not args.execute_paid:
        raise ValueError("Cloud execution requires explicit --execute-paid; prepare is offline")
    if any(
        value is None
        for value in (args.currency_cap, args.request_cap, args.output_cap, args.wall_seconds)
    ):
        raise ValueError("Execution requires currency, request, output and wall-clock caps")
    budget = RunBudget(
        args.currency_cap,
        args.request_cap,
        args.output_cap,
        args.wall_seconds,
        paid=True,
    )
    if counting_mode == "provider-allowance":
        for condition in selected.values():
            require_provider_allowance(condition)
    chosen_samples = _protocol_samples(samples, args.mode)
    identity = {
        "version": "task09e1.live_run.v1",
        "mode": args.mode,
        "counting_mode": counting_mode,
        "panel": panel,
        "stage_prompts": file_binding(stage_prompts_path) if stage_prompts_path else None,
        "conditions": {key: c.model_dump(mode="json") for key, c in selected.items()},
        "inputs": bindings,
        "config": file_binding(args.config),
        **implementation_identity(),
        "caps": {
            "currency": args.currency_cap,
            "requests": args.request_cap,
            "output_tokens": args.output_cap,
            "wall_seconds": args.wall_seconds,
        },
    }
    # No live continuation into an existing namespace: receipts can be replayed offline,
    # but a fresh process must not reset spending or wall-clock reservations.
    args.output.mkdir(parents=True, exist_ok=False)
    write_new(
        args.output / "manifest.json",
        {
            **identity,
            "deadline_unix": time.time() + args.wall_seconds,
            "identity_sha256": stable_json_sha256(identity),
        },
    )
    results: dict[str, Any] = {}
    for key, condition in selected.items():
        logs = evaluate_comparison(
            chosen_samples,
            condition,
            args.output / key,
            budget,
            identity=identity,
            protocol=args.mode,
            stage_prompts=stage_prompts,
            exploratory_provider_allowance=counting_mode == "provider-allowance",
        )
        results[key] = {
            "inspect_statuses": [log.status for log in logs],
            "logs": [log.location for log in logs],
            "inference_blockers": condition.blockers,
            "protocol_only": args.mode != "run",
            "receipt_summary": _receipt_summary(
                args.output / key, condition.pricing.model_dump(mode="json")
            ),
        }
    summary = {
        "schema_version": "task09e1.run_summary.v1",
        "conditions": results,
        "requests_reserved": budget.requests_reserved,
        "output_reserved": budget.output_reserved,
        "worst_case_currency_reserved": str(budget.currency_reserved),
        "billed_currency": None,
        "automatic_retries": 0,
        "halt_reason": budget.halt_reason,
    }
    if args.mode == "run":
        from er_commons.grounding_comparison_analysis import analyze_runs

        analysis_options = (
            {"panel": panel, "expected_sha256": expected_sha256}
            if expected_sha256 is not None
            else {}
        )
        report = analyze_runs(
            manifest_path, {key: args.output / key for key in selected}, **analysis_options
        )
        write_new(args.output / "analysis.json", report)
    write_new(args.output / "summary.json", summary)
    if budget.halt_reason is not None:
        raise ValueError("Comparison halted; inspect preserved summary and attempt receipts")
    if any(
        not row["inspect_statuses"]
        or any(status != "success" for status in row["inspect_statuses"])
        for row in results.values()
    ):
        raise ValueError("Inspect comparison failed; inspect preserved summary and logs")
    return summary


def main() -> None:
    """Keep offline preparation and each explicitly budgeted cloud selection separate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("prepare", "smoke", "cache", "run"), default="prepare")
    parser.add_argument(
        "--condition", choices=sorted(CONDITION_IDS | {"all", "all-cloud"}), default="fireworks_glm"
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute-paid", action="store_true")
    parser.add_argument(
        "--panel", choices=("dev3", "dev6", "dev6_additions", "full_dev"), default="dev3"
    )
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--stage-prompts", type=Path)
    parser.add_argument("--counting-mode", choices=("exact", "provider-allowance"), default="exact")
    parser.add_argument("--currency-cap")
    parser.add_argument("--request-cap", type=int)
    parser.add_argument("--output-cap", type=int)
    parser.add_argument("--wall-seconds", type=float)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        result = launch(args)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    LOGGER.info("Task 09E.1 artifacts: %s; mode=%s", args.output, args.mode)
    if "conditions" in result and args.mode != "prepare":
        LOGGER.info("Reserved requests: %s", result["requests_reserved"])


if __name__ == "__main__":
    main()
