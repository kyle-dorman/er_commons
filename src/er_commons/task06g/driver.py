"""Thin exact-command execution driver for Task 06G."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import cast

from er_commons.task06g.core import JsonObject, load_object, pointer_value, reference
from er_commons.task06g.phases import (
    publish_aggregate,
    publish_checkpoint_inventory,
    publish_stage_checkpoint,
)


def _runtime_values(raw_values: object, binding: JsonObject) -> dict[str, str]:
    """Load each exact runtime value from a verified checkpoint or launch binding."""
    if not isinstance(raw_values, list):
        raise ValueError("runtime_values must be a list")
    values: dict[str, str] = {}
    for raw in raw_values:
        if not isinstance(raw, dict):
            raise ValueError("runtime value must be an object")
        name = raw.get("name")
        pointer = raw.get("pointer")
        if not isinstance(name, str) or not isinstance(pointer, str) or name in values:
            raise ValueError("runtime value requires a unique name and exact pointer")
        if raw.get("authority") == "launch_binding":
            checkpoint = binding
        else:
            path = raw.get("checkpoint")
            if not isinstance(path, str):
                raise ValueError("checkpoint runtime value requires an explicit path")
            checkpoint = load_object(Path(path))
            if checkpoint.get("verified") is not True:
                raise ValueError(f"runtime checkpoint is not verified: {path}")
            if checkpoint.get("derived_id") != checkpoint.get("recomputed_id"):
                raise ValueError(f"runtime checkpoint identity mismatch: {path}")
        value = pointer_value(checkpoint, pointer)
        if not isinstance(value, str) or "{" in value or "}" in value:
            raise ValueError(f"runtime value is not a literal string: {name}")
        values[name] = value
    return values


def _materialize(argv: list[object], runtime: dict[str, str]) -> list[str]:
    result: list[str] = []
    for item in argv:
        if not isinstance(item, str):
            raise ValueError("command argv values must be strings")
        if item.startswith("{") and item.endswith("}"):
            name = item[1:-1]
            if name not in runtime:
                raise ValueError(f"unresolved command placeholder: {item}")
            item = runtime[name]
        if "{" in item or "}" in item:
            raise ValueError(f"embedded or unresolved placeholder is prohibited: {item}")
        if item.startswith("scopev1-") and item.removeprefix("scopev1-") == "0" * 64:
            raise ValueError("unresolved all-zero scope identity reached a child command")
        result.append(item)
    return result


def _resume_mode(binding: JsonObject) -> bool:
    """Select exact-reuse publication only for a verified resume receipt."""
    schema = binding.get("schema_version")
    if schema == "er_commons.task06g.resume_receipt.v1":
        if binding.get("status") != "accepted":
            raise ValueError("resume binding is not accepted")
        return True
    if schema == "er_commons.task06g.launch_intent.v1" or schema is None:
        return False
    raise ValueError(f"unsupported launch binding schema: {schema}")


def _completion_from_document_log(progress_root: Path, source_id: str) -> Path:
    log = progress_root / "runner_logs" / f"01_{source_id}.log"
    if not log.is_file():
        raise ValueError(f"document runner log is absent: {log}")
    matches = [
        line.removeprefix("document_completion=")
        for line in log.read_text(encoding="utf-8").splitlines()
        if line.startswith("document_completion=")
    ]
    if len(matches) != 1:
        raise ValueError(f"document runner log lacks one terminal completion: {source_id}")
    return Path(matches[0]).resolve()


def _completion_from_stdout(stdout: str, marker: str) -> Path:
    matches = [line.removeprefix(marker) for line in stdout.splitlines() if line.startswith(marker)]
    if len(matches) != 1:
        raise ValueError(f"command output lacks one {marker} marker")
    return Path(matches[0]).resolve()


def run_replay(execution_spec: Path, binding_path: Path, binding_sha256: str) -> None:
    """Verify launch binding, invoke reviewed argv, and checkpoint each dependency."""
    binding_ref = reference(binding_path)
    if binding_ref["sha256"] != binding_sha256:
        raise ValueError("launch or resume binding digest mismatch")
    binding = load_object(binding_path)
    resume_existing = _resume_mode(binding)
    spec = load_object(execution_spec)
    commands, expected = spec.get("commands"), spec.get("command_order")
    repository_root = spec.get("repository_working_directory", spec.get("repository_root"))
    generation_spec = spec.get("generation_spec")
    if not isinstance(commands, list) or not isinstance(repository_root, str):
        raise ValueError("execution spec requires commands and repository working directory")
    if not isinstance(generation_spec, str):
        # Retain the tiny synthetic fixture surface without weakening production specs.
        generation_spec = None
    names = [
        entry.get("stage", entry.get("name")) if isinstance(entry, dict) else None
        for entry in commands
    ]
    if expected is not None and (not isinstance(expected, list) or names != expected):
        raise ValueError("execution command order differs from reviewed order")
    for entry in commands:
        if not isinstance(entry, dict) or not isinstance(entry.get("argv"), list):
            raise ValueError("each reviewed command requires nonempty argv")
        runtime = _runtime_values(entry.get("runtime_values", []), binding)
        argv = _materialize(cast(list[object], entry["argv"]), runtime)
        try:
            completed = subprocess.run(
                argv,
                cwd=repository_root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as error:
            output = error.stdout or ""
            if output:
                print(output, end="")
            raise
        stdout = getattr(completed, "stdout", None) or ""
        if stdout:
            print(stdout, end="")
        checkpoint = entry.get("checkpoint_after")
        if checkpoint is not None:
            if generation_spec is None or not isinstance(checkpoint, dict):
                raise ValueError("checkpoint publication requires the frozen generation spec")
            stage_key, path, source = (
                checkpoint.get("stage_key"),
                checkpoint.get("path"),
                checkpoint.get("completion_source"),
            )
            if not all(isinstance(value, str) for value in (stage_key, path, source)):
                raise ValueError("checkpoint publication contract is incomplete")
            if source == "document_log":
                completion = _completion_from_document_log(
                    Path(runtime["progress_root"]), cast(str, checkpoint["source_id"])
                )
            elif source == "stdout_handoff":
                completion = _completion_from_stdout(stdout, "handoff_completion=")
            else:
                raise ValueError(f"unsupported checkpoint completion source: {source}")
            publish_stage_checkpoint(
                Path(generation_spec),
                cast(str, stage_key),
                completion,
                Path(cast(str, path)),
                resume_existing=resume_existing,
            )
    closure = spec.get("resolver_closure")
    if closure is not None:
        if not isinstance(closure, dict):
            raise ValueError("resolver_closure must be an object")
        checkpoint_root = Path(cast(str, closure["checkpoint_root"]))
        publish_checkpoint_inventory(
            checkpoint_root,
            cast(list[str], closure["checkpoint_files"]),
            resume_existing=resume_existing,
        )
        publish_aggregate(
            Path(cast(str, closure["resolved_specs_root"])),
            cast(list[str], closure["phase_directories"]),
            Path(cast(str, closure["resolved_specs_root"]))
            / cast(
                str,
                closure.get(
                    "pre_execution_identity_checkpoint",
                    "00_initial/pre_execution_production_identity_checkpoint.json",
                ),
            ),
            process_checkpoint_names=cast(list[str], closure.get("process_checkpoint_files", [])),
            pre_execution_manifest_field=cast(
                str,
                closure.get(
                    "pre_execution_manifest_field",
                    "pre_execution_production_identity_checkpoint",
                ),
            ),
            resume_existing=resume_existing,
        )


__all__ = ["run_replay"]
