"""Adapt explicitly qualified Final F1 evidence without rereading source bytes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from er_commons.artifact_io import assert_contained, publish_bytes_no_clobber
from er_commons.source_release import local_qualification
from er_commons.source_release.local_qualification import (
    RetainedQualificationObservations,
    RetainedQualificationPolicy,
    assess_retained_qualification,
)
from er_commons.source_release.models import SourceManifest, SourceRecord, SourceRole
from er_commons.source_release.qualification_request import (
    EvidenceReference,
    QualifiedAcquisitionSpec,
)
from er_commons.source_release.substitution_evidence import validate_substitution_evidence

_STATUS = "qualified_with_reviewed_exceptions"
_MEMBERS = {
    "policy.json",
    "observations.json",
    "disposition.json",
    "source_record.json",
    "publication_script.py",
}


def _compact(path: Path) -> bytes:
    """Read only bounded regular metadata, never a source payload."""
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_048_576:
        raise ValueError(f"invalid compact metadata: {path}")
    return path.read_bytes()


def _contained(root: Path, relative: str) -> Path:
    """Check lexical path components before containment resolves symbolic links."""
    value = Path(relative)
    if value.is_absolute() or ".." in value.parts:
        raise ValueError("metadata path must be relative and contained")
    current = root
    for part in value.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("symbolic evidence or source path is unsupported")
    return assert_contained(root, relative)


def _reference(root: Path, reference: EvidenceReference) -> bytes:
    """Verify an externally pinned compact evidence reference."""
    path = _contained(root, reference.relative_path)
    raw = _compact(path)
    if hashlib.sha256(raw).hexdigest() != reference.sha256:
        raise ValueError(f"retained evidence digest changed: {reference.relative_path}")
    return raw


def verify_retained_source(
    data_root: Path, completion_ref: EvidenceReference
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify exact receipt closure, evaluator provenance and unchanged source stat."""
    completion = json.loads(_reference(data_root, completion_ref))
    if (
        completion.get("schema_version") != "er_commons.recovery.retained_source_completion.v1"
        or completion.get("status") != _STATUS
    ):
        raise ValueError("unsupported retained source completion")
    directory = _contained(data_root, completion_ref.relative_path).parent
    rows = completion["files"]
    if len(rows) != len(_MEMBERS) or {row["name"] for row in rows} != _MEMBERS:
        raise ValueError("retained completion membership differs")
    if {path.name for path in directory.iterdir()} != _MEMBERS | {"completion.json"}:
        raise ValueError("retained receipt contains unexpected files")
    contents = {}
    for row in rows:
        raw = _compact(directory / row["name"])
        if len(raw) != row["byte_size"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("retained receipt member changed")
        if row["name"].endswith(".json"):
            contents[row["name"]] = json.loads(raw)
    implementation = Path(local_qualification.__file__)
    if (
        hashlib.sha256(_compact(implementation)).hexdigest()
        != completion["owned_implementation_sha256"]
    ):
        raise ValueError("retained qualification evaluator implementation changed")
    policy = RetainedQualificationPolicy.model_validate(contents["policy.json"])
    observed = RetainedQualificationObservations.model_validate(contents["observations.json"])
    disposition = assess_retained_qualification(policy, observed)
    if (
        not disposition.qualified
        or disposition.model_dump(mode="json") != contents["disposition.json"]
    ):
        raise ValueError("retained disposition does not reproduce")
    record = contents["source_record.json"]
    if (
        record.get("schema_version") != "er_commons.recovery.retained_source_record.v1"
        or record.get("status") != _STATUS
    ):
        raise ValueError("unsupported retained source record")
    if not (
        completion["source_sha256"] == record["source_sha256"] == policy.source_sha256
        and completion["policy_sha256"]
        == record["qualification_policy_sha256"]
        == disposition.policy_sha256
        and record["pdf_page_count"] == policy.page_count
        and record["exceptions"] == [item.model_dump() for item in policy.exceptions]
    ):
        raise ValueError("retained source identity or policy mismatch")
    evidence = []
    for item in policy.diagnostic_refs:
        relative, digest = item.split("#sha256=")
        evidence.append(
            json.loads(
                _reference(data_root, EvidenceReference(relative_path=relative, sha256=digest))
            )
        )
    attempts = [
        item
        for item in evidence
        if item.get("schema_version") == "er_commons.recovery.gate2_attempt.v1"
    ]
    if len(attempts) != 1:
        raise ValueError("retained source requires one sealed acquisition attempt")
    attempt = attempts[0]
    source_ref = attempt["source_ref"]
    snapshot = record["source_snapshot"]
    if (
        source_ref["relative_path"] != record["source_relative_path"]
        or source_ref["stream_sha256"] != record["source_sha256"]
        or snapshot
        != {
            "byte_size": source_ref["byte_size"],
            "inode": source_ref["observed_inode"],
            "mtime_ns": source_ref["observed_mtime_ns"],
        }
    ):
        raise ValueError("retained source differs from acquisition snapshot")
    path = _contained(data_root, record["source_relative_path"])
    stat = path.stat()
    if (
        path.is_symlink()
        or not path.is_file()
        or snapshot
        != {"byte_size": stat.st_size, "inode": stat.st_ino, "mtime_ns": stat.st_mtime_ns}
    ):
        raise ValueError("retained source metadata changed")
    return record, attempt


def _source_record(
    record: dict[str, Any], attempt: dict[str, Any], spec: QualifiedAcquisitionSpec
) -> SourceRecord:
    """Keep Final edition and original URL provenance visible in pipeline records."""
    http = attempt["http_observations"]
    if (
        record["provenance"] != spec.provenance.model_dump(mode="json")
        or http["original_url"] != spec.source_url
        or http["sha256"] != record["source_sha256"]
    ):
        raise ValueError("retained provenance differs from frozen acquisition request")
    return SourceRecord(
        source_id=spec.provenance.physical_source_id,
        official_title="Appendix F.1 Transportation Impact Assessment [Revised]",
        document_type="final_eir_appendix",
        source_role=SourceRole.QUALIFIED_SUBSTITUTE,
        landing_page_key="selected_final_f1",
        landing_page_url=spec.source_url,
        linked_file_url=spec.source_url,
        final_resolved_url=http["final_url"],
        access_timestamp_utc=http["access_timestamp_utc"],
        http_status=http["http_status"],
        response_headers=http["response_headers"],
        redirect_history=http["redirects"],
        local_path=record["source_relative_path"],
        original_filename=http["original_filename"],
        sha256=record["source_sha256"],
        byte_size=record["source_snapshot"]["byte_size"],
        delivered_mime_type=http["response_headers"]["Content-Type"],
        detected_file_type="pdf",
        pdf_signature_valid=True,
        pdf_page_count=record["pdf_page_count"],
        retrieval_status="retained_complete_download",
        validation_status=_STATUS,
        warnings=[
            *record["limitations"],
            "Final F1 only; Draft edition equivalence not established.",
        ],
        visible_terms_note=(
            "Official public source; public access does not establish an open license."
        ),
    )


def publish_retained_manifest(
    data_root: Path,
    destination: Path,
    *,
    completion_ref: EvidenceReference,
    acquisition_spec: QualifiedAcquisitionSpec,
    release_version: str,
    generated_at_utc: str,
) -> SourceManifest:
    """Publish a fresh reference-only processing manifest; never copy the PDF."""
    record, attempt = verify_retained_source(data_root, completion_ref)
    validate_substitution_evidence(data_root, acquisition_spec)
    source = _source_record(record, attempt, acquisition_spec)
    spec_raw = acquisition_spec.model_dump_json().encode()
    spec_digest = hashlib.sha256(spec_raw).hexdigest()
    manifest = SourceManifest(
        manifest_schema_version="er_commons.retained_processing_manifest.v1",
        source_release_version=release_version,
        generated_at_utc=generated_at_utc,
        source_spec_schema_version=acquisition_spec.schema_version,
        source_spec_sha256=spec_digest,
        visible_terms_note=source.visible_terms_note,
        landing_pages=[],
        sources=[source],
        warnings=source.warnings,
        aggregates={
            "retained_qualification": completion_ref.model_dump(),
            "acquisition_spec": acquisition_spec.model_dump(mode="json"),
            "substitution": record["provenance"],
        },
    )
    directory = _contained(data_root, destination.as_posix())
    directory.mkdir(parents=True, exist_ok=False)
    path = directory / "source_manifest.json"
    raw = manifest.model_dump_json(indent=2).encode() + b"\n"
    publish_bytes_no_clobber(path, raw)
    seal = {
        "schema_version": "er_commons.source_release_completion.v1",
        "source_release_version": release_version,
        "source_spec_sha256": spec_digest,
        "manifest": {
            "local_path": path.relative_to(data_root).as_posix(),
            "byte_size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
    }
    publish_bytes_no_clobber(
        directory / "completion_record.json", json.dumps(seal, indent=2).encode() + b"\n"
    )
    return manifest


def validate_processing_source(
    data_root: Path, manifest: SourceManifest, record: SourceRecord
) -> bool:
    """Allow only a verified explicit substitute; return whether metadata suffices."""
    if record.source_role == SourceRole.MODEL_CORPUS:
        return False
    if (
        record.source_role != SourceRole.QUALIFIED_SUBSTITUTE
        or manifest.manifest_schema_version != "er_commons.retained_processing_manifest.v1"
        or len(manifest.sources) != 1
    ):
        raise ValueError(
            f"source is not model_corpus or a qualified substitute: {record.source_id}"
        )
    reference = EvidenceReference.model_validate(manifest.aggregates["retained_qualification"])
    retained, attempt = verify_retained_source(data_root, reference)
    spec = QualifiedAcquisitionSpec.model_validate(manifest.aggregates["acquisition_spec"])
    validate_substitution_evidence(data_root, spec)
    if (
        record != _source_record(retained, attempt, spec)
        or manifest.aggregates["substitution"] != retained["provenance"]
        or manifest.source_spec_sha256
        != hashlib.sha256(spec.model_dump_json().encode()).hexdigest()
    ):
        raise ValueError("processing manifest differs from qualified source")
    return True
