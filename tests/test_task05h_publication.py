"""Synthetic immutable-release tests, with no production source or artifact access."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.response_inventory.release_publication import (
    accept_inventory,
    publish_inventory,
    require_authorization,
    validate_quality,
)
from er_commons.response_inventory.release_storage import (
    COMPLETION,
    MANIFEST,
    encode,
    inventory_identity,
    publish_container,
    read_container,
)


def spec(**gates: bool) -> dict[str, Any]:
    """Make all gates explicit and disabled unless a synthetic test opts in."""
    authorization = dict.fromkeys(("execution", "finalization", "publication", "acceptance"), False)
    authorization.update(gates)
    return {"authorization": authorization}


def payloads() -> dict[str, bytes]:
    """Only tiny owned references belong in the synthetic final release."""
    return {
        "inventory/components.json": encode([]),
        "records/task07_task08_handoff.json": encode({"curator_only": True}),
    }


def candidate(root: Path) -> dict[str, Any]:
    """Seal a fixture finalization independently of source or reviewer evidence."""
    return publish_container(
        root,
        payloads(),
        plan_id="plan05hv1-" + "a" * 64,
        semantic_digest="b" * 64,
        status="complete_with_limitations",
    )


def test_completion_last_and_repeat_preserves_bytes_and_mtimes(tmp_path: Path) -> None:
    root = tmp_path / "candidate"
    first = candidate(root)
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()}
    assert candidate(root) == first
    assert before == {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before}
    assert inventory_identity(first).startswith("inventoryv1-")
    assert (
        json.loads((root / COMPLETION).read_bytes())["inventory_id"]
        == json.loads((root / MANIFEST).read_bytes())["inventory_id"]
    )


def test_interruption_retains_incomplete_evidence(tmp_path: Path) -> None:
    calls = 0

    def stop() -> None:
        """Interrupt after a write, before any completion can appear."""
        nonlocal calls
        calls += 1
        if calls == 3:
            raise KeyboardInterrupt

    root = tmp_path / "candidate"
    with pytest.raises(KeyboardInterrupt):
        publish_container(
            root,
            payloads(),
            plan_id="plan05hv1-" + "a" * 64,
            semantic_digest="b" * 64,
            status="complete_with_limitations",
            guard=stop,
        )
    assert root.exists() and not (root / COMPLETION).exists()
    with pytest.raises(ValueError, match="incomplete"):
        candidate(root)


@pytest.mark.parametrize(
    "mutation", ["payload", "extra", "empty_directory", "symlink", "completion"]
)
def test_owned_closure_rejects_corruption(tmp_path: Path, mutation: str) -> None:
    root = tmp_path / "candidate"
    candidate(root)
    if mutation == "payload":
        (root / "inventory/components.json").write_bytes(b"{}\n")
    elif mutation == "extra":
        (root / "unexpected.json").write_bytes(b"{}")
    elif mutation == "empty_directory":
        (root / "unowned").mkdir()
    elif mutation == "symlink":
        (root / "shortcut").symlink_to(root / "inventory")
    else:
        row = json.loads((root / COMPLETION).read_bytes())
        row["status"] = "prepared"
        (root / COMPLETION).write_bytes(encode(row))
    with pytest.raises(ValueError):
        read_container(root)


def test_prepared_cannot_be_inventory(tmp_path: Path) -> None:
    row = publish_container(
        tmp_path / "p",
        payloads(),
        plan_id="plan05hv1-" + "a" * 64,
        semantic_digest="b" * 64,
        status="prepared",
    )
    with pytest.raises(ValueError, match="finalized"):
        inventory_identity(row)


@pytest.mark.parametrize("operation", ["prepare", "review", "finalize", "publish", "accept"])
def test_each_gate_requires_its_own_authorization(operation: str) -> None:
    with pytest.raises(ValueError, match="authorization"):
        require_authorization(spec(), operation)
    if operation != "prepare" and operation != "review":
        with pytest.raises(ValueError):
            require_authorization(spec(execution=True), operation)


def test_publish_and_accept_are_separate_and_conflicts_fail(tmp_path: Path) -> None:
    parent = tmp_path / "task05"
    working = parent / "working/05h"
    source = working / "p/attempt-001/finalized"
    completion = candidate(source)
    plan = completion["plan_id"]
    with pytest.raises(ValueError):
        publish_inventory(source, parent, spec(), plan_id=plan)
    result = publish_inventory(source, parent, spec(publication=True), plan_id=plan)
    destination = Path(result["inventory_root"])
    assert destination.name == inventory_identity(completion)
    assert not (working / "accepted.json").exists()
    assert read_container(source) == read_container(destination)
    args = dict(plan_id=plan, accepted_by="Fixture curator", accepted_at="2026-09-17T20:00:00Z")
    with pytest.raises(ValueError):
        accept_inventory(destination, working, spec(), **args)
    accepted = accept_inventory(destination, working, spec(acceptance=True), **args)
    assert accept_inventory(destination, working, spec(acceptance=True), **args) == accepted
    assert not (working / "accepted.json").exists()


def test_quality_binds_real_code_and_input_semantics() -> None:
    bindings = [{"path": "owner.py", "sha256": "f" * 64}]
    quality = {
        "plan_id": "plan",
        "input_semantic_digest": "input",
        "repository_bindings": bindings,
        "status": "passed",
        "material_findings": [],
        "reviewer": "Independent reviewer",
        "independent_review": True,
        "dimensions": dict.fromkeys(
            ("readability", "editability", "debuggability", "operations", "testing"), "passed"
        ),
    }
    validate_quality(quality, plan_id="plan", semantic_digest="input", repository_bindings=bindings)
    with pytest.raises(ValueError):
        validate_quality(
            quality, plan_id="plan", semantic_digest="changed", repository_bindings=bindings
        )


@pytest.mark.parametrize(
    "reviewer, independent", [(True, True), (" ", True), ("reviewer", "false"), ("reviewer", 1)]
)
def test_quality_requires_typed_independent_attestation(
    reviewer: object, independent: object
) -> None:
    """Truthy JSON values must not impersonate explicit independent reviewer attestation."""
    quality = {
        "plan_id": "plan",
        "input_semantic_digest": "input",
        "repository_bindings": [],
        "status": "passed",
        "material_findings": [],
        "reviewer": reviewer,
        "independent_review": independent,
        "dimensions": dict.fromkeys(
            ["readability", "editability", "debuggability", "operations", "testing"], "passed"
        ),
    }
    with pytest.raises(ValueError, match="identified independent reviewer"):
        validate_quality(quality, plan_id="plan", semantic_digest="input", repository_bindings=[])


def test_explicit_supersession_preserves_prior_acceptance(tmp_path: Path) -> None:
    """Change only the designation after verifying preserved exact prior bytes."""
    from er_commons.response_inventory.release_publication import designate_acceptance
    from er_commons.response_inventory.release_storage import digest, encode

    parent = tmp_path / "task05"
    working = parent / "working/05h"
    completion = candidate(working / "p/attempt-001/finalized")
    plan = completion["plan_id"]
    published = publish_inventory(
        working / "p/attempt-001/finalized", parent, spec(publication=True), plan_id=plan
    )
    destination = Path(published["inventory_root"])
    args = dict(plan_id=plan, accepted_by="Fixture curator", accepted_at="2026-09-17T20:00:00Z")
    old = designate_acceptance(
        destination, working, spec(acceptance=True), execution_evidence={}, **args
    )
    old_bytes = (working / "accepted.json").read_bytes()
    replacement = spec(acceptance=True)
    replacement["supersedes_acceptance"] = {
        "path": f"acceptances/{old['acceptance_id']}/acceptance.json",
        "sha256": digest(old_bytes),
    }
    args["accepted_at"] = "2026-09-24T20:00:00Z"
    new = designate_acceptance(destination, working, replacement, execution_evidence={}, **args)
    assert new != old
    assert (working / "accepted.json").read_bytes() == encode(new)
    assert (working / replacement["supersedes_acceptance"]["path"]).read_bytes() == old_bytes
    assert (
        designate_acceptance(destination, working, replacement, execution_evidence={}, **args)
        == new
    )
    with pytest.raises(ValueError, match="preserved prior pointer"):
        args["accepted_at"] = "2026-09-25T20:00:00Z"
        designate_acceptance(destination, working, replacement, execution_evidence={}, **args)
