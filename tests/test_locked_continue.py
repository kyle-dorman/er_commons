"""Invented continuation fixtures prove preservation and zero-request replay bounds."""

import asyncio
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from er_commons import locked_continue as continuation
from er_commons import locked_run as run
from er_commons.artifact_io import artifact_inventory, sha256_file, stable_json_sha256
from er_commons.locked_dispatch import LockedDispatcher, Request
from er_commons.target_generation import save


def ancestor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    """Create a fully sealed invented stopped run with one saved generation."""
    source = tmp_path / "pipelines/brisbane_baylands/task_13/original"
    source.mkdir(parents=True)
    slot = {"model": "luna", "repeat": 1, "case_id": "invented", "condition": "openai_generation"}
    preflight = {"slots": [slot], "provenance": {}, "pricing": {}}
    identity = {**slot, "run_id": stable_json_sha256({"slot": slot, "preflight": preflight})}
    loaded = {
        "slots": [slot],
        "inputs": {"invented": {}},
        "provenance": {},
        "frozen_configuration": {},
    }
    monkeypatch.setattr(continuation, "load_locked", lambda *_: loaded)
    monkeypatch.setattr(run, "implementation", lambda *_: {})
    for name, value in (
        ("preflight", preflight),
        ("inputs", loaded["inputs"]),
        ("frozen_configuration", {}),
    ):
        save(source / f"{name}.json", value)
    directory = source / "observations/luna_repeat1/invented"
    (directory / "generation").mkdir(parents=True)
    generation = {"status": "valid", "generation_calls": 1, "count_calls": 1}
    save(directory / "generation/result.json", generation)
    save(directory / "manifest.json", identity)
    failed = {
        "sample_id": "blocked",
        "status": "execution_error",
        "judge_calls": 0,
        "count_calls": 0,
    }
    save(directory / "judgments.json", [failed])
    row = {**identity, "status": "evaluation_incomplete"}
    save(directory / "summary.json", row)
    save(source / "slot_results.json", [row])
    clock = [100.0]
    with LockedDispatcher(source / "ledger", clock=lambda: clock[0]) as dispatcher:
        prefix = identity["run_id"] + "/target/"
        dispatcher.invoke(
            Request(
                prefix + "count",
                identity["run_id"],
                "count",
                Decimal(0),
                0,
                0,
                parent_key=prefix + "generation",
            ),
            lambda: (None, Decimal(0)),
        )
        dispatcher.invoke(
            Request(prefix + "generation", identity["run_id"], "generation", Decimal("0.1"), 1, 1),
            lambda: (None, Decimal("0.01")),
        )
        clock[0] = 110.0
        dispatcher.stop(continuation.STOP)
    save(source / "completion.json", artifact_inventory(source, {"completion.json"}))
    save(
        source.parent / "paid_run_claim.json",
        {
            "namespace": str(source.relative_to(tmp_path)),
            "preflight_sha256": sha256_file(source / "preflight.json"),
        },
    )
    return source, sha256_file(source / "completion.json")


def test_prepare_preserves_ancestor_and_original_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, digest = ancestor(tmp_path, monkeypatch)
    output = source.parent / "continuation"
    result = continuation.prepare(tmp_path, source, output, digest)
    assert result["actions"] == {"preserve": 0, "evaluate": 1, "generate": 0}
    assert sha256_file(source / "completion.json") == digest
    assert (source / "preflight.json").read_bytes() == (output / "preflight.json").read_bytes()
    assert run.read(output / "ledger/policy.json")["judge_per_answer"] == 30
    state = next(iter(run.read(output / "continuation_preflight.json")["slots"].values()))
    assert state["judgments"] == []
    assert state["discard_judgments"] == ["blocked"]
    assert state["evaluation_started_at"] == 100
    assert state["evaluation_elapsed_seconds"] == 10
    assert not (output / "ledger/stop.json").exists()
    assert (output / "ancestor_history/ledger/stop.json").exists()


def test_unknown_attempt_blocks_continuation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _ = ancestor(tmp_path, monkeypatch)
    next((source / "ledger").glob("*.settlement.json")).unlink()
    (source / "completion.json").unlink()
    save(source / "completion.json", artifact_inventory(source, {"completion.json"}))
    with pytest.raises(ValueError, match="Uncertain attempts"):
        continuation.verify_source(source, sha256_file(source / "completion.json"))


def test_approval_and_copied_bytes_are_checked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, digest = ancestor(tmp_path, monkeypatch)
    output = source.parent / "continuation"
    result = continuation.prepare(tmp_path, source, output, digest)
    with pytest.raises(FileNotFoundError):
        continuation.verify_preflight(tmp_path, output)
    save(
        output / "independent_continuation_review.json",
        {
            "status": "approved",
            "preflight_sha256": result["preflight_sha256"],
            "unresolved_findings": [],
        },
    )
    continuation.verify_preflight(tmp_path, output)
    (output / "observations/luna_repeat1/invented/generation/result.json").write_text("{}")
    with pytest.raises(ValueError, match="Copied ancestor bytes"):
        continuation.verify_preflight(tmp_path, output)


def test_expired_partial_is_preserved_without_remote_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, digest = ancestor(tmp_path, monkeypatch)
    output = source.parent / "continuation"
    result = continuation.prepare(tmp_path, source, output, digest)
    save(
        output / "independent_continuation_review.json",
        {
            "status": "approved",
            "preflight_sha256": result["preflight_sha256"],
            "unresolved_findings": [],
        },
    )
    monkeypatch.setattr(
        run.locked_provider, "generate_one", lambda *_: pytest.fail("generation replayed")
    )
    monkeypatch.setattr(
        run.locked_provider, "execute", lambda **_: pytest.fail("expired judge dispatched")
    )
    outcome = asyncio.run(continuation.dispatch(tmp_path, output))
    assert outcome["accounting"]["counts"] == {"count": 1, "generation": 1, "judge": 0}
    assert run.read(output / "slot_results.json")[0]["status"] == "evaluation_incomplete"


def test_saved_generation_is_reused_and_remaining_judge_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, digest = ancestor(tmp_path, monkeypatch)
    output = source.parent / "continuation"
    result = continuation.prepare(
        tmp_path,
        source,
        output,
        digest,
        exclude_sealed_pause=True,
        pause_authorization="Invented user approval",
    )
    save(
        output / "independent_continuation_review.json",
        {
            "status": "approved",
            "preflight_sha256": result["preflight_sha256"],
            "unresolved_findings": [],
        },
    )
    seen = []

    async def slot(*args: Any) -> dict[str, Any]:
        state = args[-1]
        seen.append(state)
        assert state["generation"]["status"] == "valid"
        assert state["judgments"] == []
        return {"status": "fixture_completed"}

    monkeypatch.setattr(run, "run_slot", slot)
    asyncio.run(continuation.dispatch(tmp_path, output))
    assert len(seen) == 1
    assert (source / "observations/luna_repeat1/invented/summary.json").exists()


def test_real_slot_reuses_saved_answer_and_exact_evaluation_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only a missing judge runs; retained native output and timing are unchanged."""
    source, _ = ancestor(tmp_path, monkeypatch)
    preflight = run.read(source / "preflight.json")
    slot = preflight["slots"][0]
    directory = source / "observations/luna_repeat1/invented"
    (directory / "summary.json").unlink()
    (directory / "judgments.json").unlink()
    raw = directory / "generation/raw_output.txt"
    raw.write_bytes(b"preserved invented answer")
    generation = run.read(directory / "generation/result.json")
    retained = {"sample_id": "already", "judge_calls": 1, "count_calls": 1}
    item = {
        "sample_id": "missing",
        "component": "A",
        "point_id": "p",
        "payload_sha256": "p",
        "packet": {},
    }
    plan = {"items": [item], "identity": {}}
    monkeypatch.setattr(run, "prepare_plan", lambda *_, **kwargs: plan)
    monkeypatch.setattr(run, "arm_prompt", lambda *_: "invented")
    monkeypatch.setattr(run, "component_settings", lambda *_: ("openai_generation", "", {}))
    monkeypatch.setattr(
        run.evaluation, "pending_items", lambda _, judgments: [item] if len(judgments) == 1 else []
    )
    monkeypatch.setattr(run.evaluation, "build_report", lambda *_: {"coverage_complete": True})
    monkeypatch.setattr(
        run.locked_provider, "generate_one", lambda *_: pytest.fail("saved answer regenerated")
    )
    calls = []

    async def execute(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return {"status": "completed", "judge_calls": 1, "count_calls": 1}

    monkeypatch.setattr(run.locked_provider, "execute", execute)
    state = {
        "generation": generation,
        "judgments": [retained],
        "evaluation_started_at": 123.456,
        "evaluation_elapsed_seconds": 10,
    }
    with LockedDispatcher(tmp_path / "fresh-ledger", judge_per_answer=30) as dispatcher:
        row = asyncio.run(run.run_slot(slot, preflight, source, {"mapping": {}}, dispatcher, state))
    assert row["status"] == "completed"
    assert len(calls) == 1 and calls[0]["evaluation_started_at"] == 123.456
    assert raw.read_bytes() == b"preserved invented answer"
    assert run.read(directory / "judgments.json")[0] == retained


def test_ledger_cannot_be_replaced_by_history_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Budget receipts must remain in the live cumulative ledger, even if archived."""
    source, digest = ancestor(tmp_path, monkeypatch)
    output = source.parent / "continuation"
    result = continuation.prepare(tmp_path, source, output, digest)
    save(
        output / "independent_continuation_review.json",
        {
            "status": "approved",
            "preflight_sha256": result["preflight_sha256"],
            "unresolved_findings": [],
        },
    )
    continuation._archive(output, next((output / "ledger").glob("*.reservation.json")))
    with pytest.raises(ValueError, match="Copied ancestor bytes"):
        continuation.verify_preflight(tmp_path, output)


def test_active_pause_union_preserves_live_time() -> None:
    """Overlapping administrative gaps are removed once, never resetting active time."""
    assert continuation.active_elapsed(100, 1000, [[0, 200], [150, 300], [600, 800]]) == 500
    assert continuation.active_elapsed(100, 200, [[300, 400]]) == 100


def test_second_epoch_preserves_history_claims_and_active_clock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two stopped epochs retain cost, identity and elapsed active evaluation time."""
    source, digest = ancestor(tmp_path, monkeypatch)
    first = source.parent / "first"
    prepared = continuation.prepare(tmp_path, source, first, digest)
    save(
        first / "independent_continuation_review.json",
        {
            "status": "approved",
            "preflight_sha256": prepared["preflight_sha256"],
            "unresolved_findings": [],
        },
    )
    clock = [200.0]
    monkeypatch.setattr(continuation.time, "time", lambda: clock[0])
    monkeypatch.setattr(
        continuation,
        "LockedDispatcher",
        lambda *a, **kw: LockedDispatcher(*a, clock=lambda: clock[0], **kw),
    )

    async def stop_slot(*args: Any) -> dict[str, Any]:
        directory = first / "observations/luna_repeat1/invented"
        row = run.read(source / "slot_results.json")[0]
        save(directory / "summary.json", row)
        save(directory / "judgments.json", [])
        clock[0] = 250
        args[-2].stop(continuation.DEADLINE_STOP)
        return row

    monkeypatch.setattr(run, "run_slot", stop_slot)
    asyncio.run(continuation.dispatch(tmp_path, first))
    sealed = sha256_file(first / "completion.json")
    with pytest.raises(ValueError, match="explicitly amended"):
        continuation.prepare(tmp_path, first, source.parent / "disallowed", sealed)
    second = source.parent / "second"
    result = continuation.prepare(
        tmp_path,
        first,
        second,
        sealed,
        exclude_sealed_pause=True,
        pause_authorization="yes exclude and continue",
    )
    manifest = run.read(second / "continuation_preflight.json")
    state = next(iter(manifest["slots"].values()))
    assert state["original_evaluation_started_at"] == 100
    assert state["evaluation_elapsed_seconds"] == 60  # 10 original + 50 resumed
    assert state["excluded_pause_intervals"] == [[110, 200]]
    assert (second / "ancestor_history/ledger/stop.json").exists()
    assert (second / manifest["history_prefix"] / "ledger/stop.json").exists()
    assert not (second / "observations/luna_repeat1/invented/continuation_started.json").exists()
    save(
        second / "independent_continuation_review.json",
        {
            "status": "approved",
            "preflight_sha256": result["preflight_sha256"],
            "unresolved_findings": [],
        },
    )
    continuation.verify_preflight(tmp_path, second)
    assert continuation._successor_claim(source.parent, first, sealed).name == f"{sealed}.json"
    assert manifest["cumulative_audit"]["settled_known_cost_usd"] == "0.01"
    assert sha256_file(first / "completion.json") == sealed


def test_archive_directory_retains_already_archived_receipt(tmp_path: Path) -> None:
    """An unattempted generation can archive its directory after its old epoch marker."""
    directory = tmp_path / "observations/model/case"
    save(directory / "continuation_started.json", {"at": 1})
    save(directory / "summary.json", {"status": "unattempted"})
    continuation._archive(tmp_path, directory / "continuation_started.json")
    continuation._archive(tmp_path, directory)
    assert not directory.exists()
    assert run.read(
        tmp_path / "ancestor_history/observations/model/case/continuation_started.json"
    ) == {"at": 1}
    assert (tmp_path / "ancestor_history/observations/model/case/summary.json").exists()
