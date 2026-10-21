"""Invented sealed rosters test held-out publication without reading real cases."""

import json
from pathlib import Path

import pytest

from er_commons.artifact_io import sha256_file, stable_json_sha256
from er_commons.locked_inputs import planned_slots
from er_commons.locked_reporting import load_run
from er_commons.reporting import answer_tables
from er_commons.reporting_presentation import gallery_html
from er_commons.reporting_run import _binding


def fixture_run(tmp_path: Path) -> tuple[Path, Path]:
    """Create an entirely synthetic unavailable 180-slot run with exact seals."""
    repo, source = tmp_path / "repo", tmp_path / "source"
    (repo / "docs/specs").mkdir(parents=True)
    source.mkdir()
    frozen = {"targets": {"luna": {"model": "gpt-6-luna"}, "haiku": {"model": "claude-haiku-5-5"}}}
    encoded = json.dumps(frozen)
    (repo / "docs/specs/task11e_frozen_generation_v1.json").write_text(encoded)
    (source / "frozen_configuration.json").write_text(encoded)
    cases = [f"SYNTHETIC{i:03}" for i in range(30)]
    slots = planned_slots(cases)
    preflight = {"slots": slots}
    (source / "preflight.json").write_text(json.dumps(preflight, sort_keys=True))
    (source / "inputs.json").write_text(json.dumps(dict.fromkeys(cases, {})))
    for slot in slots:
        identity = {**slot, "run_id": stable_json_sha256({"slot": slot, "preflight": preflight})}
        folder = (
            source / "observations" / f"{slot['model']}_repeat{slot['repeat']}" / slot["case_id"]
        )
        folder.mkdir(parents=True)
        (folder / "manifest.json").write_text(json.dumps(identity))
        (folder / "summary.json").write_text(json.dumps({**identity, "status": "unattempted"}))
    reseal(source)
    return repo, source


def reseal(source: Path) -> str:
    """Rebind invented fixture bytes after an intentional mutation."""
    seal = {
        "files": [
            _binding(path, str(path.relative_to(source)))
            for path in sorted(source.rglob("*"))
            if path.is_file() and path.name != "completion.json"
        ]
    }
    (source / "completion.json").write_text(json.dumps(seal))
    return sha256_file(source / "completion.json")


def test_unattempted_slots_preserved(tmp_path: Path) -> None:
    """All planned failures remain the test-only denominator for both models."""
    repo, source = fixture_run(tmp_path)
    loaded = load_run(repo, source, sha256_file(source / "completion.json"))
    assert len(loaded["rows"]) == 180
    answers = answer_tables(loaded["rows"])["answers"]
    assert {row["split"] for row in answers} == {"test"}
    assert {row["exposure_group"] for row in answers} == {"test_30"}
    assert all(row["joint"] == "unavailable" for row in answers)


def test_rejects_duplicate_slot(tmp_path: Path) -> None:
    """A resealed duplicate does not evade exact roster validation."""
    repo, source = fixture_run(tmp_path)
    path = source / "preflight.json"
    preflight = json.loads(path.read_text())
    preflight["slots"][-1] = preflight["slots"][0]
    path.write_text(json.dumps(preflight))
    with pytest.raises(ValueError, match="planned slots"):
        load_run(repo, source, reseal(source))


def test_verifies_even_unused_receipts(tmp_path: Path) -> None:
    """Whole-run verification catches tampering outside selected reporting inputs."""
    repo, source = fixture_run(tmp_path)
    receipt = source / "raw_receipt.json"
    receipt.write_text("{}")
    digest = reseal(source)
    receipt.write_text('{"changed":true}')
    with pytest.raises(ValueError, match="Sealed input mismatch"):
        load_run(repo, source, digest)


def test_gallery_discloses_incomplete_execution() -> None:
    """A stopped run states coverage and stop reason without relabeling missing scores."""
    gallery = gallery_html(
        {
            "answers": [{"split": "test", "case_id": "SYNTHETIC"}],
            "execution_status": [
                {"model": "luna", "planned": 90, "completed": 80, "stop_reason": "item limit"}
            ],
        }
    )
    assert "Incomplete evaluation" in gallery
    assert "80/90 fully evaluated slots" in gallery
    assert "Recorded stop: item limit" in gallery
    assert "main target-model results" not in gallery


@pytest.mark.parametrize("malformed", [False, True])
def test_partial_or_invalid_candidate_replays_without_summary(
    tmp_path: Path, malformed: bool
) -> None:
    """Interrupted delivery keeps replayable partial scores and malformed automatic failure."""
    from test_development_evaluation import fixture

    from er_commons import development_evaluation as evaluation
    from er_commons.artifact_io import sha256_bytes
    from er_commons.locked_reporting import _observation
    from er_commons.reporting import answer_outcomes
    from er_commons.reporting_inputs import SealedInputs

    raw, generation, record, mapping, receipt, reference = fixture()
    slot = {"arm": "test30", "model": "luna", "repeat": 1, "case_id": "C041"}
    preflight = {"slots": [slot]}
    identity = {**slot, "run_id": stable_json_sha256({"slot": slot, "preflight": preflight})}
    raw = b"{" if malformed else raw
    mapping["split"] = "test"
    generation.update(
        run_id=identity["run_id"],
        candidate_sha256=sha256_bytes(raw),
        request_sha256=sha256_bytes(json.dumps(receipt).encode()),
    )
    generation["candidate_id"] = stable_json_sha256(
        {key: generation[key] for key in generation if key != "candidate_id"}
    )
    generation.update(
        model="gpt-6-luna",
        returned_model="gpt-6-luna",
        provider="openai",
        status="invalid_output" if malformed else "valid",
    )
    relative = "observations/luna_repeat1/C041"
    folder = tmp_path / relative
    gen = folder / "generation"
    gen.mkdir(parents=True)
    (folder / "manifest.json").write_text(json.dumps(identity))
    (folder / "interruption.json").write_text(
        json.dumps({**identity, "status": "interrupted_uncertain"})
    )
    (gen / "result.json").write_text(json.dumps(generation))
    (gen / ("raw_output.txt" if malformed else "candidate.json")).write_bytes(raw)
    (gen / "native_request.json").write_text(json.dumps(receipt))
    (gen / "delivery_projection.json").write_text(json.dumps(receipt))
    (gen / "packet.json").write_text(json.dumps(record))
    plan = evaluation.prepare_candidate(
        raw, generation, record, mapping, receipt, reference, expected_split="test"
    )
    (folder / "plan.json").write_text(json.dumps(plan))
    reseal(tmp_path)
    sealed = SealedInputs(tmp_path, json.loads((tmp_path / "completion.json").read_text()))
    row = _observation(
        sealed,
        slot,
        {"record": record, "mapping": mapping, "reference": reference},
        {"targets": {"luna": {"model": "gpt-6-luna"}}},
        preflight,
    )
    assert row["report"] is not None
    assert answer_outcomes(row)["automatic"] == ("fail" if malformed else "pass")
    assert answer_outcomes(row)["joint"] == ("fail" if malformed else "unavailable")
