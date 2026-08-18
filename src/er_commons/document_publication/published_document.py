"""Narrow document evidence types consumed by publication and collections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from er_commons.document_publication.records import JsonObject


class ProducerLineage(BaseModel):
    """Code-bound parser IDs available without converting a source PDF."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    baseline: str = Field(pattern=r"^prv1-[0-9a-f]{64}$")
    hierarchy: str = Field(pattern=r"^prv1-[0-9a-f]{64}$")


TerminalDisposition = Literal["complete", "complete_with_warnings", "failed_terminal"]


@dataclass(frozen=True)
class DocumentTerminalEvidence:
    """One checksum-verified terminal document outcome for collection processing."""

    source: JsonObject
    source_ordinal: int
    evidence_kind: Literal["document_attempt", "downstream_replay"]
    transaction_id: str
    attempt: int | None
    disposition: TerminalDisposition
    terminal_event_ref: JsonObject | None
    attempt_record_ref: JsonObject | None
    downstream_replay_ref: JsonObject | None
    failure_class: str | None
    retained_evidence_refs: tuple[JsonObject, ...]
    candidate_id: str | None = None
    document_completion_ref: JsonObject | None = None
    candidate_inventory_ref: JsonObject | None = None
    cross_references_ref: JsonObject | None = None
    target_aliases_ref: JsonObject | None = None
    target_records_refs: tuple[JsonObject, ...] = ()


__all__ = ["DocumentTerminalEvidence", "ProducerLineage", "TerminalDisposition"]
