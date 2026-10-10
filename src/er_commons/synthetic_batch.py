"""Bounded Astra authoring with immutable attempts and checksum-verified recovery."""

from __future__ import annotations

import argparse
import fcntl
import json
import logging
import re
import shutil
import subprocess
import time
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from er_commons.artifact_io import (
    artifact_inventory,
    file_reference,
    json_bytes,
    publish_bytes_no_clobber,
    sha256_file,
    stable_json_sha256,
)
from er_commons.group_answer_batch import execute_codex, invocation_arguments

LOGGER = logging.getLogger(__name__)
MODEL = "gpt-6-astra"
type Executor = Callable[[list[str], str, Path], int]


def read(path: Path) -> dict[str, Any]:
    """Read an object with its filesystem identity retained by callers."""
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"Expected object: {path}")
    return value


def save(path: Path, value: Any) -> None:
    """Publish immutable JSON; repeated writes must have identical bytes."""
    publish_bytes_no_clobber(path, json_bytes(value))


def now() -> str:
    """Record explicit UTC timestamps independently of host locale."""
    return datetime.now(UTC).isoformat()


@contextmanager
def lock(root: Path) -> Iterator[None]:
    """Prevent overlapping mutations and refuse mutations after publication."""
    with (root / ".run.lock").open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            if (root / "completion.json").exists():
                raise ValueError("Published run is immutable")
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def prepare(root: Path, intake: dict[str, Any], spec_root: Path, *, smoke: bool = False) -> None:
    """Freeze packets and configuration before any source-only model invocation."""
    from er_commons.synthetic_records import CATEGORIES

    ids = [case["case_id"] for case in intake["cases"]]
    allowed = intake["dev_case_ids"]
    if (
        not ids
        or len(ids) != len(set(ids))
        or any(not re.fullmatch(r"C\d{3}", cid) for cid in ids)
        or not set(ids) <= set(allowed)
    ):
        raise ValueError("Cases must be unique safe development IDs")
    root.mkdir(parents=True, exist_ok=False)
    save(root / "intake.json", intake)
    for source, target in (
        ("task09a_output.schema.json", "output_schema.json"),
        ("task09a_generation_prompt.md", "prompt_template.md"),
        ("task09a_perturbations.json", "catalog.json"),
    ):
        publish_bytes_no_clobber(root / target, (spec_root / source).read_bytes())
    executable = shutil.which("codex")
    if executable is None:
        raise ValueError("Established codex authoring executable is unavailable")
    version = subprocess.run([executable, "--version"], capture_output=True, text=True, check=True)
    config = {
        "schema_version": "task09a.run.v1",
        "model": MODEL,
        "reasoning_effort": "high",
        "executable": executable,
        "cli_version": version.stdout.strip(),
        "default_workers": 1,
        "max_infrastructure_retries": 2,
        "backoff_seconds": [10, 30],
        "max_semantic_corrections": 1,
        "timeout_seconds": 1200,
        "smoke": smoke,
        "reservation_seed": "task09a-final-check-v1",
        "code_bindings": [
            {"path": str(p.resolve()), "sha256": sha256_file(p)}
            for p in [
                Path(__file__),
                Path(__file__).with_name("synthetic_records.py"),
                Path(__file__).with_name("synthetic_intake.py"),
                Path(__file__).with_name("group_answer_batch.py"),
            ]
        ],
    }
    save(root / "config.json", config)
    ids = []
    for original in intake["cases"]:
        packet = dict(original)
        packet["requested_categories"] = ["P01", "O01", "F03", "C05"] if smoke else list(CATEGORIES)
        case_id = packet["case_id"]
        ids.append(case_id)
        save(root / "cases" / case_id / "input.json", packet)
        prompt = (root / "prompt_template.md").read_text()
        prompt += "\n\nPERTURBATION CATALOG:\n" + (root / "catalog.json").read_text()
        prompt += "\n\nISOLATED CASE PACKET:\n"
        prompt += json.dumps(packet, ensure_ascii=False) + "\n"
        publish_bytes_no_clobber(root / "cases" / case_id / "prompt.md", prompt.encode())
    save(
        root / "prepared.json",
        {
            "case_ids": ids,
            "files": artifact_inventory(root, set())["files"],
            "configuration_id": stable_json_sha256(config),
        },
    )

    publish_bytes_no_clobber(
        root / "prepared.sha256", (sha256_file(root / "prepared.json") + "\n").encode()
    )


def verify_inputs(root: Path, *, check_code: bool = True) -> dict[str, Any]:
    """Reject altered packets, configurations, code or upstream release bindings."""
    if (root / "prepared.sha256").read_text().strip() != sha256_file(root / "prepared.json"):
        raise ValueError("Prepared manifest checksum differs")
    prepared = read(root / "prepared.json")
    for ref in prepared["files"]:
        if file_reference(root / ref["path"], root=root) != ref:
            raise ValueError(f"Prepared input changed: {ref['path']}")
    if check_code:
        for ref in read(root / "config.json")["code_bindings"]:
            if sha256_file(Path(ref["path"])) != ref["sha256"]:
                raise ValueError(f"Authoring code changed: {ref['path']}; prepare a fresh run")
    for ref in read(root / "intake.json").get("source_bindings", {}).values():
        if sha256_file(Path(ref["path"])) != ref["sha256"]:
            raise ValueError(f"Upstream changed: {ref['path']}")
    return prepared


def tool_audit(path: Path) -> dict[str, Any]:
    """Inspect actual transport events; absent backend identity is reported honestly."""
    kinds, models = [], []
    for line in path.read_text().splitlines():
        event = json.loads(line)
        kind = event.get("item", {}).get("type")
        if kind and kind not in {"reasoning", "agent_message"}:
            kinds.append(kind)
        if event.get("model"):
            models.append(event["model"])
    return {
        "valid": not kinds and all(m == MODEL for m in models),
        "tool_activity": kinds,
        "reported_models": sorted(set(models)),
        "backend_model_independently_observed": bool(models),
    }


def seal_attempt(attempt: Path, result: dict[str, Any]) -> None:
    """Write a terminal receipt only after all attempt artifacts are durable."""
    result["files"] = artifact_inventory(attempt, {"result.json", "result.sha256"})
    save(attempt / "result.json", result)
    publish_bytes_no_clobber(
        attempt / "result.sha256", (sha256_file(attempt / "result.json") + "\n").encode()
    )


def history(directory: Path) -> list[tuple[Path, dict[str, Any]]]:
    """Verify terminal history and explicitly seal a last interrupted invocation."""
    paths = sorted((directory / "attempts").glob("attempt_*"))
    rows = []
    for number, path in enumerate(paths, 1):
        if path.name != f"attempt_{number:04d}":
            raise ValueError("Noncontiguous attempt history")
        if not (path / "result.json").exists():
            if path != paths[-1]:
                raise ValueError("Only the last attempt may be interrupted")
            invocation = (
                read(path / "invocation.json") if (path / "invocation.json").exists() else {}
            )
            seal_attempt(
                path,
                {
                    "status": "infrastructure_failure",
                    "reason": "Interrupted before terminal receipt",
                    "phase": invocation.get("phase", "unknown"),
                    "ended_at": now(),
                },
            )
        result = read(path / "result.json")
        if not (path / "result.sha256").exists():
            # A crash between receipt and checksum must not promote unsealed success.
            raise ValueError("Unsealed terminal receipt; preserve attempt for explicit recovery")
        if (path / "result.sha256").read_text().strip() != sha256_file(path / "result.json"):
            raise ValueError("Attempt terminal checksum differs")
        if result["files"] != artifact_inventory(path, {"result.json", "result.sha256"}):
            raise ValueError("Attempt inventory differs")
        rows.append((path, result))
    return rows


def run_case(
    root: Path, case_id: str, executor: Executor, sleeper: Callable[[float], None]
) -> dict[str, Any]:
    """Finish one isolated case with two infrastructure retries and one corrective revision."""
    from er_commons.synthetic_records import validate_proposal

    directory = root / "cases" / case_id
    packet = read(directory / "input.json")
    while True:
        rows = history(directory)
        if rows and rows[-1][1]["status"] == "validated":
            return {
                "case_id": case_id,
                "attempt": str(rows[-1][0].relative_to(root)),
                **rows[-1][1],
            }
        failures = [(p, r) for p, r in rows if r["status"] == "semantic_failure"]
        phase = "correction" if failures else "initial"
        infra = [r for _, r in rows if r["status"] == "infrastructure_failure"]
        if len(failures) >= 2 or len(infra) >= 3:
            return {"case_id": case_id, "status": "failed", "reason": rows[-1][1]["reason"]}
        if rows and rows[-1][1]["status"] == "infrastructure_failure":
            sleeper([10, 30][min(len(infra) - 1, 1)])
        prompt = (directory / "prompt.md").read_text()
        if failures:
            previous, failure = failures[0]
            prompt += (
                "\nONE CORRECTIVE AUTHORING ATTEMPT: "
                "repair the concrete validation findings below. "
            )
            prompt += "Preserve the scope and return the complete required output.\n"
            prompt += json.dumps(failure["reason"]) + "\nPREVIOUS OUTPUT:\n"
            if (previous / "raw_output.json").exists():
                prompt += (previous / "raw_output.json").read_text()
        attempt = directory / "attempts" / f"attempt_{len(rows) + 1:04d}"
        attempt.mkdir(parents=True)
        publish_bytes_no_clobber(attempt / "prompt.md", prompt.encode())
        arguments = invocation_arguments(root, attempt)
        config = read(root / "config.json")
        arguments[0] = config["executable"]
        invocation = {
            "arguments": arguments,
            "requested_model": MODEL,
            "backend_model": None,
            "cli_version": config["cli_version"],
            "settings": {"reasoning_effort": "high"},
            "started_at": now(),
            "phase": phase,
            "input": file_reference(directory / "input.json", root=root),
            "prompt": file_reference(attempt / "prompt.md", root=root),
            "schema": file_reference(root / "output_schema.json", root=root),
            "configuration_id": read(root / "prepared.json")["configuration_id"],
        }
        save(attempt / "invocation.json", invocation)
        result: dict[str, Any] = {
            "status": "infrastructure_failure",
            "phase": phase,
            "reason": None,
        }
        try:
            code = executor(arguments, prompt, attempt)
            save(attempt / "process.json", {"returncode": code, "ended_at": now()})
            if code:
                raise RuntimeError(f"Astra process exit {code}; see stderr.txt and stdout.jsonl")
            audit = tool_audit(attempt / "stdout.jsonl")
            save(attempt / "transport_validation.json", audit)
            result["status"] = "semantic_failure"
            if not audit["valid"]:
                raise ValueError("Forbidden tool activity or model mismatch")
            output = read(attempt / "raw_output.json")
            validation = validate_proposal(output, packet)
            save(attempt / "validation.json", validation)
            if not validation["valid"]:
                raise ValueError(json.dumps(validation["errors"]))
            result["status"] = "validated"
        except Exception as error:
            result["reason"] = f"{type(error).__name__}: {error}"
        result["ended_at"] = now()
        seal_attempt(attempt, result)
        LOGGER.info(
            "case=%s phase=%s status=%s reason=%s",
            case_id,
            phase,
            result["status"],
            result["reason"],
        )


def run(
    root: Path,
    *,
    workers: int = 1,
    case_ids: list[str] | None = None,
    executor: Executor = execute_codex,
    sleeper: Callable[[float], None] = time.sleep,
) -> list[dict[str, Any]]:
    """Resume only identity-matching cases, allowing unaffected cases to continue."""
    if not 1 <= workers <= 3:
        raise ValueError("Use one to three workers")
    with lock(root):
        prepared = verify_inputs(root)
        ids = prepared["case_ids"] if case_ids is None else case_ids
        if len(ids) != len(set(ids)) or not set(ids) <= set(prepared["case_ids"]):
            raise ValueError("Requested IDs must belong to the prepared development intake")

        def isolated(case_id: str) -> dict[str, Any]:
            """Account for a damaged case without aborting unaffected jobs."""
            try:
                return run_case(root, case_id, executor, sleeper)
            except Exception as error:
                LOGGER.exception("case=%s failed before invocation", case_id)
                return {
                    "case_id": case_id,
                    "status": "failed",
                    "reason": f"{type(error).__name__}: {error}",
                }

        with ThreadPoolExecutor(max_workers=workers) as pool:
            return list(pool.map(isolated, ids))


def main() -> None:
    """Expose explicit preparation and bounded authoring without running later tasks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "run", "verify-inputs"])
    parser.add_argument("root", type=Path)
    parser.add_argument("--intake", type=Path)
    parser.add_argument("--spec-root", type=Path, default=Path("docs/specs"))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--case", action="append", dest="case_ids")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.command == "prepare":
        if args.intake is None:
            parser.error("prepare requires --intake")
        prepare(args.root, read(args.intake), args.spec_root, smoke=args.smoke)
    elif args.command == "run":
        LOGGER.info("%s", json.dumps(run(args.root, workers=args.workers, case_ids=args.case_ids)))
    else:
        verify_inputs(args.root)
        LOGGER.info("Input identities verified")


if __name__ == "__main__":
    main()
