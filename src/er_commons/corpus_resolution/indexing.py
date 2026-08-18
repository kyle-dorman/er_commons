"""Deterministic corpus target index and unavailable-source catalog."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.corpus_extraction.outcomes import DocumentTerminalEvidence
from er_commons.corpus_extraction_contract_v1_1.checks import canonical_sha256
from er_commons.corpus_extraction_contract_v1_1.identity import build_index_id
from er_commons.corpus_extraction_contract_v1_1.model import JsonObject
from er_commons.corpus_resolution.document_targets import build_document_targets
from er_commons.corpus_resolution.domain import PublishedStage, StageBuild, StageName
from er_commons.corpus_resolution.storage import (
    bytes_ref,
    inventory_ref,
    json_bytes,
    jsonl_bytes,
    read_jsonl,
)


@dataclass(frozen=True)
class TargetIndexInputs:
    """Verified upstream evidence and controls for one corpus index."""

    extraction_root: Path
    production_extraction_id: str
    scope_id: str
    accounting: JsonObject
    accounting_stage: PublishedStage
    evidence: tuple[DocumentTerminalEvidence, ...]
    ordering_policy_version: str
    target_policy_sha256: str


class TargetIndexBuilder:
    """Aggregate verified candidate aliases without changing stage-one bytes."""

    def build(self, inputs: TargetIndexInputs) -> StageBuild:
        """Build the sealed index and retained unavailable-source evidence."""
        eligible = [
            self._eligible(item) for item in inputs.evidence if item.candidate_id is not None
        ]
        unavailable = [
            self._unavailable(item) for item in inputs.evidence if item.candidate_id is None
        ]
        entries = self._entries(inputs.evidence, inputs.extraction_root)
        document_targets = build_document_targets(inputs.evidence, inputs.extraction_root)
        semantic_payloads = {
            "unavailable_sources.jsonl": jsonl_bytes(unavailable),
            "target_index.jsonl": jsonl_bytes(entries),
            "document_targets.jsonl": jsonl_bytes(document_targets),
        }
        preimage = self._identity_preimage(
            inputs,
            eligible,
            semantic_payloads,
            len(entries),
            len(document_targets),
        )
        index_id = build_index_id(preimage)
        final_relative = f"scopes/{inputs.scope_id}/target_indexes/{index_id}"
        payloads = {
            **semantic_payloads,
            "records/identity_preimage.json": json_bytes(preimage),
        }
        refs = {
            name: bytes_ref(f"{final_relative}/{name}", value) for name, value in payloads.items()
        }
        completion: JsonObject = {
            "record_type": "target_index_completion",
            "schema_version": "er_commons.target_index_completion.v1_1",
            "index_id": index_id,
            "identity_preimage": preimage,
            "identity_preimage_ref": refs["records/identity_preimage.json"],
            "accounting_ref": inputs.accounting_stage.completion_ref,
            "eligible_candidates": eligible,
            "unavailable_sources": unavailable,
            "unavailable_sources_ref": refs["unavailable_sources.jsonl"],
            "entries": entries,
            "entries_ref": refs["target_index.jsonl"],
            "entry_count": len(entries),
            "document_targets": document_targets,
            "document_targets_ref": refs["document_targets.jsonl"],
            "document_target_count": len(document_targets),
            "artifact_inventory": inventory_ref(final_relative, semantic_payloads),
            "completion_last": True,
            "status": "complete",
        }
        return StageBuild(StageName.TARGET_INDEX, index_id, payloads, completion)

    @staticmethod
    def _identity_preimage(
        inputs: TargetIndexInputs,
        eligible: list[JsonObject],
        payloads: dict[str, bytes],
        entry_count: int,
        document_target_count: int,
    ) -> JsonObject:
        return {
            "schema_version": "er_commons.corpus_target_index_identity.v1_1",
            "production_extraction_id": inputs.production_extraction_id,
            "scope_id": inputs.scope_id,
            "accounting_sha256": inputs.accounting_stage.completion_ref["sha256"],
            "eligible_candidates_sha256": canonical_sha256(eligible),
            "unavailable_sources_sha256": bytes_ref(
                "unused", payloads["unavailable_sources.jsonl"]
            )["sha256"],
            "entries_sha256": bytes_ref("unused", payloads["target_index.jsonl"])["sha256"],
            "entry_count": entry_count,
            "document_targets_sha256": bytes_ref("unused", payloads["document_targets.jsonl"])[
                "sha256"
            ],
            "document_target_count": document_target_count,
            "ordering_policy_version": inputs.ordering_policy_version,
            "target_policy_sha256": inputs.target_policy_sha256,
            "managed_inventory_sha256": inventory_ref("unused", payloads)["sha256"],
        }

    @staticmethod
    def _eligible(item: DocumentTerminalEvidence) -> JsonObject:
        if (
            item.candidate_id is None
            or item.document_completion_ref is None
            or item.candidate_inventory_ref is None
            or item.target_aliases_ref is None
        ):
            raise ValueError("successful evidence lacks index inputs")
        return {
            "source_id": item.source["source_id"],
            "source_ordinal": item.source_ordinal,
            "candidate_id": item.candidate_id,
            "document_completion_ref": item.document_completion_ref,
            "candidate_inventory_ref": item.candidate_inventory_ref,
            "target_aliases_ref": item.target_aliases_ref,
            "target_records_ref": list(item.target_records_refs),
        }

    @staticmethod
    def _unavailable(item: DocumentTerminalEvidence) -> JsonObject:
        return {
            "source": item.source,
            "source_ordinal": item.source_ordinal,
            "transaction_id": item.transaction_id,
            "attempt": item.attempt,
            "disposition": "failed_terminal",
            "failure_class": item.failure_class,
            "terminal_event_ref": item.terminal_event_ref,
            "attempt_record_ref": item.attempt_record_ref,
            "retained_evidence_refs": list(item.retained_evidence_refs),
        }

    def _entries(
        self,
        evidence: tuple[DocumentTerminalEvidence, ...],
        extraction_root: Path,
    ) -> list[JsonObject]:
        entries: list[JsonObject] = []
        seen: set[tuple[str, str]] = set()
        for item in evidence:
            if item.candidate_id is None or item.target_aliases_ref is None:
                continue
            target_ids = self._target_ids(item, extraction_root)
            for alias in read_jsonl(self._absolute(item.target_aliases_ref, extraction_root)):
                for target in alias.get("targets", []):
                    pair = (alias["id"], target["target_id"])
                    if pair in seen:
                        continue
                    if target["target_id"] not in target_ids:
                        raise ValueError("alias target is absent from sealed target streams")
                    seen.add(pair)
                    entries.append(self._entry(alias, target, item))
        return sorted(entries, key=self._order_key)

    def _target_ids(self, item: DocumentTerminalEvidence, root: Path) -> set[str]:
        return {
            record["id"]
            for reference in item.target_records_refs
            for record in read_jsonl(self._absolute(reference, root))
            if isinstance(record.get("id"), str)
        }

    @staticmethod
    def _entry(alias: JsonObject, target: JsonObject, item: DocumentTerminalEvidence) -> JsonObject:
        return {
            "alias_id": alias["id"],
            "lookup_key": alias["normalized_alias"],
            "target_type": target["target_type"],
            "source_id": item.source["source_id"],
            "source_ordinal": item.source_ordinal,
            "target_id": target["target_id"],
        }

    @staticmethod
    def _order_key(row: JsonObject) -> tuple[object, ...]:
        return (
            row["lookup_key"],
            row["target_type"],
            row["source_ordinal"],
            row["target_id"],
            row["alias_id"],
        )

    @staticmethod
    def _absolute(reference: JsonObject, extraction_root: Path) -> Path:
        path = (extraction_root / str(reference["path"])).resolve()
        if not path.is_relative_to(extraction_root.resolve()):
            raise ValueError("artifact reference escapes extraction root")
        return path
