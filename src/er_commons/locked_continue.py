"""Continue verified undispatched Task 13 work without altering its sealed ancestor."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Any

from er_commons import locked_run as run
from er_commons.artifact_io import artifact_inventory, sha256_file, stable_json_sha256
from er_commons.locked_audit import audit_ledger
from er_commons.locked_dispatch import LockedDispatcher
from er_commons.locked_inputs import load_locked
from er_commons.target_generation import REPO, save

STOP = "Answer exceeds 16 judge items; preserved without trimming"
DEADLINE_STOP = "Per-answer evaluation deadline exhausted"


def verify_source(source: Path, digest: str, *, allow_deadline: bool = False) -> dict[str, Any]:
    """Require a complete exact seal and settled, one-to-one native/count attempts."""
    if sha256_file(source / "completion.json") != digest:
        raise ValueError("Source completion digest differs")
    if run.read(source / "completion.json") != artifact_inventory(source, {"completion.json"}):
        raise ValueError("Source inventory differs")
    audit = audit_ledger(source / "ledger")
    if audit["unsettled_keys"]:
        raise ValueError("Uncertain attempts cannot continue")
    requests = [run.read(p) for p in (source / "ledger").glob("*.reservation.json")]
    settlements = {}
    for path in (source / "ledger").glob("*.settlement.json"):
        settlement = run.read(path)
        settlements[settlement["key"]] = settlement
    paid = {r["key"] for r in requests if r["kind"] != "count"}
    counted = {r["parent_key"] for r in requests if r["kind"] == "count"}
    if paid != counted:
        raise ValueError("Counting-only attempt requires separate recovery; never recount")
    for request in requests:
        settlement = settlements[request["key"]]
        if settlement["error"] or (
            settlement["actual_cost_usd"] is None
            and request.get("accounting_basis") != "user_accepted_unknown_openai_count_fee"
        ):
            raise ValueError("Failed or uncertain native attempt requires separate recovery")
    stop = run.read(source / "ledger/stop.json")
    if stop["reason"] != STOP and not (allow_deadline and stop["reason"] == DEADLINE_STOP):
        raise ValueError("Only the explicitly amended 16-item stop can continue")
    return {"audit": audit, "requests": requests, "settlements": settlements, "stop": stop}


def _archive(output: Path, path: Path, prefix: str | None = None) -> None:
    """Move replaced derived metadata into immutable ancestor history in the copy."""
    if path.exists():
        if prefix is None:
            manifest_path = output / "continuation_preflight.json"
            prefix = (
                run.read(manifest_path).get("history_prefix", "ancestor_history")
                if manifest_path.exists()
                else "ancestor_history"
            )
        destination = output / prefix / path.relative_to(output)
        if destination.exists():
            if path.is_dir() and destination.is_dir():
                for child in path.iterdir():
                    _archive(output, child, prefix)
                path.rmdir()
                return
            raise ValueError("Ancestor history cannot be replaced")
        destination.parent.mkdir(parents=True, exist_ok=True)
        path.rename(destination)


def _successor_claim(task: Path, source: Path, digest: str) -> Path:
    """Bind exactly one successor to each sealed paid ancestor."""
    if not (source / "continuation_preflight.json").exists():
        return task / "paid_continuation_claim.json"
    return task / "continuation_claims" / f"{digest}.json"


def _verified_chain(data_root: Path, source: Path) -> list[tuple[Path, dict[str, Any]]]:
    """Verify every sealed predecessor and task-wide successor claim oldest first."""
    task = data_root / "pipelines/brisbane_baylands/task_13"
    chain = []
    current = source
    seen = set()
    while (current / "continuation_preflight.json").exists():
        if current in seen or not current.is_relative_to(task):
            raise ValueError("Invalid continuation ancestry")
        seen.add(current)
        manifest = run.read(current / "continuation_preflight.json")
        previous = Path(manifest["source"]).resolve()
        digest = manifest["source_completion_sha256"]
        verify_source(previous, digest, allow_deadline=True)
        expected = {
            "namespace": str(current.relative_to(data_root)),
            "preflight_sha256": sha256_file(current / "continuation_preflight.json"),
            "source_completion_sha256": digest,
        }
        if run.read(_successor_claim(task, previous, digest)) != expected:
            raise ValueError("Continuation ancestry claim differs")
        chain.append((current, manifest))
        current = previous
    expected = {
        "namespace": str(current.relative_to(data_root)),
        "preflight_sha256": sha256_file(current / "preflight.json"),
    }
    if run.read(task / "paid_run_claim.json") != expected:
        raise ValueError("Ancestor is not the task-wide paid claim")
    return list(reversed(chain))


def _pause_intervals(chain: list[tuple[Path, dict[str, Any]]], relative: Path) -> list[list[float]]:
    """Read only verified epoch receipts; preserve live queueing in active time."""
    intervals = []
    for path, manifest in chain:
        identity = path / relative / "manifest.json"
        if identity.exists():
            slot_id = run.read(identity)["run_id"]
            if manifest["slots"][slot_id]["action"] == "evaluate":
                dispatch_receipt = path / "continuation_dispatch_started.json"
                resumed = (
                    run.read(dispatch_receipt)["at"]
                    if dispatch_receipt.exists()
                    else min(
                        run.read(p)["at"]
                        for p in (path / "observations").glob("*/*/continuation_started.json")
                    )
                )
                intervals.append([manifest["source_dispatch_end_at"], resumed])
    return intervals


def active_elapsed(start: float, end: float, intervals: list[list[float]]) -> float:
    """Subtract the union of administrative pauses intersecting this evaluation."""
    covered = 0.0
    cursor = start
    for left, right in sorted(intervals):
        if right < left:
            raise ValueError("Invalid administrative pause interval")
        left, right = max(start, left, cursor), min(end, right)
        if right > left:
            covered += right - left
            cursor = right
    return max(0.0, end - start - covered)


def prepare(
    data_root: Path,
    source: Path,
    output: Path,
    digest: str,
    *,
    exclude_sealed_pause: bool = False,
    pause_authorization: str | None = None,
) -> dict[str, Any]:
    """Copy a verified ancestor and bind an independently reviewed continuation."""
    if exclude_sealed_pause and not pause_authorization:
        raise ValueError("Explicit user pause authorization is required")
    source, output, data_root = source.resolve(), output.resolve(), data_root.resolve()
    task = data_root / "pipelines/brisbane_baylands/task_13"
    if (
        not source.is_relative_to(task)
        or not output.is_relative_to(task)
        or output == task
        or output.exists()
        or output.is_relative_to(source)
    ):
        raise ValueError("Choose a fresh separate Task 13 namespace")
    verified = verify_source(source, digest, allow_deadline=exclude_sealed_pause)
    original = run.read(source / "preflight.json")
    loaded = load_locked(REPO, data_root)
    if (
        loaded["slots"] != original["slots"]
        or loaded["inputs"] != run.read(source / "inputs.json")
        or loaded["provenance"] != original["provenance"]
        or loaded["frozen_configuration"] != run.read(source / "frozen_configuration.json")
    ):
        raise ValueError("Locked source bindings differ")
    chain = _verified_chain(data_root, source)
    expected_claim = run.read(task / "paid_run_claim.json")
    history_prefix = "ancestor_history/" + digest if chain else "ancestor_history"
    source_end = max(
        [verified["stop"]["at"], *[r["finished_at"] for r in verified["settlements"].values()]]
    )
    slots: dict[str, dict[str, Any]] = {}
    for row in run.read(source / "slot_results.json"):
        slot_id = row["run_id"]
        relative = Path("observations") / f"{row['model']}_repeat{row['repeat']}" / row["case_id"]
        directory = source / relative
        requests = [r for r in verified["requests"] if r["slot_id"] == slot_id]
        generation = (
            run.read(directory / "generation/result.json")
            if (directory / "generation/result.json").exists()
            else None
        )
        if row["status"] == "completed":
            slots[slot_id] = {"action": "preserve"}
            continue
        judgments = run.read(directory / "judgments.json")
        retained = []
        discard = []
        for judgment in judgments:
            prefix = f"{slot_id}/{judgment['sample_id']}/"
            attempted = [r for r in requests if r["key"].startswith(prefix)]
            if judgment["status"] == "execution_error" and not attempted:
                if judgment["judge_calls"] or judgment["count_calls"]:
                    raise ValueError("Unattempted judgment reports remote calls")
                discard.append(judgment["sample_id"])
            else:
                retained.append(judgment)
        generations = [r for r in requests if r["kind"] == "generation"]
        starts = [
            r["evaluation_started_at"]
            for r in requests
            if r.get("evaluation_started_at") is not None
        ]
        if generations:
            if generation is None or generation["status"] not in {"valid", "invalid_output"}:
                raise ValueError("Cannot replace attempted generation")
            start = (
                min(starts)
                if starts
                else verified["settlements"][generations[0]["key"]]["finished_at"]
            )
            for _, prior in chain:
                prior_state = prior["slots"][slot_id]
                if prior_state["action"] == "evaluate":
                    start = prior_state.get(
                        "original_evaluation_started_at", prior_state["evaluation_started_at"]
                    )
                    break
            pauses = _pause_intervals(chain, relative) if exclude_sealed_pause else []
            slots[slot_id] = {
                "action": "evaluate",
                "original_evaluation_started_at": start,
                "generation": generation,
                "judgments": retained,
                "discard_judgments": discard,
                "evaluation_started_at": start,
                "evaluation_elapsed_seconds": active_elapsed(start, source_end, pauses)
                if exclude_sealed_pause
                else max(0, source_end - start),
                "excluded_pause_intervals": pauses,
            }
        else:
            if requests:
                raise ValueError("Generation counting was attempted; do not replay")
            slots[slot_id] = {
                "action": "generate",
                "generation": None,
                "judgments": [],
                "evaluation_elapsed_seconds": 0,
            }
    manifest = {
        "schema_version": "task13.continuation_preflight.v1",
        "source": str(source),
        "source_completion_sha256": digest,
        "original_preflight_sha256": sha256_file(source / "preflight.json"),
        "implementation_sha256": run.implementation(REPO),
        "judge_per_answer": 30,
        "exclude_sealed_pause": exclude_sealed_pause,
        "pause_authorization": pause_authorization,
        "source_dispatch_end_at": source_end,
        "cumulative_audit": verified["audit"],
        "slots": slots,
        "original_paid_claim": expected_claim,
        "history_prefix": history_prefix,
        "source_chain": [
            {
                "source": str(path),
                "preflight_sha256": sha256_file(path / "continuation_preflight.json"),
            }
            for path, _ in chain
        ],
    }
    shutil.copytree(source, output)
    for name in (
        "completion.json",
        "slot_results.json",
        "accounting.json",
        "ledger/stop.json",
        "ledger/policy.json",
        "continuation_preflight.json",
        "independent_continuation_review.json",
        "continuation_dispatch_started.json",
    ):
        _archive(output, output / name, history_prefix)
    for receipt in (output / "observations").glob("*/*/continuation_started.json"):
        _archive(output, receipt, history_prefix)
    save(
        output / "ledger/policy.json",
        {"cap_usd": "10", "concurrency": 10, "version": 2, "judge_per_answer": 30},
    )
    save(output / "continuation_preflight.json", manifest)
    return {
        "preflight_sha256": sha256_file(output / "continuation_preflight.json"),
        "actions": {
            action: sum(s["action"] == action for s in slots.values())
            for action in ("preserve", "evaluate", "generate")
        },
    }


def verify_preflight(data_root: Path, output: Path) -> dict[str, Any]:
    """Require fresh independent approval and unchanged ancestor, code and inputs."""
    manifest = run.read(output / "continuation_preflight.json")
    verify_source(
        Path(manifest["source"]),
        manifest["source_completion_sha256"],
        allow_deadline=bool(manifest["exclude_sealed_pause"] and manifest["pause_authorization"]),
    )
    _verified_chain(data_root, Path(manifest["source"]))
    for binding in run.read(Path(manifest["source"]) / "completion.json")["files"]:
        relative = binding["path"]
        archived = output / manifest.get("history_prefix", "ancestor_history") / relative
        fixed = relative in {
            "preflight.json",
            "inputs.json",
            "frozen_configuration.json",
        } or relative.endswith((".reservation.json", ".settlement.json"))
        present = output / relative if fixed or not archived.exists() else archived
        if not present.is_file() or sha256_file(present) != binding["sha256"]:
            raise ValueError("Copied ancestor bytes changed")
    if run.implementation(REPO) != manifest["implementation_sha256"]:
        raise ValueError("Continuation implementation changed")
    if sha256_file(output / "preflight.json") != manifest["original_preflight_sha256"]:
        raise ValueError("Original run identity changed")
    loaded = load_locked(REPO, data_root)
    original = run.read(output / "preflight.json")
    if (
        loaded["inputs"] != run.read(output / "inputs.json")
        or loaded["provenance"] != original["provenance"]
    ):
        raise ValueError("Continuation inputs changed")
    review = run.read(output / "independent_continuation_review.json")
    if (
        review.get("status") != "approved"
        or review.get("preflight_sha256") != sha256_file(output / "continuation_preflight.json")
        or review.get("unresolved_findings")
    ):
        raise ValueError("Independent continuation approval missing or stale")
    return dict(manifest)


async def dispatch(data_root: Path, output: Path) -> dict[str, Any]:
    """Continue only never-dispatched work under the copied cumulative ledger."""
    data_root, output = data_root.resolve(), output.resolve()
    if (output / "completion.json").exists():
        raise ValueError("Sealed continuation cannot dispatch again")
    manifest = verify_preflight(data_root, output)
    task = data_root / "pipelines/brisbane_baylands/task_13"
    if run.read(task / "paid_run_claim.json") != manifest["original_paid_claim"]:
        raise ValueError("Task-wide paid claim changed")
    claim_path = _successor_claim(
        task, Path(manifest["source"]), manifest["source_completion_sha256"]
    )
    claim = {
        "namespace": str(output.relative_to(data_root)),
        "preflight_sha256": sha256_file(output / "continuation_preflight.json"),
        "source_completion_sha256": manifest["source_completion_sha256"],
    }
    if not claim_path.exists():
        save(claim_path, claim)
    if run.read(claim_path) != claim:
        raise ValueError("Continuation already claimed; cannot fork cumulative budget")
    dispatch_receipt = output / "continuation_dispatch_started.json"
    if not dispatch_receipt.exists():
        save(dispatch_receipt, {"at": time.time()})
    dispatch_started = run.read(dispatch_receipt)["at"]
    preflight = run.read(output / "preflight.json")
    data = run.read(output / "inputs.json")
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=180)
    for slot in preflight["slots"]:
        queue.put_nowait(slot)
    results = {}
    with LockedDispatcher(output / "ledger", judge_per_answer=30) as dispatcher:

        async def worker() -> None:
            """Preserve completed/expired slots and finish eligible dependencies."""
            while not queue.empty():
                slot = queue.get_nowait()
                identity = {
                    **slot,
                    "run_id": stable_json_sha256({"slot": slot, "preflight": preflight}),
                }
                state = dict(manifest["slots"][identity["run_id"]])
                directory = (
                    output
                    / "observations"
                    / f"{slot['model']}_repeat{slot['repeat']}"
                    / slot["case_id"]
                )
                if state["action"] == "evaluate" and manifest["exclude_sealed_pause"]:
                    state["evaluation_started_at"] = (
                        dispatch_started - state["evaluation_elapsed_seconds"]
                    )
                if state["action"] == "evaluate" and not manifest["exclude_sealed_pause"]:
                    state["evaluation_elapsed_seconds"] = max(
                        0, time.time() - state["evaluation_started_at"]
                    )
                if (
                    state["action"] == "preserve"
                    or (
                        state["action"] == "evaluate"
                        and state["evaluation_elapsed_seconds"] >= 1800
                    )
                    or dispatcher.snapshot()["stop_reason"]
                ):
                    row = run.read(directory / "summary.json")
                elif (directory / "continuation_started.json").exists():
                    # A restarted continuation never resets an interrupted slot's timer.
                    row = await run.run_slot(
                        slot, preflight, output, data[slot["case_id"]], dispatcher
                    )
                else:
                    if state["action"] == "generate":
                        _archive(output, directory)
                        directory.mkdir(parents=True)
                        save(directory / "manifest.json", identity)
                    else:
                        for name in (
                            "summary.json",
                            "report.json",
                            "judgments.json",
                            "completion.json",
                        ):
                            _archive(output, directory / name)
                        for sample in state["discard_judgments"]:
                            _archive(output, directory / "judgments" / sample)
                    save(
                        directory / "continuation_started.json", {"at": time.time(), "state": state}
                    )
                    row = await run.run_slot(
                        slot, preflight, output, data[slot["case_id"]], dispatcher, state
                    )
                results[stable_json_sha256(slot)] = row
                queue.task_done()

        async def guarded_worker() -> None:
            """Stop admission immediately on any integrity error, then drain peers."""
            try:
                await worker()
            except Exception:
                dispatcher.stop("Continuation worker integrity failure")
                raise

        tasks = [asyncio.create_task(guarded_worker()) for _ in range(10)]
        try:
            outcomes = await asyncio.gather(*tasks, return_exceptions=True)
            errors = [value for value in outcomes if isinstance(value, BaseException)]
            if errors:
                dispatcher.stop("Continuation worker integrity failure")
                raise RuntimeError(
                    "Continuation worker failed; preserve unsealed artifacts"
                ) from errors[0]
        except BaseException:
            for worker_task in tasks:
                worker_task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise
        accounting = dispatcher.snapshot()
    rows = [results[stable_json_sha256(s)] for s in preflight["slots"]]
    save(output / "slot_results.json", rows)
    save(output / "accounting.json", accounting)
    save(output / "completion.json", artifact_inventory(output, {"completion.json"}))
    return {"slots": len(rows), "accounting": accounting}


def main() -> None:
    """Expose separate no-call preparation and reviewed continuation admission."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "dispatch"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--completion-sha256")
    parser.add_argument("--exclude-sealed-pause", action="store_true")
    parser.add_argument("--pause-authorization")
    args = parser.parse_args()
    root = Path(os.environ["ER_COMMONS_DATA_ROOT"])
    logging.basicConfig(level=logging.INFO)
    if args.mode == "prepare":
        if args.source is None or args.completion_sha256 is None:
            parser.error("prepare requires source and completion-sha256")
        result = prepare(
            root,
            args.source,
            args.output,
            args.completion_sha256,
            exclude_sealed_pause=args.exclude_sealed_pause,
            pause_authorization=args.pause_authorization,
        )
    else:
        result = asyncio.run(dispatch(root, args.output))
    logging.info("%s", json.dumps(result))


if __name__ == "__main__":
    main()
