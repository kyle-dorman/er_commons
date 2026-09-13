"""Explicit source-free inputs and future output names for relink preparation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

from er_commons.artifact_verification import VerificationBudget


class RelinkPreparationSpec(BaseModel):
    """No production fallback, discovery, or inherited current-code inventory."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    repo_root: Path
    data_root: Path
    reviewed_descriptor: Path
    runtime_spec_authority: Literal["repository", "artifact_root"] = "repository"
    output_authority: Literal["repository", "artifact_root"] = "repository"
    base_identity: Path
    base_document_spec: Path
    base_collection_spec: Path
    production_identity: Path
    document_spec: Path
    link_spec: Path
    collection_spec: Path
    collection_schema: Path
    document_schema: Path
    production_identity_schema: Path
    replacement_scope: dict[str, Any] | None = None
    link_schema_root: Path
    source_catalog: Path
    document_artifact_root: Path
    link_artifact_root: Path
    document_roots: dict[str, Path]
    scope_root: Path
    handoff_root: Path
    linking_policy: Path
    contract_revision: str
    extraction_version_name: str
    document_contract_version: str
    collection_contract_version: str
    document_artifacts: list[Path]
    document_owned_code: list[Path]
    collection_artifacts: list[Path]
    collection_owned_code: list[Path]

    @model_validator(mode="after")
    def validate_references(self) -> Self:
        """Contain paths, reject checksum cycles, and keep input recipes immutable."""
        roots = {"repo_root", "data_root", "reviewed_descriptor"}
        for name in type(self).model_fields:
            if name in roots:
                continue
            value = getattr(self, name)
            paths = (
                value.values()
                if isinstance(value, dict)
                else value
                if isinstance(value, list)
                else [value]
            )
            for item in paths:
                if isinstance(item, Path) and (
                    item.is_absolute() or ".." in item.parts or item == Path(".")
                ):
                    raise ValueError(f"{name} must contain relative contained paths")
        outputs = {
            self.production_identity,
            self.document_spec,
            self.collection_spec,
            self.link_spec,
        }
        inputs = {self.base_identity, self.base_document_spec, self.base_collection_spec}
        if len(outputs) != 4 or outputs & inputs:
            raise ValueError("four distinct future outputs must preserve all input recipes")
        if outputs & set(self.document_artifacts + self.collection_artifacts):
            raise ValueError("generated outputs cannot enter input artifact inventories")
        if not self.document_roots:
            raise ValueError("explicit accepted document bindings are required")
        for inventory in (
            self.document_artifacts,
            self.document_owned_code,
            self.collection_artifacts,
            self.collection_owned_code,
        ):
            if not inventory or len(inventory) != len(set(inventory)):
                raise ValueError("behavior inventories must be nonempty and unique")
        return self


def load_preparation_spec(
    path: Path, *, budget: VerificationBudget | None = None
) -> RelinkPreparationSpec:
    """Resolve environment roots relative to the explicit JSON specification."""
    budget = budget if budget is not None else VerificationBudget()
    spec = RelinkPreparationSpec.model_validate(
        budget.read_json(
            path, root=path.resolve().parent, role="config", source_id="relink_preparation"
        )
    )
    return spec.model_copy(
        update={
            name: (path.resolve().parent / getattr(spec, name)).resolve()
            for name in ("repo_root", "data_root", "reviewed_descriptor")
        }
    )
