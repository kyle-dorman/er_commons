"""Read-only launch packets and explicitly authorized, supervised Task 05G replay."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shlex
from dataclasses import asdict
from pathlib import Path
from typing import Any

from er_commons.document_publication.background_execution import ExecutionLimits, supervise
from er_commons.response_inventory.reference_replay_spec import contained_path, load_replay_spec

OPERATIONS = ("all", "prepare", "build", "compare", "validate")

THREAD_ENVIRONMENT = {
    "OMP_NUM_THREADS": "2",
    "OPENBLAS_NUM_THREADS": "2",
    "MKL_NUM_THREADS": "2",
    "NUMEXPR_NUM_THREADS": "2",
    "VECLIB_MAXIMUM_THREADS": "2",
}


def _owned_bytes(root: Path) -> int:
    """Count all previous 05G bytes without traversing accepted artifact trees."""
    if any(path.is_symlink() for path in (root, *root.parents)):
        raise ValueError("05G accounting roots may not traverse symlinks")
    total = 0
    if not root.exists():
        return total
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("05G accounting tree contains a symlink")
        if path.is_file():
            total += path.stat().st_size
    return total


def build_launch_packet(
    run_spec: Path,
    repository_root: Path,
    data_root: Path,
    *,
    attempt: int = 1,
    resume_from: int | None = None,
    operation: str = "all",
) -> dict[str, Any]:
    """Resolve and account one reviewed invocation without creating any directory."""
    if operation not in OPERATIONS:
        raise ValueError("unknown supervised Task 05G operation")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
        raise ValueError("attempt must be a positive integer")
    if resume_from is not None and (
        isinstance(resume_from, bool)
        or not isinstance(resume_from, int)
        or not 0 < resume_from < attempt
    ):
        raise ValueError("resume-from must name an earlier positive attempt")
    resume_arguments = [] if resume_from is None else ["--resume-from", str(resume_from)]
    spec, digest = load_replay_spec(run_spec, repository_root)
    output_root = contained_path(data_root, spec["output_relative_root"])
    attempts_root = output_root.parent / "05g_execution_attempts"
    attempt_root = attempts_root / digest / f"attempt-{attempt:03d}"
    prior_logs = _owned_bytes(attempts_root)
    prior_output = _owned_bytes(output_root)
    maximum = spec["limits"]["max_output_bytes"]
    available = maximum - prior_logs
    limits = ExecutionLimits(
        **{
            key: value
            for key, value in spec["limits"].items()
            if key not in {"workers", "cpu_threads"}
        }
    )
    supervisor_limits = {**asdict(limits), "max_output_bytes": available}
    command = [
        "/usr/bin/env",
        *(f"{key}={value}" for key, value in THREAD_ENVIRONMENT.items()),
        "uv",
        "run",
        "python",
        "-m",
        "er_commons.response_inventory.reference_replay_workflow",
        "--run-spec",
        str(run_spec.resolve()),
        "--attempt",
        str(attempt),
        *resume_arguments,
        "--operation",
        operation,
        "--execute-stages",
    ]
    supervisor_command = [
        "uv",
        "run",
        "python",
        "-m",
        "er_commons.document_publication.background_execution",
        "--attempt-root",
        str(attempt_root),
        "--output-root",
        str(output_root),
    ]
    for key, value in supervisor_limits.items():
        supervisor_command.extend(["--" + key.replace("_", "-"), str(value)])
    supervisor_command.extend(["--", *command])
    name = f"er-commons-05g-{digest[:12]}-attempt-{attempt:03d}"
    packet = {
        "schema_version": "er_commons.task05g.launch_packet.v1",
        "spec_sha256": digest,
        "request_sha256": hashlib.sha256(run_spec.read_bytes()).hexdigest(),
        "request_text": run_spec.read_text(),
        "launch_packet_path": str(
            output_root / "plans" / digest / f"launch-attempt-{attempt:03d}.json"
        ),
        "candidate_id": "replayv1-" + digest,
        "run_spec": str(run_spec.resolve()),
        "repository_root": str(repository_root.resolve()),
        "data_root": str(data_root.resolve()),
        "input_bindings": spec["inputs"],
        "repository_bindings": spec["repository_bindings"],
        "authorization": spec["authorization"],
        "output_root": str(output_root),
        "candidate_root": str(
            output_root / "candidates" / ("replayv1-" + digest) / f"attempt-{attempt:03d}"
        ),
        "prepared_root": str(output_root / "plans" / digest / f"attempt-{attempt:03d}"),
        "resolved_root": str(
            output_root / "attempts" / digest / f"attempt-{attempt:03d}" / "resolved"
        ),
        "comparison_root": str(
            output_root / "comparisons" / ("replayv1-" + digest) / f"attempt-{attempt:03d}"
        ),
        "attempt": attempt,
        "resume_from": resume_from,
        "operation": operation,
        "attempt_root": str(attempt_root),
        "supervisor_attempts_root": str(attempts_root),
        "prior_supervisor_bytes": prior_logs,
        "prior_output_bytes": prior_output,
        "cumulative_max_bytes": maximum,
        "supervisor_limits": supervisor_limits,
        "effective_worker_thread_environment": THREAD_ENVIRONMENT,
        "supervisor_environment_note": (
            "The maintained supervisor records its four-thread defaults; the explicit env "
            "prefix overrides all five numerical thread settings to two for the worker."
        ),
        "command": command,
        "maintained_supervisor_command": supervisor_command,
        "tmux_session": name,
        "launch_command": [
            "tmux",
            "new-session",
            "-d",
            "-s",
            name,
            "-c",
            str(repository_root.resolve()),
            shlex.join(
                [
                    "uv",
                    "run",
                    "python",
                    "-m",
                    "er_commons.response_inventory.reference_replay_launch",
                    "--run-spec",
                    str(run_spec.resolve()),
                    "--attempt",
                    str(attempt),
                    *resume_arguments,
                    "--operation",
                    operation,
                ]
            ),
        ],
    }

    if len(_packet_bytes(packet)) > 65536:
        raise ValueError("05G launch packet exceeds 64 KiB reviewed metadata bound")
    return packet


def _packet_bytes(packet: dict[str, Any]) -> bytes:
    """Encode the immutable prelaunch receipt deterministically."""
    return (json.dumps(packet, sort_keys=True, separators=(",", ":")) + "\n").encode()


def launch_replay(
    run_spec: Path,
    repository_root: Path,
    data_root: Path,
    *,
    attempt: int = 1,
    resume_from: int | None = None,
    operation: str = "all",
) -> dict[str, Any]:
    """Enforce replay authorization and cumulative accounting before supervision."""
    packet = build_launch_packet(
        run_spec,
        repository_root,
        data_root,
        attempt=attempt,
        resume_from=resume_from,
        operation=operation,
    )
    if packet["authorization"]["replay"] is not True:
        raise ValueError("Task 05G replay requires separate explicit execution authorization")
    remaining = packet["supervisor_limits"]["max_output_bytes"]
    if remaining <= packet["prior_output_bytes"] + 65536:
        raise ValueError("cumulative 05G output budget exhausted; preserve prior evidence")
    attempt_root = Path(packet["attempt_root"])
    output_root = Path(packet["output_root"])
    if attempt_root.exists():
        raise FileExistsError(attempt_root)
    # Cwd determines uv's project; never silently execute under another repository.
    if Path.cwd().resolve() != repository_root.resolve():
        raise ValueError("launch must run from the bound repository root")
    output_root.mkdir(parents=True, exist_ok=True)
    attempt_root.parent.mkdir(parents=True, exist_ok=True)
    lock_path = Path(packet["supervisor_attempts_root"]) / "single-worker.lock"
    with lock_path.open("a+b") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("another Task 05G worker already holds the launch lock") from exc
        # Recount after acquiring the global lock: another invocation may have
        # finished between the packet preview and this serialized launch.
        packet = build_launch_packet(
            run_spec,
            repository_root,
            data_root,
            attempt=attempt,
            resume_from=resume_from,
            operation=operation,
        )
        if packet["authorization"]["replay"] is not True:
            raise ValueError("Task 05G replay authorization changed before launch")
        if packet["supervisor_limits"]["max_output_bytes"] <= packet["prior_output_bytes"] + 65536:
            raise ValueError("cumulative 05G output budget exhausted; preserve prior evidence")
        packet_bytes = _packet_bytes(packet)
        if (
            packet["supervisor_limits"]["max_output_bytes"]
            <= packet["prior_output_bytes"] + len(packet_bytes) + 65536
        ):
            raise ValueError("cumulative 05G budget cannot contain the immutable launch packet")
        packet_path = Path(packet["launch_packet_path"])
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        with packet_path.open("xb") as handle:
            handle.write(packet_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        return supervise(
            packet["command"],
            attempt_root=attempt_root,
            output_root=output_root,
            limits=ExecutionLimits(**packet["supervisor_limits"]),
        )


def main() -> None:
    """Print the resolved packet or run exactly one separately authorized attempt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-spec", type=Path, required=True)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--resume-from", type=int)
    parser.add_argument("--print-packet", action="store_true")
    parser.add_argument("--operation", choices=OPERATIONS, default="all")
    args = parser.parse_args()
    data_root = os.environ.get("ER_COMMONS_DATA_ROOT")
    if not data_root:
        parser.error("ER_COMMONS_DATA_ROOT must be set explicitly")
    repository_root = Path(__file__).resolve().parents[3]
    function = build_launch_packet if args.print_packet else launch_replay
    result = function(
        args.run_spec,
        repository_root,
        Path(data_root),
        attempt=args.attempt,
        resume_from=args.resume_from,
        operation=args.operation,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if not args.print_packet:
        raise SystemExit(0 if result["status"] == "succeeded" else 1)


if __name__ == "__main__":
    main()
