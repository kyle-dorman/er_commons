"""Read-only completed-run and lineage-seal audit for downstream qualification."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import read_json_object
from er_commons.chunked_conversion.qualification.diagnostics import QualificationError
from er_commons.chunked_conversion.qualification.downstream_contracts import (
    ACCEPTED_DOCUMENT_ID,
    ACCEPTED_STAGE_IDS,
    AGGREGATE_ID,
    GATE_C_RUN_ID,
    QUALIFICATION_STAGE_IDS,
    SOURCE_ID,
    DownstreamCompletion,
    DownstreamPaths,
)
from er_commons.chunked_conversion.qualification.evidence_audit import (
    EvidenceAudit,
    EvidenceRootSpec,
    RecordedClaim,
    audit_evidence_root,
)


def validate_downstream_completion(paths: DownstreamPaths) -> EvidenceAudit:
    """Require exact IDs, a strict completion, closed inventory, and pass claims."""
    completion_path = paths.downstream / "records/completion_record.json"
    try:
        completion = DownstreamCompletion.model_validate_json(completion_path.read_bytes())
    except (OSError, ValueError, TypeError) as error:
        raise QualificationError(
            "downstream_completion_record",
            stage="downstream_audit",
            path=completion_path.as_posix(),
            expected="strict expected completion",
            actual=str(error),
        ) from error
    _require_equal("gate_c_run_identity", completion.gate_c_run_id, GATE_C_RUN_ID, completion_path)
    _require_equal(
        "aggregate_identity", completion.aggregate_conversion_id, AGGREGATE_ID, completion_path
    )
    return audit_evidence_root(
        EvidenceRootSpec(
            role="downstream",
            root=paths.downstream,
            expected_id=GATE_C_RUN_ID,
            completion_id_field="gate_c_run_id",
            statuses=frozenset({"complete"}),
            claims=(
                RecordedClaim(completion.report, "/status", "complete"),
                RecordedClaim(completion.report, "/g2_inspected", False),
                RecordedClaim(completion.report, "/aggregate_conversion_id", AGGREGATE_ID),
            ),
        )
    )


def audit_stage_pairs(paths: DownstreamPaths) -> dict[str, dict[str, dict[str, Any]]]:
    """Audit accepted and qualification stage roots against their exact IDs."""
    results: dict[str, dict[str, dict[str, Any]]] = {}
    for role in ACCEPTED_STAGE_IDS:
        directory = "hierarchy_inference" if role == "hierarchy_decisions" else "document_records"
        accepted = paths.accepted_task / directory / ACCEPTED_STAGE_IDS[role]
        qualification = paths.downstream / directory / QUALIFICATION_STAGE_IDS[role]
        results[role] = {
            "accepted": _audit_record(_audit_stage(role, accepted, ACCEPTED_STAGE_IDS[role])),
            "qualification": _audit_record(
                _audit_stage(role, qualification, QUALIFICATION_STAGE_IDS[role])
            ),
        }
    return results


def verify_bounded_controls(
    paths: DownstreamPaths,
    actual_document: Path,
    seals: dict[str, dict[str, dict[str, Any]]],
) -> None:
    """Bind the two waived control digests to independently audited hierarchy roots."""
    accepted_document = paths.accepted_task / (
        f"document_publications/documents/{SOURCE_ID}/{ACCEPTED_DOCUMENT_ID}"
    )
    for disposition, content in (
        ("accepted", accepted_document / "content"),
        ("qualification", actual_document / "content"),
    ):
        control_path = content / "support/bounded_control_verification.json"
        control = read_json_object(control_path).get("control_provenance")
        seal = seals["hierarchy_decisions"][disposition]
        if not isinstance(control, dict):
            _fail("bounded_control_shape", control_path, "object", control)
        typed_control = cast(dict[str, Any], control)
        expected = (seal["artifact_inventory_sha256"], seal["completion_sha256"])
        actual = (
            typed_control.get("artifact_inventory_sha256"),
            typed_control.get("quality_gate_completion_sha256"),
        )
        _require_equal("bounded_control_seal", actual, expected, control_path)


def _audit_stage(role: str, root: Path, expected_id: str) -> EvidenceAudit:
    identity_field = (
        "candidate_id" if role in {"mapped_records", "hierarchy_decisions"} else "extraction_id"
    )
    status_field = "source_semantic_disposition" if role == "structured_document" else "status"
    statuses = (
        frozenset({"accepted_with_known_limitations", "strict_quality_gate"})
        if role == "structured_document"
        else frozenset({"complete", "complete_with_warnings"})
    )
    return audit_evidence_root(
        EvidenceRootSpec(
            role=role,
            root=root,
            expected_id=expected_id,
            completion_id_field=identity_field,
            statuses=statuses,
            canonical_inventory_seal=role == "hierarchy_decisions",
            completion_status_field=status_field,
        )
    )


def _audit_record(audit: EvidenceAudit) -> dict[str, Any]:
    record = asdict(audit)
    return {
        "id": record["identity"],
        "status": record["status"],
        "completion_sha256": record["completion_sha256"],
        "artifact_inventory_sha256": record["inventory_sha256"],
        "file_count": record["file_count"],
        "byte_count": record["byte_count"],
    }


def _require_equal(code: str, actual: object, expected: object, path: Path) -> None:
    if actual != expected:
        _fail(code, path, expected, actual)


def _fail(code: str, path: Path, expected: object, actual: object) -> None:
    raise QualificationError(
        code,
        stage="downstream_audit",
        path=path.as_posix(),
        expected=expected,
        actual=actual,
    )


__all__ = ["audit_stage_pairs", "validate_downstream_completion", "verify_bounded_controls"]
