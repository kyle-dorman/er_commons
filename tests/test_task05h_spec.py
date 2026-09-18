"""Synthetic checks for strict release requests and identity boundaries."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from er_commons.response_inventory.release_spec import (
    QUESTION_VERSION,
    SCHEMA_PATH,
    SELECTION_POLICY,
    VERSION,
    VIEW_POLICY,
    ReleaseSpec,
    contained_path,
    current_runtime_versions,
    load_release_spec,
    plan_identity,
    required_repository_paths,
    verify_repository_bindings,
)


def request(repository: Path) -> dict[str, Any]:
    """Write repository-only fixtures without production artifact access."""
    bindings = []
    for name in sorted(required_repository_paths() | {"bindings.json"}):
        path = repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n")
        bindings.append({"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    selection = repository / "selection.json"
    selection.write_text("{}\n")
    return {
        "schema_version": VERSION,
        "task_stage": "05h",
        "binding_freeze": next(item for item in bindings if item["path"] == "bindings.json"),
        "selection_freeze": {
            "path": "selection.json",
            "sha256": hashlib.sha256(selection.read_bytes()).hexdigest(),
        },
        "selection_policy": SELECTION_POLICY,
        "question_version": QUESTION_VERSION,
        "view_policy": VIEW_POLICY,
        "runtime_versions": current_runtime_versions(),
        "repository_bindings": bindings,
        "output_relative_root": (
            "pipelines/brisbane_baylands/task_05_response_inventory/working/05h"
        ),
        "authorization": {
            key: False for key in ("execution", "finalization", "publication", "acceptance")
        },
        "limits": {},
        "source_pdf_access": False,
        "image_access": False,
        "render_access": False,
        "model_access": False,
        "network_access": False,
        "hash_large_upstream_payloads": False,
    }


def test_load_is_repository_only_and_schema_matches(tmp_path: Path) -> None:
    """A valid request resolves without any external input or artifact root."""
    spec = request(tmp_path)
    path = tmp_path / "request.json"
    path.write_text(json.dumps(spec))
    normalized, digest = load_release_spec(path, tmp_path)
    assert normalized["limits"]["workers"] == 1
    assert digest == plan_identity(spec)
    checked_schema = Path(__file__).parents[1] / SCHEMA_PATH
    assert json.loads(checked_schema.read_text()) == ReleaseSpec.model_json_schema()


def test_plan_identity_excludes_later_mutable_controls(tmp_path: Path) -> None:
    """Review updates and approvals cannot create a circular plan identity."""
    spec = request(tmp_path)
    changed = copy.deepcopy(spec)
    changed["authorization"]["execution"] = True
    changed["selection_freeze"]["sha256"] = "a" * 64
    changed["review_decisions"] = {
        "authority": "artifact_root",
        "path": "decisions.jsonl",
        "sha256": "b" * 64,
    }
    changed["quality_report"] = {
        "authority": "repository",
        "path": "quality.json",
        "sha256": "c" * 64,
    }
    changed["repository_bindings"].reverse()
    assert plan_identity(changed) == plan_identity(spec)
    changed["binding_freeze"]["sha256"] = "d" * 64
    assert plan_identity(changed) != plan_identity(spec)


@pytest.mark.parametrize(
    "field",
    [
        "source_pdf_access",
        "image_access",
        "render_access",
        "model_access",
        "network_access",
        "hash_large_upstream_payloads",
    ],
)
def test_source_controls_cannot_be_enabled(tmp_path: Path, field: str) -> None:
    """A request cannot expand approved source-free operations."""
    spec = request(tmp_path)
    spec[field] = True
    with pytest.raises(ValidationError):
        ReleaseSpec.model_validate(spec)
    spec[field] = 0
    with pytest.raises(ValidationError):
        ReleaseSpec.model_validate(spec)


@pytest.mark.parametrize("value", ["../outside", "/absolute", "a/../b", "./a", "a//b", "a\\b"])
def test_path_aliases_are_rejected(tmp_path: Path, value: str) -> None:
    """Every reference has one portable contained spelling."""
    spec = request(tmp_path)
    spec["selection_freeze"]["path"] = value
    with pytest.raises(ValidationError):
        ReleaseSpec.model_validate(spec)


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    """Lexically contained paths cannot read outside their authority."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "escape").symlink_to(tmp_path)
    with pytest.raises(ValueError, match="escapes root"):
        contained_path(root, "escape/secret")


def test_exact_owners_and_digests_are_required(tmp_path: Path) -> None:
    """Dropping an owner or changing accepted bytes blocks verification."""
    spec = request(tmp_path)
    missing = copy.deepcopy(spec)
    missing["repository_bindings"].pop()
    with pytest.raises(ValueError, match="inventory differs"):
        verify_repository_bindings(missing, tmp_path)
    (tmp_path / spec["repository_bindings"][0]["path"]).write_text("changed")
    with pytest.raises(ValueError, match="digest mismatch"):
        verify_repository_bindings(spec, tmp_path)


def test_selection_is_verified_but_not_an_owner(tmp_path: Path) -> None:
    """Exact execution selection is checked independently from plan identity."""
    spec = request(tmp_path)
    (tmp_path / "selection.json").write_text("changed")
    with pytest.raises(ValueError, match="selection.json"):
        verify_repository_bindings(spec, tmp_path)
    spec["repository_bindings"].append(spec["selection_freeze"])
    with pytest.raises(ValidationError, match="mutable selection"):
        ReleaseSpec.model_validate(spec)


def test_unknown_fields_coercion_and_resource_expansion_fail(tmp_path: Path) -> None:
    """Neither ignored extra fields nor larger runtime limits are accepted."""
    spec = request(tmp_path)
    for key, value in (
        ("extra_control", False),
        ("authorization", {"execution": "yes"}),
        ("limits", {"max_seconds": 1801}),
    ):
        changed = copy.deepcopy(spec)
        changed[key] = value
        with pytest.raises(ValidationError):
            ReleaseSpec.model_validate(changed)


@pytest.mark.parametrize("runtime", ["python", "pydantic", "jsonschema", "rfc8785", "psutil"])
def test_runtime_drift_changes_identity_and_blocks_loading(tmp_path: Path, runtime: str) -> None:
    """Unchanged code cannot reuse a plan under a different interpreter or dependency."""
    spec = request(tmp_path)
    original = plan_identity(spec)
    spec["runtime_versions"][runtime] = "0.0-frozen-other-version"
    assert plan_identity(spec) != original
    path = tmp_path / "request.json"
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match=f"runtime versions differ: {runtime}"):
        load_release_spec(path, tmp_path)


@pytest.mark.parametrize("change", ["missing", "unknown", "empty", "number"])
def test_runtime_inventory_is_complete_and_strict(tmp_path: Path, change: str) -> None:
    """The version contract permits exactly the five output-affecting runtime owners."""
    spec = request(tmp_path)
    if change == "missing":
        del spec["runtime_versions"]["python"]
    elif change == "unknown":
        spec["runtime_versions"]["unreviewed_dependency"] = "1"
    elif change == "empty":
        spec["runtime_versions"]["python"] = ""
    else:
        spec["runtime_versions"]["python"] = 3
    with pytest.raises(ValidationError):
        ReleaseSpec.model_validate(spec)
