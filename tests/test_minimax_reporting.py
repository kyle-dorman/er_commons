"""Synthetic MiniMax rosters retain all failures and reject cross-condition joins."""

import json
from pathlib import Path

import pytest
from test_locked_reporting import reseal

from er_commons.artifact_io import stable_json_sha256
from er_commons.minimax_reporting import load_run
from er_commons.reporting import answer_tables


def fixture_run(tmp_path: Path) -> tuple[Path, Path]:
    """Build ninety invented unavailable observations without real benchmark data."""
    repo, source = tmp_path / "repo", tmp_path / "source"
    (repo / "docs/specs").mkdir(parents=True)
    source.mkdir()
    frozen = {"targets": {"luna": {"model": "luna"}, "haiku": {"model": "haiku"}}}
    text = json.dumps(frozen)
    (repo / "docs/specs/task11e_frozen_generation_v1.json").write_text(text)
    (source / "frozen_configuration.json").write_text(text)
    cases = [f"SYNTHETIC{i:03}" for i in range(30)]
    slots = [
        {"model": "minimax", "condition": "minimax_cloud", "repeat": r, "case_id": c}
        for r in (1, 2, 3)
        for c in cases
    ]
    preflight = {"slots": slots, "minimax_condition": {"model": "minimax-m3.1-flash"}}
    (source / "preflight.json").write_text(json.dumps(preflight))
    (source / "inputs.json").write_text(json.dumps(dict.fromkeys(cases, {})))
    outcomes = []
    for s in slots:
        identity = {**s, "run_id": stable_json_sha256({"slot": s, "preflight": preflight})}
        folder = source / "observations" / f"minimax_repeat{s['repeat']}" / s["case_id"]
        folder.mkdir(parents=True)
        row = {**identity, "status": "not_dispatched"}
        (folder / "manifest.json").write_text(json.dumps(identity))
        (folder / "summary.json").write_text(json.dumps(row))
        outcomes.append(row)
    (source / "slot_results.json").write_text(json.dumps(outcomes))
    (source / "accounting.json").write_text(json.dumps({"stop_reason": "fixture stop"}))
    reseal(source)
    return repo, source


def test_unavailable_roster_preserved(tmp_path: Path) -> None:
    """Missing calls remain ninety planned outcomes on thirty distinct questions."""
    repo, source = fixture_run(tmp_path)
    rows = load_run(repo, source, reseal(source))["rows"]
    table = answer_tables(rows)["answers"]
    assert len(table) == 90
    assert len({r["case_id"] for r in table}) == 30
    assert {r["joint"] for r in table} == {"unavailable"}
    assert {r["model_id"] for r in table} == {"minimax-m3.1-flash"}


@pytest.mark.parametrize("filename", ["preflight.json", "slot_results.json"])
def test_duplicate_slot_rejected(tmp_path: Path, filename: str) -> None:
    """A resealed duplicate must not replace a missing planned repeat."""
    repo, source = fixture_run(tmp_path)
    p = source / filename
    value = json.loads(p.read_text())
    rows = value["slots"] if filename == "preflight.json" else value
    rows[-1] = rows[0]
    p.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="roster|outcomes"):
        load_run(repo, source, reseal(source))


@pytest.mark.parametrize("malformed", [False, True])
def test_native_ollama_delivery_replays_frozen_scores_offline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, malformed: bool
) -> None:
    """Replay actual chat-message shape through canonical delivery and frozen evaluation."""
    import socket

    from test_development_evaluation import fixture

    from er_commons import development_evaluation as evaluation
    from er_commons.artifact_io import sha256_bytes
    from er_commons.locked_reporting import _observation
    from er_commons.minimax_provider import MODEL, delivery
    from er_commons.reporting import answer_outcomes
    from er_commons.reporting_inputs import SealedInputs
    from er_commons.target_generation import save

    monkeypatch.setattr(socket, "create_connection", lambda *_a, **_k: pytest.fail("network"))
    monkeypatch.setattr(socket.socket, "connect", lambda *_a, **_k: pytest.fail("network"))
    raw, generation, record, mapping, _, reference = fixture()
    raw = b"{" if malformed else raw
    mapping["split"] = "test"
    slot = {"arm": "test30", "model": "minimax", "repeat": 1, "case_id": "C041"}
    preflight = {"slots": [slot]}
    identity = {**slot, "run_id": stable_json_sha256({"slot": slot, "preflight": preflight})}
    native = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Invented frozen instruction."},
            {"role": "user", "content": json.dumps(record["payload"])},
        ],
        "max_tokens": 12288,
    }
    native_bytes = json.dumps(native).encode()
    canonical = delivery(native, "ollama")
    generation.update(
        run_id=identity["run_id"],
        candidate_sha256=sha256_bytes(raw),
        request_sha256=sha256_bytes(native_bytes),
        model=MODEL,
        returned_model=MODEL,
        provider="ollama",
        status="invalid_output" if malformed else "valid",
    )
    generation["candidate_id"] = stable_json_sha256(
        {key: generation[key] for key in evaluation.IDENTITY_FIELDS if key != "candidate_id"}
    )
    folder = tmp_path / "observations/minimax_repeat1/C041"
    gen = folder / "generation"
    gen.mkdir(parents=True)
    save(folder / "manifest.json", identity)
    save(folder / "interruption.json", {**identity, "status": "interrupted_uncertain"})
    save(gen / "result.json", generation)
    (gen / ("raw_output.txt" if malformed else "candidate.json")).write_bytes(raw)
    (gen / "native_request.json").write_bytes(native_bytes)
    save(gen / "delivery_projection.json", canonical)
    save(gen / "packet.json", record)
    plan = evaluation.prepare_candidate(
        raw, generation, record, mapping, canonical, reference, expected_split="test"
    )
    expected_report = evaluation.build_report(plan, [])
    save(folder / "plan.json", plan)
    save(folder / "report.json", expected_report)
    reseal(tmp_path)
    sealed = SealedInputs(tmp_path, json.loads((tmp_path / "completion.json").read_text()))
    row = _observation(
        sealed,
        slot,
        {"record": record, "mapping": mapping, "reference": reference},
        {"targets": {"minimax": {"model": MODEL}}},
        preflight,
        delivery_fn=delivery,
    )
    assert row["plan"] == plan
    assert row["report"] == expected_report
    assert answer_outcomes(row)["automatic"] == ("fail" if malformed else "pass")
    assert answer_outcomes(row)["joint"] == ("fail" if malformed else "unavailable")
