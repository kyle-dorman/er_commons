"""Qualified substitute preparation verifies compact evidence without PDF reads."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.source_release import local_qualification
from er_commons.source_release.local_qualification import (
    RetainedQualificationObservations,
    RetainedQualificationPolicy,
    assess_retained_qualification,
)
from er_commons.source_release.qualification_request import EvidenceReference
from er_commons.source_release.retained_processing import verify_retained_source


def _write(path: Path, value: Any) -> dict[str, Any]:
    """Write and seal synthetic compact records."""
    raw = json.dumps(value).encode()
    path.write_bytes(raw)
    return {"name": path.name, "byte_size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _fixture(root: Path) -> tuple[Path, EvidenceReference]:
    """Build a synthetic closed receipt whose source is forbidden to read."""
    source = root / "source.part"
    source.write_bytes(b"synthetic PDF fixture")
    stat = source.stat()
    snapshot = {"byte_size": stat.st_size, "inode": stat.st_ino, "mtime_ns": stat.st_mtime_ns}
    attempt = {
        "schema_version": "er_commons.recovery.gate2_attempt.v1",
        "source_ref": {
            "relative_path": source.name,
            "stream_sha256": "a" * 64,
            "byte_size": stat.st_size,
            "observed_inode": stat.st_ino,
            "observed_mtime_ns": stat.st_mtime_ns,
        },
    }
    seal = _write(root / "attempt.json", attempt)
    policy = RetainedQualificationPolicy.model_validate(
        {
            "schema_version": "retained_qualification_policy_v1",
            "source_sha256": "a" * 64,
            "page_count": 4,
            "exceptions": [
                {"object_id": 1, "generation": 0, "physical_page": 1, "reference_path": "/Thumb"}
            ],
            "diagnostic_refs": ["attempt.json#sha256=" + seal["sha256"]],
            "cover_page": 1,
            "cover_title": "Report",
            "project_phrase": "Brisbane",
            "edition_phrase": "Final EIR",
            "corroboration_page": 2,
            "corroboration_title": "Report",
            "memo_phrase": "Existing memo",
            "memo_heading_page": 3,
            "memo_body_page": 4,
            "memo_body_phrases": ["MEMORANDUM"],
            "allowed_pages": [1, 2, 3, 4],
        }
    )
    observations = RetainedQualificationObservations.model_validate(
        {
            "source_sha256": "a" * 64,
            "page_count": 4,
            "diagnostic_refs": policy.diagnostic_refs,
            "structural_failures": policy.exceptions,
            "non_thumbnail_references": [],
            "rendered_body_pages": [1],
            "pages": [
                {"physical_page": n, "text": text}
                for n, text in enumerate(
                    ["Report\nBrisbane Final EIR", "Report", "Existing memo", "MEMORANDUM"], 1
                )
            ],
        }
    )
    disposition = assess_retained_qualification(policy, observations)
    assert disposition.qualified
    record = {
        "schema_version": "er_commons.recovery.retained_source_record.v1",
        "status": "qualified_with_reviewed_exceptions",
        "source_sha256": "a" * 64,
        "qualification_policy_sha256": disposition.policy_sha256,
        "pdf_page_count": 4,
        "exceptions": [e.model_dump() for e in policy.exceptions],
        "source_snapshot": snapshot,
        "source_relative_path": "source.part",
    }
    directory = root / "receipt"
    directory.mkdir()
    rows = [
        _write(directory / name, value)
        for name, value in {
            "policy.json": policy.model_dump(mode="json"),
            "observations.json": observations.model_dump(mode="json"),
            "disposition.json": disposition.model_dump(mode="json"),
            "source_record.json": record,
            "publication_script.py": "synthetic archived script",
        }.items()
    ]
    completion = {
        "schema_version": "er_commons.recovery.retained_source_completion.v1",
        "status": "qualified_with_reviewed_exceptions",
        "source_sha256": "a" * 64,
        "policy_sha256": disposition.policy_sha256,
        "owned_implementation_sha256": hashlib.sha256(
            Path(local_qualification.__file__).read_bytes()
        ).hexdigest(),
        "files": rows,
    }
    row = _write(directory / "completion.json", completion)
    return source, EvidenceReference(relative_path="receipt/completion.json", sha256=row["sha256"])


def test_reuse_never_opens_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fresh source equality is not claimed by compact metadata verification."""
    source, ref = _fixture(tmp_path)
    original = Path.open

    def guarded(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path == source:
            raise AssertionError("PDF read forbidden")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    record, _ = verify_retained_source(tmp_path, ref)
    assert record["pdf_page_count"] == 4


@pytest.mark.parametrize(
    "damage",
    [
        "extra",
        "duplicate",
        "evaluator",
        "disposition",
        "evidence",
        "metadata",
        "symlink",
        "completion",
    ],
)
def test_reuse_rejects_corruption(tmp_path: Path, damage: str) -> None:
    """Reject seal, closure, provenance and source snapshot mismatches."""
    source, ref = _fixture(tmp_path)
    directory = tmp_path / "receipt"
    if damage == "extra":
        (directory / "extra.json").write_text("{}")
    elif damage in {"duplicate", "evaluator"}:
        completion = json.loads((directory / "completion.json").read_text())
        if damage == "duplicate":
            completion["files"].append(completion["files"][0])
        else:
            completion["owned_implementation_sha256"] = "b" * 64
        seal = _write(directory / "completion.json", completion)
        ref = ref.model_copy(update={"sha256": seal["sha256"]})
    elif damage == "disposition":
        (directory / "disposition.json").write_text("{}")
    elif damage == "evidence":
        (tmp_path / "attempt.json").write_text("{}")
    elif damage == "metadata":
        source.write_bytes(b"changed source")
    elif damage == "symlink":
        other = tmp_path / "other.part"
        source.rename(other)
        source.symlink_to(other)
    else:
        ref = ref.model_copy(update={"sha256": "0" * 64})
    with pytest.raises(ValueError):
        verify_retained_source(tmp_path, ref)


def test_manifest_adapter_and_resolvers_are_source_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The explicit physical substitute reaches both resolvers without a PDF hash."""
    from er_commons.document_parsing.content_parsing.config import CompleteSource
    from er_commons.document_parsing.content_parsing.sources import resolve_complete_source
    from er_commons.source_release.qualification_request import load_qualification_request
    from er_commons.source_release.retained_processing import (
        publish_retained_manifest,
        validate_processing_source,
    )

    source, ref = _fixture(tmp_path)
    spec = load_qualification_request(
        Path("configs/brisbane_baylands_2025_feir_task06c_qualification_v1.json")
    )
    directory = tmp_path / "receipt"
    record = json.loads((directory / "source_record.json").read_text())
    record.update(
        provenance=spec.provenance.model_dump(mode="json"), limitations=["Bounded review"]
    )
    attempt = json.loads((tmp_path / "attempt.json").read_text())
    attempt["http_observations"] = {
        "original_url": spec.source_url,
        "final_url": spec.source_url,
        "sha256": "a" * 64,
        "access_timestamp_utc": "2026-09-10T00:00:00Z",
        "http_status": 200,
        "response_headers": {"Content-Type": "application/pdf"},
        "redirects": [],
        "original_filename": "final.pdf",
    }
    row = _write(tmp_path / "attempt.json", attempt)
    policy = json.loads((directory / "policy.json").read_text())
    policy["diagnostic_refs"] = ["attempt.json#sha256=" + row["sha256"]]
    observed = json.loads((directory / "observations.json").read_text())
    observed["diagnostic_refs"] = policy["diagnostic_refs"]
    result = assess_retained_qualification(
        RetainedQualificationPolicy.model_validate(policy),
        RetainedQualificationObservations.model_validate(observed),
    )
    record["qualification_policy_sha256"] = result.policy_sha256
    completion = json.loads((directory / "completion.json").read_text())
    changed = {
        "source_record.json": record,
        "policy.json": policy,
        "observations.json": observed,
        "disposition.json": result.model_dump(mode="json"),
    }
    completion["files"] = [
        _write(directory / row["name"], changed[row["name"]]) if row["name"] in changed else row
        for row in completion["files"]
    ]
    completion["policy_sha256"] = result.policy_sha256
    row = _write(directory / "completion.json", completion)
    ref = ref.model_copy(update={"sha256": row["sha256"]})
    monkeypatch.setattr(
        "er_commons.source_release.retained_processing.validate_substitution_evidence",
        lambda *args: None,
    )
    original = Path.open

    def guarded(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path == source:
            raise AssertionError("PDF read forbidden")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    manifest = publish_retained_manifest(
        tmp_path,
        Path("processing"),
        completion_ref=ref,
        acquisition_spec=spec,
        release_version="test_release",
        generated_at_utc="2026-09-10T00:00:00Z",
    )
    record_model = manifest.sources[0]
    assert record_model.source_role == "qualified_substitute"
    assert validate_processing_source(tmp_path, manifest, record_model)
    selected = CompleteSource(
        source_id="feir_appendix_f1",
        expected_sha256="a" * 64,
        expected_byte_size=source.stat().st_size,
        expected_pdf_page_count=4,
        official_title=record_model.official_title,
    )
    assert resolve_complete_source(tmp_path, selected, manifest).source_id == "feir_appendix_f1"
    # Exercise the producer-to-table request and actual sealed table preparation.
    from test_table_reconstruction_orchestration import _config

    from er_commons.document_parsing.table_reconstruction.pipeline import (
        TablePipelineServices,
        prepare_table_run,
    )

    table_config = _config("a" * 64)
    table_config.update(
        source_release_version="test_release",
        source_id="feir_appendix_f1",
        source_manifest_relative_path="processing/source_manifest.json",
        expected_pdf_page_count=4,
    )
    table_path = tmp_path / "table.json"
    table_path.write_text(json.dumps(table_config))

    def forbidden_page_count(path: Path) -> int:
        raise AssertionError("qualified PDF page-count reopen forbidden")

    prepared = prepare_table_run(
        tmp_path,
        table_path,
        None,
        TablePipelineServices(pdf_page_count=forbidden_page_count, table_environment=lambda: {}),
        tmp_path,
    )
    assert prepared.source_path == source
    assert prepared.source_manifest_path == tmp_path / "processing/source_manifest.json"
    with pytest.raises(FileExistsError):
        publish_retained_manifest(
            tmp_path,
            Path("processing"),
            completion_ref=ref,
            acquisition_spec=spec,
            release_version="test_release",
            generated_at_utc="2026-09-10T00:00:00Z",
        )
    wrong = record_model.model_copy(update={"source_id": "feir_other"})
    with pytest.raises(ValueError, match="differs"):
        validate_processing_source(tmp_path, manifest, wrong)
    wrong = record_model.model_copy(update={"source_role": "curator_only_response_source"})
    with pytest.raises(ValueError, match="not model_corpus"):
        validate_processing_source(tmp_path, manifest, wrong)
