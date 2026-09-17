"""Separate review-bound finalization and explicit acceptance of a 05G working layer."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from er_commons.artifact_io import canonical_json_sha256, json_bytes, publish_bytes_no_clobber
from er_commons.response_inventory.reference_replay_storage import (
    publish_checkpoint,
    read_checkpoint,
)
from er_commons.response_inventory.reference_replay_workflow import (
    ReplayRun,
    _bindings,
    _existing_stage,
    _load_inputs,
    validate_replay,
)


def _review_record(path: Path) -> tuple[dict[str, Any], str]:
    """Read only a bounded JSON review record; a filename alone proves nothing."""
    if path.suffix != ".json" or path.stat().st_size > 1_048_576:
        raise ValueError("05G review must be a compact JSON record")
    raw = path.read_bytes()
    record = json.loads(raw)
    if not isinstance(record, dict):
        raise ValueError("05G review must be an object")
    return record, hashlib.sha256(raw).hexdigest()


def _selected_checks(run: ReplayRun, dependencies: list[dict[str, Any]]) -> tuple[Path, Path]:
    """Require exact selected candidate and comparison checkpoints, never a latest directory."""
    candidate = _existing_stage(run, "candidate", _bindings(run, "candidate", dependencies))
    comparison = _existing_stage(run, "comparison", _bindings(run, "comparison", dependencies))
    if candidate is None or comparison is None:
        raise ValueError("05G finalization requires candidate and comparison completion")
    return candidate, comparison


def _review_closure(
    run: ReplayRun,
    candidate: dict[str, Any],
    comparison: dict[str, Any],
    review: dict[str, Any],
    quality: dict[str, Any],
    changed: set[str],
) -> None:
    """Require review of exact changed rows and a passed independent code-quality gate."""
    expected = {
        "candidate_id": run.candidate_id,
        "run_spec_sha256": run.digest,
        "candidate_checkpoint_id": candidate["checkpoint_id"],
        "comparison_checkpoint_id": comparison["checkpoint_id"],
    }
    for document in (review, quality):
        if any(document.get(key) != value for key, value in expected.items()):
            raise ValueError("05G review binding mismatch")
        if document.get("material_findings") != [] or not document.get("reviewer"):
            raise ValueError("05G review has open material findings or missing reviewer")
    if quality.get("status") != "passed" or review.get("decision") != "approved":
        raise ValueError("05G review is incomplete or conflicting")
    ids = review.get("reviewed_mention_ids", [])
    if len(ids) != len(set(ids)) or set(ids) != changed:
        raise ValueError("05G changed-mention review population does not close")
    if review.get("limitations_acknowledged") is not True:
        raise ValueError("05G sampled/F1/figure limitations were not acknowledged")


def _execution_receipt(run: ReplayRun) -> dict[str, Any]:
    """Verify terminal supervision against its immutable prelaunch request and limits."""
    from er_commons.response_inventory.reference_replay_spec import (
        ReferenceReplaySpec,
        replay_identity,
    )

    root = run.root.parent / "05g_execution_attempts" / run.digest / f"attempt-{run.attempt:03d}"
    receipt, _ = _review_record(root / "execution.json")
    packet_path = run.root / "plans" / run.digest / f"launch-attempt-{run.attempt:03d}.json"
    packet, _ = _review_record(packet_path)
    request = packet["request_text"].encode()
    if hashlib.sha256(request).hexdigest() != packet["request_sha256"]:
        raise ValueError("05G original launch request digest mismatch")
    original = ReferenceReplaySpec.model_validate_json(request).model_dump(
        mode="json", exclude_none=True
    )
    if (
        replay_identity(original) != run.digest
        or packet["spec_sha256"] != run.digest
        or original["authorization"]["replay"] is not True
    ):
        raise ValueError("05G original launch request identity/authorization mismatch")
    if (
        receipt.get("status") != "succeeded"
        or receipt.get("returncode") != 0
        or receipt.get("surviving_pids", []) != []
    ):
        raise ValueError("05G supervisor did not succeed terminally")
    for field, expected in (
        ("command", packet["command"]),
        ("limits", packet["supervisor_limits"]),
        ("output_root", str(run.root)),
        ("attempt_root", str(root)),
    ):
        if receipt.get(field) != expected:
            raise ValueError(f"05G supervisor {field} mismatch")
    reviewed_limits = run.spec["limits"]
    limits = packet["supervisor_limits"]
    expected_limits = {
        key: value
        for key, value in reviewed_limits.items()
        if key not in {"workers", "cpu_threads"}
    }
    expected_limits["max_output_bytes"] -= packet["prior_supervisor_bytes"]
    if limits != expected_limits or packet["prior_supervisor_bytes"] < 0:
        raise ValueError("05G launch used limits different from reviewed policy")
    for observed, limit in (
        ("elapsed_seconds", "max_seconds"),
        ("peak_rss_bytes", "max_rss_bytes"),
        ("peak_swap_growth_bytes", "max_swap_growth_bytes"),
        ("peak_output_bytes", "max_output_bytes"),
    ):
        value = receipt.get(observed)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0 <= value <= limits[limit]
        ):
            raise ValueError(f"05G invalid supervisor resource result: {observed}")
    return {"supervisor": receipt, "launch_packet": packet}


def finalize_replay(run: ReplayRun, quality_path: Path, review_path: Path) -> dict[str, Any]:
    """Wrap one validated working candidate only after a separate finalization approval."""
    if run.spec["authorization"]["finalization"] is not True:
        raise ValueError("Task 05G finalization is not authorized")
    validation = validate_replay(run)
    inputs = _load_inputs(run)
    candidate_root, comparison_root = _selected_checks(run, inputs.dependencies)
    candidate = read_checkpoint(candidate_root, _bindings(run, "candidate", inputs.dependencies))
    comparison = read_checkpoint(comparison_root, _bindings(run, "comparison", inputs.dependencies))
    report = json.loads((comparison_root / "comparison.json").read_text())
    changed = {row["mention_id"] for row in report["rows"] if row.get("changed")}
    quality, quality_digest = _review_record(quality_path)
    review, review_digest = _review_record(review_path)
    _review_closure(run, candidate, comparison, review, quality, changed)
    execution = _execution_receipt(run)
    handoff = {
        "schema_version": "er_commons.task05g.task05h_handoff.v1",
        "candidate_id": run.candidate_id,
        "candidate_root": str(candidate_root.relative_to(run.artifact_root)),
        "candidate_checkpoint_id": candidate["checkpoint_id"],
        "comparison_root": str(comparison_root.relative_to(run.artifact_root)),
        "comparison_checkpoint_id": comparison["checkpoint_id"],
        "dependencies": inputs.dependencies,
        "accepted_task06h_handoff": inputs.handoff,
        "semantic_digest": validation["semantic_digest"],
        "quality_sha256": quality_digest,
        "review_sha256": review_digest,
        "execution_sha256": canonical_json_sha256(execution),
        "status": "complete_with_limitations",
        "task05h_execution_authorized": False,
    }
    root = run.root / "finalizations" / run.candidate_id / f"attempt-{run.attempt:03d}"
    completion = publish_checkpoint(
        root,
        {
            "task05h_handoff.json": json_bytes(handoff),
            "quality.json": json_bytes(quality),
            "review.json": json_bytes(review),
            "execution.json": json_bytes(execution),
        },
        _bindings(run, "finalized", inputs.dependencies),
    )
    return {"finalization_root": str(root), "completion": completion}


def accept_replay(
    run: ReplayRun,
    candidate_root: Path,
    review_path: Path,
    *,
    accepted_by: str,
    accepted_at: str,
) -> dict[str, Any]:
    """Write an adjacent explicit acceptance without modifying any managed candidate file."""
    if run.spec["authorization"]["acceptance"] is not True:
        raise ValueError("Task 05G acceptance is not authorized")
    if not accepted_by.strip() or datetime.fromisoformat(accepted_at).tzinfo is None:
        raise ValueError("05G acceptance requires an actor and timezone-aware timestamp")
    inputs = _load_inputs(run)
    selected, _ = _selected_checks(run, inputs.dependencies)
    if candidate_root.resolve() != selected.resolve():
        raise ValueError("05G acceptance candidate differs from selected request")
    final_root = run.root / "finalizations" / run.candidate_id / f"attempt-{run.attempt:03d}"
    completion = read_checkpoint(final_root, _bindings(run, "finalized", inputs.dependencies))
    review, digest = _review_record(review_path)
    sealed_review = json.loads((final_root / "review.json").read_text())
    handoff = json.loads((final_root / "task05h_handoff.json").read_text())
    if review != sealed_review or digest != handoff["review_sha256"]:
        raise ValueError("05G acceptance review differs from finalized decision")
    validate_replay(run)
    record = {
        "schema_version": "er_commons.task05g.acceptance.v1",
        "candidate_id": run.candidate_id,
        "finalization_checkpoint_id": completion["checkpoint_id"],
        "finalization_root": str(final_root.relative_to(run.artifact_root)),
        "accepted_by": accepted_by,
        "accepted_at": accepted_at,
        "status": "accepted_with_limitations",
        "task05h_execution_authorized": False,
    }
    record["acceptance_id"] = "acceptance05gv1-" + canonical_json_sha256(record)
    pointer = run.root / "accepted.json"
    if pointer.exists() and pointer.read_bytes() != json_bytes(record):
        raise ValueError("conflicting Task 05G acceptance pointer; preserve both decisions")
    root = run.root / "acceptances" / record["acceptance_id"]
    publish_checkpoint(
        root,
        {"acceptance.json": json_bytes(record)},
        _bindings(run, "accepted", inputs.dependencies),
    )
    publish_bytes_no_clobber(run.root / "accepted.json", json_bytes(record))
    return record
