"""Verify reviewed launch packets and terminal execution evidence at later gates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from er_commons.response_inventory.release_publication import require_authorization
from er_commons.response_inventory.release_storage import (
    digest,
    inventory_identity,
    no_symlinks,
    read_container,
)

if TYPE_CHECKING:
    from er_commons.response_inventory.release_workflow import ReleaseRun


def _packet(run: ReleaseRun, operation: str, attempt: int) -> dict[str, Any]:
    """Read the exact named packet, never a most-recent launch directory."""
    path = (
        run.root.parent
        / "05h_execution_attempts"
        / run.plan_id
        / f"launch-{attempt:03d}-{operation}.json"
    )
    no_symlinks(path)
    packet: dict[str, Any] = json.loads(path.read_bytes())
    expected = {
        "launch_packet_path": str(path),
        "plan_id": run.plan_id,
        "operation": operation,
        "attempt": attempt,
        "repository_bindings": run.spec["repository_bindings"],
        "selection_freeze": run.spec["selection_freeze"],
        "binding_freeze": run.spec["binding_freeze"],
        "repository_root": str(run.repository_root.resolve()),
        "data_root": str(run.artifact_root.resolve()),
    }
    if any(packet.get(k) != v for k, v in expected.items()):
        raise ValueError(f"05H launch evidence binding mismatch: {path}")
    require_authorization({"authorization": packet["authorization"]}, operation)
    return packet


def verify_worker_launch(
    run: ReleaseRun,
    request: Path,
    operation: str,
    candidate: Path | None,
    accepted_by: str,
    accepted_at: str,
) -> None:
    """Prevent the production worker from bypassing its exact supervised launch packet."""
    packet = _packet(run, operation, run.attempt)
    if packet["request_sha256"] != digest(request.read_bytes()):
        raise ValueError("05H request changed after the reviewed launch")
    expected_candidate = str(candidate.resolve()) if candidate is not None else None
    if (
        packet.get("candidate_root") != expected_candidate
        or packet.get("resume_from") != run.resume_from
    ):
        raise ValueError("05H worker differs from selected candidate/resume launch")
    command = packet["command"]
    for flag, value in (("--accepted-by", accepted_by), ("--accepted-at", accepted_at)):
        actual = command[command.index(flag) + 1] if flag in command else ""
        if actual != value:
            raise ValueError("05H acceptance attribution changed after launch")


def verify_terminal_execution(run: ReleaseRun, operation: str, attempt: int) -> dict[str, Any]:
    """Require successful supervision and reviewed limits, not only a stage completion."""
    packet = _packet(run, operation, attempt)
    expected_root = (
        run.root.parent
        / "05h_execution_attempts"
        / run.plan_id
        / f"attempt-{attempt:03d}-{operation}"
    )
    if packet["attempt_root"] != str(expected_root):
        raise ValueError("05H supervisor attempt path mismatch")
    receipt_path = expected_root / "execution.json"
    no_symlinks(receipt_path)
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes)
    expected = {
        "status": "succeeded",
        "returncode": 0,
        "command": packet["command"],
        "limits": packet["supervisor_limits"],
        "attempt_root": str(expected_root),
        "output_root": packet["output_root"],
    }
    if (
        any(receipt.get(k) != v for k, v in expected.items())
        or receipt.get("surviving_pids", []) != []
    ):
        raise ValueError(f"05H {operation} did not complete under the reviewed supervisor")
    _verify_resource_evidence(run, packet, receipt)
    return {
        "path": str(receipt_path.relative_to(run.artifact_root)),
        "sha256": digest(receipt_bytes),
        "launch_packet_sha256": digest(Path(packet["launch_packet_path"]).read_bytes()),
        "operation": operation,
        "attempt": attempt,
    }


def _verify_resource_evidence(
    run: ReleaseRun, packet: dict[str, Any], receipt: dict[str, Any]
) -> None:
    """Check measured resources and reconstruct the cumulative budget from prior output."""
    limits = packet["supervisor_limits"]
    for key, value in run.spec["limits"].items():
        if key not in {"workers", "cpu_threads", "max_output_bytes"} and limits.get(key) != value:
            raise ValueError(f"05H execution limit changed: {key}")
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
            raise ValueError(f"05H execution resource evidence invalid: {observed}")
    counts = packet["prior_bytes"]
    current = counts["cache" if packet["operation"] == "review" else "working"]
    expected_max = (
        run.spec["limits"]["max_output_bytes"]
        - (sum(counts.values()) - current)
        - packet["publication_reserve_bytes"]
        - packet["metadata_reserve_bytes"]
    )
    if limits["max_output_bytes"] != expected_max or any(v < 0 for v in counts.values()):
        raise ValueError("05H cumulative output accounting changed")


def verify_finalized_result(run: ReleaseRun, completion: dict[str, Any]) -> None:
    """Bind first publication seals to the completed worker's retained JSON result."""
    verify_terminal_execution(run, "finalize", run.attempt)
    log = (
        run.root.parent
        / "05h_execution_attempts"
        / run.plan_id
        / f"attempt-{run.attempt:03d}-finalize"
        / "command.log"
    )
    no_symlinks(log)
    lines = log.read_text().splitlines()
    if not lines:
        raise ValueError("05H finalized worker result is missing")
    result = json.loads(lines[-1])
    if result.get("completion") != completion:
        raise ValueError("05H finalized completion differs from supervised worker result")


def verify_published_candidate(run: ReleaseRun, inventory_root: Path) -> dict[str, Any]:
    """Associate the exact published inventory with its successful publication source."""
    packet = _packet(run, "publish", run.attempt)
    evidence = verify_terminal_execution(run, "publish", run.attempt)
    source = run.attempt_root / "finalized"
    if packet.get("candidate_root") != str(source.resolve()):
        raise ValueError("publication receipt names a different finalized candidate")
    completion, _ = read_container(source, plan_id=run.plan_id)
    verify_finalized_result(run, completion)
    expected = run.root.parent.parent / inventory_identity(completion)
    if inventory_root.resolve() != expected.resolve():
        raise ValueError("acceptance candidate differs from supervised publication")
    published, _ = read_container(inventory_root, plan_id=run.plan_id)
    if completion != published:
        raise ValueError("published completion differs from supervised finalization")
    return evidence
