"""Native v2 production identity validation for document publication."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from er_commons.artifact_io import sha256_file
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
) -> ProductionIdentity:
    """Verify the native v2 recipe, source scope, and optional code references."""
    if record.get("record_type") != "production_identity":
        raise ValueError("document production identity has the wrong record type")
    if record.get("schema_version") != "er_commons.document_publication_identity.v2":
        raise ValueError("document production identity schema is not v2")
    if (
        record.get("fixture_status") != "identity_recipe"
        or record.get("execution_status") != "not_executed"
    ):
        raise ValueError("document production identity cannot make an execution claim")
    preimage = _object(record, "preimage")
    if set(preimage) != PREIMAGE_FIELDS:
        raise ValueError("document production identity preimage fields differ")
    if preimage.get("schema_version") != "er_commons.document_publication_identity_preimage.v2":
        raise ValueError("document production identity preimage schema is not v2")
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
    if project_root is not None:
        _verify_contract_references(preimage, project_root)
    return ProductionIdentity(extraction_id, preimage)


def _verify_contract_references(preimage: JsonObject, project_root: Path) -> None:
    root = project_root.resolve()
    for section_name in CONTRACT_SECTIONS:
        section = _object(preimage, section_name)
        for collection in ("artifacts", "owned_code"):
            references = section.get(collection)
            if not isinstance(references, list) or not references:
                raise ValueError(f"{section_name}.{collection} must be non-empty")
            for reference in references:
                _verify_reference(reference, root)


def _verify_reference(reference: object, root: Path) -> None:
    if not isinstance(reference, dict) or set(reference) != {"path", "sha256", "byte_size"}:
        raise ValueError("document production artifact reference is not closed")
    relative = reference.get("path")
    if not isinstance(relative, str):
        raise ValueError("document production artifact path must be a string")
    path = (root / relative).resolve()
    if (
        not path.is_relative_to(root)
        or not path.is_file()
        or path.stat().st_size != reference.get("byte_size")
        or sha256_file(path) != reference.get("sha256")
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
