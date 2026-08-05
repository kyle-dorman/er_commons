"""Resolve and verify everything needed before a document attempt starts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from er_commons.corpus_extraction.config import RunSpec, load_run_spec
from er_commons.corpus_extraction.identity import build_scope_id
from er_commons.corpus_extraction.lineage_preflight import ExecutionPreflight
from er_commons.corpus_extraction.records import SourceIdentity
from er_commons.corpus_extraction.sources import resolve_manifest_source
from er_commons.corpus_extraction_contract_v1_1 import (
    validate_production_identity,
)
from er_commons.corpus_extraction_contract_v1_1.checks import canonical_sha256
from er_commons.source_freeze import assert_contained, sha256_file


@dataclass(frozen=True)
class DocumentRun:
    """Verified immutable context shared by every attempt for one document."""

    data_root: Path
    project_root: Path
    run_spec_path: Path
    spec: RunSpec
    spec_sha256: str
    source: SourceIdentity
    scope_id: str
    extraction_root: Path
    final_parent: Path
    hierarchy_disposition: dict[str, object]
    execution_preflight: ExecutionPreflight | None = None

    @property
    def maximum_attempts(self) -> int:
        """Return the initial attempt plus configured retries."""
        return self.spec.resource_policy.retry_limit + 1


def prepare_document_run(data_root: Path, run_spec_path: Path, source_id: str) -> DocumentRun:
    """Load the run contract, verify production scope, and select one source."""
    spec, spec_sha256 = load_run_spec(run_spec_path)
    project_root = Path(__file__).resolve().parents[3]
    _verify_production_contract(spec, project_root, data_root)
    source = resolve_manifest_source(data_root, spec, source_id)
    disposition = spec.hierarchy_disposition(source_id).model_dump(mode="json")
    scope_id = build_scope_id(
        run_spec_sha256=spec_sha256,
        production_extraction_id=spec.production_extraction_id,
    )
    extraction_root = assert_contained(data_root, spec.artifact_relative_root.as_posix())
    return DocumentRun(
        data_root=data_root,
        project_root=project_root,
        run_spec_path=run_spec_path.resolve(),
        spec=spec,
        spec_sha256=spec_sha256,
        source=source,
        scope_id=scope_id,
        extraction_root=extraction_root,
        final_parent=extraction_root / "documents" / source_id,
        hierarchy_disposition=disposition,
    )


def _verify_production_contract(spec: RunSpec, project_root: Path, data_root: Path) -> None:
    """Reject arbitrary or stale production identities before source work."""
    identity_path = (project_root / spec.production_identity_relative_path).resolve()
    if not identity_path.is_relative_to(project_root.resolve()) or not identity_path.is_file():
        raise FileNotFoundError(identity_path)
    identity = json.loads(identity_path.read_text())
    source_ids: list[str] | None = None
    scope_evidence: dict[str, object] | None = None
    if spec.scope_kind != "fixture":
        source_ids, scope_evidence = _production_scope_evidence(
            spec=spec,
            identity=identity,
            data_root=data_root,
        )
    validate_production_identity(
        identity,
        expected_source_ids=source_ids,
        expected_scope=scope_evidence,
        expected_scope_kind=spec.scope_kind,
        project_root=project_root if spec.scope_kind != "fixture" else None,
    )
    if identity.get("extraction_id") != spec.production_extraction_id:
        raise ValueError("run-spec production extraction ID differs from checked identity")


def _production_scope_evidence(
    *, spec: RunSpec, identity: dict[str, object], data_root: Path
) -> tuple[list[str], dict[str, object]]:
    """Join a non-fixture run spec to the sealed source release on disk."""
    preimage = identity["preimage"]
    if not isinstance(preimage, dict):
        raise ValueError("production identity preimage is invalid")
    scope = preimage["production_scope"]
    if not isinstance(scope, dict):
        raise ValueError("production identity scope is invalid")
    manifest_ref = scope["source_manifest"]
    completion_ref = scope["release_completion"]
    if not isinstance(manifest_ref, dict) or not isinstance(completion_ref, dict):
        raise ValueError("production identity source references are invalid")

    manifest_path = (data_root / spec.source_manifest_relative_path).resolve()
    completion_path = manifest_path.parent / "completion_record.json"
    configured_completion = spec.source_manifest_relative_path.parent / "completion_record.json"
    if (
        spec.source_release_version != scope["source_release_version"]
        or spec.source_manifest_relative_path.as_posix() != manifest_ref["path"]
        or configured_completion.as_posix() != completion_ref["path"]
        or not manifest_path.is_relative_to(data_root.resolve())
        or not manifest_path.is_file()
        or not completion_path.is_file()
    ):
        raise ValueError("run spec differs from production source scope")

    manifest = json.loads(manifest_path.read_text())
    model_source_records = [
        item for item in manifest["sources"] if item.get("source_role") == "model_corpus"
    ]
    model_source_ids = [item["source_id"] for item in model_source_records]
    if spec.scope_kind == "representative_pilot":
        source_ids = [owner.source_id for owner in spec.document_owners]
        missing = [source_id for source_id in source_ids if source_id not in model_source_ids]
        if missing:
            raise ValueError(f"representative pilot selects non-model sources: {missing}")
        positions = [model_source_ids.index(source_id) for source_id in source_ids]
        if positions != sorted(positions):
            raise ValueError("representative pilot sources differ from sealed manifest order")
    else:
        source_ids = model_source_ids
    selected_source_ids = set(source_ids)
    ordered_source_records = [
        {
            "source_id": item["source_id"],
            "sha256": item["sha256"],
            "pdf_page_count": item["pdf_page_count"],
        }
        for item in model_source_records
        if item["source_id"] in selected_source_ids
    ]
    evidence = {
        "source_release_version": manifest["source_release_version"],
        "source_manifest_sha256": sha256_file(manifest_path),
        "release_completion_sha256": sha256_file(completion_path),
        "ordered_source_records_sha256": canonical_sha256(ordered_source_records),
    }
    return source_ids, evidence
