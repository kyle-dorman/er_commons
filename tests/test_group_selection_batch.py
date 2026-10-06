"""Mutation boundaries for restartable 08B batch project setup."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from er_commons.group_selection_batch import merge_register, project_for_group, verify_project


class FakeClient:
    """Record writes while serving immutable snapshots of existing native data."""

    def __init__(self, native: list[dict[str, Any]] | None = None) -> None:
        self.native = native or []
        self.writes: list[str] = []

    def project(self, project_id: int) -> dict[str, Any]:
        """Return a shared form and sequential queue."""
        return {
            "id": project_id,
            "title": "existing",
            "label_config": "form",
            "sampling": "Sequential sampling",
        }

    def tasks(self, project_id: int) -> list[dict[str, Any]]:
        """Return saved tasks without modifying annotation objects."""
        return deepcopy(self.native)

    def create(self, title: str, form: str) -> dict[str, Any]:
        """Track newly created project."""
        self.writes.append("create")
        return {"id": 10, "title": title}

    def import_tasks(self, project_id: int, tasks: list[dict[str, Any]]) -> None:
        """Track blank imports; never fabricate annotations."""
        self.writes.append("import")
        self.native = [{"id": i, **deepcopy(task)} for i, task in enumerate(tasks, 1)]

    def ordered_view(self, project_id: int) -> int:
        """Return an existing ordered view."""
        return 9


def queue() -> list[dict[str, Any]]:
    """Provide two distinct source-bound payloads in intended order."""
    return [{"data": {"group": "g", "comment_id": f"c{i}", "rank": i}} for i in (1, 2)]


def test_reuse_preserves_saved_annotations(tmp_path: Path) -> None:
    native = [
        {"id": i, **task, "annotations": [{"result": ["human"]}]}
        for i, task in enumerate(queue(), 1)
    ]
    client = FakeClient(native)
    before = deepcopy(client.native)
    pid, status, verification = project_for_group(
        client, [], "g", queue(), "form", [{"project_id": 7}], tmp_path / "project.json"
    )  # type: ignore[arg-type]
    assert (pid, status, verification["annotations"]) == (7, "reused", 2)
    assert client.native == before
    assert not client.writes


def test_create_then_restart_has_no_duplicate_writes(tmp_path: Path) -> None:
    client = FakeClient()
    receipt = tmp_path / "project.json"
    assert project_for_group(client, [], "g", queue(), "form", [], receipt)[1] == "newly_created"  # type: ignore[arg-type]
    assert client.writes == ["create", "import"]
    assert project_for_group(client, [], "g", queue(), "form", [], receipt)[1] == "newly_created"  # type: ignore[arg-type]
    assert client.writes == ["create", "import"]


def test_partial_import_is_held_without_reset(tmp_path: Path) -> None:
    client = FakeClient([{"id": 1, **queue()[0]}])
    with pytest.raises(ValueError, match="coverage"):
        project_for_group(
            client, [], "g", queue(), "form", [{"project_id": 7}], tmp_path / "project.json"
        )  # type: ignore[arg-type]
    assert not client.writes


def test_duplicate_project_is_held(tmp_path: Path) -> None:
    client = FakeClient()
    with pytest.raises(ValueError, match="Multiple"):
        project_for_group(
            client,
            [],
            "g",
            queue(),
            "form",
            [{"project_id": 7}, {"project_id": 8}],
            tmp_path / "project.json",
        )  # type: ignore[arg-type]
    assert not client.writes


def test_order_or_source_change_rejected() -> None:
    project = FakeClient().project(7)
    native = [{"id": i, **task} for i, task in enumerate(reversed(queue()), 1)]
    with pytest.raises(ValueError, match="order"):
        verify_project(project, native, queue(), "form")


def test_register_preserves_latest_other_stage(tmp_path: Path) -> None:
    path = tmp_path / "register.json"
    preserved = {"stage": "08E", "group": "health", "state": "concurrent update"}
    path.write_text(json.dumps({"batches": [preserved], "other": "unchanged"}))
    before = path.read_bytes()
    merge_register(
        path, [{"stage": "08B", "group": "new", "state": "prepared", "project_id": 10}], tmp_path
    )
    after = json.loads(path.read_bytes())
    assert after["batches"][0] == preserved
    assert after["other"] == "unchanged"
    assert next(tmp_path.glob("batch_register_before_*.json")).read_bytes() == before


def test_register_refuses_concurrent_completed_review(tmp_path: Path) -> None:
    path = tmp_path / "register.json"
    path.write_text(
        json.dumps({"batches": [{"stage": "08B", "group": "new", "state": "selection_complete"}]})
    )
    before = path.read_bytes()
    with pytest.raises(ValueError, match="completed"):
        merge_register(path, [{"stage": "08B", "group": "new", "project_id": 10}], tmp_path)
    assert path.read_bytes() == before


def test_invalid_schema_group_does_not_block_ready_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Malformed intake remains blocked while the next verified group reaches setup."""
    from jsonschema import ValidationError

    from er_commons import group_selection_batch as batch

    entries = []
    for group in ("invalid", "ready"):
        entry: dict[str, Any] = {
            "group": group,
            "slug": group,
            "candidate_count": 1,
            "interface_version": "v2",
        }
        for key in ("input", "proposal", "handoff", "manifest", "completion"):
            entry[key] = {"path": str(tmp_path / group / f"{key}.json"), "sha256": "fake"}
        entries.append(entry)
    monkeypatch.setattr(batch, "verified_index", lambda *_: {"groups": entries})
    register = tmp_path / "register.json"
    monkeypatch.setattr(
        batch,
        "checked",
        lambda path, *_: b'{"batches": []}' if path == register else b'{"schema_version": "v2"}',
    )
    monkeypatch.setattr(batch.group_selection, "prepare", lambda *_: None)

    def load(path: Path) -> list[dict[str, Any]]:
        """Reject one schema without impeding the next group."""
        if "invalid" in path.parts:
            raise ValidationError("invalid schema fixture")
        return queue()

    monkeypatch.setattr(batch.group_selection, "load_prepared", load)
    monkeypatch.setattr(
        batch, "project_for_group", lambda *_: (10, "newly_created", {"view_id": 9})
    )
    saved_updates: list[dict[str, Any]] = []
    monkeypatch.setattr(batch, "merge_register", lambda _, rows, __: saved_updates.extend(rows))

    class EmptyServer(FakeClient):
        """Supply an empty project listing for the isolated orchestration fixture."""

        url = "http://example.test"

        def projects(self) -> list[dict[str, Any]]:
            """List no preexisting project."""
            return []

    result = batch.setup(
        tmp_path / "index.json",
        tmp_path / "completion.json",
        tmp_path,
        tmp_path / "out",
        register,
        EmptyServer(),
    )  # type: ignore[arg-type]
    assert [row["status"] for row in result["groups"]] == ["blocked", "newly_created"]
    assert [row["state"] for row in saved_updates] == [
        "setup_blocked",
        "prepared_awaiting_human_review",
    ]


def test_native_form_outer_whitespace_only_is_accepted() -> None:
    """Server trimming a trailing newline preserves form identity, internal edits do not."""
    project = FakeClient().project(7)
    native = [{"id": i, **task} for i, task in enumerate(queue(), 1)]
    result = verify_project(project, native, queue(), "form\n")
    assert result["form_sha256"] != result["native_form_sha256"]
    with pytest.raises(ValueError, match="template"):
        verify_project(project, native, queue(), "fo rm\n")


def test_retry_created_empty_receipt_reuses_id_and_preserves_origin(tmp_path: Path) -> None:
    """The initial create receipt survives an interrupted import and records setup origin."""
    client = FakeClient()
    receipt = tmp_path / "project.json"
    receipt.write_text(json.dumps({"project_id": 7, "state": "created_empty", "title": "saved"}))
    pid, status, _ = project_for_group(client, [], "g", queue(), "form\n", [], receipt)  # type: ignore[arg-type]
    assert (pid, status) == (7, "newly_created")
    assert client.writes == ["import"]
    assert json.loads(receipt.read_bytes())["created_in_setup"] is True
