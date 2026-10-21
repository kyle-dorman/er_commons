"""Offline structural audit of Task 13's durable request ledger."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any


def audit_ledger(directory: Path) -> dict[str, Any]:
    """Reconcile unique attempts, admission limits and conservative timed liability.

    An unsettled attempt stays active through the end of this audit. Timestamp
    ties release settlements first, matching sequential reuse of a permit. This
    checks recorded attempts, not unknowable provider-side billing or retries.
    """
    policy = json.loads((directory / "policy.json").read_text())
    cap = Decimal(policy["cap_usd"])
    if not 0 < cap <= 10 or not 1 <= policy["concurrency"] <= 10:
        raise ValueError("Invalid policy")
    evaluation_seconds = policy.get("evaluation_seconds", 1800)
    if type(evaluation_seconds) is not int or evaluation_seconds not in (1800, 5400):
        raise ValueError("Invalid evaluation deadline policy")
    reservations: dict[str, Any] = {}
    settlements: dict[str, Any] = {}
    for suffix, target in (("reservation", reservations), ("settlement", settlements)):
        for path in directory.glob(f"*.{suffix}.json"):
            row = json.loads(path.read_text())
            key = row["key"]
            digest = hashlib.sha256(key.encode()).hexdigest()
            if key in target or path.name != f"{digest}.{suffix}.json":
                raise ValueError("Duplicate or invalid request identity")
            target[key] = row
    if not settlements.keys() <= reservations.keys():
        raise ValueError("Orphan settlement")
    counts = Counter(row["kind"] for row in reservations.values())
    judge_per_answer = policy.get("judge_per_answer", 16)
    if judge_per_answer not in (16, 30):
        raise ValueError("Invalid per-answer judge policy")
    caps = {"generation": 180, "judge": 2880, "count": 3060}
    if any(kind not in caps or value > caps[kind] for kind, value in counts.items()):
        raise ValueError("Request ceiling exceeded")
    by_slot = Counter((row["slot_id"], row["kind"]) for row in reservations.values())
    if any(
        n > (1 if kind == "generation" else judge_per_answer)
        for (_, kind), n in by_slot.items()
        if kind != "count"
    ):
        raise ValueError("Per-slot request ceiling exceeded")
    parents = [r["parent_key"] for r in reservations.values() if r["kind"] == "count"]
    if None in parents or len(parents) != len(set(parents)):
        raise ValueError("Duplicate or missing count parent")
    events = []
    first = min((r["started_at"] for r in reservations.values()), default=None)
    settled_cost = Decimal(0)
    held = Decimal(0)
    for key, row in reservations.items():
        reserve = Decimal(row["maximum_cost_usd"])
        if not reserve.is_finite() or reserve < 0:
            raise ValueError("Invalid reservation")
        output_cap = 12288 if row["kind"] == "generation" else 4096
        if not 0 <= row["input_tokens"] <= 100000 or not 0 <= row["output_tokens"] <= output_cap:
            raise ValueError("Token limit exceeded")
        if first is not None and row["started_at"] - first >= 21600:
            raise ValueError("Dispatch window exceeded")
        evaluation_start = row.get("evaluation_started_at")
        if (
            evaluation_start is not None
            and row["started_at"] - evaluation_start >= evaluation_seconds
        ):
            raise ValueError("Evaluation admission deadline exceeded")
        events.append((row["started_at"], 1, key, reserve))
        settlement = settlements.get(key)
        actual = None if settlement is None else settlement["actual_cost_usd"]
        if actual is None:
            held += reserve
        else:
            actual = Decimal(actual)
            if not actual.is_finite() or not 0 <= actual <= reserve:
                raise ValueError("Invalid settlement charge")
            settled_cost += actual
        if settlement is not None:
            if settlement["finished_at"] < row["started_at"]:
                raise ValueError("Settlement precedes reservation")
            # Exact equal timestamps need reservation first for this same request.
            priority = 2 if settlement["finished_at"] == row["started_at"] else 0
            events.append(
                (
                    settlement["finished_at"],
                    priority,
                    key,
                    Decimal(0) if actual is None else actual - reserve,
                )
            )
    active = peak_active = 0
    liability = peak_liability = Decimal(0)
    for _, priority, _, delta in sorted(events):
        active += 1 if priority == 1 else -1
        liability += delta
        peak_active = max(peak_active, active)
        peak_liability = max(peak_liability, liability)
        if active < 0 or active > policy["concurrency"] or liability > cap:
            raise ValueError("Recorded concurrency or atomic budget ceiling exceeded")
    return {
        "schema_version": "task13.ledger_audit.v1",
        "counts": {kind: counts[kind] for kind in caps},
        "peak_recorded_concurrency": peak_active,
        "peak_reserved_liability_usd": str(peak_liability),
        "settled_known_cost_usd": str(settled_cost),
        "held_planning_liability_usd": str(held),
        "final_planning_liability_usd": str(settled_cost + held),
        "unsettled_keys": sorted(reservations.keys() - settlements.keys()),
        "unknown_actual_cost_keys": sorted(
            k for k, r in settlements.items() if r["actual_cost_usd"] is None
        ),
        "limitation": "Recorded ledger audit; accepted unknown count fees are not verified zero.",
    }
