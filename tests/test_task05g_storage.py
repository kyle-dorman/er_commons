"""Synthetic stage interruptions and exact restart closure for Task 05G."""

from pathlib import Path

import pytest

from er_commons.response_inventory import reference_replay_storage as storage


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path / "working" / "05g" / "attempts" / "synthetic" / "prepared"


@pytest.fixture
def bindings() -> dict[str, str]:
    return {"code": "synthetic-code", "spec": "synthetic-spec", "input": "synthetic-input"}


def test_complete_exact_repeat_is_read_only(root: Path, bindings: dict[str, str]) -> None:
    payloads = {"records/a.json": b"{}\n", "records/b.jsonl": b'{"id":1}\n'}
    first = storage.publish_checkpoint(root, payloads, bindings)
    mtimes = {path: path.stat().st_mtime_ns for path in root.rglob("*")}
    assert storage.publish_checkpoint(root, payloads, bindings) == first
    assert {path: path.stat().st_mtime_ns for path in root.rglob("*")} == mtimes
    assert storage.read_checkpoint(root, bindings) == first


@pytest.mark.parametrize("stage", ["prepared", "resolved", "indexes", "comparison"])
@pytest.mark.parametrize("interruption", [1, 2])
def test_each_stage_keeps_interruption_evidence(
    root: Path,
    bindings: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
    interruption: int,
) -> None:
    root = root.parent / stage
    real_write = storage._write_owned
    calls = 0

    def interrupted(path: Path, data: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == interruption:
            raise KeyboardInterrupt("synthetic interruption")
        real_write(path, data)

    monkeypatch.setattr(storage, "_write_owned", interrupted)
    with pytest.raises(KeyboardInterrupt):
        storage.publish_checkpoint(root, {"records.json": b"{}"}, bindings)
    assert not (root / "completion.json").exists()
    assert (root / "failure.json").is_file()
    with pytest.raises(ValueError, match="incomplete"):
        storage.publish_checkpoint(root, {"records.json": b"{}"}, bindings)
    monkeypatch.setattr(storage, "_write_owned", real_write)
    replacement = root.parent / (stage + "-attempt2")
    assert storage.publish_checkpoint(replacement, {"records.json": b"{}"}, bindings)
    assert (root / "failure.json").is_file()


@pytest.mark.parametrize("key", ["code", "spec", "input"])
def test_restart_rejects_changed_binding(root: Path, bindings: dict[str, str], key: str) -> None:
    storage.publish_checkpoint(root, {"a.json": b"{}"}, bindings)
    with pytest.raises(ValueError, match="mismatch"):
        storage.read_checkpoint(root, {**bindings, key: "changed"})


@pytest.mark.parametrize("mutation", ["bytes", "extra", "empty_directory", "missing", "symlink"])
def test_restart_rejects_tree_mutations(
    root: Path, bindings: dict[str, str], mutation: str
) -> None:
    storage.publish_checkpoint(root, {"a.json": b"{}"}, bindings)
    if mutation == "bytes":
        (root / "a.json").write_bytes(b"[]")
    elif mutation == "extra":
        (root / "extra.json").write_bytes(b"{}")
    elif mutation == "empty_directory":
        (root / "extra").mkdir()
    elif mutation == "missing":
        (root / "a.json").unlink()
    else:
        (root / "a.json").unlink()
        (root / "a.json").symlink_to(root / "completion.json")
    with pytest.raises(ValueError):
        storage.read_checkpoint(root, bindings)


def test_conflicting_repeat_never_overwrites(root: Path, bindings: dict[str, str]) -> None:
    first = storage.publish_checkpoint(root, {"a.json": b"{}"}, bindings)
    with pytest.raises(ValueError, match="conflicting"):
        storage.publish_checkpoint(root, {"a.json": b"[]"}, bindings)
    assert storage.read_checkpoint(root, bindings) == first


@pytest.mark.parametrize("name", ["../a.json", "/a.json", "a//b.json", "completion.json", "a.pdf"])
def test_unsafe_path_rejected_before_writes(
    root: Path, bindings: dict[str, str], name: str
) -> None:
    with pytest.raises(ValueError):
        storage.publish_checkpoint(root, {name: b"{}"}, bindings)
    assert not root.exists()


def test_resource_stop_suppresses_completion(root: Path, bindings: dict[str, str]) -> None:
    calls = 0

    def guard() -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise RuntimeError("synthetic output byte limit")

    with pytest.raises(RuntimeError, match="byte limit"):
        storage.publish_checkpoint(root, {"a.json": b"{}"}, bindings, before_completion=guard)
    assert (root / "a.json").is_file()
    assert (root / "failure.json").is_file()
    assert not (root / "completion.json").exists()


def test_upstream_namespace_is_rejected(tmp_path: Path, bindings: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="working/05g"):
        storage.publish_checkpoint(tmp_path / "accepted", {"a.json": b"{}"}, bindings)
    assert not (tmp_path / "accepted").exists()
