"""Task 13 preflight and bounded locked execution; never tune or replace outputs."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from er_commons import context_comparison as context
from er_commons import development_evaluation as evaluation
from er_commons import judge_inspect, locked_provider
from er_commons.artifact_io import (
    artifact_inventory,
    publish_bytes_no_clobber,
    sha256_file,
    stable_json_sha256,
)
from er_commons.development_evaluation_provider import component_settings
from er_commons.locked_dispatch import LockedDispatcher
from er_commons.locked_inputs import load_locked
from er_commons.locked_pricing import bounded_or_accepted
from er_commons.target_generation import REPO, save

LOG = logging.getLogger(__name__)


def read(path: Path) -> Any:
    """Read structured local metadata without constructing providers."""
    return json.loads(path.read_text())


def implementation(repo: Path) -> dict[str, str]:
    """Bind all package/config/reporting definition bytes independently of Git commits."""
    paths = [
        *sorted((repo / "src/er_commons").rglob("*.py")),
        *sorted((repo / "configs").rglob("*.json")),
        repo / "uv.lock",
    ]
    paths += sorted((repo / "docs/specs").glob("task12_*.md"))
    paths += [
        repo / "docs/specs/task09g_judge_freeze_v1.json",
        repo / "docs/specs/task11e_frozen_generation_v1.json",
    ]
    return {str(p.relative_to(repo)): sha256_file(p) for p in paths}


def arm_prompt(frozen: dict[str, Any], component: str = "target") -> str:
    """Reproduce the exact shared overview and unchanged frozen core."""
    core = (
        (REPO / frozen["prompt_path"]).read_text()
        if component == "target"
        else component_settings(component)[1]
    )
    overview = (REPO / frozen["context_path"]).read_text()
    prompt = f"<project_context>\n{overview}\n</project_context>\n\n{core}"
    hashes = frozen["effective_prompts_sha256"]["all19"]
    expected = hashes["target"] if component == "target" else hashes["judges"][component]
    if stable_json_sha256(prompt) != expected:
        raise ValueError("Frozen effective prompt differs")
    return prompt


def pricing_blockers(pricing: dict[str, Any]) -> list[str]:
    """Refuse unknown fees except the user's specific OpenAI counting exception."""
    return [
        f"{p}: provider/count pricing lacks a verified upper bound"
        for p in ("openai", "anthropic")
        if not bounded_or_accepted(p, pricing[p])
    ]


def prepare(data_root: Path, output: Path) -> dict[str, Any]:
    """Create the locked roster and immutable preflight; this makes no remote requests."""
    data_root, output = data_root.resolve(), output.resolve()
    required = data_root / "pipelines/brisbane_baylands/task_13"
    if not output.is_relative_to(required) or output == required or output.exists():
        raise ValueError("Choose a fresh Task 13 external namespace")
    loaded = load_locked(REPO, data_root)
    frozen = loaded["frozen_configuration"]
    for label, condition in (("luna", "openai_generation"), ("haiku", "anthropic_generation")):
        target = frozen["targets"][label]
        profile = judge_inspect.profile(condition)
        config = context._execution_config(condition, "target", arm_prompt(frozen), 12288)
        schema = context._expected_schema(config, profile.provider)
        example_binding = target["native_example"]
        example_path = data_root / example_binding["path_relative_to_data_root"]
        if sha256_file(example_path) != example_binding["sha256"]:
            raise ValueError("Frozen native example changed")
        example = read(example_path)
        native_format = (
            example["text"]["format"] if profile.provider == "openai" else example["output_format"]
        )
        if (
            profile.model != target["model"]
            or schema != native_format["schema"]
            or stable_json_sha256(native_format) != target["native_schema_sha256"]
        ):
            raise ValueError("Frozen target model/schema differs")
    for component in ("target", "A", "G", "S", "C"):
        arm_prompt(frozen, component)
    pricing = read(REPO / "configs/task13_pricing_v1.json")
    preflight = {
        "schema_version": "task13.preflight.v1",
        "baseline_commit": "ab38a3c",
        "slots": loaded["slots"],
        "case_ids": loaded["case_ids"],
        "source_sha256": stable_json_sha256(loaded["inputs"]),
        "provenance": loaded["provenance"],
        "implementation_sha256": implementation(REPO),
        "pricing": pricing,
        "billing_blockers": pricing_blockers(pricing),
        "limits": {
            "generation": 180,
            "judge": 2880,
            "count": 3060,
            "judge_per_answer": 16,
            "concurrency": 10,
            "usd": 10,
            "input_tokens": 100000,
            "generation_output_tokens": 12288,
            "judge_output_tokens": 4096,
            "request_seconds": 900,
            "evaluation_seconds": 1800,
            "dispatch_seconds": 21600,
            "retries": 0,
        },
        "prompt_hashes": {
            c: stable_json_sha256(arm_prompt(frozen, c)) for c in ("target", "A", "G", "S", "C")
        },
    }
    output.mkdir(parents=True, exist_ok=False)
    save(output / "inputs.json", loaded["inputs"])
    save(output / "references.json", loaded["references"])
    publish_bytes_no_clobber(
        output / "frozen_configuration.json",
        (REPO / "docs/specs/task11e_frozen_generation_v1.json").read_bytes(),
    )
    save(output / "preflight.json", preflight)
    save(output / "planned_slots.json", loaded["slots"])
    return {
        "slots": len(loaded["slots"]),
        "billing_blockers": preflight["billing_blockers"],
        "preflight_sha256": sha256_file(output / "preflight.json"),
    }


def verify_preflight(output: Path, data_root: Path) -> dict[str, Any]:
    """Revalidate sources, code and independent review immediately before admission."""
    preflight = read(output / "preflight.json")
    if implementation(REPO) != preflight["implementation_sha256"]:
        raise ValueError("Implementation changed: fresh preflight and review required")
    loaded = load_locked(REPO, data_root)
    if (
        loaded["slots"] != preflight["slots"]
        or loaded["provenance"] != preflight["provenance"]
        or loaded["frozen_configuration"] != read(output / "frozen_configuration.json")
        or stable_json_sha256(loaded["inputs"]) != preflight["source_sha256"]
        or loaded["inputs"] != read(output / "inputs.json")
    ):
        raise ValueError("Locked sources or roster changed")
    blockers = pricing_blockers(preflight["pricing"])
    if blockers:
        raise ValueError("; ".join(blockers))
    review = read(output / "independent_preflight_review.json")
    if (
        review.get("status") != "approved"
        or review.get("preflight_sha256") != sha256_file(output / "preflight.json")
        or review.get("unresolved_findings")
    ):
        raise ValueError("Independent preflight approval is missing or stale")
    return dict(preflight)


def prepare_plan(
    data: dict[str, Any],
    generation: dict[str, Any],
    directory: Path,
    *,
    delivery_fn: Callable[[dict[str, Any], str], dict[str, Any]] = context.delivery,
) -> dict[str, Any]:
    """Reconstruct score inputs from actual native delivery, never intended delivery."""
    actual = delivery_fn(read(directory / "native_request.json"), generation["provider"])
    if actual != read(directory / "delivery_projection.json"):
        raise ValueError("Saved native delivery differs")
    candidate = directory / "candidate.json"
    # Malformed candidates remain an automatic failure through the frozen evaluator.
    content = (
        candidate.read_bytes()
        if candidate.exists()
        else (directory / "raw_output.txt").read_bytes()
    )
    return evaluation.prepare_candidate(
        content,
        generation,
        data["record"],
        data["mapping"],
        actual,
        data["reference"],
        expected_split="test",
    )


async def run_slot(
    slot: dict[str, Any],
    preflight: dict[str, Any],
    output: Path,
    data: dict[str, Any],
    dispatcher: LockedDispatcher,
    continuation: dict[str, Any] | None = None,
    *,
    generate_one: Callable[..., Awaitable[dict[str, Any]]] | None = None,
    delivery_fn: Callable[[dict[str, Any], str], dict[str, Any]] = context.delivery,
) -> dict[str, Any]:
    """Preserve one answer and all dependency-ordered judgments, including failures."""
    directory = (
        output / "observations" / f"{slot['model']}_repeat{slot['repeat']}" / slot["case_id"]
    )
    identity = {**slot, "run_id": stable_json_sha256({"slot": slot, "preflight": preflight})}
    slot_id = identity["run_id"]
    if (directory / "completion.json").exists():
        if read(directory / "completion.json") != artifact_inventory(
            directory, {"completion.json"}
        ):
            raise ValueError("Saved slot seal differs")
        if read(directory / "manifest.json") != identity:
            raise ValueError("Saved slot identity differs")
        return dict(read(directory / "summary.json"))
    if directory.exists() and continuation is None:
        # No automatic replay of any partial slot, including attempts whose SDK
        # outcome was never durably saved. Other untouched slots may resume.
        row = {
            **identity,
            "status": "interrupted_uncertain",
            "reason": "Partial slot preserved; no redispatch",
        }
        if not (directory / "interruption.json").exists():
            save(directory / "interruption.json", row)
        return row
    directory.mkdir(parents=True, exist_ok=continuation is not None)
    if not (directory / "manifest.json").exists():
        save(directory / "manifest.json", identity)
    row = {
        **identity,
        "status": "not_dispatched",
        "generation_calls": 0,
        "judge_calls": 0,
        "count_calls": 0,
    }
    judgments: list[dict[str, Any]] = (
        [] if continuation is None else list(continuation["judgments"])
    )
    frozen = read(output / "frozen_configuration.json")
    # The dispatcher owns wall-clock admission deadlines. Hooks use an infinite
    # deadline so a completed count cannot cause deletion of an in-flight response.
    deadline = float("inf")
    try:
        stop_reason = dispatcher.snapshot()["stop_reason"]
        if stop_reason:
            row["reason"] = stop_reason
        else:
            generation_dir = directory / "generation"
            if continuation is not None and continuation.get("generation") is not None:
                generation = continuation["generation"]
            else:
                generation_dir.mkdir()
                save(generation_dir / "packet.json", data["record"])
                generation = await (generate_one or locked_provider.generate_one)(
                    data["record"],
                    generation_dir,
                    slot["condition"],
                    arm_prompt(frozen),
                    deadline,
                    identity,
                    dispatcher,
                    slot_id,
                    preflight["pricing"],
                )
            row.update(
                generation=generation,
                generation_calls=generation["generation_calls"],
                count_calls=generation["count_calls"],
            )
            row["status"] = "generation_failed"
            if generation["status"] == "execution_error":
                if not generation.get("rate_limited", False):
                    dispatcher.stop("Generation execution error; no retries or replacements")
            elif generation["generation_calls"] and (generation_dir / "raw_output.txt").exists():
                plan = prepare_plan(data, generation, generation_dir, delivery_fn=delivery_fn)
                if not (directory / "plan.json").exists():
                    save(directory / "plan.json", plan)
                    save(directory / "mapping.json", data["mapping"])
                started = (
                    continuation["evaluation_started_at"]
                    if continuation is not None and "evaluation_started_at" in continuation
                    else time.time()
                )
                judge_limit = dispatcher.judge_per_answer
                allowed = len(plan["items"]) <= judge_limit
                if not allowed:
                    dispatcher.stop(
                        f"Answer exceeds {judge_limit} judge items; preserved without trimming"
                    )
                while (
                    allowed
                    and not dispatcher.snapshot()["stop_reason"]
                    and (pending := evaluation.pending_items(plan, judgments))
                ):
                    for item in pending:
                        location = directory / "judgments" / item["sample_id"]
                        location.mkdir(parents=True)
                        condition, _, _ = component_settings(item["component"])
                        prompt = arm_prompt(frozen, item["component"])
                        envelope = {
                            "parent_sample_id": item["sample_id"],
                            "prompt": prompt,
                            "payload": item["packet"],
                            "reference_publication_sha256": data["reference_publication_sha256"]
                            if item["component"] == "C"
                            else None,
                        }
                        envelope["context_id"] = stable_json_sha256(envelope)
                        save(location / "context_envelope.json", envelope)
                        save(location / "item.json", item)
                        outcome = await locked_provider.execute(
                            directory=location,
                            condition=condition,
                            component=item["component"],
                            prompt=prompt,
                            payload=item["packet"],
                            deadline=deadline,
                            max_output_tokens=4096,
                            dispatcher=dispatcher,
                            slot_id=slot_id,
                            pricing=preflight["pricing"],
                            evaluation_started_at=started,
                        )
                        judgment = {
                            k: item[k]
                            for k in ("sample_id", "component", "point_id", "payload_sha256")
                        }
                        judgment.update(
                            outcome, identity=plan["identity"], context_id=envelope["context_id"]
                        )
                        if judgment["status"] == "invalid_output":
                            judgment["status"] = "execution_error"
                        save(location / "judgment.json", judgment)
                        save(
                            location / "completion.json",
                            artifact_inventory(location, {"completion.json"}),
                        )
                        judgments.append(judgment)
                        if judgment["status"] == "execution_error" and not judgment.get(
                            "rate_limited", False
                        ):
                            dispatcher.stop("Judge execution error; no retries")
                            break
                report = evaluation.build_report(plan, judgments)
                save(directory / "report.json", report)
                row.update(
                    status="completed" if report["coverage_complete"] else "evaluation_incomplete",
                    coverage_complete=report["coverage_complete"],
                )
    except Exception as error:
        row.update(status="integrity_failure", reason=f"{type(error).__name__}: {error}")
        dispatcher.stop("Slot integrity failure")
    save(directory / "judgments.json", judgments)
    row["judge_calls"] = sum(j["judge_calls"] for j in judgments)
    row["count_calls"] += sum(j["count_calls"] for j in judgments)
    save(directory / "summary.json", row)
    save(directory / "completion.json", artifact_inventory(directory, {"completion.json"}))
    LOG.info(
        "slot=%s model=%s repeat=%s status=%s",
        slot["case_id"],
        slot["model"],
        slot["repeat"],
        row["status"],
    )
    return row


async def dispatch(data_root: Path, output: Path) -> dict[str, Any]:
    """Run a bounded queue of ten answer workers under one shared remote ledger."""
    output, data_root = output.resolve(), data_root.resolve()
    if not output.is_relative_to(data_root / "pipelines/brisbane_baylands/task_13"):
        raise ValueError("Run must be under external Task 13 root")
    if (output / "completion.json").exists():
        raise ValueError("Sealed run cannot dispatch again")
    preflight = verify_preflight(output, data_root)
    # A fresh namespace must never reset the task-wide authorization. Claim the
    # sole paid run before constructing any provider, using create-only publication.
    claim_path = data_root / "pipelines/brisbane_baylands/task_13/paid_run_claim.json"
    claim = {
        "namespace": str(output.relative_to(data_root)),
        "preflight_sha256": sha256_file(output / "preflight.json"),
    }
    if not claim_path.exists():
        save(claim_path, claim)
    if read(claim_path) != claim:
        raise ValueError("Task 13 paid run already claimed; cumulative budget cannot reset")
    data = read(output / "inputs.json")
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=180)
    for slot in preflight["slots"]:
        queue.put_nowait(slot)
    results: dict[str, dict[str, Any]] = {}
    with LockedDispatcher(output / "ledger") as dispatcher:

        async def worker() -> None:
            """Consume independent slots; each slot enforces its own judge dependencies."""
            while not queue.empty():
                slot = queue.get_nowait()
                try:
                    row = await run_slot(slot, preflight, output, data[slot["case_id"]], dispatcher)
                except Exception:
                    dispatcher.stop("Worker integrity failure; preserve artifacts for inspection")
                    raise
                results[stable_json_sha256(slot)] = row
                queue.task_done()

        tasks = [asyncio.create_task(worker()) for _ in range(10)]
        try:
            outcomes = await asyncio.gather(*tasks, return_exceptions=True)
            errors = [value for value in outcomes if isinstance(value, BaseException)]
            if errors:
                raise RuntimeError("Worker failed; unsealed run preserved") from errors[0]
        except BaseException:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise
        accounting = dispatcher.snapshot()
    rows = [results[stable_json_sha256(s)] for s in preflight["slots"]]
    save(output / "slot_results.json", rows)
    save(output / "accounting.json", accounting)
    save(output / "completion.json", artifact_inventory(output, {"completion.json"}))
    return {"slots": len(rows), "accounting": accounting}


def main() -> None:
    """Expose explicit no-call preflight and separately gated paid dispatch."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "dispatch"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(os.environ["ER_COMMONS_DATA_ROOT"])
    logging.basicConfig(level=logging.INFO)
    result = (
        prepare(root, args.output)
        if args.mode == "prepare"
        else asyncio.run(dispatch(root, args.output))
    )
    LOG.info("%s", json.dumps(result))


if __name__ == "__main__":
    main()
