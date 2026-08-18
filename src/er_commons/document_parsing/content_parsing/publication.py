"""Own staging, failure evidence, and atomic producer publication."""

from __future__ import annotations

import platform
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from er_commons.artifact_io import write_json_atomic
from er_commons.document_parsing.content_parsing.records import AttemptRecord
from er_commons.document_parsing.content_parsing.services import GitState


@dataclass(frozen=True)
class ProducerWorkspace:
    """One unpublished staging tree and its deterministic final destination."""

    staging_root: Path
    records_root: Path
    final_root: Path


def format_utc(value: datetime) -> str:
    """Serialize an aware timestamp using the existing ISO artifact convention."""
    if value.tzinfo is None:
        raise ValueError("producer timestamps must be timezone-aware")
    return value.isoformat()


def task_artifact_root(data_root: Path, relative_root: Path) -> Path:
    """Resolve and contain the task root below ER_COMMONS_DATA_ROOT."""
    root = (data_root / relative_root).resolve()
    if not root.is_relative_to(data_root.resolve()):
        raise ValueError("producer artifact root escapes ER_COMMONS_DATA_ROOT")
    root.mkdir(parents=True, exist_ok=True)
    return root


def reserve_workspace(
    task_root: Path,
    producer_run_id: str,
    *,
    token: str,
) -> ProducerWorkspace:
    """Reserve a unique staging tree without touching the final destination."""
    final_root = task_root / producer_run_id
    staging_root = task_root / ".tmp" / f"{producer_run_id}.{token}"
    staging_root.mkdir(parents=True, exist_ok=False)
    records_root = staging_root / "records"
    records_root.mkdir()
    return ProducerWorkspace(
        staging_root=staging_root,
        records_root=records_root,
        final_root=final_root,
    )


def write_preflight_records(
    workspace: ProducerWorkspace,
    *,
    config_path: Path,
    config_sha256: str,
    producer_run_id: str,
    identity: dict[str, Any],
    runtime: dict[str, Any],
    generated_at: datetime,
    git_state: GitState,
) -> None:
    """Persist the reviewed configuration, identity, runtime, and environment."""
    (workspace.records_root / "configuration.json").write_bytes(config_path.read_bytes())
    write_json_atomic(
        workspace.records_root / "producer_identity.json",
        {
            "producer_run_id": producer_run_id,
            "configuration_sha256": config_sha256,
            "identity": identity,
        },
    )
    write_json_atomic(workspace.records_root / "runtime_configuration.json", runtime)
    write_json_atomic(
        workspace.records_root / "environment.json",
        {
            "generated_at_utc": format_utc(generated_at),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "git_commit": git_state.commit,
            "git_dirty": git_state.dirty,
            "timeout_policy": "none; interruption preserves attempt evidence",
        },
    )


def publish_workspace(workspace: ProducerWorkspace) -> Path:
    """Atomically rename completed staging into an absent final destination."""
    if workspace.final_root.exists():
        raise FileExistsError(
            f"producer final root appeared during publication: {workspace.final_root}"
        )
    workspace.staging_root.rename(workspace.final_root)
    return workspace.final_root / "records" / "completion_record.json"


def preserve_failed_attempt(
    *,
    staging_root: Path | None,
    task_root: Path,
    producer_run_id: str | None,
    failed_stage: str,
    started_at: datetime,
    finished_at: datetime,
    wall_seconds: float,
    error: BaseException,
    token: str,
) -> Path:
    """Move partial work to attempts and remove any invalid completion marker."""
    attempt_id = (
        finished_at.strftime("%Y%m%dT%H%M%S")
        + "-"
        + (producer_run_id or "preflight")[:18]
        + "-"
        + token[:8]
    )
    attempt_root = task_root / "attempts" / attempt_id
    if staging_root is not None and staging_root.exists():
        attempt_root.parent.mkdir(parents=True, exist_ok=True)
        staging_root.rename(attempt_root)
    else:
        attempt_root.mkdir(parents=True, exist_ok=False)

    invalid_completion = attempt_root / "records" / "completion_record.json"
    removed_completion_marker = invalid_completion.exists()
    invalid_completion.unlink(missing_ok=True)
    record = AttemptRecord(
        schema_version="1.0.0",
        attempt_id=attempt_id,
        producer_run_id=producer_run_id,
        status="failed",
        failed_stage=failed_stage,
        exception_type=type(error).__name__,
        message=str(error),
        started_at_utc=format_utc(started_at),
        finished_at_utc=format_utc(finished_at),
        wall_seconds=wall_seconds,
        completion_record=None,
        removed_invalid_completion_marker=removed_completion_marker,
    )
    write_json_atomic(
        attempt_root / "attempt_record.json",
        record.model_dump(mode="json"),
    )
    return attempt_root
