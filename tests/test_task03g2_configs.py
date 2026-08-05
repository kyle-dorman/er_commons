"""Offline checks for the fresh Task 03G.2 checked-in configuration set."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from er_commons.canonical_extraction.config import load_canonicalization_config
from er_commons.corpus_extraction import fresh_preflight
from er_commons.corpus_extraction.config import load_run_spec
from er_commons.corpus_extraction.fresh_preflight import validate_fresh_build_templates
from er_commons.corpus_extraction.owner_inputs import OwnerConfigs, _require_selected_source
from er_commons.corpus_extraction_contract_v1_1.identity import validate_production_identity
from er_commons.corpus_resolution.catalog import CorpusCatalog
from er_commons.corpus_resolution.config import load_scope_run_spec
from er_commons.cross_reference_enrichment.config import CrossReferenceEnrichmentConfig
from er_commons.document_extraction.producer_config import load_producer_config
from er_commons.hierarchy_correction.configuration import load_hierarchy_correction_config
from er_commons.semantic_materialization.config import load_semantic_materialization_config
from er_commons.source_freeze import sha256_file

ROOT = Path(__file__).parents[1]
CONFIG_ROOT = ROOT / "configs"
DOCUMENT_SPEC = CONFIG_ROOT / "brisbane_baylands_2025_deir_task03g2_document_v1.json"
SCOPE_SPEC = CONFIG_ROOT / "brisbane_baylands_2025_deir_task03g2_scope_v1.json"
ZERO_EXV1 = f"exv1-{'0' * 64}"
ZERO_PRV1 = f"prv1-{'0' * 64}"
ZERO_HCORV1 = f"hcorv1-{'0' * 64}"
EXPECTED_SOURCES = {
    "deir_main": {
        "slug": "main",
        "sha256": "0b81e84176c86205c07d9ae6b2a9994fcd45405e516546bcfc7ab9b1f88cf83f",
        "byte_size": 65_818_524,
        "page_count": 2_092,
    },
    "deir_appendix_d": {
        "slug": "appendix_d",
        "sha256": "0e0d0dc3d5c9d75ca52ec698f3943da59e560e69dde8dfa4763c9afd6673e1c3",
        "byte_size": 62_423_471,
        "page_count": 356,
    },
    "deir_appendix_p": {
        "slug": "appendix_p",
        "sha256": "2dfceac46931a946bc343d52b09104b7b58ed8831bc4f49a03f0b8655e4e6ea1",
        "byte_size": 6_528_561,
        "page_count": 222,
    },
}


def test_document_and_scope_specs_freeze_the_exact_fresh_pilot_shape() -> None:
    document, _ = load_run_spec(DOCUMENT_SPEC)
    scope, _ = load_scope_run_spec(SCOPE_SPEC)
    expected_ids = list(EXPECTED_SOURCES)

    assert document.scope_kind == "representative_pilot"
    identity_path = ROOT / document.production_identity_relative_path
    identity = json.loads(identity_path.read_text())
    assert document.production_extraction_id == identity["extraction_id"]
    assert document.production_extraction_id != ZERO_EXV1
    assert identity["preimage"]["contract_revision"] == "task_03g2_representative_pilot_v1"
    assert (
        validate_production_identity(
            identity,
            expected_source_ids=expected_ids,
            expected_scope_kind="representative_pilot",
            project_root=ROOT,
        ).value
        == document.production_extraction_id
    )
    assert [owner.source_id for owner in document.document_owners] == expected_ids
    assert all(owner.lineage_mode == "fresh_build" for owner in document.document_owners)
    assert [item.source_id for item in document.hierarchy_dispositions] == expected_ids
    assert all(item.authority == "machine_validation" for item in document.hierarchy_dispositions)
    assert all(item.authorization_relative_path is None for item in document.hierarchy_dispositions)
    assert scope.source_ids == tuple(expected_ids)
    assert scope.document_run_spec.name == DOCUMENT_SPEC.name
    assert scope.blocking_policy == "all_sources_successful"
    assert document.artifact_relative_root.as_posix().endswith("task_03g2_representative_pilot")
    resources = document.resource_policy
    assert resources.document_concurrency == 1
    assert resources.cpu_threads_per_document == 4
    assert resources.device == "cpu"
    assert resources.memory_estimate_bytes == 17_179_869_184
    assert resources.storage_estimate_bytes == 107_374_182_400
    assert resources.retry_limit == 1


def test_all_18_owner_templates_load_and_select_only_their_source() -> None:
    document, _ = load_run_spec(DOCUMENT_SPEC)
    observed_paths: set[Path] = set()
    for owner in document.document_owners:
        expected = EXPECTED_SOURCES[owner.source_id]
        configs = owner.configs
        for relative_path in configs.model_dump().values():
            path = ROOT / relative_path
            assert path.is_file()
            assert path not in observed_paths
            observed_paths.add(path)
            _require_selected_source(path, owner.source_id)

        baseline, _ = load_producer_config(ROOT / configs.baseline_producer)
        hierarchy, _ = load_producer_config(ROOT / configs.hierarchy_producer)
        canonical, _ = load_canonicalization_config(ROOT / configs.canonical)
        correction, _ = load_hierarchy_correction_config(ROOT / configs.hierarchy_correction)
        semantic, _ = load_semantic_materialization_config(ROOT / configs.semantic)
        cross_references = CrossReferenceEnrichmentConfig.load(ROOT / configs.cross_references)

        for producer in (baseline, hierarchy):
            assert producer.source.source_id == owner.source_id
            assert producer.source.expected_sha256 == expected["sha256"]
            assert producer.source.expected_byte_size == expected["byte_size"]
            assert producer.source.expected_pdf_page_count == expected["page_count"]
            assert producer.artifact_relative_root.as_posix().endswith(
                "task_03g2_document_producers"
            )
        assert canonical.selected_source_id == owner.source_id
        assert canonical.producer_run_id == ZERO_PRV1
        assert canonical.artifact_relative_root.as_posix().endswith("task_03g2_canonical_records")
        assert correction.source.source_id == owner.source_id
        assert correction.producer_run_id == ZERO_PRV1
        assert correction.publication_authorization == "machine_validation"
        assert correction.bounded_acceptance_artifact_relative_root is None
        assert correction.bounded_acceptance_config_relative_path is None
        assert semantic.source.source_id == owner.source_id
        assert semantic.control_profile == "strict_quality_gate"
        assert semantic.expectations is None
        assert semantic.baseline_candidate_id == ZERO_EXV1
        assert semantic.hierarchy_candidate_id == ZERO_HCORV1
        assert semantic.bounded_acceptance_relative_path is None
        assert semantic.bounded_acceptance_policy_relative_path is None
        assert semantic.producer_comparison_relative_path is None
        assert cross_references.source_id == owner.source_id
        assert cross_references.upstream_candidate_id == ZERO_EXV1
        assert cross_references.upstream_completion_sha256 == "0" * 64
        assert cross_references.upstream_inventory_sha256 == "0" * 64

    assert len(observed_paths) == 18


def test_scope_policy_digests_name_real_checked_in_policy_bytes() -> None:
    scope, _ = load_scope_run_spec(SCOPE_SPEC)
    target = CONFIG_ROOT / "brisbane_baylands_2025_deir_task03g2_target_policy_v1.json"
    resolution = CONFIG_ROOT / "brisbane_baylands_2025_deir_task03g2_resolution_policy_v1.json"

    assert scope.target_policy_sha256 == sha256_file(target)
    assert scope.resolution_policy_sha256 == sha256_file(resolution)
    assert json.loads(target.read_text())["policy_version"] == "task03g2-corpus-target-policy-v1"
    assert (
        json.loads(resolution.read_text())["policy_version"]
        == "task03g2-corpus-resolution-policy-v1"
    )


@pytest.mark.parametrize("source_id", list(EXPECTED_SOURCES))
def test_fresh_template_preflight_accepts_each_source_without_downstream_candidates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source_id: str,
) -> None:
    document, _ = load_run_spec(DOCUMENT_SPEC)
    selected = document.content_owners(source_id)
    configs = OwnerConfigs(
        **{role: ROOT / relative for role, relative in selected.model_dump().items()}
    )
    cross_references = CrossReferenceEnrichmentConfig.load(configs.cross_references)
    manifest = tmp_path / cross_references.source_manifest_relative_path
    manifest.parent.mkdir(parents=True)
    manifest.write_text("{}")
    monkeypatch.setattr(
        fresh_preflight,
        "sha256_file",
        lambda _path: cross_references.source_manifest_sha256,
    )

    final_root, authorization = validate_fresh_build_templates(
        configs=configs,
        source_id=source_id,
        disposition=document.hierarchy_disposition(source_id),
        data_root=tmp_path,
    )

    assert final_root.as_posix().endswith("task_03g2_canonical_records")
    assert authorization is None


def test_checked_in_catalog_is_a_valid_exact_three_source_scope_input(tmp_path: Path) -> None:
    scope, _ = load_scope_run_spec(SCOPE_SPEC)
    checked_in = CONFIG_ROOT / "brisbane_baylands_2025_deir_task03g2_corpus_catalog_v1.json"
    staged = tmp_path / scope.corpus_catalog_relative_path
    staged.parent.mkdir(parents=True)
    staged.write_bytes(checked_in.read_bytes())

    catalog = CorpusCatalog.load(tmp_path, scope.corpus_catalog_relative_path)
    value = json.loads(catalog.raw_bytes)

    assert [item["source"]["source_id"] for item in value["documents"]] == list(EXPECTED_SOURCES)
    assert all(item["lookup_keys"] for item in value["documents"])
    assert catalog.lookup["appendix d"][0]["source_id"] == "deir_appendix_d"
    assert catalog.lookup["appendix p"][0]["source_id"] == "deir_appendix_p"
