"""Restartable, completion-last Task 08F model preparation without human decisions."""

from __future__ import annotations

import argparse
import fcntl
import json
import logging
import os
import re
import signal
import subprocess
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
)

LOGGER = logging.getLogger(__name__)
MODEL = "gpt-6-astra"
_TERMINAL_FILES = {"result.json", "result.sha256"}
type Executor = Callable[[list[str], str, Path], int]


def _read(path: Path) -> dict[str, Any]:
    """Read an object and fail with its path when its shape is wrong."""
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _save(path: Path, value: object) -> None:
    """Durably save a new record, accepting only byte-identical replay."""
    publish_bytes_no_clobber(path, json_bytes(value))


def _now() -> str:
    """Return an explicit UTC recording time, independent of host timezone."""
    return datetime.now(UTC).isoformat()


@contextmanager
def _lock(root: Path) -> Iterator[None]:
    """Exclude concurrent batch mutation while retaining a harmless lock file."""
    with (root / ".run.lock").open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            if (root / "completion.json").exists():
                raise ValueError("Completed preparation is immutable")
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def prepare_batch(
    root: Path, intake: dict[str, Any], prompt_template: str, schema: dict[str, Any]
) -> dict[str, Any]:
    """Create isolated case inputs in a fresh namespace and seal preparation inputs."""
    cases = intake["cases"]
    ids = [case["case_id"] for case in cases]
    if not ids or len(ids) != len(set(ids)) or any(not re.fullmatch(r"C\d{3}", i) for i in ids):
        raise ValueError("Case IDs must be nonempty, unique and C plus three digits")
    root.mkdir(parents=True, exist_ok=False)
    _save(root / "intake.json", intake)
    _save(root / "output_schema.json", schema)
    publish_bytes_no_clobber(root / "prompt_template.md", prompt_template.encode())
    for case in cases:
        directory = root / "cases" / case["case_id"]
        _save(directory / "input.json", case)
        prompt = (
            prompt_template
            + "\n\nUse only the isolated approved case JSON below. Do not use tools, web, "
            "other files, official responses, or external knowledge as answer evidence. "
            "Do not rewrite the question or infer human approval. Before returning, check each "
            "assertion, inference and qualification against actual cited source text; review_notes "
            "must describe this advisory grounding check and concrete limitations, never judge "
            "scores. Preserve approved framing and list substantive_changes explicitly "
            "(empty for format-only changes). Citations whose role is optional_context may "
            "appear only in optional_context, never as support for conclusion, supporting_points, "
            "or qualifications. Choose short exact substring citation_locators "
            "from full_source_text "
            "for every cited occurrence. Return only the required JSON.\n\n"
            + json.dumps(case, ensure_ascii=False, indent=2)
            + "\n"
        )
        publish_bytes_no_clobber(directory / "prompt.md", prompt.encode())
    manifest = {
        "contract": "task08f.phase_a.v1",
        "ordered_case_ids": ids,
        "model": MODEL,
        "human_answer_approval": None,
        "final_disposition": None,
        "files": artifact_inventory(root, set())["files"],
    }
    _save(root / "prepared_inputs.json", manifest)
    return manifest


def _verify_inputs(root: Path) -> dict[str, Any]:
    """Check all prepared inputs before an invocation or publication."""
    manifest = _read(root / "prepared_inputs.json")
    for record in manifest["files"]:
        if file_reference(root / record["path"], root=root) != record:
            raise ValueError(f"Prepared input changed: {record['path']}")
    return manifest


def invocation_arguments(root: Path, attempt: Path) -> list[str]:
    """Describe the exact ephemeral, source-only model invocation without a shell."""
    return [
        "codex",
        "exec",
        "--ignore-user-config",
        "--ephemeral",
        "--skip-git-repo-check",
        "-C",
        str(attempt.resolve()),
        "-m",
        MODEL,
        "-s",
        "read-only",
        "-c",
        'web_search="disabled"',
        "-c",
        "features.shell_tool=false",
        "-c",
        'model_reasoning_effort="high"',
        "--json",
        "--output-schema",
        str((root / "output_schema.json").resolve()),
        "-o",
        str((attempt / "raw_output.json").resolve()),
        "-",
    ]


def execute_codex(arguments: list[str], prompt: str, attempt: Path) -> int:
    """Stream process receipts to disk; preserve partial output on failure or timeout."""
    with (
        (attempt / "stdout.jsonl").open("xb") as stdout,
        (attempt / "stderr.txt").open("xb") as stderr,
    ):
        process = subprocess.Popen(
            arguments,
            stdin=subprocess.PIPE,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        try:
            process.communicate(input=prompt.encode(), timeout=1200)
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            raise
        return process.returncode


def _tool_audit(attempt: Path) -> dict[str, Any]:
    """Reject tool activity in the source-only authoring transport receipt."""
    forbidden: list[str] = []
    models: list[str] = []
    for line in (attempt / "stdout.jsonl").read_text().splitlines():
        event = json.loads(line)
        item = event.get("item", {})
        kind = item.get("type", "")
        if kind and kind not in {"reasoning", "agent_message"}:
            forbidden.append(kind)
        if isinstance(event.get("model"), str):
            models.append(event["model"])
    return {
        "tool_activity": forbidden,
        "reported_models": sorted(set(models)),
        "valid": not forbidden and all(model == MODEL for model in models),
    }


def _latest(directory: Path) -> tuple[Path | None, dict[str, Any] | None]:
    """Resolve only the last numbered attempt; incomplete attempts never imply success."""
    attempts = sorted((directory / "attempts").glob("attempt_*"))
    if not attempts:
        return None, None
    path = attempts[-1]
    return path, _read(path / "result.json") if (path / "result.json").exists() else None


def _save_result(attempt: Path, result: dict[str, Any]) -> None:
    """Bind the terminal receipt itself separately from its attempt-file inventory."""
    _save(attempt / "result.json", result)
    publish_bytes_no_clobber(
        attempt / "result.sha256", (sha256_file(attempt / "result.json") + "\n").encode()
    )


def _verify_history(root: Path, directory: Path, *, allow_incomplete: bool = False) -> None:
    """Verify every terminal attempt; only the newest interrupted attempt may be unsealed."""
    attempts = sorted((directory / "attempts").glob("attempt_*"))
    for index, attempt in enumerate(attempts, 1):
        if attempt.name != f"attempt_{index:04d}":
            raise ValueError("Attempt history has missing or reordered versions")
        if not (attempt / "result.json").exists():
            if allow_incomplete and attempt == attempts[-1]:
                continue
            raise ValueError(f"Historical attempt has no terminal receipt: {attempt}")
        _verify_result(root, directory, attempt, _read(attempt / "result.json"))


def _run_case(root: Path, case_id: str, executor: Executor) -> dict[str, Any]:
    """Record one new attempt, preserving failed predecessors and exact input bindings."""
    from er_commons.group_answer_records import render_answer, validate_preparation

    directory = root / "cases" / case_id
    _verify_history(root, directory, allow_incomplete=True)
    previous, result = _latest(directory)
    if result and result["status"] == "validated_proposal":
        _verify_result(root, directory, previous, result)
        return result
    if previous is not None and result is None:
        result = {
            "case_id": case_id,
            "version": int(previous.name.split("_")[-1]),
            "status": "blocked",
            "reason": "Interrupted: no terminal receipt was saved",
            "human_answer_approval": None,
            "final_disposition": None,
            "attempt": str(previous.relative_to(root)),
            "files": artifact_inventory(previous, _TERMINAL_FILES)["files"],
        }
        _save_result(previous, result)
    attempt_number = 1 if previous is None else int(previous.name.split("_")[-1]) + 1
    attempt = directory / "attempts" / f"attempt_{attempt_number:04d}"
    attempt.mkdir(parents=True, exist_ok=False)
    input_record = _read(directory / "input.json")
    prompt = (directory / "prompt.md").read_text()
    if previous:
        prior_failure = result or {"status": "interrupted", "reason": "No terminal receipt saved"}
        prompt += "\nPrevious attempt failed validation; repair within the same approved scope:\n"
        prompt += json.dumps({"reason": prior_failure["reason"]}, ensure_ascii=False) + "\n"
        previous_raw = previous / "raw_output.json"
        if previous_raw.is_file():
            prompt += (
                "Exact previous raw output follows; repair it, preserving supported content:\n"
            )
            prompt += previous_raw.read_text() + "\n"
    publish_bytes_no_clobber(attempt / "prompt.md", prompt.encode())
    _save(attempt / "input.json", input_record)
    arguments = invocation_arguments(root, attempt)
    _save(
        attempt / "invocation.json",
        {
            "arguments": arguments,
            "requested_model": MODEL,
            "started_at": _now(),
            "input_sha256": sha256_file(attempt / "input.json"),
            "prompt_sha256": sha256_file(attempt / "prompt.md"),
            "schema_sha256": sha256_file(root / "output_schema.json"),
            "predecessor_attempt": str(previous.relative_to(root)) if previous else None,
            "transport": "ephemeral codex exec; no persistent chat",
            "backend_model": None,
        },
    )
    result = {
        "case_id": case_id,
        "version": attempt_number,
        "status": "blocked",
        "human_answer_approval": None,
        "final_disposition": None,
        "attempt": str(attempt.relative_to(root)),
        "reason": None,
    }
    try:
        returncode = executor(arguments, prompt, attempt)
        _save(attempt / "process.json", {"returncode": returncode, "ended_at": _now()})
        if returncode:
            raise ValueError(f"Model process exited {returncode}")
        audit = _tool_audit(attempt)
        _save(attempt / "transport_validation.json", audit)
        if not audit["valid"]:
            raise ValueError(
                "Forbidden tool activity or reported model mismatch during isolated authoring"
            )
        proposal = _read(attempt / "raw_output.json")
        validation = validate_preparation(proposal, input_record)
        _save(attempt / "validation.json", validation)
        if not validation["valid"]:
            raise ValueError(f"Proposal validation failed: {validation}")
        _save(attempt / "proposal.json", proposal)
        if proposal.get("status") == "blocked":
            result["reason"] = proposal.get(
                "blocked_reason", "Model reported a preparation blocker"
            )
        else:
            display = render_answer(proposal["answer"], input_record)
            publish_bytes_no_clobber(attempt / "display.md", display.encode())
            result["status"] = "validated_proposal"
            result["display_sha256"] = sha256_file(attempt / "display.md")
        result["files"] = artifact_inventory(attempt, _TERMINAL_FILES)["files"]
    except BaseException as error:
        result["reason"] = f"{type(error).__name__}: {error}"
        result["files"] = artifact_inventory(attempt, _TERMINAL_FILES)["files"]
        _save_result(attempt, result)
        if not isinstance(error, Exception):
            raise
        LOGGER.warning("case=%s status=blocked reason=%s", case_id, error)
    else:
        _save_result(attempt, result)
    return result


def _verify_result(
    root: Path, directory: Path, attempt: Path | None, result: dict[str, Any]
) -> None:
    """Reject changed attempt files and recheck structural source bindings before reuse."""
    from er_commons.group_answer_records import validate_preparation

    if attempt is None or result["case_id"] != directory.name:
        raise ValueError("Invalid case attempt identity")
    if result["attempt"] != str(attempt.relative_to(root)) or result["version"] != int(
        attempt.name.split("_")[-1]
    ):
        raise ValueError("Terminal receipt version or attempt binding differs")
    digest_path = attempt / "result.sha256"
    if not digest_path.is_file() or digest_path.read_text().strip() != sha256_file(
        attempt / "result.json"
    ):
        raise ValueError(f"Terminal receipt changed: {attempt}")
    if result.get("files") != artifact_inventory(attempt, _TERMINAL_FILES)["files"]:
        raise ValueError(f"Attempt files changed: {attempt}")
    if result["human_answer_approval"] is not None or result["final_disposition"] is not None:
        raise ValueError("Phase A cannot contain human approval or disposition")
    if result["status"] == "validated_proposal":
        validation = validate_preparation(
            _read(attempt / "proposal.json"), _read(directory / "input.json")
        )
        if not validation["valid"] or not _tool_audit(attempt)["valid"]:
            raise ValueError(f"Saved proposal no longer validates: {attempt}")
        if result["display_sha256"] != sha256_file(attempt / "display.md"):
            raise ValueError("Saved display checksum differs")
    elif result["status"] != "blocked" or not result["reason"]:
        raise ValueError("Every case needs a validated proposal or explicit blocker")


def run_batch(
    root: Path,
    *,
    executor: Executor = execute_codex,
    max_workers: int = 3,
    case_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Run or resume a bounded batch; successful proposals are never overwritten."""
    if not 1 <= max_workers <= 3:
        raise ValueError("Concurrency must be between one and three")
    with _lock(root):
        if (root / "review.md").exists() or (root / "handoff.json").exists():
            raise ValueError("Publication already started; resume seal without new attempts")
        manifest = _verify_inputs(root)
        ids = manifest["ordered_case_ids"]
        if case_ids is not None:
            if len(set(case_ids)) != len(case_ids) or not set(case_ids) <= set(ids):
                raise ValueError("Requested cases must be unique members of prepared intake")
            ids = [case_id for case_id in ids if case_id in case_ids]
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            return list(pool.map(lambda case_id: _run_case(root, case_id, executor), ids))


def seal_batch(root: Path) -> dict[str, Any]:
    """Publish every attempted case in saved order, explicitly retaining preparation blockers."""
    with _lock(root):
        manifest = _verify_inputs(root)
        cases: list[dict[str, Any]] = []
        review = [
            "# Prepared answers — awaiting human review",
            "",
            "These are proposals. No new answer approvals or dispositions are recorded.",
            "",
        ]
        for case_id in manifest["ordered_case_ids"]:
            _verify_history(root, root / "cases" / case_id)
            path, result = _latest(root / "cases" / case_id)
            if path is None or result is None:
                raise ValueError(f"Case has no terminal preparation receipt: {case_id}")
            _verify_result(root, root / "cases" / case_id, path, result)
            source = _read(root / "cases" / case_id / "input.json")
            row = dict(result)
            row["question"] = source["question"]
            row["eligibility_provenance"] = source.get("eligibility_provenance")
            row["source_bindings"] = source.get("source_bindings", [])
            row["input"] = file_reference(root / "cases" / case_id / "input.json", root=root)
            row["artifacts"] = {
                name: file_reference(path / name, root=root)
                for name in (
                    "proposal.json",
                    "display.md",
                    "validation.json",
                    "invocation.json",
                    "raw_output.json",
                    "result.json",
                )
                if (path / name).is_file()
            }
            cases.append(row)
            if result["status"] == "validated_proposal":
                review.extend([(path / "display.md").read_text(), "", "---", ""])
            else:
                review.extend(
                    [
                        f"## {case_id}: preparation blocked",
                        source["question"],
                        str(result["reason"]),
                        "",
                        "---",
                        "",
                    ]
                )
        publish_bytes_no_clobber(root / "review.md", "\n".join(review).encode())
        handoff = {
            "contract": "task08f.phase_a.v1",
            "status": "prepared, awaiting human review",
            "ordered_cases": cases,
            "case_count": len(cases),
            "validated_proposals": sum(c["status"] == "validated_proposal" for c in cases),
            "blocked_cases": [c["case_id"] for c in cases if c["status"] == "blocked"],
            "intake": file_reference(root / "intake.json", root=root),
            "readable_review": file_reference(root / "review.md", root=root),
            "validation_limits": "Mechanical checks verify structure, source membership and "
            "saved bindings. Model source-grounding notes are advisory and do not establish "
            "semantic correctness or human approval.",
            "next_stage": None,
            "human_answer_approval": None,
            "final_disposition": None,
            "review_instructions": "Verify completion.json, then review saved proposals from C001 "
            "in order. Keep actual display events, feedback and revisions in a separate namespace. "
            "Preparation is not approval. Do not rerun initial authoring for validated cases.",
        }
        _save(root / "handoff.json", handoff)
        _save(
            root / "completion.json",
            {
                "contract": "task08f.phase_a.completion.v1",
                "status": "prepared, awaiting human review",
                "inventory": artifact_inventory(root, {"completion.json"}),
            },
        )
    return verify_batch(root)


def verify_batch(root: Path) -> dict[str, Any]:
    """Verify the exact preparation closure and unchanged inputs; never establish approval."""
    completion = _read(root / "completion.json")
    actual = artifact_inventory(root, {"completion.json"})
    if completion["inventory"] != actual:
        raise ValueError("Preparation inventory differs: missing, added, or changed files")
    _verify_inputs(root)
    handoff = _read(root / "handoff.json")
    ids = [case["case_id"] for case in handoff["ordered_cases"]]
    if ids != _read(root / "prepared_inputs.json")["ordered_case_ids"]:
        raise ValueError("Handoff case order/accounting differs from intake")
    for case in handoff["ordered_cases"]:
        _verify_history(root, root / "cases" / case["case_id"])
        _verify_result(root, root / "cases" / case["case_id"], root / case["attempt"], case)
    return {
        "valid": True,
        "case_count": len(ids),
        "handoff": str(root / "handoff.json"),
        "completion_sha256": sha256_file(root / "completion.json"),
        "validated_proposals": handoff["validated_proposals"],
        "blocked_cases": handoff["blocked_cases"],
    }


def main() -> None:
    """Expose a small package CLI; preparation consumes a previously audited intake JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "run", "seal", "verify"])
    parser.add_argument("root", type=Path)
    parser.add_argument("--intake", type=Path)
    parser.add_argument("--prompt", type=Path)
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--case", action="append", dest="case_ids")
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.command == "prepare":
        if not all((args.intake, args.prompt, args.schema)):
            parser.error("prepare requires --intake, --prompt and --schema")
        result = prepare_batch(
            args.root, _read(args.intake), args.prompt.read_text(), _read(args.schema)
        )
    elif args.command == "run":
        result = {"cases": run_batch(args.root, max_workers=args.workers, case_ids=args.case_ids)}
    elif args.command == "seal":
        result = seal_batch(args.root)
    else:
        result = verify_batch(args.root)
    LOGGER.info("%s", json.dumps(result))


if __name__ == "__main__":
    main()
