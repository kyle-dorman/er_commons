"""Semantic-specific completed-candidate verification and failure retention."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.canonical_extraction.publication import build_inventory, sha256_file, write_json
from er_commons.semantic_materialization.errors import SemanticMaterializationInvariantError
from er_commons.semantic_materialization.support import SUPPORT_PATHS

JsonObject = dict[str, Any]


def _require_publication_value(
    *,
    invariant: str,
    expected: object,
    observed: object,
    subject: str,
) -> None:
    """Raise one evidence-bearing reuse-boundary error when values differ."""
    if observed != expected:
        raise SemanticMaterializationInvariantError(
            stage="candidate reuse verification",
            invariant=invariant,
            expected=expected,
            observed=observed,
            subject=subject,
        )


def _load_record(path: Path) -> JsonObject:
    """Load one candidate record and require a JSON object root."""
    try:
        value = json.loads(path.read_bytes())
    except json.JSONDecodeError as error:
        raise SemanticMaterializationInvariantError(
            stage="candidate reuse verification",
            invariant="candidate record contains valid JSON",
            expected="valid JSON",
            observed=f"{error.msg} at line {error.lineno}, column {error.colno}",
            subject=path.as_posix(),
        ) from error
    if not isinstance(value, dict):
        raise SemanticMaterializationInvariantError(
            stage="candidate reuse verification",
            invariant="candidate record has a JSON object at its root",
            expected="object",
            observed=type(value).__name__,
            subject=path.as_posix(),
        )
    return value


def verify_completed_semantic_candidate(root: Path, candidate_id: str) -> Path:
    """Fail closed unless a v2 candidate, support set, and inventory are exact."""
    completion_path = root / "records" / "completion_record.json"
    inventory_path = root / "records" / "artifact_inventory.json"
    manifest_path = root / "records" / "manifest.json"
    terminal_records = (completion_path, inventory_path, manifest_path)
    missing_records = [
        path.relative_to(root).as_posix() for path in terminal_records if not path.is_file()
    ]
    if missing_records:
        raise SemanticMaterializationInvariantError(
            stage="candidate reuse verification",
            invariant="semantic candidate terminal records are present",
            expected=[],
            observed=missing_records,
            subject=root.as_posix(),
        )
    completion = _load_record(completion_path)
    inventory = _load_record(inventory_path)
    manifest = _load_record(manifest_path)
    expected_completion = {
        "schema_version": "er_commons.canonical_extraction_completion.v2",
        "extraction_id": candidate_id,
        "support_files_verified": True,
        "undeclared_difference_count": 0,
    }
    for key, expected in expected_completion.items():
        _require_publication_value(
            invariant=f"semantic completion field {key} matches",
            expected=expected,
            observed=completion.get(key),
            subject=completion_path.as_posix(),
        )
    disposition = completion.get("source_semantic_disposition")
    allowed_dispositions = {"accepted_with_known_limitations", "strict_quality_gate"}
    if disposition not in allowed_dispositions:
        raise SemanticMaterializationInvariantError(
            stage="candidate reuse verification",
            invariant="semantic completion has a supported source disposition",
            expected=sorted(allowed_dispositions),
            observed=disposition,
            subject=completion_path.as_posix(),
        )
    status = completion.get("status")
    allowed_statuses = {"complete", "complete_with_warnings"}
    if status not in allowed_statuses:
        raise SemanticMaterializationInvariantError(
            stage="candidate reuse verification",
            invariant="semantic completion has a terminal status",
            expected=sorted(allowed_statuses),
            observed=status,
            subject=completion_path.as_posix(),
        )
    if disposition == "accepted_with_known_limitations":
        _require_publication_value(
            invariant="bounded semantic completion retains limitation warnings",
            expected="complete_with_warnings",
            observed=status,
            subject=completion_path.as_posix(),
        )
    _require_publication_value(
        invariant="semantic manifest candidate identity matches completion",
        expected=candidate_id,
        observed=manifest.get("extraction_id"),
        subject=manifest_path.as_posix(),
    )
    _require_publication_value(
        invariant="semantic manifest disposition matches completion",
        expected=disposition,
        observed=manifest.get("source_semantic_disposition"),
        subject=manifest_path.as_posix(),
    )
    _require_publication_value(
        invariant="semantic completion seals its inventory",
        expected=sha256_file(inventory_path),
        observed=completion.get("artifact_inventory_sha256"),
        subject=completion_path.as_posix(),
    )
    expected_inventory = build_inventory(root)
    _require_publication_value(
        invariant="semantic candidate inventory matches the managed file set",
        expected=expected_inventory,
        observed=inventory,
        subject=inventory_path.as_posix(),
    )
    support_files = manifest.get("support_files")
    if not isinstance(support_files, list) or not all(
        isinstance(item, dict) and isinstance(item.get("role"), str) for item in support_files
    ):
        raise SemanticMaterializationInvariantError(
            stage="candidate reuse verification",
            invariant="semantic candidate support entries have named roles",
            expected="list of objects with string role fields",
            observed=support_files,
            subject=manifest_path.as_posix(),
        )
    support = {item["role"]: item for item in support_files}
    _require_publication_value(
        invariant="semantic candidate support roles are exact and unique",
        expected=sorted(SUPPORT_PATHS),
        observed=sorted(support) if len(support) == len(support_files) else "duplicate roles",
        subject=manifest_path.as_posix(),
    )
    for role, relative in SUPPORT_PATHS.items():
        item = support[role]
        path = root / relative
        _require_publication_value(
            invariant=f"semantic support path matches for role {role}",
            expected=relative,
            observed=item.get("path"),
            subject=manifest_path.as_posix(),
        )
        if not path.is_file():
            raise SemanticMaterializationInvariantError(
                stage="candidate reuse verification",
                invariant=f"semantic support file exists for role {role}",
                expected="file",
                observed="missing",
                subject=path.as_posix(),
            )
        _require_publication_value(
            invariant=f"semantic support checksum matches for role {role}",
            expected=sha256_file(path),
            observed=item.get("sha256"),
            subject=path.as_posix(),
        )
    return completion_path


def preserve_failed_attempt(
    task_root: Path,
    staging_root: Path,
    *,
    candidate_id: str | None = None,
    error: Exception | None = None,
) -> Path:
    """Retain a failed build and optional structured diagnostic without completion."""
    failed = task_root / "attempts" / staging_root.name
    failed.parent.mkdir(parents=True, exist_ok=True)
    (staging_root / "records" / "completion_record.json").unlink(missing_ok=True)
    if error is not None:
        write_json(
            staging_root / "records" / "attempt_record.json",
            {
                "candidate_id": candidate_id,
                "status": "failed",
                "stage": "semantic_materialization",
                "exception_type": type(error).__name__,
                "detail": str(error) or type(error).__name__,
            },
        )
    if staging_root.exists():
        staging_root.rename(failed)
    return failed
