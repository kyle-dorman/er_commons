"""Closed RFC 8785 identity recipes for executable corpus contract v1.1."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from er_commons.corpus_extraction_contract_v1_1.checks import (
    bytes_sha256,
    canonical_sha256,
    fail,
)
from er_commons.corpus_extraction_contract_v1_1.model import DerivedIdentity, JsonObject

INDEX_PREIMAGE_FIELDS = (
    "schema_version",
    "production_extraction_id",
    "scope_id",
    "accounting_sha256",
    "eligible_candidates_sha256",
    "unavailable_sources_sha256",
    "entries_sha256",
    "entry_count",
    "document_targets_sha256",
    "document_target_count",
    "ordering_policy_version",
    "target_policy_sha256",
    "managed_inventory_sha256",
)
RESOLUTION_PREIMAGE_FIELDS = (
    "schema_version",
    "production_extraction_id",
    "scope_id",
    "index_completion_sha256",
    "mention_input_manifest_sha256",
    "resolutions_sha256",
    "counts_sha256",
    "before_after_inventories_sha256",
    "resolution_policy_sha256",
    "managed_inventory_sha256",
)
HANDOFF_PREIMAGE_FIELDS = (
    "schema_version",
    "production_extraction_id",
    "scope_id",
    "accounting_completion_sha256",
    "index_completion_sha256",
    "resolution_completion_sha256",
    "blocking_policy_sha256",
    "status",
    "blocking_reasons_sha256",
    "task04_status",
    "managed_inventory_sha256",
)
PRODUCTION_PREIMAGE_FIELDS = (
    "schema_version",
    "contract_revision",
    "extraction_version_name",
    "production_scope",
    "producer_contract",
    "canonical_contract",
    "hierarchy_contract",
    "cross_reference_contract",
    "corpus_workflow_contract",
)
PRODUCTION_CONTRACT_SECTIONS = (
    "producer_contract",
    "canonical_contract",
    "hierarchy_contract",
    "cross_reference_contract",
    "corpus_workflow_contract",
)
ProductionScopeKind = Literal[
    "fixture",
    "engineering_smoke",
    "representative_pilot",
    "production_full",
]
PRODUCTION_IDENTITY_PROFILES: dict[str, tuple[str, int, frozenset[ProductionScopeKind]]] = {
    "task_03g1a_remediation_v1": (
        "brisbane_baylands_model_corpus_v1",
        35,
        frozenset({"fixture", "engineering_smoke", "production_full"}),
    ),
    "task_03g2_representative_pilot_v1": (
        "brisbane_baylands_representative_pilot_v1",
        3,
        frozenset({"fixture", "representative_pilot"}),
    ),
}


def build_index_id(preimage: JsonObject) -> str:
    """Derive `idxv1-` from the exact closed target-index preimage."""
    return _build_typed_id(
        "idxv1",
        preimage,
        fields=INDEX_PREIMAGE_FIELDS,
        schema_version="er_commons.corpus_target_index_identity.v1_1",
    )


def validate_index_id(index_id: str, preimage: JsonObject) -> DerivedIdentity:
    """Require a persisted index identity to derive from its exact preimage."""
    return _validate_typed_id(index_id, build_index_id(preimage), preimage, "index_identity")


def build_resolution_id(preimage: JsonObject) -> str:
    """Derive `resv1-` from the exact closed corpus-resolution preimage."""
    return _build_typed_id(
        "resv1",
        preimage,
        fields=RESOLUTION_PREIMAGE_FIELDS,
        schema_version="er_commons.corpus_resolution_identity.v1_1",
    )


def validate_resolution_id(resolution_id: str, preimage: JsonObject) -> DerivedIdentity:
    """Require a persisted resolution identity to derive from its exact preimage."""
    return _validate_typed_id(
        resolution_id,
        build_resolution_id(preimage),
        preimage,
        "resolution_identity",
    )


def build_handoff_id(preimage: JsonObject) -> str:
    """Derive `handoffv1-` from the exact closed candidate-handoff preimage."""
    return _build_typed_id(
        "handoffv1",
        preimage,
        fields=HANDOFF_PREIMAGE_FIELDS,
        schema_version="er_commons.candidate_handoff_identity.v1_1",
    )


def validate_handoff_id(handoff_id: str, preimage: JsonObject) -> DerivedIdentity:
    """Require a persisted handoff identity to derive from its exact preimage."""
    return _validate_typed_id(
        handoff_id,
        build_handoff_id(preimage),
        preimage,
        "handoff_identity",
    )


def validate_production_identity(
    record: JsonObject,
    *,
    expected_source_ids: list[str] | None = None,
    expected_scope: JsonObject | None = None,
    expected_scope_kind: ProductionScopeKind | None = None,
    project_root: Path | None = None,
) -> DerivedIdentity:
    """Verify the refreshed non-execution recipe and all checked references."""
    if (
        record.get("record_type") != "production_identity"
        or record.get("schema_version") != "er_commons.corpus_extraction_identity.v1_1"
    ):
        fail("identity_schema", "production identity uses the wrong v1.1 record schema")
    if (
        record.get("fixture_status") != "identity_recipe"
        or record.get("execution_status") != "not_executed"
    ):
        fail("identity_status", "production identity recipe cannot make an execution claim")
    preimage = _require_object(record, "preimage", code="identity_preimage")
    _require_closed_fields(preimage, PRODUCTION_PREIMAGE_FIELDS, code="identity_preimage")
    if preimage["schema_version"] != "er_commons.corpus_extraction_identity_preimage.v1_1":
        fail("identity_preimage", "production identity uses the wrong v1.1 preimage schema")
    revision = preimage["contract_revision"]
    if not isinstance(revision, str):
        fail("identity_preimage", "production identity contract revision must be a string")
    profile = PRODUCTION_IDENTITY_PROFILES.get(revision)
    if profile is None:
        fail("identity_preimage", "production identity uses an unsupported contract revision")
    version_name, source_count, allowed_scope_kinds = profile
    if preimage["extraction_version_name"] != version_name:
        fail("identity_preimage", "production identity uses an unexpected extraction version")
    if expected_scope_kind is not None and expected_scope_kind not in allowed_scope_kinds:
        fail(
            "production_scope",
            "production identity profile does not authorize the selected run scope kind",
        )
    digest = canonical_sha256(preimage)
    extraction_id = f"exv1-{digest}"
    if record.get("identity_sha256") != digest or record.get("extraction_id") != extraction_id:
        fail("identity_digest", "production identity does not derive from its preimage")

    scope = _require_object(preimage, "production_scope", code="production_scope")
    source_ids = scope.get("ordered_source_ids")
    if (
        not isinstance(source_ids, list)
        or not all(isinstance(source_id, str) for source_id in source_ids)
        or len(source_ids) != source_count
        or len(set(source_ids)) != len(source_ids)
    ):
        fail(
            "production_scope",
            f"production identity profile must contain {source_count} unique sources",
        )
    if expected_source_ids is not None and source_ids != expected_source_ids:
        fail("production_scope", "production source order differs from sealed evidence")
    if expected_scope is not None:
        _validate_scope_evidence(scope, expected_scope)
    if project_root is not None:
        _validate_referenced_artifacts(preimage, project_root)
    return DerivedIdentity(extraction_id, preimage)


def _build_typed_id(
    prefix: str,
    preimage: JsonObject,
    *,
    fields: tuple[str, ...],
    schema_version: str,
) -> str:
    _require_closed_fields(preimage, fields, code=f"{prefix}_preimage")
    if preimage["schema_version"] != schema_version:
        fail(f"{prefix}_preimage", f"unexpected identity schema: {preimage['schema_version']}")
    return f"{prefix}-{canonical_sha256(preimage)}"


def _validate_typed_id(
    observed: str,
    expected: str,
    preimage: JsonObject,
    code: str,
) -> DerivedIdentity:
    if observed != expected:
        fail(code, "typed identity does not derive from its exact preimage")
    return DerivedIdentity(expected, preimage)


def _require_closed_fields(value: JsonObject, fields: tuple[str, ...], *, code: str) -> None:
    expected = set(fields)
    observed = set(value)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        fail(code, f"identity preimage fields differ: missing={missing}, extra={extra}")


def _require_object(value: JsonObject, field: str, *, code: str) -> JsonObject:
    observed = value.get(field)
    if not isinstance(observed, dict):
        fail(code, f"{field} must be an object")
    return observed


def _validate_scope_evidence(scope: JsonObject, evidence: JsonObject) -> None:
    observed = {
        "source_release_version": scope.get("source_release_version"),
        "source_manifest_sha256": _artifact_sha(scope, "source_manifest"),
        "release_completion_sha256": _artifact_sha(scope, "release_completion"),
        "ordered_source_records_sha256": scope.get("ordered_source_records_sha256"),
    }
    if observed != evidence:
        fail("production_scope", "production scope differs from checked evidence")


def _artifact_sha(container: JsonObject, field: str) -> Any:
    reference = container.get(field)
    return reference.get("sha256") if isinstance(reference, dict) else None


def _validate_referenced_artifacts(preimage: JsonObject, project_root: Path) -> None:
    root = project_root.resolve()
    for section_name in PRODUCTION_CONTRACT_SECTIONS:
        section = _require_object(preimage, section_name, code="identity_artifact")
        for collection in ("artifacts", "owned_code"):
            references = section.get(collection)
            if not isinstance(references, list) or not references:
                fail("identity_artifact", f"{section_name}.{collection} must be non-empty")
            for reference in references:
                _validate_artifact_reference(reference, root)


def _validate_artifact_reference(reference: Any, root: Path) -> None:
    if not isinstance(reference, dict) or set(reference) != {
        "path",
        "sha256",
        "byte_size",
    }:
        fail("identity_artifact", "production artifact reference is not closed")
    relative_path = reference["path"]
    if not isinstance(relative_path, str):
        fail("identity_artifact", "production artifact path must be a string")
    path = (root / relative_path).resolve()
    if (
        not path.is_relative_to(root)
        or not path.is_file()
        or path.stat().st_size != reference["byte_size"]
        or bytes_sha256(path.read_bytes()) != reference["sha256"]
    ):
        fail(
            "identity_artifact",
            "identity artifact differs from checked bytes",
            subject=relative_path,
        )
