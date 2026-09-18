"""Read-only 05H launch previews and one explicitly authorized supervised worker."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shlex
from pathlib import Path
from typing import Any

from er_commons.document_publication.background_execution import ExecutionLimits, supervise
from er_commons.response_inventory.release_publication import require_authorization
from er_commons.response_inventory.release_storage import (
    COMPLETION,
    VERSION,
    encode,
    inventory_identity,
    no_symlinks,
    read_container,
    write_file,
)
from er_commons.response_inventory.release_workflow import open_run

OPERATIONS = ("prepare", "review", "finalize", "publish", "accept")
RESERVE_BYTES = 65536
THREAD_ENVIRONMENT = dict.fromkeys(
    (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ),
    "2",
)


def owned_bytes(root: Path) -> int:
    """Count only a declared 05H output tree, refusing symlinks instead of following them."""
    no_symlinks(root)
    total = 0
    if root.exists():
        for path in root.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"05H accounting tree contains a symlink: {path}")
            if path.is_file():
                total += path.stat().st_size
    return total


def _release_bytes(parent: Path) -> int:
    """Account published and interrupted new releases without traversing upstream trees."""
    no_symlinks(parent)
    total = 0
    for root in parent.glob("inventoryv1-*"):
        no_symlinks(root)
        completion = root / COMPLETION
        no_symlinks(completion)
        if completion.exists():
            payload = json.loads(completion.read_bytes())
            if payload.get("schema_version") != VERSION or payload.get("stage") != "05h":
                continue
        # Interrupted publication has no completion yet and must remain charged.
        total += owned_bytes(root)
    return total


def _operation_arguments(
    run_spec: Path,
    attempt: int,
    operation: str,
    resume_from: int | None,
    candidate: Path | None,
    accepted_by: str,
    accepted_at: str,
) -> list[str]:
    """Give the launcher and supervised worker exactly the same operation arguments."""
    arguments = [
        "--run-spec",
        str(run_spec.resolve()),
        "--attempt",
        str(attempt),
        "--operation",
        operation,
    ]
    if resume_from is not None:
        arguments += ["--resume-from", str(resume_from)]
    if candidate is not None:
        arguments += ["--candidate-root", str(candidate.resolve())]
    if accepted_by:
        arguments += ["--accepted-by", accepted_by]
    if accepted_at:
        arguments += ["--accepted-at", accepted_at]
    return arguments


def _publication_reserve(
    operation: str, candidate: Path | None, release_parent: Path, plan_id: str
) -> int:
    """Reserve the prospective copy and require acceptance to name its published root."""
    if operation not in {"publish", "accept"}:
        return 0
    if candidate is None:
        raise ValueError("publication/acceptance requires an exact candidate root")
    no_symlinks(candidate)
    completion, _ = read_container(candidate, plan_id=plan_id)
    final_root = release_parent / inventory_identity(completion)
    if operation == "accept" and candidate.resolve() != final_root.resolve():
        raise ValueError("acceptance requires the exact published inventory root")
    if operation == "publish" and not final_root.exists():
        return owned_bytes(candidate)
    return 0


def build_launch_packet(
    run_spec: Path,
    repository_root: Path,
    data_root: Path,
    *,
    attempt: int = 1,
    operation: str = "prepare",
    resume_from: int | None = None,
    candidate: Path | None = None,
    accepted_by: str = "",
    accepted_at: str = "",
) -> dict[str, Any]:
    """Bind exact controls and cumulative budget without writing or reading source payloads."""
    if operation not in OPERATIONS:
        raise ValueError("unknown supervised Task 05H operation")
    if type(attempt) is not int or attempt < 1:
        raise ValueError("attempt must be a positive integer")
    if resume_from is not None and (type(resume_from) is not int or not 0 < resume_from < attempt):
        raise ValueError("resume-from must name an earlier positive attempt")
    run = open_run(run_spec, repository_root, data_root, attempt)
    cache = run.root.parent / "cache" / "05h"
    logs = run.root.parent / "05h_execution_attempts"
    monitored = cache if operation == "review" else run.root
    counts = {
        "working": owned_bytes(run.root),
        "cache": owned_bytes(cache),
        "supervisor": owned_bytes(logs),
        "published": _release_bytes(run.root.parent.parent),
    }
    publication_reserve = _publication_reserve(
        operation, candidate, run.root.parent.parent, run.plan_id
    )
    current = counts["cache" if operation == "review" else "working"]
    other = sum(counts.values()) - current
    maximum = run.spec["limits"]["max_output_bytes"]
    limits = {k: v for k, v in run.spec["limits"].items() if k not in {"workers", "cpu_threads"}}
    limits["max_output_bytes"] = maximum - other - publication_reserve - RESERVE_BYTES
    operation_arguments = _operation_arguments(
        run_spec, attempt, operation, resume_from, candidate, accepted_by, accepted_at
    )
    command = [
        "/usr/bin/env",
        *(f"{key}={value}" for key, value in THREAD_ENVIRONMENT.items()),
        f"ER_COMMONS_DATA_ROOT={data_root.resolve()}",
        "uv",
        "run",
        "python",
        "-m",
        "er_commons.response_inventory.release_workflow",
        *operation_arguments,
    ]
    attempt_root = logs / run.plan_id / f"attempt-{attempt:03d}-{operation}"
    packet_path = logs / run.plan_id / f"launch-{attempt:03d}-{operation}.json"
    launch_command = [
        "uv",
        "run",
        "python",
        "-m",
        "er_commons.response_inventory.release_launch",
        *operation_arguments,
    ]
    packet = {
        "schema_version": "er_commons.task05h.launch_packet.v1",
        "plan_id": run.plan_id,
        "request_sha256": hashlib.sha256(run_spec.read_bytes()).hexdigest(),
        "run_spec": str(run_spec.resolve()),
        "repository_root": str(repository_root.resolve()),
        "data_root": str(data_root.resolve()),
        "binding_freeze": run.spec["binding_freeze"],
        "selection_freeze": run.spec["selection_freeze"],
        "repository_bindings": run.spec["repository_bindings"],
        "authorization": run.spec["authorization"],
        "attempt": attempt,
        "resume_from": resume_from,
        "operation": operation,
        "candidate_root": str(candidate.resolve()) if candidate is not None else None,
        "output_root": str(monitored),
        "working_root": str(run.root),
        "cache_root": str(cache),
        "attempt_root": str(attempt_root),
        "supervisor_attempts_root": str(logs),
        "launch_packet_path": str(packet_path),
        "prior_bytes": counts,
        "prior_output_bytes": current,
        "publication_reserve_bytes": publication_reserve,
        "metadata_reserve_bytes": RESERVE_BYTES,
        "cumulative_max_bytes": maximum,
        "supervisor_limits": limits,
        "command": command,
        "effective_worker_thread_environment": THREAD_ENVIRONMENT,
        "launch_command": [
            "tmux",
            "new-session",
            "-d",
            "-s",
            f"er-commons-05h-{run.plan_id[-12:]}-{attempt:03d}-{operation}",
            "-c",
            str(repository_root.resolve()),
            shlex.join(launch_command),
        ],
    }
    if len(encode(packet)) > RESERVE_BYTES:
        raise ValueError("05H launch packet exceeds 64 KiB metadata reserve")
    return packet


def _check_launch(packet: dict[str, Any]) -> None:
    """Fail all admission checks before creating launch artifacts."""
    require_authorization({"authorization": packet["authorization"]}, packet["operation"])
    if (
        packet["supervisor_limits"]["max_output_bytes"]
        <= packet["prior_output_bytes"] + RESERVE_BYTES
    ):
        raise ValueError("cumulative 05H output budget exhausted; preserve prior evidence")
    for key in ("attempt_root", "launch_packet_path"):
        if Path(packet[key]).exists() and packet["operation"] != "accept":
            raise FileExistsError(packet[key])
    if Path.cwd().resolve() != Path(packet["repository_root"]):
        raise ValueError("launch must run from the bound repository root")


def launch_release(
    run_spec: Path,
    repository_root: Path,
    data_root: Path,
    *,
    attempt: int = 1,
    operation: str = "prepare",
    resume_from: int | None = None,
    candidate: Path | None = None,
    accepted_by: str = "",
    accepted_at: str = "",
) -> dict[str, Any]:
    """Serialize production execution and recount every retained 05H byte before launch."""
    arguments: dict[str, Any] = dict(
        attempt=attempt,
        resume_from=resume_from,
        operation=operation,
        candidate=candidate,
        accepted_by=accepted_by,
        accepted_at=accepted_at,
    )
    packet = build_launch_packet(run_spec, repository_root, data_root, **arguments)
    _check_launch(packet)
    logs = Path(packet["supervisor_attempts_root"])
    logs.mkdir(parents=True, exist_ok=True)
    with (logs / "single-worker.lock").open("a+b") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("another Task 05H worker holds the launch lock") from exc
        packet = build_launch_packet(run_spec, repository_root, data_root, **arguments)
        _check_launch(packet)
        packet_path = Path(packet["launch_packet_path"])
        if operation == "accept" and packet_path.exists():
            return _complete_acceptance(
                run_spec,
                repository_root,
                data_root,
                attempt=attempt,
                resume_from=resume_from,
                candidate=candidate,
                accepted_by=accepted_by,
                accepted_at=accepted_at,
            )
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        Path(packet["output_root"]).mkdir(parents=True, exist_ok=True)
        write_file(packet_path, encode(packet))
        result = supervise(
            packet["command"],
            attempt_root=Path(packet["attempt_root"]),
            output_root=Path(packet["output_root"]),
            limits=ExecutionLimits(**packet["supervisor_limits"]),
        )
        if operation == "accept" and result.get("status") == "succeeded":
            return _complete_acceptance(
                run_spec,
                repository_root,
                data_root,
                attempt=attempt,
                resume_from=resume_from,
                candidate=candidate,
                accepted_by=accepted_by,
                accepted_at=accepted_at,
            )
        return result


def _complete_acceptance(
    request: Path,
    repository: Path,
    data_root: Path,
    *,
    attempt: int,
    resume_from: int | None,
    candidate: Path | None,
    accepted_by: str,
    accepted_at: str,
) -> dict[str, Any]:
    """Designate only after terminal success, under the launcher's single-worker lock."""
    from er_commons.response_inventory.release_execution import (
        verify_published_candidate,
        verify_terminal_execution,
        verify_worker_launch,
    )
    from er_commons.response_inventory.release_publication import designate_acceptance

    run = open_run(request, repository, data_root, attempt, resume_from)
    if candidate is None:
        raise ValueError("acceptance requires the exact published inventory")
    verify_worker_launch(run, request, "accept", candidate, accepted_by, accepted_at)
    execution = verify_terminal_execution(run, "accept", run.attempt)
    publication = verify_published_candidate(run, candidate)
    packet_path = (
        run.root.parent
        / "05h_execution_attempts"
        / run.plan_id
        / f"launch-{run.attempt:03d}-accept.json"
    )
    remaining_metadata_bytes = RESERVE_BYTES - len(packet_path.read_bytes())
    # No payload reads or production work follows this bounded metadata designation.
    record = designate_acceptance(
        candidate,
        run.root,
        run.spec,
        plan_id=run.plan_id,
        accepted_by=accepted_by,
        accepted_at=accepted_at,
        execution_evidence={"accept": execution, "publish": publication},
        max_metadata_bytes=remaining_metadata_bytes,
    )
    return {"status": "succeeded", "acceptance": record}


def main() -> None:
    """Preview a launch or execute exactly one separately authorized operation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-spec", required=True, type=Path)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--resume-from", type=int)
    parser.add_argument("--operation", choices=OPERATIONS, default="prepare")
    parser.add_argument("--candidate-root", type=Path)
    parser.add_argument("--accepted-by", default="")
    parser.add_argument("--accepted-at", default="")
    parser.add_argument("--print-packet", action="store_true")
    args = parser.parse_args()
    if not (root := os.environ.get("ER_COMMONS_DATA_ROOT")):
        parser.error("ER_COMMONS_DATA_ROOT must be set explicitly")
    function = build_launch_packet if args.print_packet else launch_release
    result = function(
        args.run_spec,
        Path(__file__).resolve().parents[3],
        Path(root),
        attempt=args.attempt,
        resume_from=args.resume_from,
        operation=args.operation,
        candidate=args.candidate_root,
        accepted_by=args.accepted_by,
        accepted_at=args.accepted_at,
    )
    print(json.dumps(result, sort_keys=True, indent=2))
    if not args.print_packet:
        raise SystemExit(0 if result["status"] == "succeeded" else 1)


if __name__ == "__main__":
    main()
