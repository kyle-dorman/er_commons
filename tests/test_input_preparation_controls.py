"""Prepared control objects are reused without hidden file or manifest hashing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from er_commons.artifact_verification import VerificationBudget
from er_commons.authority_reference import AuthorityReference
from er_commons.document_publication import fresh_preflight, process_inputs
from er_commons.document_publication.config import load_document_run_spec
from er_commons.document_publication.process_inputs import (
    ProcessConfigs,
    verify_reused_completion_inputs,
)


def test_reused_completion_uses_the_compact_completion_hash_role(tmp_path: Path) -> None:
    """A sealed JSON resume input stays hashable without widening the payload allowlist."""
    producer_id = f"prv1-{'1' * 64}"
    completion = tmp_path / "producers" / producer_id / "records/completion_record.json"
    completion.parent.mkdir(parents=True)
    completion.write_text(
        json.dumps({"producer_run_id": producer_id, "source_id": "example"}) + "\n"
    )
    reference = AuthorityReference(
        authority="artifact_root",
        path=completion.relative_to(tmp_path).as_posix(),
        sha256=hashlib.sha256(completion.read_bytes()).hexdigest(),
        byte_size=completion.stat().st_size,
    )
    reused = SimpleNamespace(selected=lambda: {"content_parsing": reference})
    selection = SimpleNamespace(reused_completions=reused)
    prepared = SimpleNamespace(
        repository_root=tmp_path / "repository",
        data_root=tmp_path,
        spec=SimpleNamespace(process_selection=lambda _source_id: selection),
    )

    budget = VerificationBudget()
    verify_reused_completion_inputs(prepared, "example", budget)

    hashed = [item for item in budget.observations if item.get("sha256")]
    assert len(hashed) == 1
    assert hashed[0]["role"] == "completion"


def test_preparsed_controls_do_not_reopen_configs_or_hash_the_manifest(tmp_path, monkeypatch):
    root = Path(__file__).parents[1]
    spec, _ = load_document_run_spec(
        root / "configs/brisbane_baylands_2025_deir_task03h_document_v3.json"
    )
    selected = spec.document_processes[0]
    paths = {role: root / relative for role, relative in selected.configs.model_dump().items()}
    parsed = {role: json.loads(path.read_text()) for role, path in paths.items()}
    configs = ProcessConfigs(**paths)
    link = parsed["document_reference_linking"]
    relative = Path(link["source_manifest_relative_path"])
    manifest = tmp_path / relative
    manifest.parent.mkdir(parents=True)
    manifest.write_text("synthetic metadata; never hash me")

    def forbidden(*args, **kwargs):
        raise AssertionError("reopened an already prepared control")

    monkeypatch.setattr(fresh_preflight, "_json", forbidden)
    monkeypatch.setattr(fresh_preflight, "sha256_file", forbidden)
    monkeypatch.setattr(process_inputs, "load_content_parsing_config", forbidden)
    fresh_preflight.validate_fresh_build_templates(
        configs=configs,
        source_id=selected.source_id,
        disposition=spec.hierarchy_disposition(selected.source_id),
        data_root=tmp_path,
        recorded_manifest_digest=(relative, link["source_manifest_sha256"]),
        parsed_values=parsed,
    )
    process_inputs.verify_process_resource_contract(configs, spec, parsed_values=parsed)


def test_preparation_rejects_transplanted_materialization_source():
    """Record mapping retains its exact one-source/digest selection boundary."""
    import pytest

    from er_commons.document_publication.input_preparation import _require_source_config

    for record in (
        {"source_id": "wrong", "source_sha256": "a" * 64},
        {"source_id": "alpha", "source_sha256": "b" * 64},
    ):
        with pytest.raises(ValueError, match="materialization source"):
            _require_source_config(
                {"ordered_materialization_scope": [record]}, "alpha", "a" * 64, "record_mapping"
            )
