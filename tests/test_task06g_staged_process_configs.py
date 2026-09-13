from __future__ import annotations

import json
from pathlib import Path

import pytest

from er_commons.document_publication.process_inputs import ProcessConfigs
from er_commons.document_records.record_mapping.identity import extraction_identity_sha256
from er_commons.task06g.staged_process_configs import Task06GProcessConfigResolver

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATION_SPEC = PROJECT_ROOT / "configs/task06/v1/task06g_generation_v1.json"


def _configs(source_id: str) -> ProcessConfigs:
    base = (
        PROJECT_ROOT / "configs/task06/v1" / source_id
        if source_id == "feir_appendix_f1"
        else PROJECT_ROOT / "configs/task03h/v4" / source_id
    )
    task06 = PROJECT_ROOT / "configs/task06/v1" / source_id
    return ProcessConfigs(
        content_parsing=base / "content_parsing.json",
        heading_evidence_parsing=base / "heading_evidence_parsing.json",
        record_mapping=base / "record_mapping.json",
        hierarchy_inference=base / "hierarchy_inference.json",
        document_structure=task06 / "document_structure.json",
        document_reference_linking=task06 / "document_reference_linking.json",
    )


def _completion(root: Path, role: str, candidate_id: str, source_id: str) -> Path:
    records = root / role / candidate_id / "records"
    records.mkdir(parents=True)
    identity_field = {
        "content_parsing": "producer_run_id",
        "heading_evidence_parsing": "producer_run_id",
        "record_mapping": "candidate_id",
        "hierarchy_inference": "candidate_id",
        "document_structure": "extraction_id",
        "document_reference_linking": "extraction_id",
    }[role]
    value: dict[str, object] = {identity_field: candidate_id}
    if role in {"content_parsing", "heading_evidence_parsing"}:
        value["source_id"] = source_id
    (records / "completion_record.json").write_text(json.dumps(value))
    (records / "artifact_inventory.json").write_text('{"complete":true}')
    return records / "completion_record.json"


def _resolver(tmp_path: Path, source_id: str, reused: dict[str, Path]):
    return Task06GProcessConfigResolver(
        data_root=tmp_path,
        project_root=PROJECT_ROOT,
        source_id=source_id,
        templates=_configs(source_id),
        resolved_specs_root=tmp_path / "resolved_specs_v1",
        generation_spec=GENERATION_SPEC,
        reused_completions=reused,
    )


def _trust_synthetic_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        Task06GProcessConfigResolver,
        "_verify_template",
        lambda _self, _entry, _template: None,
    )
    monkeypatch.setattr(
        Task06GProcessConfigResolver,
        "_verify_owner_identity",
        lambda _self, _role, completion, _config, *, reused: completion.parents[1].name,
    )


def test_f1_stages_configs_only_after_predecessor_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _trust_synthetic_owner(monkeypatch)
    source = "feir_appendix_f1"
    content = _completion(tmp_path, "content_parsing", f"prv1-{'1' * 64}", source)
    resolver = _resolver(tmp_path, source, {"content_parsing": content})

    heading_config = resolver.config_for("heading_evidence_parsing")
    with pytest.raises(ValueError, match="unpublished checkpoint"):
        resolver.config_for("record_mapping")
    heading = _completion(tmp_path, "heading_evidence_parsing", f"prv1-{'2' * 64}", source)
    resolver.record_completion("heading_evidence_parsing", heading)
    mapping_config = resolver.config_for("record_mapping")
    mapping_value = json.loads(mapping_config.read_text())
    assert mapping_value["producer_run_id"] == f"prv1-{'1' * 64}"
    assert mapping_value["producer_artifact_relative_root"] == "content_parsing"
    mapping_receipt = json.loads(mapping_config.with_suffix(".receipt.json").read_text())
    assert [
        (item["pointer"], item["source_pointer"]) for item in mapping_receipt["populated_pointers"]
    ] == [
        ("/producer_artifact_relative_root", "/outputs/producer_root"),
        ("/producer_run_id", "/derived_id"),
    ]

    mapping = _completion(tmp_path, "record_mapping", f"exv1-{'3' * 64}", source)
    resolver.record_completion("record_mapping", mapping)
    hierarchy_config = resolver.config_for("hierarchy_inference")
    hierarchy_value = json.loads(hierarchy_config.read_text())
    assert hierarchy_value["producer_run_id"] == f"prv1-{'2' * 64}"
    assert hierarchy_value["producer_artifact_relative_root"] == "heading_evidence_parsing"
    hierarchy = _completion(tmp_path, "hierarchy_inference", f"hcorv1-{'4' * 64}", source)
    resolver.record_completion("hierarchy_inference", hierarchy)

    structure_config = resolver.config_for("document_structure")
    structure_value = json.loads(structure_config.read_text())
    assert structure_value["baseline_candidate_id"] == f"exv1-{'3' * 64}"
    assert structure_value["hierarchy_candidate_id"] == f"hcorv1-{'4' * 64}"
    structure = _completion(tmp_path, "document_structure", f"exv1-{'5' * 64}", source)
    resolver.record_completion("document_structure", structure)

    link_config = resolver.config_for("document_reference_linking")
    link_value = json.loads(link_config.read_text())
    assert link_value["upstream_candidate_id"] == f"exv1-{'5' * 64}"
    link = _completion(tmp_path, "document_reference_linking", f"exv1-{'6' * 64}", source)
    resolver.record_completion("document_reference_linking", link)
    assert heading_config.is_file()
    assert set(resolver.config_references()) == set(_configs(source).as_dict())


@pytest.mark.parametrize("source", ["deir_appendix_a", "deir_main"])
def test_reused_prefix_unlocks_only_structure_then_link(
    tmp_path: Path, source: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    _trust_synthetic_owner(monkeypatch)
    reused = {
        "content_parsing": _completion(tmp_path, "content_parsing", f"prv1-{'1' * 64}", source),
        "heading_evidence_parsing": _completion(
            tmp_path, "heading_evidence_parsing", f"prv1-{'2' * 64}", source
        ),
        "record_mapping": _completion(tmp_path, "record_mapping", f"exv1-{'3' * 64}", source),
        "hierarchy_inference": _completion(
            tmp_path, "hierarchy_inference", f"hcorv1-{'4' * 64}", source
        ),
    }
    resolver = _resolver(tmp_path, source, reused)
    structure = resolver.config_for("document_structure")
    assert json.loads(structure.read_text())["baseline_candidate_id"] == f"exv1-{'3' * 64}"
    completion = _completion(tmp_path, "document_structure", f"exv1-{'5' * 64}", source)
    resolver.record_completion("document_structure", completion)
    link = json.loads(resolver.config_for("document_reference_linking").read_text())
    assert link["artifact_relative_root"] == completion.parents[2].relative_to(tmp_path).as_posix()
    assert (
        Path(link["artifact_relative_root"]).name
        == Path(json.loads(structure.read_text())["artifact_relative_root"]).name
    )


def test_resume_reuses_exact_phase_but_tamper_and_unsealed_config_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _trust_synthetic_owner(monkeypatch)
    source = "feir_appendix_f1"
    content = _completion(tmp_path, "content_parsing", f"prv1-{'1' * 64}", source)
    first = _resolver(tmp_path, source, {"content_parsing": content})
    first.config_for("heading_evidence_parsing")
    second = _resolver(tmp_path, source, {"content_parsing": content})
    config = second.config_for("heading_evidence_parsing")
    assert second.verify_resolved_config("heading_evidence_parsing", config)["authority"] == (
        "artifact_root"
    )

    unsealed = tmp_path / "unsealed.json"
    unsealed.write_text(config.read_text())
    with pytest.raises(ValueError, match="predetermined phase"):
        second.verify_resolved_config("heading_evidence_parsing", unsealed)

    config.write_text("{}")
    with pytest.raises(ValueError, match="phase differs"):
        _resolver(tmp_path, source, {"content_parsing": content}).config_for(
            "heading_evidence_parsing"
        )


def test_process_checkpoint_rejects_completion_without_owner_identity(tmp_path: Path) -> None:
    """A matching directory/completion ID is not an independent identity proof."""
    source = "feir_appendix_f1"
    resolver = _resolver(tmp_path, source, {})
    completion = _completion(tmp_path, "content_parsing", f"prv1-{'1' * 64}", source)
    with pytest.raises(ValueError, match="producer_identity.json"):
        resolver.record_completion("content_parsing", completion)


@pytest.mark.parametrize("mutation", ["producer_root", "inventory", "authority"])
def test_process_checkpoint_recomputes_authority_owned_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    """A sealed ID cannot authorize a changed producer root or inventory reference."""
    _trust_synthetic_owner(monkeypatch)
    source = "feir_appendix_f1"
    completion = _completion(tmp_path, "content_parsing", f"prv1-{'1' * 64}", source)
    resolver = _resolver(tmp_path, source, {})
    checkpoint = resolver.record_completion("content_parsing", completion)
    value = json.loads(checkpoint.read_text())
    if mutation == "producer_root":
        value["outputs"]["producer_root"] = "poisoned/root"
    elif mutation == "inventory":
        value["stage_inventory"]["path"] = value["stage_completion"]["path"]
    else:
        value["stage_inventory"]["authority"] = "repository"
    checkpoint.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="checkpoint (outputs|inventory) differ"):
        resolver._verify_checkpoint("content_parsing", checkpoint)


@pytest.mark.parametrize(
    ("role", "contract_field"),
    [
        ("document_structure", "document_structure_contract"),
        ("document_reference_linking", "cross_reference_contract"),
    ],
)
def test_extraction_stage_identity_uses_owner_shaped_completion_and_preimage(
    tmp_path: Path,
    role: str,
    contract_field: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise the real extraction-ID formula and each owner's completion field."""
    source = "feir_appendix_f1"
    identity: dict[str, object] = {
        "schema_version": "er_commons.extraction_identity.v3",
        "extraction_version_name": "synthetic_owner_shape",
        "upstream_candidate_id": f"exv1-{'0' * 64}",
        contract_field: {"schema_version": f"synthetic.{role}.v1"},
    }
    digest = extraction_identity_sha256(identity)
    candidate_id = f"exv1-{digest}"
    identity.update({"extraction_id": candidate_id, "identity_sha256": digest})
    completion = _completion(tmp_path, role, candidate_id, source)
    records = completion.parent
    (records / "extraction_identity.json").write_text(json.dumps(identity))
    resolver = _resolver(tmp_path, source, {})
    verifier = (
        "er_commons.document_records.document_structure.publication."
        "verify_completed_document_structure"
        if role == "document_structure"
        else "er_commons.document_records.document_references.publication."
        "verify_completed_candidate"
    )
    monkeypatch.setattr(verifier, lambda *_: completion)

    assert resolver._verify_owner_identity(role, completion, Path("unused"), reused=False) == (
        candidate_id
    )
