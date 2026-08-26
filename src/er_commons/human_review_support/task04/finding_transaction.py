"""Recoverable staged publication for Task 04 finding-derived records."""

from __future__ import annotations

import os
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.human_review_support.task04.json_io import (
    read_json_object,
    require_mapping,
    require_string,
)
from er_commons.human_review_support.task04.models import JsonValue
from er_commons.human_review_support.task04.records import RecordValidator


@dataclass(frozen=True)
class FindingFiles:
    """Authoritative Task 04 records involved in one finding update."""

    selection: Path
    inventory: Path
    register: Path
    handoff: Path
    manifest: Path


def finding_files(review_root: Path) -> FindingFiles:
    """Resolve the fixed record paths for one immutable review-run directory."""
    records = review_root / "records"
    return FindingFiles(
        records / "selection_manifest.json",
        records / "input_inventory.json",
        records / "finding_register.json",
        records / "task03i_handoff.json",
        records / "review_bundle_manifest.json",
    )


def publish_finding_update(
    files: FindingFiles,
    register: dict[str, JsonValue],
    handoff: dict[str, JsonValue],
    validator: RecordValidator,
) -> None:
    """Stage, seal, and replace finding-derived records with crash recovery evidence."""
    staging = files.register.parent / f".finding-update-{uuid.uuid4().hex}"
    new_root = staging / "new"
    backup_root = staging / "backup"
    new_root.mkdir(parents=True)
    backup_root.mkdir()
    targets = (files.register, files.handoff)
    try:
        _prepare_update(staging, files, targets, register, handoff, validator)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    try:
        for target in targets:
            _replace_authoritative(new_root / target.name, target)
    except Exception:
        raise RuntimeError(
            f"Task 04 finding publication was interrupted; rerun to recover {staging}"
        ) from None
    shutil.rmtree(staging)


def _prepare_update(
    staging: Path,
    files: FindingFiles,
    targets: tuple[Path, ...],
    register: dict[str, JsonValue],
    handoff: dict[str, JsonValue],
    validator: RecordValidator,
) -> None:
    """Write and validate complete old/new evidence before authoritative changes."""
    for target in targets:
        shutil.copy2(target, staging / "backup" / target.name)
    staged_register = staging / "new" / files.register.name
    write_json_atomic(staged_register, register)
    handoff["finding_register_sha256"] = sha256_file(staged_register)
    handoff["input_inventory_sha256"] = sha256_file(files.inventory)
    handoff["selection_manifest_sha256"] = sha256_file(files.selection)
    handoff["review_bundle_manifest_sha256"] = sha256_file(files.manifest)
    staged_handoff = staging / "new" / files.handoff.name
    write_json_atomic(staged_handoff, handoff)
    validator.validate("task03i_handoff", handoff)
    _write_transaction_journal(staging, targets)


def _write_transaction_journal(staging: Path, targets: tuple[Path, ...]) -> None:
    """Seal old and new bytes before any authoritative replacement begins."""
    records: dict[str, JsonValue] = {}
    for target in targets:
        records[target.name] = {
            "old_sha256": sha256_file(staging / "backup" / target.name),
            "new_sha256": sha256_file(staging / "new" / target.name),
        }
    write_json_atomic(staging / "transaction.json", {"version": 1, "files": records})


def recover_finding_update(review_root: Path) -> None:
    """Finish one retained staged update or diagnose unsafe recovery state."""
    files = finding_files(review_root)
    journals = sorted(files.register.parent.glob(".finding-update-*"))
    if not journals:
        return
    if len(journals) != 1:
        names = ", ".join(path.name for path in journals)
        raise ValueError(f"ambiguous Task 04 finding recovery: multiple journals: {names}")
    staging = journals[0]
    entries = _read_journal(staging)
    targets = (files.register, files.handoff)
    expected_names = {target.name for target in targets}
    if set(entries) != expected_names:
        raise ValueError(
            f"corrupt finding journal file set at {staging}: "
            f"expected={sorted(expected_names)}, found={sorted(entries)}"
        )
    states = [_recovery_state(staging, target, entries[target.name]) for target in targets]
    if not all(state == "new" for state in states):
        for target, state in zip(targets, states, strict=True):
            if state == "old":
                _replace_authoritative(staging / "new" / target.name, target)
    shutil.rmtree(staging)


def _read_journal(staging: Path) -> dict[str, JsonValue]:
    """Read one transaction journal with explicit corruption context."""
    try:
        journal = read_json_object(staging / "transaction.json")
    except ValueError as error:
        raise ValueError(f"corrupt finding recovery journal at {staging}: {error}") from error
    if journal.get("version") != 1:
        raise ValueError(f"unsupported or corrupt finding journal version: {staging}")
    return require_mapping(journal.get("files"), path=f"{staging}.files")


def _recovery_state(staging: Path, target: Path, value: JsonValue) -> str:
    """Classify one transaction target and verify retained recovery evidence."""
    entry = require_mapping(value, path=f"{staging}.files.{target.name}")
    old_sha = require_string(entry.get("old_sha256"), path=f"{target.name}.old_sha256")
    new_sha = require_string(entry.get("new_sha256"), path=f"{target.name}.new_sha256")
    backup = staging / "backup" / target.name
    if not backup.is_file() or sha256_file(backup) != old_sha:
        raise ValueError(f"corrupt finding recovery backup: {backup}")
    actual = sha256_file(target)
    if actual == new_sha:
        return "new"
    if actual != old_sha:
        raise ValueError(
            f"finding recovery target has unrecognized bytes: {target}; "
            f"expected old={old_sha} or new={new_sha}, found={actual}"
        )
    staged = staging / "new" / target.name
    if not staged.is_file() or sha256_file(staged) != new_sha:
        raise ValueError(f"corrupt finding recovery payload: {staged}")
    return "old"


def _replace_authoritative(staged: Path, target: Path) -> None:
    """Single fault-injection seam for authoritative transaction replacements."""
    os.replace(staged, target)


__all__ = [
    "FindingFiles",
    "finding_files",
    "publish_finding_update",
    "recover_finding_update",
]
