"""Continue only undispatched MiniMax work under the authorized longer active clock."""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any

from er_commons import locked_run as run
from er_commons import minimax_provider, minimax_run
from er_commons.artifact_io import artifact_inventory, sha256_file, stable_json_sha256
from er_commons.locked_audit import audit_ledger
from er_commons.locked_continue import _archive
from er_commons.locked_inputs import load_locked
from er_commons.target_generation import REPO, save

DEADLINE = 5400
HISTORY = "ancestor_history"


def verify_source(source: Path, digest: str) -> dict[str, Any]:
    """Verify sealed receipts, accepting held generation charges without replaying them."""
    if sha256_file(source / "completion.json") != digest:
        raise ValueError("Source completion digest changed")
    if run.read(source / "completion.json") != artifact_inventory(source, {"completion.json"}):
        raise ValueError("Source inventory changed")
    audit = audit_ledger(source / "ledger")
    if audit["unsettled_keys"]:
        raise ValueError("Unsettled request cannot continue")
    stop = run.read(source / "ledger/stop.json")
    if stop["reason"] != "Per-answer evaluation deadline exhausted":
        raise ValueError("Only the authorized evaluation deadline stop can continue")
    requests = [run.read(p) for p in (source / "ledger").glob("*.reservation.json")]
    settlements = {
        run.read(p)["key"]: run.read(p) for p in (source / "ledger").glob("*.settlement.json")
    }
    return {
        "audit": audit,
        "requests": requests,
        "settlements": settlements,
        "source_end": max(stop["at"], *(row["finished_at"] for row in settlements.values())),
    }


def classify_slot(directory: Path, row: dict[str, Any], verified: dict[str, Any]) -> dict[str, Any]:
    """Never replace a wire attempt; only discard explicitly zero-wire judge failures."""
    requests = [r for r in verified["requests"] if r["slot_id"] == row["run_id"]]
    generation_path = directory / "generation/result.json"
    generation = run.read(generation_path) if generation_path.exists() else None
    generations = [r for r in requests if r["kind"] == "generation"]
    if len(generations) > 1:
        raise ValueError("Multiple generation attempts")
    if row["status"] == "completed":
        return {"action": "preserve"}
    if not generations:
        if requests or (generation and generation.get("generation_calls", 0)):
            raise ValueError("Uncertain no-wire generation cannot continue")
        return {"action": "generate", "generation": None, "judgments": []}
    if generation is None:
        raise ValueError("Attempted generation missing receipt")
    if generation["status"] != "valid":
        return {"action": "preserve"}
    retained, discarded = [], []
    for judgment in run.read(directory / "judgments.json"):
        prefix = f"{row['run_id']}/{judgment['sample_id']}/"
        attempted = [r for r in requests if r["key"].startswith(prefix)]
        if judgment["status"] == "execution_error" and not attempted:
            if judgment["judge_calls"] or judgment["count_calls"]:
                raise ValueError("No-wire judgment claims calls")
            discarded.append(judgment["sample_id"])
        else:
            # Do not let a count-only interrupted item acquire a fresh request.
            if judgment["status"] == "execution_error":
                return {"action": "preserve"}
            retained.append(judgment)
    counted = {r["parent_key"] for r in requests if r["kind"] == "count"}
    judged = {r["key"] for r in requests if r["kind"] == "judge"}
    if counted != judged:
        raise ValueError("Count-only or uncounted judgment cannot continue")
    starts = [
        r["evaluation_started_at"] for r in requests if r.get("evaluation_started_at") is not None
    ]
    start = min(starts) if starts else verified["settlements"][generations[0]["key"]]["finished_at"]
    return {
        "action": "evaluate",
        "generation": generation,
        "judgments": retained,
        "discard_judgments": discarded,
        "original_evaluation_started_at": start,
        "evaluation_elapsed_seconds": max(0, verified["source_end"] - start),
    }


def prepare(data_root: Path, source: Path, output: Path, digest: str) -> dict[str, Any]:
    """Create a linked snapshot preserving all original bytes and every slot identity."""
    data_root, source, output = data_root.resolve(), source.resolve(), output.resolve()
    task = data_root / minimax_run.ROOT
    if (
        not source.is_relative_to(task)
        or not output.is_relative_to(task)
        or output == task
        or output.exists()
        or output.is_relative_to(source)
    ):
        raise ValueError("Choose a fresh separate Task 13A namespace")
    verified = verify_source(source, digest)
    original = run.read(source / "preflight.json")
    loaded = load_locked(REPO, data_root)
    if (
        original["slots"] != minimax_run.planned_slots(loaded["case_ids"])
        or loaded["inputs"] != run.read(source / "inputs.json")
        or loaded["references"] != run.read(source / "references.json")
        or loaded["provenance"] != original["provenance"]
        or loaded["frozen_configuration"] != run.read(source / "frozen_configuration.json")
        or original["minimax_condition"] != minimax_run.CONDITION
    ):
        raise ValueError("Frozen source inputs changed")
    claim = {
        "namespace": str(source.relative_to(data_root)),
        "preflight_sha256": sha256_file(source / "preflight.json"),
    }
    if run.read(task / "paid_run_claim.json") != claim:
        raise ValueError("Source is not original claimed run")
    rows = run.read(source / "slot_results.json")
    expected = {
        stable_json_sha256({"slot": s, "preflight": original}): s for s in original["slots"]
    }
    if len(rows) != 90 or {row["run_id"] for row in rows} != set(expected):
        raise ValueError("Original outcome roster differs")
    states = {}
    for row in rows:
        if any(row[k] != v for k, v in expected[row["run_id"]].items()):
            raise ValueError("Original slot identity differs")
        directory = (
            source / "observations" / f"{row['model']}_repeat{row['repeat']}" / row["case_id"]
        )
        states[row["run_id"]] = classify_slot(directory, row, verified)
    manifest = {
        "schema_version": "task13a.continuation_preflight.v1",
        "source": str(source),
        "source_completion_sha256": digest,
        "original_paid_claim": claim,
        "original_preflight_sha256": sha256_file(source / "preflight.json"),
        "implementation_sha256": run.implementation(REPO),
        "slots": states,
        "source_dispatch_end_at": verified["source_end"],
        "cumulative_audit": verified["audit"],
        "evaluation_seconds": DEADLINE,
        "workers": 1,
        "partial_first": True,
        "exclude_sealed_pause": True,
        "pause_authorization": "yes exclude and continue",
        "pause_basis": "Prior explicit approval and Task 13A active evaluation contract",
        "history_prefix": HISTORY,
    }
    shutil.copytree(source, output)
    for name in (
        "completion.json",
        "slot_results.json",
        "accounting.json",
        "ledger/stop.json",
        "ledger/policy.json",
    ):
        _archive(output, output / name, HISTORY)
    policy = run.read(source / "ledger/policy.json")
    policy.update(version=3, evaluation_seconds=DEADLINE)
    save(output / "ledger/policy.json", policy)
    save(output / "continuation_preflight.json", manifest)
    return {
        "preflight_sha256": sha256_file(output / "continuation_preflight.json"),
        "actions": {
            action: sum(s["action"] == action for s in states.values())
            for action in ("preserve", "evaluate", "generate")
        },
    }


def verify_preflight(data_root: Path, output: Path) -> dict[str, Any]:
    """Revalidate ancestor bytes, original claim, sources and fresh independent approval."""
    manifest = run.read(output / "continuation_preflight.json")
    source = Path(manifest["source"])
    verify_source(source, manifest["source_completion_sha256"])
    if (
        run.implementation(REPO) != manifest["implementation_sha256"]
        or manifest["evaluation_seconds"] != DEADLINE
        or manifest["workers"] != 1
        or not manifest["partial_first"]
        or not manifest["exclude_sealed_pause"]
        or manifest["pause_authorization"] != "yes exclude and continue"
    ):
        raise ValueError("Continuation implementation or authorized policy changed")
    if (
        run.read(data_root / minimax_run.ROOT / "paid_run_claim.json")
        != manifest["original_paid_claim"]
    ):
        raise ValueError("Original paid claim changed")
    archived_metadata = {
        "completion.json",
        "slot_results.json",
        "accounting.json",
        "ledger/stop.json",
        "ledger/policy.json",
    }
    for binding in run.read(source / "completion.json")["files"]:
        relative = binding["path"]
        present = (
            output / HISTORY / relative if relative in archived_metadata else output / relative
        )
        if not present.is_file() or sha256_file(present) != binding["sha256"]:
            raise ValueError("Copied ancestor bytes changed")
    if sha256_file(output / "preflight.json") != manifest["original_preflight_sha256"]:
        raise ValueError("Original preflight identity changed")
    loaded = load_locked(REPO, data_root)
    original = run.read(output / "preflight.json")
    if (
        loaded["inputs"] != run.read(output / "inputs.json")
        or loaded["provenance"] != original["provenance"]
        or original["minimax_condition"] != minimax_run.CONDITION
    ):
        raise ValueError("Locked inputs changed")
    review = run.read(output / "independent_continuation_review.json")
    if (
        review.get("status") != "approved"
        or review.get("unresolved_findings")
        or review.get("preflight_sha256") != sha256_file(output / "continuation_preflight.json")
    ):
        raise ValueError("Independent continuation approval missing or stale")
    return dict(manifest)


async def dispatch(data_root: Path, output: Path) -> dict[str, Any]:
    """Resume verified work serially; preserve attempts and original six-hour clock.

    An interrupted continuation fails closed on changed ancestor-derived files;
    further recovery requires another explicit verified snapshot, never automatic replay.
    """
    data_root, output = data_root.resolve(), output.resolve()
    if (
        not output.is_relative_to(data_root / minimax_run.ROOT)
        or (output / "completion.json").exists()
    ):
        raise ValueError("Invalid or sealed continuation")
    manifest = verify_preflight(data_root, output)
    claim_path = (
        data_root
        / minimax_run.ROOT
        / "continuation_claims"
        / (manifest["source_completion_sha256"] + ".json")
    )
    claim = {
        "namespace": str(output.relative_to(data_root)),
        "preflight_sha256": sha256_file(output / "continuation_preflight.json"),
        "source_completion_sha256": manifest["source_completion_sha256"],
    }
    save(claim_path, claim)
    restart = output / "continuation_dispatch_started.json"
    if not restart.exists():
        save(restart, {"at": time.time()})
    started = run.read(restart)["at"]
    preflight = run.read(output / "preflight.json")
    data = run.read(output / "inputs.json")

    def identity(slot: dict[str, Any]) -> str:
        """Retain the original run identifier despite the operational amendment."""
        return stable_json_sha256({"slot": slot, "preflight": preflight})

    ordered = sorted(
        preflight["slots"],
        key=lambda s: {"evaluate": 0, "preserve": 1, "generate": 2}[
            manifest["slots"][identity(s)]["action"]
        ],
    )
    results = {}
    with minimax_run.ComparisonDispatcher(
        output / "ledger", preflight["cumulative_basis"], evaluation_seconds=DEADLINE
    ) as dispatcher:
        for slot in ordered:
            state = dict(manifest["slots"][identity(slot)])
            directory = (
                output
                / "observations"
                / f"{slot['model']}_repeat{slot['repeat']}"
                / slot["case_id"]
            )
            if state["action"] == "preserve" or dispatcher.snapshot()["stop_reason"]:
                row = run.read(directory / "summary.json")
            elif (directory / "continuation_started.json").exists():
                row = await run.run_slot(
                    slot,
                    preflight,
                    output,
                    data[slot["case_id"]],
                    dispatcher,
                    generate_one=minimax_provider.generate_one,
                    delivery_fn=minimax_provider.delivery,
                )
            else:
                if state["action"] == "evaluate":
                    state["evaluation_started_at"] = started - state["evaluation_elapsed_seconds"]
                    if time.time() - state["evaluation_started_at"] >= DEADLINE:
                        results[identity(slot)] = run.read(directory / "summary.json")
                        continue
                    for name in (
                        "summary.json",
                        "report.json",
                        "judgments.json",
                        "completion.json",
                    ):
                        _archive(output, directory / name, HISTORY)
                    for sample in state["discard_judgments"]:
                        _archive(output, directory / "judgments" / sample, HISTORY)
                else:
                    _archive(output, directory, HISTORY)
                    directory.mkdir(parents=True)
                    save(directory / "manifest.json", {**slot, "run_id": identity(slot)})
                save(directory / "continuation_started.json", {"at": time.time(), "state": state})
                row = await run.run_slot(
                    slot,
                    preflight,
                    output,
                    data[slot["case_id"]],
                    dispatcher,
                    state,
                    generate_one=minimax_provider.generate_one,
                    delivery_fn=minimax_provider.delivery,
                )
            results[identity(slot)] = row
        accounting = dispatcher.snapshot()
    rows = [results[identity(s)] for s in preflight["slots"]]
    save(output / "slot_results.json", rows)
    save(output / "accounting.json", accounting)
    save(output / "completion.json", artifact_inventory(output, {"completion.json"}))
    return {"slots": len(rows), "accounting": accounting}
