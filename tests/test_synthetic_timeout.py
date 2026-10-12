"""Configured authoring deadlines reach the real transport without launching a process."""

import subprocess
from pathlib import Path
from typing import Any

import pytest

from er_commons import group_answer_batch, synthetic_batch, synthetic_records


@pytest.mark.parametrize("staged,expected", [(False, 1200), (True, 3600)])
def test_configured_deadline_reaches_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, staged: bool, expected: int
) -> None:
    """Check legacy/default compatibility and the fresh batch's longer bounded deadline."""
    intake: dict[str, Any] = {
        "cases": [{"case_id": "C001"}],
        "dev_case_ids": ["C001"],
        "source_bindings": {},
    }
    if staged:
        intake["annotation_version"] = "task09a2.stage_expectations.v1"
        intake["cases"][0].update(
            annotation_version=intake["annotation_version"], regeneration_slots={"P01": "slot"}
        )
    root = tmp_path / "run"
    synthetic_batch.prepare(root, intake, synthetic_records.SPEC_ROOT, smoke=True)
    assert synthetic_batch.read(root / "config.json")["timeout_seconds"] == expected
    seen: list[int] = []

    class FakeProcess:
        """Supply only the successful process interface consumed by execute_codex."""

        returncode = 0

        def __init__(self, arguments: list[str], **kwargs: Any) -> None:
            self.output = Path(arguments[arguments.index("-o") + 1])
            kwargs["stdout"].write(b'{"type":"thread.started"}\n')

        def communicate(self, *, input: bytes, timeout: int) -> None:
            """Capture the effective timeout and emit a deterministic test response."""
            assert input
            seen.append(timeout)
            synthetic_batch.save(self.output, {"valid": True})

    monkeypatch.setattr(subprocess, "Popen", FakeProcess)
    monkeypatch.setattr(
        synthetic_records, "validate_proposal", lambda output, packet: {"valid": True, "errors": []}
    )
    result = synthetic_batch.run(root)
    assert result[0]["status"] == "validated", result
    assert seen == [expected]


def test_direct_transport_keeps_default_deadline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Existing three-argument transport callers retain the1200-second default."""
    seen: list[int] = []

    class FakeProcess:
        returncode = 0

        def __init__(self, arguments: list[str], **kwargs: Any) -> None:
            pass

        def communicate(self, *, input: bytes, timeout: int) -> None:
            seen.append(timeout)

    monkeypatch.setattr(subprocess, "Popen", FakeProcess)
    assert group_answer_batch.execute_codex(["unused"], "fixture", tmp_path) == 0
    assert seen == [1200]
