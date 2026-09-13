"""Reconstruct and validate the durable cross-stage contract bundle."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.collection_processing.contract import JsonObject, collection_identity_fields
from er_commons.collection_processing.preflight import CollectionRun
from er_commons.collection_processing.semantic_validation import (
    CollectionArtifactReader,
    validate_collection_bundle,
)
from er_commons.collection_processing.storage import json_bytes, read_json
from er_commons.document_publication.identity import build_transaction_id
from er_commons.document_publication.published_document import DocumentTerminalEvidence
from er_commons.document_publication.records import AttemptRecord


class ContractBundleWriter:
    """Join stage-one evidence and stage-two products under the executable gate."""

    def __init__(
        self,
        run: CollectionRun,
        *,
        collection_production_id: str | None = None,
        imported_selection_sha256: str | None = None,
        collection_production_identity_ref: JsonObject | None = None,
        imported_selection_ref: JsonObject | None = None,
        imported_document_evidence: JsonObject | None = None,
    ) -> None:
        self._run = run
        self._identity_fields = collection_identity_fields(
            run.document_spec.production_extraction_id,
            collection_production_id,
            imported_selection_sha256,
        )
        self._recovery_refs = {
            "collection_production_identity_ref": collection_production_identity_ref,
            "imported_selection_ref": imported_selection_ref,
            "imported_document_evidence": imported_document_evidence,
        }
        self._is_recovery = collection_production_id is not None
        if self._is_recovery != all(value is not None for value in self._recovery_refs.values()):
            raise ValueError("collection recovery requires all identity and imported evidence refs")
        if not self._is_recovery and any(
            value is not None for value in self._recovery_refs.values()
        ):
            raise ValueError("v2 collection cannot carry recovery evidence")

    def publish(
        self,
        *,
        evidence: tuple[DocumentTerminalEvidence, ...],
        accounting: JsonObject,
        index: JsonObject,
        resolution: JsonObject,
        handoff: JsonObject,
        stage_attempts: list[JsonObject],
    ) -> Path:
        """Reconstruct, validate, and exactly persist one durable bundle."""
        events, attempts, completions, replays = (
            ([], [], [], []) if self._is_recovery else self._stage_one_records(evidence)
        )
        policy = self._run.document_spec.resource_policy
        bundle: JsonObject = {
            "schema_version": "er_commons.collection_workflow_contract.v2",
            "collection_scope": "runtime_scope",
            "production_extraction_id": self._run.document_spec.production_extraction_id,
            "resource_policy": {
                "document_concurrency": policy.document_concurrency,
                "page_batch_size": policy.page_batch_size,
                "cpu_threads_per_document": policy.cpu_threads_per_document,
                "device": policy.device,
                "docling_timeout_seconds": policy.docling_timeout_seconds,
                "outer_process_deadline_seconds": policy.outer_process_deadline_seconds,
                "retry_limit": policy.retry_limit,
            },
            "state_events": events,
            "document_attempts": attempts,
            "document_completions": completions,
            "downstream_replays": replays,
            "accounting": accounting,
            "target_index": index,
            "resolution_completion": resolution,
            "handoff": handoff,
            "collection_stage_attempts": stage_attempts,
            "task04_freezes": [],
        }
        if self._is_recovery:
            for field in (
                "production_extraction_id",
                "state_events",
                "document_attempts",
                "document_completions",
                "downstream_replays",
            ):
                del bundle[field]
            bundle.update(
                schema_version="er_commons.collection_workflow_contract.v3",
                **self._identity_fields,
                **self._recovery_refs,
            )
        self._validate(bundle)
        path = self._run.extraction_root / "scopes" / self._run.scope_id / "contract_bundle.json"
        self._write_exact(path, json_bytes(bundle))
        return path

    def _stage_one_records(
        self, evidence: tuple[DocumentTerminalEvidence, ...]
    ) -> tuple[list[JsonObject], list[JsonObject], list[JsonObject], list[JsonObject]]:
        events: list[JsonObject] = []
        attempts: list[JsonObject] = []
        completions: list[JsonObject] = []
        replays: list[JsonObject] = []
        source_by_id = {str(item.source["source_id"]): item for item in evidence}
        for root in sorted((self._run.extraction_root / "attempts").glob("txv1-*.*")):
            record_path = root / "attempt_record.json"
            if not record_path.is_file():
                continue
            attempt = AttemptRecord.model_validate_json(record_path.read_bytes())
            source = source_by_id.get(attempt.source_id)
            if source is None or attempt.transaction_id != self._transaction_id(source, attempt):
                continue
            attempts.append(attempt.model_dump(mode="json"))
            events.extend(read_json(root / path) for path in attempt.state_event_paths)
        attempts.sort(
            key=lambda row: (source_by_id[row["source_id"]].source_ordinal, row["attempt"])
        )
        events.sort(
            key=lambda row: (
                source_by_id[row["source_id"]].source_ordinal,
                row["attempt"],
                row["sequence"],
            )
        )
        for item in evidence:
            if item.document_completion_ref is not None:
                completions.append(
                    read_json(self._run.extraction_root / str(item.document_completion_ref["path"]))
                )
            if item.downstream_replay_ref is not None:
                replays.append(
                    read_json(self._run.extraction_root / str(item.downstream_replay_ref["path"]))
                )
        return events, attempts, completions, replays

    def _transaction_id(self, source: DocumentTerminalEvidence, attempt: AttemptRecord) -> str:
        return build_transaction_id(
            scope_id=self._run.scope_id,
            source_id=attempt.source_id,
            source_sha256=str(source.source["sha256"]),
            attempt=attempt.attempt,
        )

    def _validate(self, bundle: JsonObject) -> None:
        project_root = Path(__file__).resolve().parents[3]
        version = "v3" if self._is_recovery else "v2"
        schema_path = project_root / (
            f"benchmarks/er_bench/schemas/collection_processing/{version}/records.schema.json"
        )
        Draft202012Validator(json.loads(schema_path.read_bytes())).validate(bundle)
        validate_collection_bundle(bundle, CollectionArtifactReader(self._run.extraction_root))

    @staticmethod
    def _write_exact(path: Path, value: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_bytes() != value:
            raise ValueError(f"conflicting contract bundle: {path}")
        if not path.exists():
            path.write_bytes(value)
