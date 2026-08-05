"""Offline identity checks for the exact Task 03G.2 representative pilot."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, cast

import pytest

from er_commons.corpus_extraction.config import RunSpec
from er_commons.corpus_extraction.preflight import _production_scope_evidence
from er_commons.corpus_extraction_contract_v1_1 import CorpusExtractionContractError
from er_commons.corpus_extraction_contract_v1_1.checks import canonical_sha256
from er_commons.corpus_extraction_contract_v1_1.identity import (
    ProductionScopeKind,
    validate_production_identity,
)

ROOT = Path(__file__).parents[1]
CURRENT_IDENTITY = (
    ROOT
    / "benchmarks"
    / "er_bench"
    / "fixtures"
    / "corpus_extraction"
    / "v1_1"
    / "production_identity_preimage.json"
)
HISTORICAL_IDENTITY = CURRENT_IDENTITY.with_name("task03g1a_production_identity_preimage.json")
PILOT_SOURCE_IDS = ["deir_main", "deir_appendix_d", "deir_appendix_p"]


def _pilot_identity() -> dict[str, object]:
    record: dict[str, Any] = copy.deepcopy(json.loads(CURRENT_IDENTITY.read_text()))
    preimage = record["preimage"]
    preimage["contract_revision"] = "task_03g2_representative_pilot_v1"
    preimage["extraction_version_name"] = "brisbane_baylands_representative_pilot_v1"
    preimage["production_scope"]["ordered_source_ids"] = PILOT_SOURCE_IDS
    digest = canonical_sha256(preimage)
    record["extraction_id"] = f"exv1-{digest}"
    record["identity_sha256"] = digest
    return cast(dict[str, object], record)


@pytest.mark.parametrize("scope_kind", ["engineering_smoke", "production_full"])
def test_historical_identity_still_requires_the_complete_35_source_profile(
    scope_kind: ProductionScopeKind,
) -> None:
    record = json.loads(HISTORICAL_IDENTITY.read_text())

    validated = validate_production_identity(
        record,
        expected_source_ids=record["preimage"]["production_scope"]["ordered_source_ids"],
        expected_scope_kind=scope_kind,
    )

    assert validated.value == record["extraction_id"]


def test_representative_pilot_identity_binds_exact_selected_source_order() -> None:
    record = _pilot_identity()

    validated = validate_production_identity(
        record,
        expected_source_ids=PILOT_SOURCE_IDS,
        expected_scope_kind="representative_pilot",
    )

    assert validated.value == record["extraction_id"]


def test_checked_in_identity_is_the_exact_three_source_pilot_recipe() -> None:
    record = json.loads(CURRENT_IDENTITY.read_text())

    validated = validate_production_identity(
        record,
        expected_source_ids=PILOT_SOURCE_IDS,
        expected_scope_kind="representative_pilot",
        project_root=ROOT,
    )

    assert validated.value == record["extraction_id"]


@pytest.mark.parametrize(
    ("expected_ids", "scope_kind"),
    [
        (["deir_main", "deir_appendix_p", "deir_appendix_d"], "representative_pilot"),
        (PILOT_SOURCE_IDS, "production_full"),
    ],
)
def test_representative_pilot_identity_rejects_scope_drift(
    expected_ids: list[str], scope_kind: ProductionScopeKind
) -> None:
    with pytest.raises(CorpusExtractionContractError) as raised:
        validate_production_identity(
            _pilot_identity(),
            expected_source_ids=expected_ids,
            expected_scope_kind=scope_kind,
        )

    assert raised.value.code == "production_scope"


def test_preflight_selects_run_spec_owners_in_manifest_order(tmp_path: Path) -> None:
    manifest_relative = Path("release/records/source_manifest.json")
    manifest_path = tmp_path / manifest_relative
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "source_release_version": "release-v1",
                "sources": [
                    _source_record("deir_main", "1" * 64, 10),
                    _source_record("deir_appendix_d", "2" * 64, 20),
                    _source_record("deir_appendix_o", "3" * 64, 30),
                    _source_record("deir_appendix_p", "4" * 64, 40),
                ],
            }
        )
    )
    (manifest_path.parent / "completion_record.json").write_text("{}")
    spec = _run_spec(manifest_relative, PILOT_SOURCE_IDS)
    identity: dict[str, object] = {
        "preimage": {
            "production_scope": {
                "source_release_version": "release-v1",
                "source_manifest": {"path": manifest_relative.as_posix()},
                "release_completion": {
                    "path": (manifest_relative.parent / "completion_record.json").as_posix()
                },
                "ordered_source_records_sha256": "a" * 64,
            }
        }
    }

    source_ids, evidence = _production_scope_evidence(
        spec=spec,
        identity=identity,
        data_root=tmp_path,
    )

    assert source_ids == PILOT_SOURCE_IDS
    assert evidence["ordered_source_records_sha256"] == canonical_sha256(
        [
            {"source_id": "deir_main", "sha256": "1" * 64, "pdf_page_count": 10},
            {"source_id": "deir_appendix_d", "sha256": "2" * 64, "pdf_page_count": 20},
            {"source_id": "deir_appendix_p", "sha256": "4" * 64, "pdf_page_count": 40},
        ]
    )


def test_preflight_rejects_pilot_owner_order_that_differs_from_manifest(tmp_path: Path) -> None:
    manifest_relative = Path("release/records/source_manifest.json")
    manifest_path = tmp_path / manifest_relative
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "source_release_version": "release-v1",
                "sources": [
                    _source_record("deir_main", "1" * 64, 10),
                    _source_record("deir_appendix_d", "2" * 64, 20),
                    _source_record("deir_appendix_p", "3" * 64, 30),
                ],
            }
        )
    )
    (manifest_path.parent / "completion_record.json").write_text("{}")
    spec = _run_spec(
        manifest_relative,
        ["deir_main", "deir_appendix_p", "deir_appendix_d"],
    )
    identity: dict[str, object] = {
        "preimage": {
            "production_scope": {
                "source_release_version": "release-v1",
                "source_manifest": {"path": manifest_relative.as_posix()},
                "release_completion": {
                    "path": (manifest_relative.parent / "completion_record.json").as_posix()
                },
                "ordered_source_records_sha256": "a" * 64,
            }
        }
    }

    with pytest.raises(ValueError, match="sealed manifest order"):
        _production_scope_evidence(spec=spec, identity=identity, data_root=tmp_path)


def _run_spec(manifest_relative: Path, source_ids: list[str]) -> RunSpec:
    configs = {
        "baseline_producer": "configs/baseline.json",
        "hierarchy_producer": "configs/hierarchy.json",
        "canonical": "configs/canonical.json",
        "hierarchy_correction": "configs/correction.json",
        "semantic": "configs/semantic.json",
        "cross_references": "configs/cross_references.json",
    }
    return RunSpec.model_validate(
        {
            "schema_version": "er_commons.document_run_spec.v1",
            "production_extraction_id": f"exv1-{'a' * 64}",
            "production_identity_relative_path": "identity.json",
            "scope_kind": "representative_pilot",
            "source_release_version": "release-v1",
            "source_manifest_relative_path": manifest_relative.as_posix(),
            "artifact_relative_root": "pipelines/pilot",
            "document_owners": [
                {
                    "source_id": source_id,
                    "lineage_mode": "fresh_build",
                    "configs": configs,
                }
                for source_id in source_ids
            ],
            "hierarchy_dispositions": [
                {"source_id": source_id, "authority": "machine_validation"}
                for source_id in source_ids
            ],
            "resource_policy": {
                "document_concurrency": 1,
                "page_batch_size": 4,
                "stage_batch_size": 4,
                "queue_capacity": 100,
                "cpu_threads_per_document": 4,
                "device": "cpu",
                "memory_estimate_bytes": 1,
                "storage_estimate_bytes": 1,
                "docling_timeout_seconds": None,
                "outer_process_deadline_seconds": 10,
                "cancellation_grace_seconds": 1,
                "retry_limit": 0,
            },
        }
    )


def _source_record(source_id: str, sha256: str, page_count: int) -> dict[str, object]:
    return {
        "source_id": source_id,
        "source_role": "model_corpus",
        "sha256": sha256,
        "pdf_page_count": page_count,
    }
