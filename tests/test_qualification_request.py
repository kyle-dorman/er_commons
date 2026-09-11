"""Source-free request, provenance and command-boundary regression checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from er_commons.cli import app
from er_commons.source_release.qualification_request import (
    QualifiedAcquisitionSpec,
    load_qualification_request,
)
from er_commons.source_release.substitution_evidence import validate_substitution_evidence

CONFIG = Path("configs/brisbane_baylands_2025_feir_task06c_qualification_v1.json")


def test_validation_command_cannot_contact_source(monkeypatch):
    """The Gate 1 command validates the reviewed request without a request or PDF read."""
    import requests

    def forbidden(*args, **kwargs):
        raise AssertionError("source access forbidden")

    monkeypatch.setattr(requests.Session, "request", forbidden)
    result = CliRunner().invoke(
        app, ["sources", "validate-qualification-spec", "--spec", str(CONFIG)]
    )
    assert result.exit_code == 0, result.output
    assert "qualification_spec=valid" in result.output


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        (None, "destination", "../outside"),
        (None, "destination", "/tmp/acquisition"),
        (None, "destination", "datasets/ceqa"),
        ("provenance", "physical_source_id", "feir_appendix_f2"),
        ("provenance", "edition", "draft_eir"),
        ("provenance", "scope_exception", "all_final_sources"),
        ("provenance", "edition_equivalence", "established"),
        ("policy", "expected_document_center_id", 553),
        ("limits", "retries", 1),
        ("limits", "total_timeout_seconds", float("inf")),
    ],
)
def test_request_rejects_changed_scope(section, field, value):
    """The F1 exception cannot silently become a broader processing permission."""
    raw = json.loads(CONFIG.read_text())
    target = raw if section is None else raw[section]
    target[field] = value
    with pytest.raises(ValueError):
        QualifiedAcquisitionSpec.model_validate(raw)


def _evidence_fixture(tmp_path):
    """Create tiny census and source seals without any PDF payload."""
    raw = json.loads(CONFIG.read_text())
    provenance = raw["provenance"]
    provenance["census_ref"]["relative_path"] = "packet/census.json"
    provenance["original_release_ref"]["relative_path"] = "old/records/source_manifest.json"
    census = {
        "format": "er_commons.task06a.f1_substitution_evidence.v1",
        "selected_inventory_records": [
            {
                "linked_url": raw["source_url"],
                "document_center_id": 2972,
                "label": raw["policy"]["advertised_label"],
            }
        ],
        "wrong_source_records": [
            {"source_id": "deir_appendix_f1", "sha256": provenance["wrong_source_sha256"]}
        ],
        "wrong_source_manifest_path": provenance["original_release_ref"]["relative_path"],
        "revision_contexts": [
            {"unit": {"unit_id": value}} for value in provenance["revision_context_unit_ids"]
        ],
    }
    payload = json.dumps(census).encode()
    provenance["census_ref"]["sha256"] = hashlib.sha256(payload).hexdigest()
    path = tmp_path / "packet/census.json"
    path.parent.mkdir()
    path.write_bytes(payload)
    manifest = tmp_path / provenance["original_release_ref"]["relative_path"]
    manifest.parent.mkdir(parents=True)
    manifest.write_bytes(b"preserved manifest, deliberately not parsed")
    seal = {
        "schema_version": "er_commons.source_release_completion.v1",
        "manifest": {
            "local_path": provenance["original_release_ref"]["relative_path"],
            "sha256": provenance["original_release_ref"]["sha256"],
            "byte_size": manifest.stat().st_size,
        },
    }
    (manifest.parent / "completion_record.json").write_text(json.dumps(seal))
    return QualifiedAcquisitionSpec.model_validate(raw)


def test_original_manifest_metadata_only(tmp_path, monkeypatch):
    """Accepted manifest and PDF payloads are never opened during this compact preflight."""
    spec = _evidence_fixture(tmp_path)
    original = Path.open

    def guarded(path, *args, **kwargs):
        if path.name.endswith(".pdf") or path.name == "source_manifest.json":
            raise AssertionError("accepted payload opened")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    validate_substitution_evidence(tmp_path, spec)


@pytest.mark.parametrize("changed", ["census", "seal"])
def test_changed_census_and_original_seal_stop(tmp_path, changed):
    """A receipt cannot quietly retarget the accepted source or revision census."""
    spec = _evidence_fixture(tmp_path)
    if changed == "census":
        census = tmp_path / spec.provenance.census_ref.relative_path
        census.write_bytes(census.read_bytes() + b" ")
        message = "census digest"
    else:
        path = tmp_path / spec.provenance.original_release_ref.relative_path
        completion = path.parent / "completion_record.json"
        payload = json.loads(completion.read_text())
        payload["manifest"]["sha256"] = "0" * 64
        completion.write_text(json.dumps(payload))
        message = "manifest seal"
    with pytest.raises(ValueError, match=message):
        validate_substitution_evidence(tmp_path, spec)


def test_config_is_finite_and_keeps_original_identity():
    """The shipped proposal preserves routing and a separately gated processing contract."""
    spec = load_qualification_request(CONFIG)
    assert spec.policy.expected_document_center_id == 2972
    assert spec.provenance.logical_source_id == "deir_appendix_f1"
    assert spec.provenance.physical_source_id == "feir_appendix_f1"
    assert spec.limits.max_temporary_plus_final_bytes <= 512 * 1024**2
