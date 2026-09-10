"""Offline checks for the exact Task 03H production-full specification set."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator

from er_commons.artifact_io import sha256_file
from er_commons.collection_processing.config import load_collection_run_spec
from er_commons.document_parsing.content_parsing.config import load_content_parsing_config
from er_commons.document_publication import fresh_preflight
from er_commons.document_publication.config import load_document_run_spec
from er_commons.document_publication.config_generation import process_templates
from er_commons.document_publication.fresh_preflight import validate_fresh_build_templates
from er_commons.document_publication.input_preparation import completed_candidate_markers
from er_commons.document_publication.process_inputs import (
    ProcessConfigs,
    verify_process_resource_contract,
)
from er_commons.document_publication.production_identity import validate_production_identity
from er_commons.document_records.document_references.config import DocumentReferenceConfig
from er_commons.document_records.document_structure.config import (
    load_document_structure_config,
)
from er_commons.document_records.record_mapping.config import load_record_mapping_config
from er_commons.hierarchy_inference.config import load_hierarchy_inference_config
from er_commons.source_family_catalog import SourceFamilyCatalog

ROOT = Path(__file__).parents[1]
CONFIG_ROOT = ROOT / "configs"
DOCUMENT_SPEC = CONFIG_ROOT / "brisbane_baylands_2025_deir_task03h_document_v3.json"
COLLECTION_SPEC = CONFIG_ROOT / "brisbane_baylands_2025_deir_task03h_collection_v3.json"
CATALOG = CONFIG_ROOT / "brisbane_baylands_2025_deir_task03h_v3_source_family_catalog_v1.json"
ZERO_SHA = "0" * 64
ZERO_PRV1 = f"prv1-{ZERO_SHA}"
ZERO_EXV1 = f"exv1-{ZERO_SHA}"
ZERO_HCORV1 = f"hcorv1-{ZERO_SHA}"


def test_task03h_v3_specs_and_identity_are_strict_native_v2() -> None:
    document, _ = load_document_run_spec(DOCUMENT_SPEC)
    collection, _ = load_collection_run_spec(COLLECTION_SPEC)
    identity_path = ROOT / document.production_identity_relative_path
    identity = json.loads(identity_path.read_text())
    schemas = {
        DOCUMENT_SPEC: ROOT
        / "benchmarks/er_bench/schemas/document_publication/v2/document_run_spec.schema.json",
        COLLECTION_SPEC: ROOT
        / "benchmarks/er_bench/schemas/collection_processing/v2/collection_run_spec.schema.json",
        identity_path: ROOT
        / "benchmarks/er_bench/schemas/document_publication/v2/production_identity.schema.json",
    }
    for value_path, schema_path in schemas.items():
        Draft202012Validator(json.loads(schema_path.read_text())).validate(
            json.loads(value_path.read_text())
        )

    catalog_value = json.loads(CATALOG.read_text())
    source_ids = [source["source"]["source_id"] for source in catalog_value["sources"]]
    assert len(source_ids) == 35
    assert sum(source["source"]["pdf_page_count"] for source in catalog_value["sources"]) == 48_341
    assert (
        sum(source["source"]["byte_size"] for source in catalog_value["sources"]) == 1_519_926_399
    )
    assert [selection.source_id for selection in document.document_processes] == source_ids
    assert [item.source_id for item in document.hierarchy_dispositions] == source_ids
    assert list(collection.source_ids) == source_ids
    page_counts = [source["source"]["pdf_page_count"] for source in catalog_value["sources"]]
    assert page_counts == sorted(page_counts)
    assert document.scope_kind == "production_full"
    assert document.artifact_relative_root == Path(
        "pipelines/brisbane_baylands/task_03h_clean_full_v3/document_publications"
    )
    assert all(selection.lineage_mode == "fresh_build" for selection in document.document_processes)
    assert all(item.authority == "machine_validation" for item in document.hierarchy_dispositions)
    assert all(item.authorization_relative_path is None for item in document.hierarchy_dispositions)
    assert identity["preimage"]["production_scope"]["allowed_scope_kinds"] == ["production_full"]
    collection_artifacts = {
        item["path"] for item in identity["preimage"]["collection_process_contract"]["artifacts"]
    }
    assert (
        "benchmarks/er_bench/schemas/collection_processing/v2/records.schema.json"
        in collection_artifacts
    )
    document_code = {
        item["path"] for item in identity["preimage"]["document_process_contract"]["owned_code"]
    }
    assert "scripts/prepare_task03h.py" in document_code
    validated = validate_production_identity(
        identity,
        expected_source_ids=source_ids,
        expected_scope_kind="production_full",
    )
    assert validated.value == document.production_extraction_id


def test_all_210_task03h_process_configs_load_and_match_their_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    document, _ = load_document_run_spec(DOCUMENT_SPEC)
    catalog = json.loads(CATALOG.read_text())
    expected = {source["source"]["source_id"]: source["source"] for source in catalog["sources"]}
    manifest = tmp_path / document.source_manifest_relative_path
    manifest.parent.mkdir(parents=True)
    manifest.write_text("{}\n")
    monkeypatch.setattr(
        fresh_preflight,
        "sha256_file",
        lambda _path: "fede3e4af815378b77a7f7f54c863ef095328da789859d4f4b25a524f3408f38",
    )
    observed: set[Path] = set()

    for selection in document.document_processes:
        source = expected[selection.source_id]
        paths = {role: ROOT / path for role, path in selection.configs.model_dump().items()}
        assert not observed.intersection(paths.values())
        observed.update(paths.values())
        content, _ = load_content_parsing_config(paths["content_parsing"])
        heading, _ = load_content_parsing_config(paths["heading_evidence_parsing"])
        mapping, _ = load_record_mapping_config(paths["record_mapping"])
        hierarchy, _ = load_hierarchy_inference_config(paths["hierarchy_inference"])
        structure, _ = load_document_structure_config(paths["document_structure"])
        references = DocumentReferenceConfig.load(paths["document_reference_linking"])
        for producer in (content, heading):
            assert producer.source.source_id == selection.source_id
            assert producer.source.expected_sha256 == source["sha256"]
            assert producer.source.expected_byte_size == source["byte_size"]
            assert producer.source.expected_pdf_page_count == source["pdf_page_count"]
        assert mapping.selected_source_id == selection.source_id
        assert mapping.producer_run_id == ZERO_PRV1
        assert hierarchy.source.source_id == selection.source_id
        assert hierarchy.producer_run_id == ZERO_PRV1
        assert hierarchy.publication_authorization == "machine_validation"
        assert hierarchy.bounded_acceptance_config_relative_path is None
        assert structure.source.source_id == selection.source_id
        assert structure.control_profile == "strict_quality_gate"
        assert structure.baseline_candidate_id == ZERO_EXV1
        assert structure.baseline_producer_run_id == ZERO_PRV1
        assert structure.hierarchy_producer_run_id == ZERO_PRV1
        assert structure.hierarchy_candidate_id == ZERO_HCORV1
        assert references.source_id == selection.source_id
        assert references.upstream_candidate_id == ZERO_EXV1
        assert references.upstream_completion_sha256 == ZERO_SHA
        assert references.upstream_inventory_sha256 == ZERO_SHA
        assert references.source_family_catalog_sha256 == sha256_file(CATALOG)
        configs = ProcessConfigs(**paths)
        validate_fresh_build_templates(
            configs=configs,
            source_id=selection.source_id,
            disposition=document.hierarchy_disposition(selection.source_id),
            data_root=tmp_path,
        )
        verify_process_resource_contract(configs, document)

    assert len(observed) == 210


def test_task03h_generation_owns_current_templates() -> None:
    request = SimpleNamespace(
        templates={
            role: Path("configs/task03h_templates") / f"{role}.json"
            for role in process_templates.PROCESS_ROLES
        },
        project_path=lambda path: ROOT / path,
    )
    templates = process_templates.load_process_templates(request)

    assert set(templates) == {
        "content_parsing",
        "heading_evidence_parsing",
        "record_mapping",
        "hierarchy_inference",
        "document_structure",
        "document_reference_linking",
    }
    assert all((CONFIG_ROOT / "task03h_templates" / f"{role}.json").is_file() for role in templates)


def test_task03h_catalog_is_exact_and_multipart_aliases_are_conservative() -> None:
    catalog = SourceFamilyCatalog.load(CATALOG)
    value = json.loads(catalog.raw_bytes)
    sources = value["sources"]
    assert [source["source"]["source_id"] for source in sources][0] == "deir_appendix_k4"
    assert [source["source"]["pdf_page_count"] for source in sources] == sorted(
        source["source"]["pdf_page_count"] for source in sources
    )
    assert all(source["family_root_source_id"] == "deir_main" for source in sources)
    multipart = [source for source in sources if "_part_" in source["source"]["source_id"]]
    assert len(multipart) == 9
    assert all(source["document_role"] == "top_level_appendix" for source in multipart)
    assert all(
        "appendix k1" not in source["reference_aliases"]
        and "appendix k2" not in source["reference_aliases"]
        for source in multipart
    )
    explicit = catalog.cross_document_match(
        source_id="deir_main",
        mention_class="appendix",
        lookup_key="appendix k1 part 1 of 4",
        source_text="See Appendix K1 Part 1 of 4.",
        mention_start=4,
        mention_end=27,
    )
    assert explicit is not None
    assert explicit.intended_target_source_ids == ("deir_appendix_k1_part_1_of_4",)
    assert (
        catalog.cross_document_match(
            source_id="deir_main",
            mention_class="appendix",
            lookup_key="appendix k1",
            source_text="See Appendix K1.",
            mention_start=4,
            mention_end=15,
        )
        is None
    )


def test_task03h_collection_hashes_exact_accepted_policy_bytes() -> None:
    collection, _ = load_collection_run_spec(COLLECTION_SPEC)
    target = CONFIG_ROOT / "brisbane_baylands_2025_deir_task03g2_target_policy_v1.json"
    resolution = CONFIG_ROOT / "brisbane_baylands_2025_deir_task03g2_resolution_policy_v1.json"
    assert collection.document_run_spec.name == DOCUMENT_SPEC.name
    assert collection.blocking_policy == "all_sources_successful"
    assert collection.document_evidence_mode == "document_attempt"
    assert collection.ordering_policy_version == "record_target_order_v2"
    assert collection.target_policy_sha256 == sha256_file(target)
    assert collection.resolution_policy_sha256 == sha256_file(resolution)


def test_preparation_scans_only_the_explicit_namespace(tmp_path: Path) -> None:
    """Historical completions do not block a distinct explicitly selected namespace."""
    historical = tmp_path / "old/records/completion_record.json"
    historical.parent.mkdir(parents=True)
    historical.write_text("{}")
    selected = tmp_path / "new"
    assert completed_candidate_markers(selected) == []
    current = selected / "documents/current/records/completion_record.json"
    current.parent.mkdir(parents=True)
    current.write_text("{}")
    assert completed_candidate_markers(selected) == [
        "documents/current/records/completion_record.json"
    ]
