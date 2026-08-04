"""Deterministic multi-document evidence for the v1.1 offline contract gate."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from er_commons.corpus_extraction_contract_v1_1.accounting import unavailable_source_digest
from er_commons.corpus_extraction_contract_v1_1.checks import (
    bytes_sha256,
    canonical_sha256,
    fail,
)
from er_commons.corpus_extraction_contract_v1_1.identity import (
    build_handoff_id,
    build_index_id,
    build_resolution_id,
)
from er_commons.corpus_extraction_contract_v1_1.model import JsonObject

PRODUCTION_ID = "exv1-" + "1" * 64
SCOPE_ID = "scopev1-" + "2" * 64
SOURCE_NAMES = ("fixture_alpha", "fixture_beta", "fixture_gamma", "fixture_epsilon")


@dataclass
class MemoryArtifacts:
    """Exact in-memory artifact store used by the checked synthetic fixture."""

    values: dict[str, bytes] = field(default_factory=dict)

    def add_json(self, path: str, value: object) -> JsonObject:
        """Serialize one stable JSON value and return its sealed reference."""
        return self.add_bytes(path, _json_bytes(value))

    def add_jsonl(self, path: str, rows: list[JsonObject]) -> JsonObject:
        """Serialize ordered compact JSONL rows and return their reference."""
        value = b"".join(_json_bytes(row) for row in rows)
        return self.add_bytes(path, value)

    def add_bytes(self, path: str, value: bytes) -> JsonObject:
        """Add one unique path and return its exact size and digest."""
        if path in self.values:
            raise ValueError(f"duplicate fixture artifact: {path}")
        self.values[path] = value
        return {"path": path, "sha256": bytes_sha256(value), "byte_size": len(value)}

    def read_bytes(self, reference: JsonObject) -> bytes:
        """Read bytes by path for the ArtifactReader protocol."""
        path = reference.get("path")
        if not isinstance(path, str) or path not in self.values:
            fail("artifact_path", "fixture artifact is absent", subject=str(path))
        return self.values[path]


@dataclass(frozen=True)
class SyntheticFixture:
    """One positive contract bundle plus its independent serialized evidence."""

    bundle: JsonObject
    artifacts: MemoryArtifacts


def build_valid_fixture() -> SyntheticFixture:
    """Build one scope covering success, failure, zero mentions, and all reasons."""
    artifacts = MemoryArtifacts()
    sources = _sources()
    stage_one = _stage_one_evidence(artifacts, sources)
    accounting = _accounting(artifacts, sources, stage_one)
    index = _target_index(artifacts, accounting, stage_one, sources)
    resolution = _resolution(artifacts, accounting, index, stage_one, sources)
    handoff = _handoff(artifacts, accounting, index, resolution)
    bundle: JsonObject = {
        "schema_version": "er_commons.corpus_extraction_contract_fixture.v1_1",
        "fixture_scope": "synthetic_multi_document",
        "production_extraction_id": PRODUCTION_ID,
        "resource_policy": {
            "document_concurrency": 1,
            "page_batch_size": 4,
            "cpu_threads_per_document": 4,
            "device": "cpu",
            "docling_timeout_seconds": 60,
            "outer_process_deadline_seconds": 90,
            "retry_limit": 1,
        },
        "state_events": stage_one["events"],
        "document_attempts": stage_one["attempts"],
        "document_completions": stage_one["completions"],
        "accounting": accounting,
        "target_index": index,
        "resolution_completion": resolution,
        "handoff": handoff,
        "corpus_stage_attempts": _stage_attempts(artifacts, accounting, index, resolution, handoff),
        "task04_freezes": [],
    }
    return SyntheticFixture(bundle, artifacts)


def _sources() -> list[JsonObject]:
    return [
        {"source_id": source_id, "sha256": character * 64, "pdf_page_count": 2}
        for source_id, character in zip(SOURCE_NAMES, "abce", strict=True)
    ]


def _stage_one_evidence(artifacts: MemoryArtifacts, sources: list[JsonObject]) -> JsonObject:
    events: list[JsonObject] = []
    attempts: list[JsonObject] = []
    completions: list[JsonObject] = []
    records: dict[str, JsonObject] = {}
    for ordinal, source in enumerate(sources, start=1):
        source_id = str(source["source_id"])
        successful = source_id != "fixture_beta"
        transaction_id = "txv1-" + f"{ordinal:x}" * 64
        candidate_id = "docv1-" + f"{ordinal + 8:x}" * 64 if successful else None
        disposition = (
            "complete_with_warnings"
            if source_id == "fixture_gamma"
            else ("complete" if successful else "failed_terminal")
        )
        source_events = _events(transaction_id, source_id, disposition)
        event_refs = [
            artifacts.add_json(f"stage_one/{source_id}/events/{index:04d}.json", event)
            for index, event in enumerate(source_events, start=1)
        ]
        terminal_ref = event_refs[-1]
        inventory_ref = (
            artifacts.add_json(
                f"stage_one/{source_id}/artifact_inventory.json",
                {"source_id": source_id, "files": []},
            )
            if successful
            else None
        )
        completion = (
            {
                "record_type": "document_completion",
                "schema_version": "er_commons.document_completion.v1",
                "transaction_id": transaction_id,
                "source": source,
                "scope_kind": "full_document",
                "processed_pages": [1, 2],
                "raw_docling_status": "SUCCESS",
                "candidate_id": candidate_id,
                "candidate_inventory": _legacy_ref(inventory_ref),
                "completion_last": True,
            }
            if successful
            else None
        )
        completion_ref = (
            artifacts.add_json(f"stage_one/{source_id}/completion_record.json", completion)
            if completion is not None
            else None
        )
        retained_refs = (
            []
            if successful
            else [
                artifacts.add_json(
                    f"stage_one/{source_id}/failure.json",
                    {"failure_class": "SyntheticTerminalFailure"},
                )
            ]
        )
        attempt = {
            "schema_version": "er_commons.document_attempt.v1",
            "transaction_id": transaction_id,
            "source_id": source_id,
            "attempt": 1,
            "disposition": disposition,
            "failure_class": None if successful else "SyntheticTerminalFailure",
            "message": None if successful else "synthetic terminal evidence",
            "state_event_paths": [reference["path"] for reference in event_refs],
            "completion_path": completion_ref["path"] if completion_ref else None,
        }
        attempt_ref = artifacts.add_json(f"stage_one/{source_id}/attempt_record.json", attempt)
        cross_reference_rows = _cross_references(source_id, candidate_id)
        cross_references_ref = artifacts.add_jsonl(
            f"stage_one/{source_id}/canonical/cross_references.jsonl",
            cross_reference_rows,
        )
        alias_rows, target_rows = _targets(source_id, candidate_id)
        aliases_ref = artifacts.add_jsonl(
            f"stage_one/{source_id}/canonical/target_aliases.jsonl", alias_rows
        )
        targets_ref = artifacts.add_jsonl(
            f"stage_one/{source_id}/canonical/documents.jsonl", target_rows
        )
        events.extend(source_events)
        attempts.append(attempt)
        if completion is not None:
            completions.append(completion)
        records[source_id] = {
            "transaction_id": transaction_id,
            "candidate_id": candidate_id,
            "disposition": disposition,
            "terminal_event_ref": terminal_ref,
            "attempt_record_ref": attempt_ref,
            "completion_ref": completion_ref,
            "inventory_ref": inventory_ref,
            "retained_evidence_refs": retained_refs,
            "cross_references_ref": cross_references_ref,
            "target_aliases_ref": aliases_ref,
            "target_records_ref": [targets_ref],
        }
    return {
        "events": events,
        "attempts": attempts,
        "completions": completions,
        "by_source": records,
    }


def _events(transaction_id: str, source_id: str, disposition: str) -> list[JsonObject]:
    raw_status = "SUCCESS" if disposition.startswith("complete") else "FAILURE"
    return [
        _event(transaction_id, source_id, 1, None, "selected", "PENDING"),
        _event(transaction_id, source_id, 2, "selected", "running", "STARTED"),
        _event(transaction_id, source_id, 3, "running", disposition, raw_status),
    ]


def _event(
    transaction_id: str,
    source_id: str,
    sequence: int,
    from_state: str | None,
    to_state: str,
    raw_status: str,
) -> JsonObject:
    return {
        "record_type": "document_state_event",
        "schema_version": "er_commons.document_state_event.v1",
        "transaction_id": transaction_id,
        "source_id": source_id,
        "attempt": 1,
        "sequence": sequence,
        "from_state": from_state,
        "to_state": to_state,
        "raw_docling_status": raw_status,
    }


def _cross_references(source_id: str, candidate_id: object) -> list[JsonObject]:
    if source_id != "fixture_alpha":
        return []
    document_id = f"{candidate_id}/document/{source_id}"
    keys = (
        ("report gamma", "deferred_cross_document"),
        ("report gamma unique", "deferred_cross_document"),
        ("report beta", "deferred_cross_document"),
        ("report delta", "deferred_cross_document"),
        ("report epsilon", "deferred_cross_document"),
        ("outside report", "external_document_outside_corpus"),
    )
    return [
        {
            "id": f"{candidate_id}/cross-reference/{source_id}/ref{sequence:06d}",
            "document_id": document_id,
            "sequence": sequence,
            "mention_class": "document",
            "lookup_key": lookup_key,
            "resolution_status": "unresolved",
            "unresolved_reason": reason,
        }
        for sequence, (lookup_key, reason) in enumerate(keys, start=1)
    ]


def _targets(source_id: str, candidate_id: object) -> tuple[list[JsonObject], list[JsonObject]]:
    if candidate_id is None:
        return [], []
    target_id = f"{candidate_id}/document/{source_id}"
    records = [{"id": target_id, "source_id": source_id}]
    if source_id not in {"fixture_alpha", "fixture_gamma"}:
        return [], records
    lookup_keys = (
        ("report gamma",)
        if source_id == "fixture_alpha"
        else ("report gamma", "report gamma unique")
    )
    aliases = [
        {
            "id": f"{candidate_id}/target-alias/{source_id}/alias{ordinal:06d}",
            "normalized_alias": lookup_key,
            "targets": [{"target_id": target_id, "target_type": "document"}],
        }
        for ordinal, lookup_key in enumerate(lookup_keys, start=1)
    ]
    return aliases, records


def _accounting(
    artifacts: MemoryArtifacts,
    sources: list[JsonObject],
    stage_one: JsonObject,
) -> JsonObject:
    rows: list[JsonObject] = []
    for ordinal, source in enumerate(sources, start=1):
        source_id = str(source["source_id"])
        evidence = stage_one["by_source"][source_id]
        successful = evidence["candidate_id"] is not None
        rows.append(
            {
                "source_id": source_id,
                "source_ordinal": ordinal,
                "terminal_state": evidence["disposition"],
                "transaction_id": evidence["transaction_id"],
                "attempt": 1,
                "terminal_event_ref": evidence["terminal_event_ref"],
                "attempt_record_ref": evidence["attempt_record_ref"],
                "candidate_id": evidence["candidate_id"],
                "document_completion_ref": evidence["completion_ref"],
                "candidate_inventory_ref": evidence["inventory_ref"],
                "failure_class": None if successful else "SyntheticTerminalFailure",
                "retained_evidence_refs": evidence["retained_evidence_refs"],
            }
        )
    inventory = artifacts.add_json("corpus/accounting/artifact_inventory.json", {"files": []})
    return {
        "record_type": "scope_accounting",
        "schema_version": "er_commons.scope_accounting.v1_1",
        "scope_id": SCOPE_ID,
        "scope_kind": "fixture",
        "production_extraction_id": PRODUCTION_ID,
        "ordered_sources": sources,
        "rows": rows,
        "counts": {"total": 4, "complete": 2, "complete_with_warnings": 1, "failed_terminal": 1},
        "artifact_inventory": inventory,
        "completion_last": True,
        "status": "complete",
    }


def _target_index(
    artifacts: MemoryArtifacts,
    accounting: JsonObject,
    stage_one: JsonObject,
    sources: list[JsonObject],
) -> JsonObject:
    accounting_ref = artifacts.add_json("corpus/accounting/completion_record.json", accounting)
    eligible: list[JsonObject] = []
    for row in accounting["rows"]:
        if row["candidate_id"] is None:
            continue
        evidence = stage_one["by_source"][row["source_id"]]
        eligible.append(
            {
                "source_id": row["source_id"],
                "source_ordinal": row["source_ordinal"],
                "candidate_id": row["candidate_id"],
                "document_completion_ref": row["document_completion_ref"],
                "candidate_inventory_ref": row["candidate_inventory_ref"],
                "target_aliases_ref": evidence["target_aliases_ref"],
                "target_records_ref": evidence["target_records_ref"],
            }
        )
    failed_row = accounting["rows"][1]
    beta_source = sources[1]
    unavailable = [
        {
            "source": beta_source,
            "source_ordinal": 2,
            "transaction_id": failed_row["transaction_id"],
            "attempt": 1,
            "disposition": "failed_terminal",
            "failure_class": "SyntheticTerminalFailure",
            "terminal_event_ref": failed_row["terminal_event_ref"],
            "attempt_record_ref": failed_row["attempt_record_ref"],
            "retained_evidence_refs": failed_row["retained_evidence_refs"],
        }
    ]
    unavailable_ref = artifacts.add_jsonl("corpus/index/unavailable_sources.jsonl", unavailable)
    entries: list[JsonObject] = []
    for candidate in eligible:
        source_id = candidate["source_id"]
        evidence = stage_one["by_source"][source_id]
        aliases = [
            json.loads(line)
            for line in artifacts.read_bytes(evidence["target_aliases_ref"]).decode().splitlines()
        ]
        for alias in aliases:
            entries.append(
                {
                    "alias_id": alias["id"],
                    "lookup_key": alias["normalized_alias"],
                    "target_type": alias["targets"][0]["target_type"],
                    "source_id": source_id,
                    "source_ordinal": candidate["source_ordinal"],
                    "target_id": alias["targets"][0]["target_id"],
                }
            )
    entries.sort(
        key=lambda row: (
            row["lookup_key"],
            row["target_type"],
            row["source_ordinal"],
            row["target_id"],
            row["alias_id"],
        )
    )
    entries_ref = artifacts.add_jsonl("corpus/index/target_index.jsonl", entries)
    inventory = artifacts.add_json("corpus/index/artifact_inventory.json", {"files": []})
    preimage = {
        "schema_version": "er_commons.corpus_target_index_identity.v1_1",
        "production_extraction_id": PRODUCTION_ID,
        "scope_id": SCOPE_ID,
        "accounting_sha256": accounting_ref["sha256"],
        "eligible_candidates_sha256": canonical_sha256(eligible),
        "unavailable_sources_sha256": unavailable_ref["sha256"],
        "entries_sha256": entries_ref["sha256"],
        "entry_count": len(entries),
        "ordering_policy_version": "corpus_target_order_v1",
        "target_policy_sha256": "d" * 64,
        "managed_inventory_sha256": inventory["sha256"],
    }
    preimage_ref = artifacts.add_json("corpus/index/identity_preimage.json", preimage)
    return {
        "record_type": "target_index_completion",
        "schema_version": "er_commons.target_index_completion.v1_1",
        "index_id": build_index_id(preimage),
        "identity_preimage": preimage,
        "identity_preimage_ref": preimage_ref,
        "accounting_ref": accounting_ref,
        "eligible_candidates": eligible,
        "unavailable_sources": unavailable,
        "unavailable_sources_ref": unavailable_ref,
        "entries": entries,
        "entries_ref": entries_ref,
        "entry_count": len(entries),
        "artifact_inventory": inventory,
        "completion_last": True,
        "status": "complete",
    }


def _resolution(
    artifacts: MemoryArtifacts,
    accounting: JsonObject,
    index: JsonObject,
    stage_one: JsonObject,
    sources: list[JsonObject],
) -> JsonObject:
    index_ref = artifacts.add_json("corpus/index/completion_record.json", index)
    catalog = _catalog(sources)
    catalog_ref = artifacts.add_json("corpus/catalog.json", catalog)
    candidates: list[JsonObject] = []
    all_mentions: list[JsonObject] = []
    for candidate in index["eligible_candidates"]:
        source_id = candidate["source_id"]
        evidence = stage_one["by_source"][source_id]
        mentions = _eligible_mentions(evidence["cross_references_ref"], artifacts, catalog)
        candidates.append(
            {
                "source_id": source_id,
                "source_ordinal": candidate["source_ordinal"],
                "candidate_id": candidate["candidate_id"],
                "document_completion_ref": candidate["document_completion_ref"],
                "candidate_inventory_ref": candidate["candidate_inventory_ref"],
                "cross_references_ref": evidence["cross_references_ref"],
                "eligible_mention_count": len(mentions),
                "eligible_mentions": mentions,
            }
        )
        all_mentions.extend(mentions)
    manifest = {
        "schema_version": "er_commons.corpus_mention_input_manifest.v1_1",
        "index_id": index["index_id"],
        "corpus_catalog_ref": catalog_ref,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "eligible_mention_count": len(all_mentions),
        "eligible_mentions_sha256": canonical_sha256(all_mentions),
    }
    manifest_ref = artifacts.add_json("corpus/resolution/mention_input_manifest.json", manifest)
    alpha_inventory = candidates[0]["candidate_inventory_ref"]
    beta_unavailable = index["unavailable_sources"][0]
    resolutions = [
        _resolution_row(
            mention,
            candidates[0]["candidate_id"],
            alpha_inventory,
            index,
            beta_unavailable,
            catalog_ref,
        )
        for mention in all_mentions
    ]
    resolutions_ref = artifacts.add_jsonl("corpus/resolution/resolutions.jsonl", resolutions)
    snapshots = [
        {
            "candidate_id": candidate["candidate_id"],
            "inventory_ref": candidate["candidate_inventory_ref"],
        }
        for candidate in candidates
    ]
    counts = {"total": 5, "resolved": 1, "ambiguous": 1, "unresolved": 3}
    inventory = artifacts.add_json("corpus/resolution/artifact_inventory.json", {"files": []})
    preimage = {
        "schema_version": "er_commons.corpus_resolution_identity.v1_1",
        "production_extraction_id": PRODUCTION_ID,
        "scope_id": SCOPE_ID,
        "index_completion_sha256": index_ref["sha256"],
        "mention_input_manifest_sha256": manifest_ref["sha256"],
        "resolutions_sha256": resolutions_ref["sha256"],
        "counts_sha256": canonical_sha256(counts),
        "before_after_inventories_sha256": canonical_sha256(
            {"before": snapshots, "after": snapshots}
        ),
        "resolution_policy_sha256": "e" * 64,
        "managed_inventory_sha256": inventory["sha256"],
    }
    preimage_ref = artifacts.add_json("corpus/resolution/identity_preimage.json", preimage)
    return {
        "record_type": "resolution_completion",
        "schema_version": "er_commons.resolution_completion.v1_1",
        "resolution_id": build_resolution_id(preimage),
        "index_id": index["index_id"],
        "identity_preimage": preimage,
        "identity_preimage_ref": preimage_ref,
        "index_completion_ref": index_ref,
        "mention_input_manifest": manifest,
        "mention_input_manifest_ref": manifest_ref,
        "resolutions": resolutions,
        "resolutions_ref": resolutions_ref,
        "counts": counts,
        "candidate_inventories_before": snapshots,
        "candidate_inventories_after": snapshots,
        "artifact_inventory": inventory,
        "completion_last": True,
        "status": "complete",
    }


def _catalog(sources: list[JsonObject]) -> JsonObject:
    delta = {"source_id": "fixture_delta", "sha256": "d" * 64, "pdf_page_count": 2}
    all_sources = [*sources, delta]
    documents = []
    for source in all_sources:
        source_name = str(source["source_id"]).removeprefix("fixture_")
        lookup_keys = [f"report {source_name}"]
        if source_name == "alpha":
            lookup_keys.append("report gamma")
        elif source_name == "gamma":
            lookup_keys.append("report gamma unique")
        documents.append({"source": source, "lookup_keys": lookup_keys})
    return {"documents": documents}


def _eligible_mentions(
    reference: JsonObject, artifacts: MemoryArtifacts, catalog: JsonObject
) -> list[JsonObject]:
    lookup: dict[str, list[str]] = {}
    for document in catalog["documents"]:
        for key in document["lookup_keys"]:
            lookup.setdefault(key, []).append(document["source"]["source_id"])
    records = [json.loads(line) for line in artifacts.read_bytes(reference).decode().splitlines()]
    return [
        {
            "mention_id": record["id"],
            "candidate_local_sequence": record["sequence"],
            "document_id": record["document_id"],
            "mention_class": "document",
            "lookup_key": record["lookup_key"],
            "intended_target_source_ids": lookup[record["lookup_key"]],
        }
        for record in records
        if record["unresolved_reason"] == "deferred_cross_document"
    ]


def _resolution_row(
    mention: JsonObject,
    source_candidate_id: object,
    source_inventory: JsonObject,
    index: JsonObject,
    beta_unavailable: JsonObject,
    catalog_ref: JsonObject,
) -> JsonObject:
    lookup_key = mention["lookup_key"]
    base = {
        "mention_id": mention["mention_id"],
        "source_candidate_id": source_candidate_id,
        "candidate_local_sequence": mention["candidate_local_sequence"],
        "lookup_key": lookup_key,
        "target_type": "document",
        "intended_target_source_ids": mention["intended_target_source_ids"],
        "source_inventory_before_ref": source_inventory,
        "source_inventory_after_ref": source_inventory,
    }
    candidate_targets = [
        {
            "target_id": entry["target_id"],
            "target_source_id": entry["source_id"],
            "target_type": entry["target_type"],
        }
        for entry in index["entries"]
        if entry["lookup_key"] == lookup_key
        and entry["source_id"] in mention["intended_target_source_ids"]
    ]
    if candidate_targets:
        return {
            **base,
            "candidate_targets": candidate_targets,
            "status": "resolved" if len(candidate_targets) == 1 else "ambiguous",
            "unresolved_reason": None,
            "reason_evidence": None,
        }
    reason: JsonObject
    if lookup_key == "report beta":
        reason = {
            "reason": "target_source_failed",
            "target_source_id": "fixture_beta",
            "unavailable_source_sha256": unavailable_source_digest(beta_unavailable),
        }
    elif lookup_key == "report delta":
        reason = {
            "reason": "target_not_in_scope",
            "target_source": {
                "source_id": "fixture_delta",
                "sha256": "d" * 64,
                "pdf_page_count": 2,
            },
            "production_manifest_ref": catalog_ref,
            "scope_id": SCOPE_ID,
        }
    else:
        reason = {
            "reason": "target_unavailable",
            "target_source_id": "fixture_epsilon",
            "target_candidate_id": next(
                row["candidate_id"]
                for row in index["eligible_candidates"]
                if row["source_id"] == "fixture_epsilon"
            ),
            "index_id": index["index_id"],
            "entries_sha256": index["entries_ref"]["sha256"],
        }
    return {
        **base,
        "candidate_targets": [],
        "status": "unresolved",
        "unresolved_reason": reason["reason"],
        "reason_evidence": reason,
    }


def _handoff(
    artifacts: MemoryArtifacts,
    accounting: JsonObject,
    index: JsonObject,
    resolution: JsonObject,
) -> JsonObject:
    accounting_ref = _existing_ref(artifacts, "corpus/accounting/completion_record.json")
    index_ref = _existing_ref(artifacts, "corpus/index/completion_record.json")
    resolution_ref = artifacts.add_json("corpus/resolution/completion_record.json", resolution)
    policy_ref = artifacts.add_json("corpus/handoff/blocking_policy.json", "all_sources_successful")
    reason = {
        "code": "terminal_source_failure",
        "source_id": "fixture_beta",
        "transaction_id": accounting["rows"][1]["transaction_id"],
        "unavailable_source_sha256": unavailable_source_digest(index["unavailable_sources"][0]),
    }
    reasons = [reason]
    inventory = artifacts.add_json("corpus/handoff/artifact_inventory.json", {"files": []})
    preimage = {
        "schema_version": "er_commons.candidate_handoff_identity.v1_1",
        "production_extraction_id": PRODUCTION_ID,
        "scope_id": SCOPE_ID,
        "accounting_completion_sha256": accounting_ref["sha256"],
        "index_completion_sha256": index_ref["sha256"],
        "resolution_completion_sha256": resolution_ref["sha256"],
        "blocking_policy_sha256": policy_ref["sha256"],
        "status": "blocked",
        "blocking_reasons_sha256": canonical_sha256(reasons),
        "task04_status": "not_evaluated",
        "managed_inventory_sha256": inventory["sha256"],
    }
    preimage_ref = artifacts.add_json("corpus/handoff/identity_preimage.json", preimage)
    return {
        "record_type": "candidate_handoff",
        "schema_version": "er_commons.candidate_handoff.v1_1",
        "handoff_id": build_handoff_id(preimage),
        "scope_id": SCOPE_ID,
        "index_id": index["index_id"],
        "resolution_id": resolution["resolution_id"],
        "identity_preimage": preimage,
        "identity_preimage_ref": preimage_ref,
        "accounting_completion_ref": accounting_ref,
        "index_completion_ref": index_ref,
        "resolution_completion_ref": resolution_ref,
        "blocking_policy": "all_sources_successful",
        "blocking_policy_ref": policy_ref,
        "blocking_reasons": reasons,
        "status": "blocked",
        "task04_status": "not_evaluated",
        "artifact_inventory": inventory,
        "completion_last": True,
    }


def _stage_attempts(
    artifacts: MemoryArtifacts,
    accounting: JsonObject,
    index: JsonObject,
    resolution: JsonObject,
    handoff: JsonObject,
) -> list[JsonObject]:
    completions = {
        "accounting": (accounting["scope_id"], "corpus/accounting/completion_record.json"),
        "target_index": (index["index_id"], "corpus/index/completion_record.json"),
        "resolution": (resolution["resolution_id"], "corpus/resolution/completion_record.json"),
        "handoff": (
            handoff["handoff_id"],
            "corpus/handoff/completion_record.json",
        ),
    }
    artifacts.add_json("corpus/handoff/completion_record.json", handoff)
    attempts: list[JsonObject] = []
    for stage_type, (stage_id, path) in completions.items():
        prior_disposition = {
            "target_index": "failed_retryable",
            "resolution": "cancelled",
        }.get(stage_type)
        if prior_disposition is not None:
            prior_event_ref = artifacts.add_json(
                f"corpus/attempts/{stage_type}/attempt_1_event.json",
                {"state": prior_disposition},
            )
            attempts.append(
                {
                    "schema_version": "er_commons.corpus_stage_attempt.v1",
                    "stage_type": stage_type,
                    "stage_id": stage_id,
                    "attempt": 1,
                    "disposition": prior_disposition,
                    "failure_class": "SyntheticInterruptedPublication",
                    "state_event_refs": [prior_event_ref],
                    "completion_ref": None,
                }
            )
        final_attempt = 2 if prior_disposition is not None else 1
        event_ref = artifacts.add_json(
            f"corpus/attempts/{stage_type}/attempt_{final_attempt}_event.json",
            {"state": "complete"},
        )
        attempts.append(
            {
                "schema_version": "er_commons.corpus_stage_attempt.v1",
                "stage_type": stage_type,
                "stage_id": stage_id,
                "attempt": final_attempt,
                "disposition": "complete",
                "failure_class": None,
                "state_event_refs": [event_ref],
                "completion_ref": _existing_ref(artifacts, path),
            }
        )
    return attempts


def _legacy_ref(reference: object) -> JsonObject:
    if not isinstance(reference, dict):
        raise TypeError("legacy reference requires a sealed artifact")
    return {"path": reference["path"], "sha256": reference["sha256"]}


def _existing_ref(artifacts: MemoryArtifacts, path: str) -> JsonObject:
    value = artifacts.values[path]
    return {"path": path, "sha256": bytes_sha256(value), "byte_size": len(value)}


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
