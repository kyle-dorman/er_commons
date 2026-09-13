"""Semantic-specific completed-candidate verification and failure retention."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.document_records.document_structure.constants import (
    REPEATED_HEADING_CORRESPONDENCE_SCHEMA_RELATIVE_PATH,
)
from er_commons.document_records.document_structure.errors import (
    DocumentStructureInvariantError,
    StructureContractError,
)
from er_commons.document_records.document_structure.support import (
    MISSING_CHAPTER_CORRESPONDENCE_PATH,
    REPEATED_HEADING_CORRESPONDENCE_PATH,
    SUPPORT_PATHS,
)
from er_commons.document_records.record_mapping.errors import MappingContractError
from er_commons.document_records.record_mapping.identity import extraction_identity_sha256
from er_commons.document_records.record_mapping.publication import (
    CandidateWorkspace,
    retain_workspace_without_completion,
    sha256_file,
    validate_inventory_metadata,
    write_json,
)

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class _CandidateRecords:
    """Loaded terminal records and their evidence-bearing paths."""

    completion_path: Path
    inventory_path: Path
    manifest_path: Path
    completion: JsonObject
    inventory: JsonObject
    manifest: JsonObject


def _require_publication_value(
    *,
    invariant: str,
    expected: object,
    observed: object,
    subject: str,
) -> None:
    """Raise one evidence-bearing reuse-boundary error when values differ."""
    if observed != expected:
        raise DocumentStructureInvariantError(
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
        raise DocumentStructureInvariantError(
            stage="candidate reuse verification",
            invariant="candidate record contains valid JSON",
            expected="valid JSON",
            observed=f"{error.msg} at line {error.lineno}, column {error.colno}",
            subject=path.as_posix(),
        ) from error
    if not isinstance(value, dict):
        raise DocumentStructureInvariantError(
            stage="candidate reuse verification",
            invariant="candidate record has a JSON object at its root",
            expected="object",
            observed=type(value).__name__,
            subject=path.as_posix(),
        )
    return value


def _load_candidate_records(root: Path) -> _CandidateRecords:
    """Require and load the three terminal records used to verify reuse."""
    completion_path = root / "records" / "completion_record.json"
    inventory_path = root / "records" / "artifact_inventory.json"
    manifest_path = root / "records" / "manifest.json"
    terminal_records = (completion_path, inventory_path, manifest_path)
    missing_records = [
        path.relative_to(root).as_posix() for path in terminal_records if not path.is_file()
    ]
    if missing_records:
        raise DocumentStructureInvariantError(
            stage="candidate reuse verification",
            invariant="semantic candidate terminal records are present",
            expected=[],
            observed=missing_records,
            subject=root.as_posix(),
        )
    return _CandidateRecords(
        completion_path=completion_path,
        inventory_path=inventory_path,
        manifest_path=manifest_path,
        completion=_load_record(completion_path),
        inventory=_load_record(inventory_path),
        manifest=_load_record(manifest_path),
    )


def _verify_completion(records: _CandidateRecords, candidate_id: str) -> str:
    """Verify completion identity, status, and its inventory seal."""
    is_v3 = records.manifest.get("schema_version") == "er_commons.canonical_extraction_manifest.v3"
    expected_completion = {
        "schema_version": (
            "er_commons.canonical_extraction_completion.v3"
            if is_v3
            else "er_commons.canonical_extraction_completion.v2"
        ),
        "extraction_id": candidate_id,
        "support_files_verified": True,
        "undeclared_difference_count": 0,
    }
    for key, expected in expected_completion.items():
        _require_publication_value(
            invariant=f"semantic completion field {key} matches",
            expected=expected,
            observed=records.completion.get(key),
            subject=records.completion_path.as_posix(),
        )
    disposition = records.completion.get("source_semantic_disposition")
    allowed_dispositions = {"accepted_with_known_limitations", "strict_quality_gate"}
    if not isinstance(disposition, str) or disposition not in allowed_dispositions:
        raise DocumentStructureInvariantError(
            stage="candidate reuse verification",
            invariant="semantic completion has a supported source disposition",
            expected=sorted(allowed_dispositions),
            observed=disposition,
            subject=records.completion_path.as_posix(),
        )
    status = records.completion.get("status")
    allowed_statuses = {"complete", "complete_with_warnings"}
    if status not in allowed_statuses:
        raise DocumentStructureInvariantError(
            stage="candidate reuse verification",
            invariant="semantic completion has a terminal status",
            expected=sorted(allowed_statuses),
            observed=status,
            subject=records.completion_path.as_posix(),
        )
    if disposition == "accepted_with_known_limitations":
        _require_publication_value(
            invariant="bounded semantic completion retains limitation warnings",
            expected="complete_with_warnings",
            observed=status,
            subject=records.completion_path.as_posix(),
        )
    _require_publication_value(
        invariant="semantic completion seals its inventory",
        expected=sha256_file(records.inventory_path),
        observed=records.completion.get("artifact_inventory_sha256"),
        subject=records.completion_path.as_posix(),
    )
    return disposition


def _verify_manifest_and_inventory(
    root: Path,
    records: _CandidateRecords,
    candidate_id: str,
    disposition: str,
) -> None:
    """Verify manifest identity and the inventory's exact managed file set."""
    _require_publication_value(
        invariant="semantic manifest candidate identity matches completion",
        expected=candidate_id,
        observed=records.manifest.get("extraction_id"),
        subject=records.manifest_path.as_posix(),
    )
    _require_publication_value(
        invariant="semantic manifest disposition matches completion",
        expected=disposition,
        observed=records.manifest.get("source_semantic_disposition"),
        subject=records.manifest_path.as_posix(),
    )
    try:
        validate_inventory_metadata(root, records.inventory)
    except MappingContractError as error:
        raise DocumentStructureInvariantError(
            stage="candidate reuse verification",
            invariant="semantic candidate inventory metadata matches the managed file set",
            expected="unique contained files with exact sizes and totals",
            observed=str(error),
            subject=records.inventory_path.as_posix(),
        ) from error


def _support_entries(records: _CandidateRecords) -> tuple[dict[str, JsonObject], int]:
    """Load support entries keyed by role and retain the declared count."""
    support_files = records.manifest.get("support_files")
    if not isinstance(support_files, list) or not all(
        isinstance(item, dict) and isinstance(item.get("role"), str) for item in support_files
    ):
        raise DocumentStructureInvariantError(
            stage="candidate reuse verification",
            invariant="semantic candidate support entries have named roles",
            expected="list of objects with string role fields",
            observed=support_files,
            subject=records.manifest_path.as_posix(),
        )
    return {item["role"]: item for item in support_files}, len(support_files)


def _expected_support_paths(
    root: Path,
    records: _CandidateRecords,
    support: dict[str, JsonObject],
) -> tuple[dict[str, str], JsonObject | None]:
    """Derive versioned support roles and load optional candidate identity."""
    expected_paths = dict(SUPPORT_PATHS)
    identity_path = root / "records" / "extraction_identity.json"
    identity = _load_record(identity_path) if identity_path.is_file() else None
    semantic_contract = identity.get("semantic_contract") if identity is not None else None
    repeated_contract = (
        semantic_contract.get("repeated_heading_repair", {})
        if isinstance(semantic_contract, dict)
        else {}
    )
    requires_repeated_correspondence = (
        isinstance(repeated_contract, dict) and "correspondence_schema" in repeated_contract
    )
    if "repeated_heading_correspondence" in support or requires_repeated_correspondence:
        expected_paths["repeated_heading_correspondence"] = REPEATED_HEADING_CORRESPONDENCE_PATH
    if records.manifest.get("schema_version") == "er_commons.canonical_extraction_manifest.v3":
        expected_paths["missing_chapter_correspondence"] = MISSING_CHAPTER_CORRESPONDENCE_PATH
    return expected_paths, identity


def _verify_repeated_heading_correspondence(
    root: Path,
    records: _CandidateRecords,
    identity: JsonObject | None,
    relative_path: str,
) -> None:
    """Verify repeated-heading correspondence against identity and schema."""
    from er_commons.document_records.document_structure.repeated_heading_correspondence import (
        validate_repeated_heading_correspondence,
    )

    path = root / relative_path
    try:
        if identity is None:
            raise StructureContractError("repeated-heading candidate identity is absent")
        identity_digest = extraction_identity_sha256(identity)
        if (
            identity.get("extraction_id") != records.manifest["extraction_id"]
            or identity.get("extraction_id") != f"exv1-{identity_digest}"
            or identity.get("identity_sha256") != identity_digest
            or records.manifest.get("identity_sha256") != identity_digest
        ):
            raise StructureContractError(
                "repeated-heading identity digest or candidate binding is invalid"
            )
        repeated_contract = identity["semantic_contract"]["repeated_heading_repair"]
        expected_decision_ref = repeated_contract["decisions"]
        if not isinstance(expected_decision_ref, dict):
            raise StructureContractError(
                "repeated-heading identity lacks its decision artifact reference"
            )
        schema_path = (
            Path(__file__).resolve().parents[4]
            / REPEATED_HEADING_CORRESPONDENCE_SCHEMA_RELATIVE_PATH
        )
        expected_schema_ref = {
            "path": REPEATED_HEADING_CORRESPONDENCE_SCHEMA_RELATIVE_PATH.as_posix(),
            "sha256": sha256_file(schema_path),
        }
        if repeated_contract.get("correspondence_schema") != expected_schema_ref:
            raise StructureContractError(
                "repeated-heading identity correspondence schema binding differs"
            )
        validate_repeated_heading_correspondence(
            _load_record(path),
            schema_path=schema_path,
            candidate_id=str(records.manifest["extraction_id"]),
            expected_decision_ref=expected_decision_ref,
        )
        record_count = len(_load_record(path)["records"])
        _require_publication_value(
            invariant="semantic completion repeated-heading count matches",
            expected=record_count,
            observed=records.completion.get("repeated_heading_correspondence_count"),
            subject=records.completion_path.as_posix(),
        )
    except (KeyError, StructureContractError) as error:
        raise DocumentStructureInvariantError(
            stage="candidate reuse verification",
            invariant="repeated-heading correspondence matches its closed schema",
            expected="valid er_commons.recovery.repeated_heading_correspondence.v1",
            observed=str(error),
            subject=path.as_posix(),
        ) from error


def _verify_missing_chapter_correspondence(
    root: Path,
    records: _CandidateRecords,
    relative_path: str,
) -> None:
    """Verify missing-chapter correspondence against candidate identity."""
    from er_commons.document_records.document_structure.missing_chapter_correspondence import (
        validate_missing_chapter_correspondence,
    )

    path = root / relative_path
    identity_path = root / "records" / "extraction_identity.json"
    try:
        identity = _load_record(identity_path)
        identity_digest = extraction_identity_sha256(identity)
        if (
            identity.get("extraction_id") != records.manifest["extraction_id"]
            or identity.get("extraction_id") != f"exv1-{identity_digest}"
            or identity.get("identity_sha256") != identity_digest
            or records.manifest.get("identity_sha256") != identity_digest
        ):
            raise StructureContractError(
                "missing-chapter identity digest or candidate binding is invalid"
            )
        expected_decision_ref = identity["semantic_contract"]["missing_chapter_repair"]["decisions"]
        if not isinstance(expected_decision_ref, dict):
            raise StructureContractError(
                "missing-chapter identity lacks its decision artifact reference"
            )
        validate_missing_chapter_correspondence(
            _load_record(path),
            candidate_id=str(records.manifest["extraction_id"]),
            expected_decision_ref=expected_decision_ref,
        )
    except (KeyError, StructureContractError) as error:
        raise DocumentStructureInvariantError(
            stage="candidate reuse verification",
            invariant="missing-chapter correspondence matches its closed schema",
            expected="valid er_commons.recovery.missing_chapter_correspondence.v1",
            observed=str(error),
            subject=path.as_posix(),
        ) from error


def _verify_support_files(root: Path, records: _CandidateRecords) -> None:
    """Verify every declared support role, path, file, and checksum."""
    support, declared_count = _support_entries(records)
    expected_paths, identity = _expected_support_paths(root, records, support)
    _require_publication_value(
        invariant="semantic candidate support roles are exact and unique",
        expected=sorted(expected_paths),
        observed=sorted(support) if len(support) == declared_count else "duplicate roles",
        subject=records.manifest_path.as_posix(),
    )
    for role, relative in expected_paths.items():
        item = support[role]
        path = root / relative
        _require_publication_value(
            invariant=f"semantic support path matches for role {role}",
            expected=relative,
            observed=item.get("path"),
            subject=records.manifest_path.as_posix(),
        )
        if not path.is_file():
            raise DocumentStructureInvariantError(
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
    repeated_path = expected_paths.get("repeated_heading_correspondence")
    if repeated_path is not None:
        _verify_repeated_heading_correspondence(root, records, identity, repeated_path)
    correspondence_path = expected_paths.get("missing_chapter_correspondence")
    if correspondence_path is not None:
        _verify_missing_chapter_correspondence(root, records, correspondence_path)


def verify_completed_document_structure(root: Path, candidate_id: str) -> Path:
    """Verify the immutable seal and metadata without hashing large semantic streams."""
    records = _load_candidate_records(root)
    disposition = _verify_completion(records, candidate_id)
    _verify_manifest_and_inventory(root, records, candidate_id, disposition)
    _verify_support_files(root, records)
    return records.completion_path


def deep_audit_completed_document_structure(root: Path, candidate_id: str) -> Path:
    """Stream-hash every managed semantic byte after fast seal verification."""
    completion = verify_completed_document_structure(root, candidate_id)
    records = _load_candidate_records(root)
    managed_files = validate_inventory_metadata(root, records.inventory)
    for item in managed_files:
        observed = sha256_file(item.path)
        if observed != item.sha256:
            raise DocumentStructureInvariantError(
                stage="candidate deep audit",
                invariant="semantic candidate managed checksum matches",
                expected=item.sha256,
                observed=observed,
                subject=item.path.as_posix(),
            )
    return completion


def preserve_failed_attempt(
    task_root: Path,
    staging_root: Path,
    *,
    candidate_id: str | None = None,
    error: BaseException | None = None,
) -> Path:
    """Retain a failed build and optional structured diagnostic without completion."""
    final_root = task_root / candidate_id if candidate_id is not None else task_root / "unpublished"
    workspace = CandidateWorkspace(staging_root=staging_root, final_root=final_root)
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
    retained = retain_workspace_without_completion(workspace, task_root / "attempts")
    if retained is None:
        raise FileNotFoundError(f"failed semantic workspace is missing: {staging_root}")
    return retained
