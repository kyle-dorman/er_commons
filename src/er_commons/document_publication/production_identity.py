"""Native v2 production identity validation for document publication."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from er_commons.artifact_io import sha256_file
from er_commons.artifact_verification import VerificationBudget
from er_commons.document_publication.identity import canonical_digest
from er_commons.document_publication.records import JsonObject

ProductionScopeKind = Literal[
    "fixture",
    "engineering_smoke",
    "representative_pilot",
    "production_full",
]
PREIMAGE_FIELDS = frozenset(
    {
        "schema_version",
        "contract_revision",
        "extraction_version_name",
        "production_scope",
        "document_process_contract",
        "collection_process_contract",
    }
)
CONTRACT_SECTIONS = ("document_process_contract", "collection_process_contract")


@dataclass(frozen=True)
class ProductionIdentity:
    """One verified extraction identity and its closed v2 preimage."""

    value: str
    preimage: JsonObject


def validate_production_identity(
    record: JsonObject,
    *,
    expected_source_ids: list[str] | None = None,
    expected_scope: JsonObject | None = None,
    expected_scope_kind: ProductionScopeKind | None = None,
    project_root: Path | None = None,
    artifact_root: Path | None = None,
    budget: VerificationBudget | None = None,
) -> ProductionIdentity:
    """Verify the native v2 recipe, source scope, and optional code references."""
    if record.get("record_type") != "production_identity":
        raise ValueError("document production identity has the wrong record type")
    schema_version = record.get("schema_version")
    if schema_version not in {
        "er_commons.document_publication_identity.v2",
        "er_commons.document_publication_identity.v3",
    }:
        raise ValueError("document production identity schema is not v2 or v3")
    if (
        record.get("fixture_status") != "identity_recipe"
        or record.get("execution_status") != "not_executed"
    ):
        raise ValueError("document production identity cannot make an execution claim")
    preimage = _object(record, "preimage")
    if set(preimage) != PREIMAGE_FIELDS:
        raise ValueError("document production identity preimage fields differ")
    expected_preimage_version = str(schema_version).replace("_identity.v", "_identity_preimage.v")
    if preimage.get("schema_version") != expected_preimage_version:
        raise ValueError("document production identity preimage schema differs")
    digest = canonical_digest(preimage)
    extraction_id = f"exv1-{digest}"
    if record.get("identity_sha256") != digest or record.get("extraction_id") != extraction_id:
        raise ValueError("document production identity does not derive from its preimage")

    scope = _object(preimage, "production_scope")
    source_ids = scope.get("ordered_source_ids")
    if (
        not isinstance(source_ids, list)
        or not source_ids
        or not all(isinstance(source_id, str) for source_id in source_ids)
        or len(source_ids) != len(set(source_ids))
    ):
        raise ValueError("document production scope must contain unique ordered sources")
    if expected_source_ids is not None and source_ids != expected_source_ids:
        raise ValueError("document production source order differs from sealed evidence")
    allowed_scope_kinds = scope.get("allowed_scope_kinds")
    if (
        expected_scope_kind is not None
        and isinstance(allowed_scope_kinds, list)
        and expected_scope_kind not in allowed_scope_kinds
    ):
        raise ValueError("document production identity does not authorize the run scope")
    if expected_scope is not None:
        observed_scope = {
            "source_release_version": scope.get("source_release_version"),
            "source_manifest_sha256": _artifact_sha(scope, "source_manifest"),
            "release_completion_sha256": _artifact_sha(scope, "release_completion"),
            "ordered_source_records_sha256": scope.get("ordered_source_records_sha256"),
        }
        if observed_scope != expected_scope:
            raise ValueError("document production scope differs from checked evidence")
    _validate_contract_shapes(preimage, authority_required=schema_version.endswith(".v3"))
    if project_root is not None:
        _verify_contract_references(
            preimage, project_root, artifact_root=artifact_root, budget=budget
        )
    return ProductionIdentity(extraction_id, preimage)


def _validate_contract_shapes(preimage: JsonObject, *, authority_required: bool) -> None:
    """Validate historical contract records without consulting today's paths."""
    for section_name in CONTRACT_SECTIONS:
        section = _object(preimage, section_name)
        if set(section) != {"version", "artifacts", "owned_code"}:
            raise ValueError(f"document production contract fields differ: {section_name}")
        if not isinstance(section["version"], str) or not section["version"]:
            raise ValueError(f"document production contract version is missing: {section_name}")
        for collection in ("artifacts", "owned_code"):
            references = section[collection]
            if not isinstance(references, list):
                raise ValueError(f"{section_name}.{collection} must be a list")
            for reference in references:
                _validate_reference_shape(reference, authority_required=authority_required)


def _validate_reference_shape(reference: object, *, authority_required: bool = False) -> JsonObject:
    """Require a portable closed byte reference independently of file availability."""
    fields = (
        {"path", "sha256", "byte_size", "authority"}
        if authority_required
        else {
            "path",
            "sha256",
            "byte_size",
        }
    )
    if not isinstance(reference, dict) or set(reference) != fields:
        raise ValueError("document production artifact reference is not closed")
    if authority_required and reference.get("authority") not in {"repository", "artifact_root"}:
        raise ValueError("document production artifact authority is invalid")
    relative = reference["path"]
    if (
        not isinstance(relative, str)
        or not relative
        or Path(relative).is_absolute()
        or ".." in Path(relative).parts
        or Path(relative) == Path(".")
    ):
        raise ValueError("document production artifact path must be a contained relative path")
    digest = reference["sha256"]
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError("document production artifact digest must be SHA-256")
    size = reference["byte_size"]
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise ValueError("document production artifact size must be a nonnegative integer")
    return reference


def _verify_contract_references(
    preimage: JsonObject,
    project_root: Path,
    *,
    artifact_root: Path | None = None,
    budget: VerificationBudget | None = None,
) -> None:
    """Verify current writer files only after the recorded recipe shape is valid."""
    root = project_root.resolve()
    for section_name in CONTRACT_SECTIONS:
        section = _object(preimage, section_name)
        for collection in ("artifacts", "owned_code"):
            references = section.get(collection)
            if not isinstance(references, list) or not references:
                raise ValueError(f"{section_name}.{collection} must be non-empty")
            for reference in references:
                _verify_reference(
                    reference,
                    root,
                    artifact_root=artifact_root,
                    budget=budget,
                    role="code" if collection == "owned_code" else "config",
                )


def _verify_reference(
    reference: object,
    root: Path,
    *,
    artifact_root: Path | None = None,
    budget: VerificationBudget | None = None,
    role: str = "config",
) -> None:
    """Match one current repository file to its already validated byte reference."""
    authority_required = isinstance(reference, dict) and "authority" in reference
    reference = _validate_reference_shape(reference, authority_required=authority_required)
    if reference.get("authority") == "artifact_root":
        if artifact_root is None:
            raise ValueError("artifact-root production reference lacks its declared root")
        root = artifact_root.resolve()
    relative = str(reference["path"])
    path = (root / relative).resolve()
    if (
        not path.is_relative_to(root)
        or not path.is_file()
        or path.stat().st_size != reference.get("byte_size")
        or (
            budget.hash_file(path, role=role, source_id="production_recipe", root=root)
            if budget is not None
            else sha256_file(path)
        )
        != reference.get("sha256")
    ):
        raise ValueError(f"document production artifact differs: {relative}")


def _object(value: JsonObject, field: str) -> JsonObject:
    observed = value.get(field)
    if not isinstance(observed, dict):
        raise ValueError(f"document production identity field must be an object: {field}")
    return observed


def _artifact_sha(container: JsonObject, field: str) -> Any:
    reference = container.get(field)
    return reference.get("sha256") if isinstance(reference, dict) else None


__all__ = ["ProductionIdentity", "ProductionScopeKind", "validate_production_identity"]
