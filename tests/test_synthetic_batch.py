"""Exercise authoring failure boundaries without model or source-corpus access."""

from pathlib import Path
from typing import Any

import pytest

from er_commons import synthetic_batch as batch
from er_commons import synthetic_records


@pytest.fixture
def prepared(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Prepare two source-free dev cases with the actual sealed transport configuration."""
    root = tmp_path / "run"
    batch.prepare(
        root,
        {
            "cases": [{"case_id": "C001"}, {"case_id": "C002"}],
            "dev_case_ids": ["C001", "C002"],
            "source_bindings": {},
        },
        synthetic_records.SPEC_ROOT,
    )
    monkeypatch.setattr(
        synthetic_records,
        "validate_proposal",
        lambda output, packet: {
            "valid": output.get("valid", True),
            "errors": ["concrete fixture defect"],
        },
    )
    return root


def executor_for(outcomes: list[str], prompts: list[str]) -> Any:
    """Create a deterministic process double preserving normal attempt receipts."""

    def execute(arguments: list[str], prompt: str, attempt: Path) -> int:
        """Emit one controlled infrastructure, semantic, or successful outcome."""
        prompts.append(prompt)
        outcome = outcomes.pop(0)
        (attempt / "stdout.jsonl").write_text('{"type":"thread.started"}\n')
        (attempt / "stderr.txt").write_text("")
        if outcome == "interrupt":
            raise KeyboardInterrupt
        if outcome == "infra":
            return 1
        batch.save(attempt / "raw_output.json", {"valid": outcome == "ok"})
        return 0

    return execute


def test_retry_inputs_and_correction_are_bounded(prepared: Path) -> None:
    """Infrastructure retries retain exact prompts; correction includes concrete defects once."""
    prompts: list[str] = []
    sleeps: list[float] = []
    result = batch.run(
        prepared,
        case_ids=["C001"],
        executor=executor_for(["infra", "semantic", "infra", "ok"], prompts),
        sleeper=sleeps.append,
    )
    assert result[0]["status"] == "validated"
    assert prompts[0] == prompts[1]
    assert prompts[2] == prompts[3] and prompts[2] != prompts[1]
    assert "concrete fixture defect" in prompts[2]
    assert sleeps == [10, 30]
    receipts = batch.history(prepared / "cases" / "C001")
    assert [r["phase"] for _, r in receipts] == ["initial", "initial", "correction", "correction"]
    assert len({batch.read(p / "invocation.json")["input"]["sha256"] for p, _ in receipts}) == 1
    before = len(prompts)
    batch.run(prepared, case_ids=["C001"], executor=executor_for([], prompts))
    assert len(prompts) == before


def test_limits_and_unaffected_case(prepared: Path) -> None:
    """Exhaustion closes a failed case and still runs its neighbor."""
    prompts: list[str] = []
    result = batch.run(
        prepared,
        executor=executor_for(["infra", "infra", "infra", "ok"], prompts),
        sleeper=lambda _: None,
    )
    assert [r["status"] for r in result] == ["failed", "validated"]
    assert len(prompts) == 4


def test_semantic_correction_limit(prepared: Path) -> None:
    """A second invalid semantic result cannot trigger unlimited corrective calls."""
    result = batch.run(
        prepared, case_ids=["C001"], executor=executor_for(["semantic", "semantic"], [])
    )
    assert result[0]["status"] == "failed"
    assert len(batch.history(prepared / "cases" / "C001")) == 2


def test_interrupted_replay_preserves_attempt(prepared: Path) -> None:
    """An interrupted invocation remains visible and resumes with identical input."""
    prompts: list[str] = []
    with pytest.raises(KeyboardInterrupt):
        batch.run(prepared, case_ids=["C001"], executor=executor_for(["interrupt"], prompts))
    result = batch.run(
        prepared, case_ids=["C001"], executor=executor_for(["ok"], prompts), sleeper=lambda _: None
    )
    assert result[0]["status"] == "validated"
    assert prompts[0] == prompts[1]
    assert batch.history(prepared / "cases" / "C001")[0][1]["status"] == "infrastructure_failure"


def test_interruption_before_invocation(prepared: Path) -> None:
    """A crash immediately after creating an attempt directory is also recoverable."""
    attempt = prepared / "cases/C001/attempts/attempt_0001"
    attempt.mkdir(parents=True)
    result = batch.run(
        prepared, case_ids=["C001"], executor=executor_for(["ok"], []), sleeper=lambda _: None
    )
    assert result[0]["status"] == "validated"
    assert batch.read(attempt / "result.json")["phase"] == "unknown"


@pytest.mark.parametrize("relative", ["cases/C001/input.json", "config.json", "prepared.json"])
def test_changed_preparation_rejected(prepared: Path, relative: str) -> None:
    """Changed sealed inputs and intake membership cannot silently resume."""
    path = prepared / relative
    path.write_text(path.read_text() + " ")
    with pytest.raises(ValueError, match="changed|checksum"):
        batch.run(prepared, executor=executor_for([], []))


def test_changed_completed_attempt_blocks_only_its_case(prepared: Path) -> None:
    """Tampered saved output is never reused while an unaffected case continues."""
    batch.run(prepared, case_ids=["C001"], executor=executor_for(["ok"], []))
    (prepared / "cases/C001/attempts/attempt_0001/raw_output.json").write_text("{}")
    result = batch.run(prepared, executor=executor_for(["ok"], []))
    assert [r["status"] for r in result] == ["failed", "validated"]
    assert "inventory" in result[0]["reason"]


@pytest.mark.parametrize("ids", [["C999"], ["C001", "C001"], ["../escape"]])
def test_run_rejects_outside_or_duplicate_ids(prepared: Path, ids: list[str]) -> None:
    """No invocation may escape the exact prepared dev-case membership."""
    with pytest.raises(ValueError, match="development intake"):
        batch.run(prepared, case_ids=ids, executor=executor_for([], []))


@pytest.mark.parametrize("ids", [["C999"], ["C001", "C001"], ["../escape"]])
def test_prepare_rejects_bad_membership(tmp_path: Path, ids: list[str]) -> None:
    """Reject dangerous, duplicate or non-dev IDs before creating artifacts."""
    root = tmp_path / "bad"
    with pytest.raises(ValueError, match="development IDs"):
        batch.prepare(
            root,
            {"cases": [{"case_id": c} for c in ids], "dev_case_ids": ["C001"]},
            synthetic_records.SPEC_ROOT,
        )
    assert not root.exists()
