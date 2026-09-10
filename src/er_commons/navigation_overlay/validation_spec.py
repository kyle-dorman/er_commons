"""Explicit regression populations and context for document relink audits."""

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NavigationControl(BaseModel):
    """Expected result counts for a disjoint, named population."""

    model_config = ConfigDict(extra="forbid", strict=True)
    population: int = Field(ge=0)
    resolved: int = Field(ge=0)

    @model_validator(mode="after")
    def require_subset(self) -> "NavigationControl":
        """A resolved population cannot exceed its full population."""
        if self.resolved > self.population:
            raise ValueError("resolved count exceeds population")
        return self


class RelinkValidationSpec(BaseModel):
    """Select regression evidence without silently choosing a corpus or pass."""

    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal["er_commons.document_relink_validation.v1"]
    expected_source_count: int = Field(ge=1)
    reviewed_source_ids: list[str]
    context_entries: list[dict[str, Any]]
    parent_relations: list[dict[str, Any]]
    navigation_controls: dict[str, NavigationControl]
    primary_rule_counts: dict[str, int]
    expected_baseline_count: int = Field(ge=0)

    @model_validator(mode="after")
    def require_consistent_population(self) -> "RelinkValidationSpec":
        """Reject duplicate selection and impossible regression count claims."""
        if len(set(self.reviewed_source_ids)) != len(self.reviewed_source_ids):
            raise ValueError("reviewed source selection contains duplicates")
        if not self.navigation_controls or any(n < 0 for n in self.primary_rule_counts.values()):
            raise ValueError("regression populations must be explicit and nonnegative")
        if sum(self.primary_rule_counts.values()) != sum(
            control.resolved for control in self.navigation_controls.values()
        ):
            raise ValueError("primary rule counts differ from resolved population")
        return self


def load_validation_spec(path: Path) -> dict[str, Any]:
    """Read one bounded current request; accepted payloads are not accessed here."""
    if path.stat().st_size > 1024 * 1024:
        raise ValueError(f"role=validation_spec path={path}: exceeds 1 MiB request limit")
    return RelinkValidationSpec.model_validate_json(path.read_bytes()).model_dump()
