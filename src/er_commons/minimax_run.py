"""Separate Task 13A execution with immutable inputs and cumulative spending."""

from __future__ import annotations

import asyncio
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from er_commons import locked_run, minimax_provider
from er_commons.artifact_io import (
    artifact_inventory,
    publish_bytes_no_clobber,
    sha256_file,
    stable_json_sha256,
)
from er_commons.locked_audit import audit_ledger
from er_commons.locked_dispatch import LockedDispatcher, Request
from er_commons.locked_inputs import load_locked
from er_commons.reporting_inputs import SealedInputs
from er_commons.target_generation import REPO, output_schema, save

ROOT = Path("pipelines/brisbane_baylands/task_13a")
PROBES = ROOT / "compatibility_20261020_v2"
PROBE_SEAL = "0dd80c20501904536c4462b1651bde082f73c4de6cc7892c984144cf22f2e841"
CONDITION = {
    "model": "minimax-m3.1-flash",
    "condition": "minimax_cloud",
    "provider": "ollama",
    "endpoint": "https://ollama.com/v1/chat/completions",
    "reasoning_effort": "medium",
    "schema_delivery": "native_response_format",
    "repair": False,
    "max_output_tokens": 12288,
    "ordinary_input_per_million": "0.15",
    "ordinary_output_per_million": "0.60",
    "reservation_usd": "0.0223728",
    "promotion_ends_at": "2026-10-22T23:59:00Z",
}
LIMITS = {
    "concurrency": 10,
    "judge_per_answer": 30,
    "dispatch_seconds": 21600,
    "evaluation_seconds": 1800,
    "request_seconds": 900,
    "retries": 0,
}


def planned_slots(cases: list[str]) -> list[dict[str, Any]]:
    """Retain exactly thirty questions and three fresh answers without sampling."""
    if len(cases) != 30 or len(set(cases)) != 30:
        raise ValueError("Expected thirty unique test cases")
    return [
        {
            "arm": "test30",
            "model": "minimax",
            "condition": "minimax_cloud",
            "repeat": repeat,
            "case_id": case,
        }
        for repeat in (1, 2, 3)
        for case in cases
    ]


def input_bounds(inputs: dict[str, Any], prompt: str) -> dict[str, int]:
    """Bound serialized input bytes before dispatch without reading model outcomes.

    Default JSON spacing exceeds compact wire serialization; the template allowance
    is conservative rather than an exact tokenizer count, verified again on the wire.
    """
    bounds = {}
    for case, data in inputs.items():
        native = {
            "model": minimax_provider.MODEL,
            "max_tokens": minimax_provider.OUTPUT_LIMIT,
            "reasoning_effort": "medium",
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": minimax_provider.SCHEMA_NAME,
                    "schema": output_schema(),
                    "description": None,
                    "strict": None,
                },
            },
            "messages": [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": json.dumps(data["record"]["payload"], ensure_ascii=False),
                },
            ],
        }
        bound = len(json.dumps(native, ensure_ascii=False).encode()) + 4096
        if bound > minimax_provider.INPUT_LIMIT:
            raise ValueError(f"Conservative serialized input bound exceeded: {case}")
        bounds[case] = bound
    return bounds


def cumulative_basis(data_root: Path) -> dict[str, Any]:
    """Bind prior sealed accounting and every compatibility receipt before spending."""
    pointer = locked_run.read(REPO / "docs/specs/task13_result.json")
    binding = pointer["run_completion"]
    completion = data_root / binding["path"]
    if sha256_file(completion) != binding["sha256"]:
        raise ValueError("Prior Task 13 seal changed")
    source = completion.parent
    sealed = SealedInputs(source, locked_run.read(completion))
    accounting = sealed.json("accounting.json")
    for name in sealed.files:
        if name.startswith("ledger/"):
            sealed.read(name)
    prior = audit_ledger(source / "ledger")
    if (
        prior["unsettled_keys"]
        or accounting["stop_reason"]
        or Decimal(accounting["liability_usd"]) != Decimal(prior["final_planning_liability_usd"])
    ):
        raise ValueError("Prior Task 13 accounting unresolved")
    probes = data_root / PROBES
    if sha256_file(probes / "completion.json") != PROBE_SEAL:
        raise ValueError("Compatibility seal changed")
    probe_sealed = SealedInputs(probes, locked_run.read(probes / "completion.json"))
    for name in probe_sealed.files:
        probe_sealed.read(name)
    development = probe_sealed.json("development_summary.json")
    probe_audit = audit_ledger(probes / "ledger")
    if (
        development["format"] != "valid_without_repair"
        or probe_audit["unsettled_keys"]
        or probe_audit["counts"] != {"generation": 2, "judge": 0, "count": 0}
    ):
        raise ValueError("Development compatibility or probe accounting unresolved")
    liability = Decimal(prior["final_planning_liability_usd"]) + Decimal(
        probe_audit["final_planning_liability_usd"]
    )
    remaining = Decimal("10") - liability
    if not 0 < remaining <= 10:
        raise ValueError("No authorized allowance remains")
    return {
        "prior_completion": binding,
        "prior_audit": prior,
        "probe_completion_sha256": PROBE_SEAL,
        "probe_audit": probe_audit,
        "cap_usd": str(remaining),
        "request_caps": {
            "generation": 90,
            "judge": 2880 - prior["counts"]["judge"],
            "count": 3060 - prior["counts"]["count"],
        },
    }


def prepare(data_root: Path, output: Path) -> dict[str, Any]:
    """Freeze the separate condition and all ninety slots without constructing a client."""
    data_root, output = data_root.resolve(), output.resolve()
    if not output.is_relative_to(data_root / ROOT) or output == data_root / ROOT or output.exists():
        raise ValueError("Choose a fresh Task 13A namespace")
    loaded = load_locked(REPO, data_root)
    frozen = loaded["frozen_configuration"]
    for component in ("target", "A", "G", "S", "C"):
        locked_run.arm_prompt(frozen, component)
    pricing = locked_run.read(REPO / "configs/task13_pricing_v1.json")
    if locked_run.pricing_blockers(pricing):
        raise ValueError("Judge pricing is blocked")
    preflight = {
        "schema_version": "task13a.preflight.v1",
        "slots": planned_slots(loaded["case_ids"]),
        "case_ids": loaded["case_ids"],
        "source_sha256": stable_json_sha256(loaded["inputs"]),
        "input_bounds": input_bounds(loaded["inputs"], locked_run.arm_prompt(frozen)),
        "provenance": loaded["provenance"],
        "implementation_sha256": locked_run.implementation(REPO),
        "pricing": pricing,
        "minimax_condition": CONDITION,
        "cumulative_basis": cumulative_basis(data_root),
        "prompt_hashes": {
            c: stable_json_sha256(locked_run.arm_prompt(frozen, c))
            for c in ("target", "A", "G", "S", "C")
        },
        "limits": LIMITS,
    }
    output.mkdir(parents=True)
    for name, value in (
        ("inputs", loaded["inputs"]),
        ("references", loaded["references"]),
        ("preflight", preflight),
        ("planned_slots", preflight["slots"]),
    ):
        save(output / f"{name}.json", value)
    publish_bytes_no_clobber(
        output / "frozen_configuration.json",
        (REPO / "docs/specs/task11e_frozen_generation_v1.json").read_bytes(),
    )
    return preflight


def verify_preflight(output: Path, data_root: Path) -> dict[str, Any]:
    """Reject changed inputs, code, budget basis or stale independent approval."""
    preflight = locked_run.read(output / "preflight.json")
    loaded = load_locked(REPO, data_root)
    if (
        preflight["input_bounds"]
        != input_bounds(loaded["inputs"], locked_run.arm_prompt(loaded["frozen_configuration"]))
        or preflight["limits"] != LIMITS
        or preflight["case_ids"] != loaded["case_ids"]
        or preflight["pricing"] != locked_run.read(REPO / "configs/task13_pricing_v1.json")
        or locked_run.read(output / "planned_slots.json") != preflight["slots"]
        or preflight["minimax_condition"] != CONDITION
        or preflight["implementation_sha256"] != locked_run.implementation(REPO)
        or preflight["slots"] != planned_slots(loaded["case_ids"])
        or preflight["provenance"] != loaded["provenance"]
        or preflight["source_sha256"] != stable_json_sha256(loaded["inputs"])
        or locked_run.read(output / "inputs.json") != loaded["inputs"]
        or locked_run.read(output / "references.json") != loaded["references"]
        or locked_run.read(output / "frozen_configuration.json") != loaded["frozen_configuration"]
        or preflight["cumulative_basis"] != cumulative_basis(data_root)
    ):
        raise ValueError("Frozen implementation, sources or accounting changed")
    review = locked_run.read(output / "independent_preflight_review.json")
    if (
        review.get("status") != "approved"
        or review.get("unresolved_findings")
        or review.get("preflight_sha256") != sha256_file(output / "preflight.json")
    ):
        raise ValueError("Missing or stale independent preflight approval")
    return dict(preflight)


class ComparisonDispatcher(LockedDispatcher):
    """Add remaining cumulative call ceilings to the existing atomic admission gate."""

    def __init__(
        self, directory: Path, basis: dict[str, Any], *, evaluation_seconds: int = 1800
    ) -> None:
        """Persist the additional policy alongside the unchanged base ledger policy."""
        self.request_caps = basis["request_caps"]
        super().__init__(
            directory,
            cap_usd=Decimal(basis["cap_usd"]),
            concurrency=10,
            judge_per_answer=30,
            evaluation_seconds=evaluation_seconds,
        )
        try:
            policy = directory / "comparison_policy.json"
            if policy.exists():
                if locked_run.read(policy) != basis:
                    raise ValueError("Cumulative comparison policy changed")
            else:
                save(policy, basis)
        except BaseException:
            self.close()
            raise

    def _admit(self, request: Request) -> str:
        """Check tighter counts under the same lock as durable reservation."""
        with self._condition:
            while self._active >= self.concurrency and not self._closed and not self._stop:
                self._condition.wait(timeout=1)
            if self._closed or self._stop:
                return super()._admit(request)
            if self._count(request.kind) >= self.request_caps[request.kind]:
                self._stop_dispatch("Cumulative comparison request ceiling exhausted")
            return super()._admit(request)


async def dispatch(data_root: Path, output: Path) -> dict[str, Any]:
    """Execute one claimed ninety-slot condition, retaining every outcome and failure."""
    data_root, output = data_root.resolve(), output.resolve()
    if not output.is_relative_to(data_root / ROOT) or (output / "completion.json").exists():
        raise ValueError("Invalid or already sealed Task 13A run")
    preflight = verify_preflight(output, data_root)
    claim = {
        "namespace": str(output.relative_to(data_root)),
        "preflight_sha256": sha256_file(output / "preflight.json"),
    }
    claim_path = data_root / ROOT / "paid_run_claim.json"
    if claim_path.exists():
        if locked_run.read(claim_path) != claim:
            raise ValueError("Task 13A already claimed; cannot reset cumulative allowance")
    else:
        save(claim_path, claim)
    data = locked_run.read(output / "inputs.json")
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=90)
    for slot in preflight["slots"]:
        queue.put_nowait(slot)
    results: dict[str, dict[str, Any]] = {}
    with ComparisonDispatcher(output / "ledger", preflight["cumulative_basis"]) as dispatcher:

        async def worker() -> None:
            """Process slots sequentially per worker under one shared remote gate."""
            while not queue.empty():
                slot = queue.get_nowait()
                try:
                    row = await locked_run.run_slot(
                        slot,
                        preflight,
                        output,
                        data[slot["case_id"]],
                        dispatcher,
                        generate_one=minimax_provider.generate_one,
                        delivery_fn=minimax_provider.delivery,
                    )
                except Exception:
                    dispatcher.stop("Worker integrity failure; preserve all receipts")
                    raise
                results[stable_json_sha256(slot)] = row
                queue.task_done()

        tasks = [asyncio.create_task(worker()) for _ in range(10)]
        try:
            outcomes = await asyncio.gather(*tasks, return_exceptions=True)
            errors = [outcome for outcome in outcomes if isinstance(outcome, BaseException)]
            if errors:
                raise RuntimeError("Unsealed comparison worker failure") from errors[0]
        except BaseException:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise
        accounting = dispatcher.snapshot()
    rows = [results[stable_json_sha256(slot)] for slot in preflight["slots"]]
    save(output / "slot_results.json", rows)
    save(output / "accounting.json", accounting)
    save(output / "completion.json", artifact_inventory(output, {"completion.json"}))
    return {"slots": len(rows), "accounting": accounting}
