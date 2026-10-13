"""Offline rendered-request, prefix and conservative cost audit for the frozen panel."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons import grounding_comparison_semantics as semantics
from er_commons.artifact_io import stable_json_sha256
from er_commons.grounding_abstention import abstention_input
from er_commons.grounding_comparison_panel import file_binding, implementation_identity
from er_commons.grounding_comparison_providers import (
    Condition,
    StageKind,
    cache_prefix_text,
    render_request,
)
from er_commons.grounding_comparison_safety import rates_for_condition, worst_case_cost
from er_commons.grounding_records import SavedGroundingSample
from er_commons.grounding_stages import point_inputs
from er_commons.judge_qualification import write_new


def prefix_bytes(left: bytes, right: bytes) -> int:
    """Measure a byte prefix only; this does not establish cache token eligibility."""
    return next(
        (i for i, pair in enumerate(zip(left, right, strict=False)) if pair[0] != pair[1]),
        min(len(left), len(right)),
    )


def request_plan(sample: SavedGroundingSample) -> list[tuple[StageKind, str, dict[str, Any]]]:
    """Enumerate stage shapes with explicitly synthetic conclusion observations."""
    inputs = point_inputs(sample.packet)
    planned: list[tuple[StageKind, str, dict[str, Any]]] = [
        ("abstention", "abstention", abstention_input(sample.packet))
    ]
    planned.extend(("point", p["point"]["point_id"], p) for p in inputs)
    for flag in (False, True):
        observations = [{"point_id": p["point"]["point_id"], "supported": flag} for p in inputs]
        planned.append(
            (
                "conclusion",
                f"conclusion_audit_all_{str(flag).lower()}",
                semantics.conclusion_input(sample.packet, observations),
            )
        )
    return planned


def audit_condition(
    samples: list[SavedGroundingSample],
    condition: Condition,
    output: Path,
    *,
    stage_prompts: dict[StageKind, str] | None = None,
) -> dict[str, Any]:
    """Persist each rendered request without inferring model output or exact tokens."""
    if not samples:
        raise ValueError("Require a nonempty development panel")
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    previous: dict[str, bytes] = {}
    for sample in samples:
        for kind, key, payload in request_plan(sample):
            rendered = render_request(
                condition,
                kind,
                payload,
                semantics.native_stage_prompt(kind)
                if condition.kind == "decision"
                else (stage_prompts or {}).get(kind, semantics.stage_prompt(kind)),
                semantics.stage_schema(kind, payload),
            )
            data = json.dumps(rendered["body"], ensure_ascii=False, separators=(",", ":")).encode()
            visible = cache_prefix_text(rendered).encode()
            identity = stable_json_sha256({"sample_id": sample.sample_id, "stage": key})
            write_new(
                output / f"{identity}.json",
                {
                    "sample_id": sample.sample_id,
                    "stage": key,
                    "kind": kind,
                    "audit_only": True,
                    "synthetic_observations": kind == "conclusion",
                    "request": rendered,
                },
            )
            rows.append(
                {
                    "sample_id": sample.sample_id,
                    "kind": kind,
                    "stage": key,
                    "request_sha256": rendered["request_sha256"],
                    "body_bytes": len(data),
                    "previous_same_stage_visible_prefix_bytes": prefix_bytes(
                        previous.get(kind, b""), visible
                    ),
                    "body_limit_exceeded": condition.body_bytes_limit is not None
                    and len(data) > condition.body_bytes_limit,
                }
            )
            previous[kind] = visible
    stage_cap = sum(len(point_inputs(s.packet)) + 2 for s in samples)
    rates = rates_for_condition(condition.pricing.model_dump(mode="json"))
    ceiling = (
        str(stage_cap * worst_case_cost(condition.context_limit, condition.output_cap, rates))
        if condition.context_limit is not None
        else None
    )
    summary = {
        "condition": condition.id,
        "sample_count": len(samples),
        "rendered_requests": len(rows),
        "maximum_stage_calls": stage_cap,
        "automatic_retries": 0,
        "maximum_output_tokens": stage_cap * condition.output_cap,
        "body_limit_exceeded": sum(r["body_limit_exceeded"] for r in rows),
        "body_bytes_min": min(r["body_bytes"] for r in rows),
        "body_bytes_max": max(r["body_bytes"] for r in rows),
        "prefix_unit": "bytes_of_visible_prefix_not_exact_tokens",
        "prefix_bytes_max": max(r["previous_same_stage_visible_prefix_bytes"] for r in rows),
        "exact_input_tokens": None,
        "cache_eligibility_verified": False,
        "native_cache_measurements": None,
        "no_cache_estimate_usd": None,
        "plausible_cache_estimate_usd": None,
        "worst_case_context_ceiling_usd": ceiling,
        "ceiling_basis": (
            "Every call at full context plus output; includes highest write/tier rates"
        ),
        "cache_savings_assumed": "0; exact eligible prefixes and native cache receipts unavailable",
        "estimate_limitation": (
            "Exact request counts unavailable offline; no speculative token conversion"
        ),
        "pricing": condition.pricing.model_dump(mode="json"),
        "cache_policy": condition.cache.model_dump(mode="json"),
        "inference_blockers": condition.blockers,
        "requests": rows,
    }
    write_new(output / "audit.json", summary)
    return {key: value for key, value in summary.items() if key != "requests"}


def prepare_audit(
    samples: list[SavedGroundingSample],
    bindings: dict[str, Any],
    conditions: dict[str, Condition],
    output: Path,
    config_path: Path,
    *,
    stage_prompts: dict[StageKind, str] | None = None,
    stage_prompts_path: Path | None = None,
) -> dict[str, Any]:
    """Seal a fresh offline experiment with exact code, configuration and input bindings."""
    if not samples:
        raise ValueError("Require a nonempty development panel")
    output.mkdir(parents=True, exist_ok=False)
    audits = {
        key: audit_condition(samples, condition, output / key, stage_prompts=stage_prompts)
        for key, condition in conditions.items()
    }
    manifest = {
        "schema_version": "task09e1.experiment.v1",
        "mode": "offline_readiness",
        "result_version": semantics.VERSION,
        "inputs": bindings,
        "configuration": file_binding(config_path),
        "stage_prompts": file_binding(stage_prompts_path) if stage_prompts_path else None,
        "conditions": {key: c.model_dump(mode="json") for key, c in conditions.items()},
        **implementation_identity(),
        "semantic_contract": file_binding(
            Path(__file__).resolve().parents[2] / "docs/specs/task09e1_comparison_v1.md"
        ),
        "audits": audits,
        "inference_calls": 0,
        "paid_calls": 0,
        "prior_artifacts_modified": False,
        "expectations_loaded": False,
        "conclusion_audit": "all-false/all-true shapes only; runtime requires actual observations",
    }
    write_new(output / "manifest.json", manifest)
    inventory = [file_binding(p) for p in sorted(output.rglob("*.json"))]
    write_new(
        output / "completion.json", {"schema_version": "task09e1.completion.v1", "files": inventory}
    )
    return manifest
