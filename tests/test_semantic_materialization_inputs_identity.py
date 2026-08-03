"""Focused tests for Task 03E.4 input verification and identity."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from er_commons.document_extraction.producer_records import CompletionRecord
from er_commons.semantic_materialization.config import (
    BASELINE_CANDIDATE_ID,
    BASELINE_PRODUCER_RUN_ID,
    HIERARCHY_PRODUCER_RUN_ID,
    SOURCE_ID,
    SOURCE_SHA256,
    SemanticMaterializationConfig,
    load_semantic_materialization_config,
)
from er_commons.semantic_materialization.identity import (
    build_semantic_candidate_identity,
    normalized_bridge_preimage,
    normalized_bridge_preimage_sha256,
    normalized_support_preimage_sha256,
)
from er_commons.semantic_materialization.inputs import (
    ArtifactReference,
    SemanticMaterializationInputs,
    VerifiedProducer,
    load_semantic_materialization_inputs,
)
from er_commons.semantic_structure.constants import (
    EXPECTED_AGGREGATE_DIGEST,
    EXPECTED_SEMANTIC_FILE_SET_DIGEST,
)

ROOT = Path(__file__).parents[1]
CONFIG_PATH = ROOT / "configs" / "brisbane_baylands_2025_deir_task03e4_semantic_v1.json"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def _completion(run_id: str, source_manifest_sha256: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "producer_run_id": run_id,
        "producer_status": "complete_with_warnings",
        "publication_status": "complete",
        "source_id": SOURCE_ID,
        "source_sha256": SOURCE_SHA256,
        "source_manifest_sha256": source_manifest_sha256,
        "artifact_inventory": "records/artifact_inventory.json",
        "artifact_inventory_sha256": "a" * 64,
        "completed_at_utc": "2026-07-31T00:00:00+00:00",
    }


def _bridge(candidate_id: str) -> list[dict[str, Any]]:
    return [
        {
            "stable_item_key": "1" * 64,
            "hierarchy_producer_run_id": HIERARCHY_PRODUCER_RUN_ID,
            "hierarchy_raw_pointer": "#/texts/1",
            "baseline_producer_run_id": BASELINE_PRODUCER_RUN_ID,
            "baseline_raw_pointer": "#/texts/2",
            "status": "mapped",
            "canonical_record_ids": [f"{candidate_id}/block/{SOURCE_ID}/blk000001"],
            "disposition": None,
        },
        {
            "stable_item_key": "2" * 64,
            "hierarchy_producer_run_id": HIERARCHY_PRODUCER_RUN_ID,
            "hierarchy_raw_pointer": "#/texts/3",
            "baseline_producer_run_id": BASELINE_PRODUCER_RUN_ID,
            "baseline_raw_pointer": "#/texts/4",
            "status": "permitted_unmapped",
            "canonical_record_ids": [],
            "disposition": "canonical_table_replacement_descendant",
        },
    ]


def test_checked_in_config_is_strict_and_freezes_review_sample() -> None:
    config, digest = load_semantic_materialization_config(CONFIG_PATH)
    assert config.review_pages == (2, 4, 8, 73, 82, 96, 105, 112, 166, 220)
    assert config.baseline_candidate_id == BASELINE_CANDIDATE_ID
    assert len(digest) == 64

    invalid = json.loads(CONFIG_PATH.read_text())
    invalid["artifact_relative_root"] = "../escape"
    with pytest.raises(ValidationError, match="contained relative paths"):
        SemanticMaterializationConfig.model_validate(invalid)


def test_bridge_preimage_breaks_only_candidate_identity_cycle() -> None:
    first = _bridge("exv1-" + "a" * 64)
    second = _bridge("exv1-" + "b" * 64)
    assert normalized_bridge_preimage_sha256(first) == normalized_bridge_preimage_sha256(second)
    assert normalized_bridge_preimage(first)[0]["canonical_record_ids"] == [
        f"<EXTRACTION_ID>/block/{SOURCE_ID}/blk000001"
    ]

    changed = copy.deepcopy(first)
    changed[0]["baseline_raw_pointer"] = "#/texts/99"
    assert normalized_bridge_preimage_sha256(first) != normalized_bridge_preimage_sha256(changed)


def test_support_preimage_normalizes_only_candidate_identity_values() -> None:
    first_id = "exv1-" + "a" * 64
    second_id = "exv1-" + "b" * 64
    first = {
        "new_candidate_id": first_id,
        "nested": [f"{first_id}/block/{SOURCE_ID}/blk000001"],
        "unrelated": f"comparison:{first_id}",
    }
    second = {
        "new_candidate_id": second_id,
        "nested": [f"{second_id}/block/{SOURCE_ID}/blk000001"],
        "unrelated": f"comparison:{first_id}",
    }

    first_hash = normalized_support_preimage_sha256(first)
    assert first_hash == normalized_support_preimage_sha256(second)

    changed_unrelated = copy.deepcopy(second)
    changed_unrelated["unrelated"] = f"comparison:{second_id}"
    assert first_hash != normalized_support_preimage_sha256(changed_unrelated)


def test_input_loader_verifies_all_upstream_seals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data_root = tmp_path / "data"
    project_root = tmp_path / "project"
    config, _ = load_semantic_materialization_config(CONFIG_PATH)

    source_manifest_path = data_root / config.source_manifest_relative_path
    _write_json(
        source_manifest_path,
        {
            "sources": [
                {
                    "source_id": SOURCE_ID,
                    "sha256": SOURCE_SHA256,
                    "pdf_page_count": 222,
                }
            ]
        },
    )
    manifest_sha = hashlib.sha256(source_manifest_path.read_bytes()).hexdigest()

    baseline_root = data_root / config.baseline_candidate_relative_root
    _write_json(
        baseline_root / "records" / "completion_record.json",
        {"candidate_id": BASELINE_CANDIDATE_ID},
    )
    _write_json(baseline_root / "records" / "artifact_inventory.json", {"files": []})

    producer_root = data_root / config.baseline_producer_relative_root
    for run_id in (BASELINE_PRODUCER_RUN_ID, HIERARCHY_PRODUCER_RUN_ID):
        _write_json(
            producer_root / run_id / "records" / "completion_record.json",
            _completion(run_id, manifest_sha),
        )
        _write_json(producer_root / run_id / "records" / "artifact_inventory.json", {})

    hierarchy_root = data_root / config.hierarchy_candidate_relative_root
    _write_json(hierarchy_root / "records" / "completion_record.json", {})
    _write_json(hierarchy_root / "records" / "artifact_inventory.json", {})
    acceptance_path = data_root / config.bounded_acceptance_relative_path
    _write_json(acceptance_path, {"status": "accepted_with_known_limitations"})
    comparison_path = data_root / config.producer_comparison_relative_path
    comparison_path.parent.mkdir(parents=True, exist_ok=True)
    comparison_path.write_bytes(b"verified-comparison\n")
    comparison_sha = hashlib.sha256(comparison_path.read_bytes()).hexdigest()

    monkeypatch.setattr(
        "er_commons.semantic_materialization.inputs.verify_completed_candidate",
        lambda root, candidate_id: root / "records" / "completion_record.json",
    )
    monkeypatch.setattr(
        "er_commons.semantic_materialization.inputs.verify_completed_run",
        lambda root, run_id: root / "records" / "completion_record.json",
    )
    control = {"acceptance_status": "accepted_with_known_limitations"}
    monkeypatch.setattr(
        "er_commons.semantic_materialization.inputs.verify_task03e2d_control",
        lambda root, path: control,
    )
    monkeypatch.setattr(
        "er_commons.semantic_materialization.inputs.EXPECTED_PRODUCER_COMPARISON_SHA256",
        comparison_sha,
    )

    inputs = load_semantic_materialization_inputs(
        data_root=data_root,
        project_root=project_root,
        config=config,
    )
    assert inputs.baseline_producer.run_id == BASELINE_PRODUCER_RUN_ID
    assert inputs.hierarchy_producer.run_id == HIERARCHY_PRODUCER_RUN_ID
    assert inputs.control_provenance is control
    assert inputs.producer_comparison_ref.sha256 == comparison_sha


def test_identity_binds_every_normative_input(tmp_path: Path) -> None:
    project_root = tmp_path
    config, _ = load_semantic_materialization_config(CONFIG_PATH)
    config_copy = project_root / "config.json"
    config_copy.write_bytes(CONFIG_PATH.read_bytes())
    spec = project_root / config.semantic_spec_relative_path
    schema = project_root / config.semantic_schema_relative_path
    owned = project_root / "src" / "owned.py"
    for path, raw in ((spec, b"spec"), (schema, b"schema"), (owned, b"code")):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    baseline_completion = _completion(BASELINE_PRODUCER_RUN_ID, "3" * 64)
    hierarchy_completion = _completion(HIERARCHY_PRODUCER_RUN_ID, "3" * 64)
    inputs = SemanticMaterializationInputs(
        baseline_candidate_root=tmp_path / "baseline",
        baseline_completion={"candidate_id": BASELINE_CANDIDATE_ID},
        baseline_completion_ref=ArtifactReference("baseline/completion.json", "4" * 64),
        baseline_inventory_ref=ArtifactReference("baseline/inventory.json", "5" * 64),
        baseline_producer=VerifiedProducer(
            BASELINE_PRODUCER_RUN_ID,
            CompletionRecord.model_validate(baseline_completion),
            ArtifactReference("baseline-producer/completion.json", "6" * 64),
            ArtifactReference("baseline-producer/inventory.json", "7" * 64),
        ),
        hierarchy_producer=VerifiedProducer(
            HIERARCHY_PRODUCER_RUN_ID,
            CompletionRecord.model_validate(hierarchy_completion),
            ArtifactReference("hierarchy-producer/completion.json", "8" * 64),
            ArtifactReference("hierarchy-producer/inventory.json", "9" * 64),
        ),
        hierarchy_candidate_root=tmp_path / "hierarchy",
        hierarchy_completion_ref=ArtifactReference("hierarchy/completion.json", "a" * 64),
        hierarchy_inventory_ref=ArtifactReference("hierarchy/inventory.json", "b" * 64),
        bounded_acceptance_ref=ArtifactReference("acceptance.json", "c" * 64),
        producer_comparison_ref=ArtifactReference("comparison.json", "d" * 64),
        control_provenance={"acceptance_status": "accepted_with_known_limitations"},
        source_manifest_ref=ArtifactReference("source_manifest.json", "3" * 64),
    )
    identity = build_semantic_candidate_identity(
        project_root=project_root,
        config_path=config_copy,
        config=config,
        inputs=inputs,
        bridge_entries=_bridge("exv1-" + "e" * 64),
        support_preimages={"candidate_correspondence": {"new_candidate_id": "exv1-" + "e" * 64}},
        owned_paths=(owned,),
    )
    assert identity["extraction_id"].startswith("exv1-")
    assert identity["extraction_id"] != BASELINE_CANDIDATE_ID
    assert identity["baseline_canonical"]["inventory"]["sha256"] == "5" * 64
    assert identity["producer_inputs"]["comparison"]["sha256"] == "d" * 64
    correction = identity["hierarchy_correction"]
    assert correction["semantic_file_set_sha256"] == EXPECTED_SEMANTIC_FILE_SET_DIGEST
    assert correction["aggregate_semantic_sha256"] == EXPECTED_AGGREGATE_DIGEST
    contract = identity["semantic_contract"]
    assert contract["bridge_preimage_sha256"] == normalized_bridge_preimage_sha256(
        _bridge("exv1-" + "f" * 64)
    )
    assert set(contract) == {
        "policy_version",
        "specification",
        "schema",
        "configuration",
        "bridge_preimage_sha256",
        "support_preimage_sha256s",
        "owned_code_bundle_sha256",
    }
