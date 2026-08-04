"""Exact manifest-ordered scope accounting."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from er_commons.corpus_extraction.outcomes import DocumentTerminalEvidence
from er_commons.corpus_extraction_contract_v1_1.model import JsonObject
from er_commons.corpus_resolution.domain import StageBuild, StageName
from er_commons.corpus_resolution.storage import inventory_ref, jsonl_bytes


@dataclass(frozen=True)
class AccountingInputs:
    """Identity and terminal evidence required for scope accounting."""

    scope_id: str
    scope_kind: str
    production_extraction_id: str
    evidence: tuple[DocumentTerminalEvidence, ...]


class AccountingBuilder:
    """Build exactly one terminal row for every declared source."""

    def build(self, inputs: AccountingInputs) -> StageBuild:
        """Return deterministic accounting bytes ready for publication."""
        rows = [self._row(item) for item in inputs.evidence]
        counts = Counter(row["terminal_state"] for row in rows)
        payloads = {"accounting_rows.jsonl": jsonl_bytes(rows)}
        final_relative = f"scopes/{inputs.scope_id}/accounting/{inputs.scope_id}"
        completion: JsonObject = {
            "record_type": "scope_accounting",
            "schema_version": "er_commons.scope_accounting.v1_1",
            "scope_id": inputs.scope_id,
            "scope_kind": inputs.scope_kind,
            "production_extraction_id": inputs.production_extraction_id,
            "ordered_sources": [item.source for item in inputs.evidence],
            "rows": rows,
            "counts": {
                "total": len(rows),
                "complete": counts["complete"],
                "complete_with_warnings": counts["complete_with_warnings"],
                "failed_terminal": counts["failed_terminal"],
            },
            "artifact_inventory": inventory_ref(final_relative, payloads),
            "completion_last": True,
            "status": "complete",
        }
        return StageBuild(StageName.ACCOUNTING, inputs.scope_id, payloads, completion)

    @staticmethod
    def _row(item: DocumentTerminalEvidence) -> JsonObject:
        return {
            "source_id": item.source["source_id"],
            "source_ordinal": item.source_ordinal,
            "terminal_state": item.disposition,
            "transaction_id": item.transaction_id,
            "attempt": item.attempt,
            "terminal_event_ref": item.terminal_event_ref,
            "attempt_record_ref": item.attempt_record_ref,
            "candidate_id": item.candidate_id,
            "document_completion_ref": item.document_completion_ref,
            "candidate_inventory_ref": item.candidate_inventory_ref,
            "failure_class": item.failure_class,
            "retained_evidence_refs": list(item.retained_evidence_refs),
        }
