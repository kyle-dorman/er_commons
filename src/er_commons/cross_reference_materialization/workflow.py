"""Short orchestration shell for the Task 03E.5 cross-reference stage."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from er_commons.canonical_extraction.publication import publish_workspace, reserve_workspace
from er_commons.cross_reference_materialization.config import load_config
from er_commons.cross_reference_materialization.construction import construct_candidate
from er_commons.cross_reference_materialization.identity import build_identity
from er_commons.cross_reference_materialization.io import sha256_file
from er_commons.cross_reference_materialization.publication import (
    preserve_failed_attempt,
    serialize_candidate,
    verify_completed_candidate,
)
from er_commons.cross_reference_materialization.validation import (
    validate_build,
    validate_serialized_candidate,
)


def run_cross_reference_materialization(data_root: Path, config_path: Path) -> Path:
    """Verify input, identify/reuse, build twice, validate, and atomically publish."""
    project_root = Path(__file__).resolve().parents[3]
    config_path = config_path.resolve()
    config = load_config(config_path)
    task_root = data_root / config.artifact_relative_root
    upstream_root = task_root / config.upstream_candidate_id
    _verify_upstream(
        upstream_root, config.upstream_completion_sha256, config.upstream_inventory_sha256
    )
    identity = build_identity(project_root=project_root, config_path=config_path, config=config)
    candidate_id = identity["extraction_id"]
    candidate_root = task_root / candidate_id
    if candidate_root.exists():
        return verify_completed_candidate(candidate_root, candidate_id)

    workspaces = []
    try:
        for _ in range(2):
            workspace = reserve_workspace(task_root, candidate_id, uuid.uuid4().hex)
            workspaces.append(workspace)
            build = construct_candidate(
                upstream_root=upstream_root,
                upstream_id=config.upstream_candidate_id,
                candidate_id=candidate_id,
            )
            validate_build(
                build=build,
                upstream_root=upstream_root,
                upstream_id=config.upstream_candidate_id,
                candidate_id=candidate_id,
                schema_path=project_root / config.schema_relative_path,
                identity_extension=identity["cross_reference_contract"],
            )
            serialize_candidate(
                root=workspace.staging_root,
                upstream_root=upstream_root,
                build=build,
                identity=identity,
            )
            validate_serialized_candidate(
                workspace.staging_root, project_root / config.schema_relative_path
            )
        if _file_bytes(workspaces[0].staging_root) != _file_bytes(workspaces[1].staging_root):
            raise RuntimeError("fresh cross-reference builds differ")
        shutil.rmtree(workspaces[1].staging_root)
        completion = publish_workspace(workspaces[0])
        verify_completed_candidate(candidate_root, candidate_id)
        return completion
    except Exception:
        for workspace in workspaces:
            if workspace.staging_root.exists():
                preserve_failed_attempt(task_root, workspace.staging_root)
        raise


def _verify_upstream(root: Path, completion_sha256: str, inventory_sha256: str) -> None:
    completion = root / "records" / "completion_record.json"
    inventory = root / "records" / "artifact_inventory.json"
    if sha256_file(completion) != completion_sha256 or sha256_file(inventory) != inventory_sha256:
        raise RuntimeError("accepted Task 03E.4 input checksum differs")


def _file_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
