"""Closed production identity for a pinned-input collection publication."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.authority_reference import AuthorityReference
from er_commons.collection_processing.contract import JsonObject, canonical_sha256

_COLLECTION_NAMESPACE_PREFIX = "pipelines/brisbane_baylands/task_06_recovery_v1/06g"
V33_COLLECTION_OUTPUT_NAMESPACE = f"{_COLLECTION_NAMESPACE_PREFIX}/replay_v33/document_publications"
V34_COLLECTION_OUTPUT_NAMESPACE = f"{_COLLECTION_NAMESPACE_PREFIX}/replay_v34/document_publications"
V35_COLLECTION_OUTPUT_NAMESPACE = f"{_COLLECTION_NAMESPACE_PREFIX}/replay_v35/document_publications"
V36_COLLECTION_OUTPUT_NAMESPACE = f"{_COLLECTION_NAMESPACE_PREFIX}/replay_v36/document_publications"
V37_COLLECTION_OUTPUT_NAMESPACE = f"{_COLLECTION_NAMESPACE_PREFIX}/replay_v37/document_publications"
V38_COLLECTION_OUTPUT_NAMESPACE = f"{_COLLECTION_NAMESPACE_PREFIX}/replay_v38/document_publications"
COLLECTION_OUTPUT_NAMESPACES = frozenset(
    {
        V33_COLLECTION_OUTPUT_NAMESPACE,
        V34_COLLECTION_OUTPUT_NAMESPACE,
        V35_COLLECTION_OUTPUT_NAMESPACE,
        V36_COLLECTION_OUTPUT_NAMESPACE,
        V37_COLLECTION_OUTPUT_NAMESPACE,
        V38_COLLECTION_OUTPUT_NAMESPACE,
    }
)


class CollectionProductionIdentityPreimage(BaseModel):
    """Every byte and namespace that can affect the collection-only product."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["er_commons.collection_production_identity_preimage.v1"]
    generation_ref: AuthorityReference
    collection_template_ref: AuthorityReference
    collection_schema_ref: AuthorityReference
    owned_code_refs: tuple[AuthorityReference, ...] = Field(min_length=1)
    imported_selection_ref: AuthorityReference
    imported_selection_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_catalog_ref: AuthorityReference
    source_policy_refs: tuple[AuthorityReference, ...] = Field(min_length=1)
    output_namespace: str = Field(min_length=1)

    @model_validator(mode="after")
    def require_authorities_order_and_accepted_namespace(self) -> Self:
        """Reject ambiguous authority, ordering, or output-root representations."""
        repository_refs = (
            self.generation_ref,
            self.collection_template_ref,
            self.collection_schema_ref,
            *self.owned_code_refs,
            *self.source_policy_refs,
        )
        if any(item.authority != "repository" for item in repository_refs):
            raise ValueError(
                "collection production recipe references must use repository authority"
            )
        if self.imported_selection_ref.authority != "artifact_root":
            raise ValueError("imported selection must use artifact_root authority")
        if self.source_catalog_ref.authority != "artifact_root":
            raise ValueError("source catalog must use artifact_root authority")
        if self.imported_selection_sha256 != self.imported_selection_ref.sha256:
            raise ValueError("imported selection digest differs from its exact reference")
        self._require_unique_sorted(self.owned_code_refs, "owned code")
        self._require_unique_sorted(self.source_policy_refs, "source policy")
        if any(Path(item.path).suffix != ".py" for item in self.owned_code_refs):
            raise ValueError("collection production owned code references must be Python files")
        json_refs = (
            self.generation_ref,
            self.collection_template_ref,
            self.collection_schema_ref,
            self.imported_selection_ref,
            self.source_catalog_ref,
            *self.source_policy_refs,
        )
        if any(Path(item.path).suffix != ".json" for item in json_refs):
            raise ValueError("collection production control references must be JSON files")
        all_refs = (
            self.generation_ref,
            self.collection_template_ref,
            self.collection_schema_ref,
            *self.owned_code_refs,
            self.imported_selection_ref,
            self.source_catalog_ref,
            *self.source_policy_refs,
        )
        selected_paths = [(item.authority, item.path) for item in all_refs]
        if len(selected_paths) != len(set(selected_paths)):
            raise ValueError("collection production roles must bind distinct references")
        namespace = PurePosixPath(self.output_namespace)
        if (
            namespace.is_absolute()
            or namespace == PurePosixPath(".")
            or ".." in namespace.parts
            or "\\" in self.output_namespace
            or namespace.as_posix() != self.output_namespace
            or self.output_namespace not in COLLECTION_OUTPUT_NAMESPACES
        ):
            raise ValueError(
                "collection production output namespace is not a frozen "
                "replay_v33/v34/v35/v36/v37/v38 root"
            )
        return self

    @staticmethod
    def _require_unique_sorted(values: tuple[AuthorityReference, ...], label: str) -> None:
        paths = [item.path for item in values]
        if len(paths) != len(set(paths)):
            raise ValueError(f"collection production {label} references repeat a path")
        if paths != sorted(paths):
            raise ValueError(f"collection production {label} references are not sorted")


class CollectionProductionIdentity(BaseModel):
    """A deterministic cprodv1 identity and its complete unexecuted preimage."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_type: Literal["collection_production_identity"]
    schema_version: Literal["er_commons.collection_production_identity.v1"]
    execution_status: Literal["not_executed"]
    collection_production_id: str = Field(pattern=r"^cprodv1-[0-9a-f]{64}$")
    identity_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    preimage: CollectionProductionIdentityPreimage

    @model_validator(mode="after")
    def require_derived_identity(self) -> Self:
        """Require the ID and digest to derive only from the RFC 8785 preimage."""
        digest = canonical_sha256(self.preimage.model_dump(mode="json"))
        if self.identity_sha256 != digest or self.collection_production_id != f"cprodv1-{digest}":
            raise ValueError("collection production identity does not derive from its preimage")
        return self


def build_collection_production_identity(
    preimage: CollectionProductionIdentityPreimage | JsonObject,
) -> JsonObject:
    """Derive one deterministic unexecuted identity from a strict closed preimage."""
    validated = (
        preimage
        if isinstance(preimage, CollectionProductionIdentityPreimage)
        else CollectionProductionIdentityPreimage.model_validate(preimage)
    )
    rendered = validated.model_dump(mode="json")
    digest = canonical_sha256(rendered)
    return CollectionProductionIdentity(
        record_type="collection_production_identity",
        schema_version="er_commons.collection_production_identity.v1",
        execution_status="not_executed",
        collection_production_id=f"cprodv1-{digest}",
        identity_sha256=digest,
        preimage=validated,
    ).model_dump(mode="json")


def validate_collection_production_identity(
    record: JsonObject,
    *,
    repository_root: Path,
    artifact_root: Path,
    expected_imported_selection_ref: AuthorityReference | JsonObject | None = None,
    expected_output_namespace: str | None = None,
) -> CollectionProductionIdentity:
    """Validate derivation, exact caller expectations, and every referenced byte."""
    identity = CollectionProductionIdentity.model_validate(record)
    preimage = identity.preimage
    if expected_imported_selection_ref is not None:
        expected = (
            expected_imported_selection_ref
            if isinstance(expected_imported_selection_ref, AuthorityReference)
            else AuthorityReference.model_validate(expected_imported_selection_ref)
        )
        if preimage.imported_selection_ref != expected:
            raise ValueError("collection production imported selection differs")
    if (
        expected_output_namespace is not None
        and preimage.output_namespace != expected_output_namespace
    ):
        raise ValueError("collection production output namespace differs")
    references = (
        preimage.generation_ref,
        preimage.collection_template_ref,
        preimage.collection_schema_ref,
        *preimage.owned_code_refs,
        preimage.imported_selection_ref,
        preimage.source_catalog_ref,
        *preimage.source_policy_refs,
    )
    for item in references:
        item.resolve(repository_root=repository_root, artifact_root=artifact_root)
    output = artifact_root.resolve().joinpath(*PurePosixPath(preimage.output_namespace).parts)
    if not output.is_relative_to(artifact_root.resolve()):
        raise ValueError("collection production output namespace escapes artifact root")
    return identity


__all__ = [
    "CollectionProductionIdentity",
    "CollectionProductionIdentityPreimage",
    "V33_COLLECTION_OUTPUT_NAMESPACE",
    "V34_COLLECTION_OUTPUT_NAMESPACE",
    "V35_COLLECTION_OUTPUT_NAMESPACE",
    "V36_COLLECTION_OUTPUT_NAMESPACE",
    "V37_COLLECTION_OUTPUT_NAMESPACE",
    "V38_COLLECTION_OUTPUT_NAMESPACE",
    "build_collection_production_identity",
    "validate_collection_production_identity",
]
