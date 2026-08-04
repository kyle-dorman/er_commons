"""Reconstruct and validate the durable cross-stage contract bundle."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.corpus_extraction.identity import build_transaction_id
from er_commons.corpus_extraction.outcomes import DocumentTerminalEvidence
from er_commons.corpus_extraction.records import AttemptRecord
from er_commons.corpus_extraction_contract_v1_1.artifacts import DirectoryArtifactReader
from er_commons.corpus_extraction_contract_v1_1.model import JsonObject
from er_commons.corpus_extraction_contract_v1_1.validation import validate_contract_bundle
from er_commons.corpus_resolution.preflight import ScopeRun
from er_commons.corpus_resolution.storage import json_bytes, read_json


class ContractBundleWriter:
    """Join stage-one evidence and stage-two products under the executable gate."""

    def __init__(self, run: ScopeRun) -> None:
        self._run = run

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
        events, attempts, completions = self._stage_one_records(evidence)
        policy = self._run.document_spec.resource_policy
        bundle: JsonObject = {
            "schema_version": "er_commons.corpus_extraction_contract_fixture.v1_1",
            "fixture_scope": "runtime_scope",
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
            "accounting": accounting,
            "target_index": index,
            "resolution_completion": resolution,
            "handoff": handoff,
            "corpus_stage_attempts": stage_attempts,
            "task04_freezes": [],
        }
        self._validate(bundle)
        path = self._run.extraction_root / "scopes" / self._run.scope_id / "contract_bundle.json"
        self._write_exact(path, json_bytes(bundle))
        return path

    def _stage_one_records(
        self, evidence: tuple[DocumentTerminalEvidence, ...]
    ) -> tuple[list[JsonObject], list[JsonObject], list[JsonObject]]:
        events: list[JsonObject] = []
        attempts: list[JsonObject] = []
        completions: list[JsonObject] = []
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
        return events, attempts, completions

    def _transaction_id(self, source: DocumentTerminalEvidence, attempt: AttemptRecord) -> str:
        return build_transaction_id(
            scope_id=self._run.scope_id,
            source_id=attempt.source_id,
            source_sha256=str(source.source["sha256"]),
            attempt=attempt.attempt,
        )

    def _validate(self, bundle: JsonObject) -> None:
        project_root = Path(__file__).resolve().parents[3]
        schema_path = (
            project_root / "benchmarks/er_bench/schemas/corpus_extraction/v1_1/records.schema.json"
        )
        Draft202012Validator(json.loads(schema_path.read_bytes())).validate(bundle)
        validate_contract_bundle(bundle, DirectoryArtifactReader(self._run.extraction_root))

    @staticmethod
    def _write_exact(path: Path, value: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_bytes() != value:
            raise ValueError(f"conflicting contract bundle: {path}")
        if not path.exists():
            path.write_bytes(value)
