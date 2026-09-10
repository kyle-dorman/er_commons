"""Explicit immutable input contracts for source-free navigation publications."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _Bindings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PreparationBindings(_Bindings):
    """Accepted identities and population assertions for this invocation."""

    production_extraction_id: str
    scope_id: str
    handoff_id: str
    task04a_review_id: str
    task04a_gate_a_id: str
    expected_source_count: int = Field(ge=0)
    expected_census_page_count: int = Field(ge=0)
    expected_decision_count: int = Field(ge=0)
    expected_decision_counts: dict[str, int]
    expected_ambiguous_link_count: int = Field(ge=0)


class MaterializationBindings(_Bindings):
    """Accepted identities and population assertions for this invocation."""

    accepted_gate_a_id: str
    expected_decision_count: int = Field(ge=0)
    expected_accounting: dict[str, int]


class ReconciliationBindings(_Bindings):
    """Accepted identities and population assertions for this invocation."""

    accepted_gate_a_id: str
    accepted_gate_b_id: str
    expected_source_count: int = Field(ge=0)
    expected_ambiguity_count: int = Field(ge=0)
    expected_table_count: int = Field(ge=0)
    expected_entry_count: int = Field(ge=0)
