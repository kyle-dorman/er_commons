"""Synthetic qualification of isolated, restartable answer-preparation records."""

from pathlib import Path

import pytest

from er_commons import group_answer_batch as batch
from er_commons.artifact_io import json_bytes


def _prepare(tmp_path: Path) -> Path:
    """Prepare two source-free cases to expose accidental pooling or order changes."""
    root = tmp_path / "batch"
    batch.prepare_batch(
        root,
        {
            "cases": [
                {"case_id": "C002", "question": "Second?", "evidence": "two"},
                {"case_id": "C001", "question": "First?", "evidence": "one"},
            ]
        },
        "Synthetic prompt",
        {"type": "object"},
    )
    return root


@pytest.fixture
def record_stubs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate storage qualification from the independently tested answer contract."""
    from er_commons import group_answer_records as records

    monkeypatch.setattr(
        records,
        "validate_preparation",
        lambda output, case: {
            "valid": output["answer"]["case_id"] == case["case_id"],
        },
    )
    monkeypatch.setattr(records, "render_answer", lambda answer, case: case["question"])


def _executor(arguments: list[str], prompt: str, attempt: Path) -> int:
    """Write transport-compatible fake receipts with a case-local answer."""
    case = batch._read(attempt / "input.json")
    assert '"case_id": "' + case["case_id"] + '"' in prompt
    assert "--ephemeral" in arguments and "gpt-6-astra" in arguments
    (attempt / "raw_output.json").write_bytes(
        json_bytes(
            {
                "status": "proposed",
                "answer": {"case_id": case["case_id"]},
                "blocked_reason": None,
            }
        )
    )
    (attempt / "stdout.jsonl").write_text(
        '{"type":"item.completed","item":{"type":"agent_message"}}\n'
    )
    (attempt / "stderr.txt").write_text("")
    return 0


def test_restart_order_seal_and_tampering(tmp_path: Path, record_stubs: None) -> None:
    """Completed cases are reused and closure catches extra or modified files."""
    root = _prepare(tmp_path)
    results = batch.run_batch(root, executor=_executor)
    assert [r["case_id"] for r in results] == ["C002", "C001"]
    assert all(r["human_answer_approval"] is None for r in results)
    batch.run_batch(root, executor=lambda *_: pytest.fail("must reuse completed cases"))
    report = batch.seal_batch(root)
    assert report["valid"] and report["validated_proposals"] == 2
    with pytest.raises(ValueError, match="immutable"):
        batch.run_batch(root, executor=_executor)
    (root / "unexpected.txt").write_text("extra")
    with pytest.raises(ValueError, match="inventory"):
        batch.verify_batch(root)


def test_failure_and_interruption_preserve_retry_history(
    tmp_path: Path, record_stubs: None
) -> None:
    """Failed and abruptly interrupted attempts cannot masquerade as a proposal."""
    root = _prepare(tmp_path)
    first = batch.run_batch(root, executor=lambda *_: 17, case_ids=["C002"])
    assert first[0]["status"] == "blocked"
    incomplete = root / "cases/C001/attempts/attempt_0001"
    incomplete.mkdir(parents=True)
    (incomplete / "partial.txt").write_text("interrupted receipt")
    results = batch.run_batch(root, executor=_executor)
    assert all(r["version"] == 2 for r in results)
    assert (incomplete / "partial.txt").read_text() == "interrupted receipt"
    assert batch.seal_batch(root)["validated_proposals"] == 2


def test_blocked_accounting_and_no_unattempted_seal(tmp_path: Path, record_stubs: None) -> None:
    """Explicit technical blockers preserve blank decisions; missing cases prohibit sealing."""
    root = _prepare(tmp_path)
    batch.run_batch(root, executor=lambda *_: 1, case_ids=["C002"])
    with pytest.raises(ValueError, match="no terminal"):
        batch.seal_batch(root)
    batch.run_batch(root, executor=_executor, case_ids=["C001"])
    report = batch.seal_batch(root)
    assert report["blocked_cases"] == ["C002"]
    assert report["validated_proposals"] == 1


def test_input_mutation_and_case_selection_fail_closed(tmp_path: Path) -> None:
    """Changed frozen input and duplicate selections cannot reach execution."""
    root = _prepare(tmp_path)
    with pytest.raises(ValueError, match="unique"):
        batch.run_batch(root, executor=_executor, case_ids=["C001", "C001"])
    (root / "cases/C001/input.json").write_text("{}")
    with pytest.raises(ValueError, match="input changed"):
        batch.run_batch(root, executor=_executor)


def test_tool_activity_is_blocked(tmp_path: Path, record_stubs: None) -> None:
    """Even successful JSON output is rejected after unexpected tool use."""
    root = _prepare(tmp_path)

    def with_tool(arguments: list[str], prompt: str, attempt: Path) -> int:
        """Inject a forbidden command event into the fake transport."""
        _executor(arguments, prompt, attempt)
        (attempt / "stdout.jsonl").write_text('{"item":{"type":"command_execution"}}\n')
        return 0

    results = batch.run_batch(root, executor=with_tool)
    assert all(r["status"] == "blocked" and "tool" in r["reason"] for r in results)


def test_success_receipts_are_verified_before_reuse(tmp_path: Path, record_stubs: None) -> None:
    """An altered proposal cannot be silently reused simply because its status says valid."""
    root = _prepare(tmp_path)
    batch.run_batch(root, executor=_executor)
    (root / "cases/C001/attempts/attempt_0001/raw_output.json").write_text("{}")
    with pytest.raises(ValueError, match="Attempt files changed"):
        batch.run_batch(root, executor=_executor)


@pytest.mark.parametrize("target", ["raw", "reason", "approval"])
def test_blocked_history_tampering_rejected_before_retry(
    tmp_path: Path, record_stubs: None, target: str
) -> None:
    """Terminal blockers and their raw evidence are immutable retry predecessors."""
    root = _prepare(tmp_path)

    def failed(arguments: list[str], prompt: str, attempt: Path) -> int:
        """Preserve raw output even when the transport reports failure."""
        _executor(arguments, prompt, attempt)
        return 1

    batch.run_batch(root, executor=failed)
    attempt = root / "cases/C001/attempts/attempt_0001"
    if target == "raw":
        (attempt / "raw_output.json").write_text("changed")
    else:
        result = batch._read(attempt / "result.json")
        result["reason" if target == "reason" else "human_answer_approval"] = "changed"
        (attempt / "result.json").write_bytes(json_bytes(result))
    with pytest.raises(ValueError, match="changed"):
        batch.run_batch(root, executor=_executor)


def test_older_blocked_history_verified_at_seal(tmp_path: Path, record_stubs: None) -> None:
    """A later successful proposal does not hide corrupted failure history."""
    root = _prepare(tmp_path)
    batch.run_batch(root, executor=lambda *_: 1)
    batch.run_batch(root, executor=_executor)
    (root / "cases/C001/attempts/attempt_0001/process.json").write_text("{}")
    with pytest.raises(ValueError, match="Attempt files changed"):
        batch.seal_batch(root)


def test_partial_publication_only_allows_seal_resume(
    tmp_path: Path, record_stubs: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An interrupted completion-last publication is resumable without changing proposals."""
    root = _prepare(tmp_path)
    batch.run_batch(root, executor=_executor)
    save = batch._save

    def interrupt_completion(path: Path, value: object) -> None:
        """Simulate interruption after handoff publication and before completion."""
        if path.name == "completion.json":
            raise OSError("simulated interruption")
        save(path, value)

    monkeypatch.setattr(batch, "_save", interrupt_completion)
    with pytest.raises(OSError, match="interruption"):
        batch.seal_batch(root)
    with pytest.raises(ValueError, match="Publication already started"):
        batch.run_batch(root, executor=_executor)
    monkeypatch.setattr(batch, "_save", save)
    assert batch.seal_batch(root)["valid"]


def test_reported_model_mismatch_is_blocked(tmp_path: Path, record_stubs: None) -> None:
    """An explicitly reported different model cannot pass on configured-model provenance."""
    root = _prepare(tmp_path)

    def wrong_model(arguments: list[str], prompt: str, attempt: Path) -> int:
        """Supply an explicit mismatching backend-model event."""
        _executor(arguments, prompt, attempt)
        with (attempt / "stdout.jsonl").open("a") as stream:
            stream.write('{"model":"different-model"}\n')
        return 0

    results = batch.run_batch(root, executor=wrong_model)
    assert all(
        result["status"] == "blocked" and "model mismatch" in result["reason"] for result in results
    )
