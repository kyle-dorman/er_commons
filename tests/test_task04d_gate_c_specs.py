"""Offline closure checks for Task 04D's Gate C production specifications."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.collection_processing.config import load_collection_run_spec
from er_commons.document_publication.config import load_document_run_spec
from er_commons.document_publication.production_identity import validate_production_identity
from er_commons.document_records.document_references.relinking_config import (
    load_document_link_run_spec,
)

ROOT = Path(__file__).parents[1]
IDENTITY = (
    ROOT / "benchmarks/er_bench/fixtures/document_publication/v5/task04d_production_identity.json"
)
DOCUMENT_SPEC = ROOT / "configs/brisbane_baylands_2025_deir_task04d_document_v1.json"
LINK_SPEC = ROOT / "configs/brisbane_baylands_2025_deir_task04d_link_v1.json"
COLLECTION_SPEC = ROOT / "configs/brisbane_baylands_2025_deir_task04d_collection_v1.json"


def test_gate_c_specs_bind_one_fresh_closed_35_source_lineage() -> None:
    """Keep production, document, and link specs mutually consistent."""
    identity = json.loads(IDENTITY.read_bytes())
    document, _ = load_document_run_spec(DOCUMENT_SPEC)
    link, _ = load_document_link_run_spec(LINK_SPEC)
    collection, _ = load_collection_run_spec(COLLECTION_SPEC)
    source_ids = list(link.selected_source_ids)

    validated = validate_production_identity(
        identity,
        expected_source_ids=source_ids,
        expected_scope_kind="production_full",
        project_root=ROOT,
    )
    assert len(source_ids) == 35
    assert validated.value == document.production_extraction_id
    assert document.production_identity_relative_path == IDENTITY.relative_to(ROOT)
    assert [item.source_id for item in document.document_processes] == source_ids
    assert (
        link.replacement_production_identity_recipe_ref.path
        == IDENTITY.relative_to(ROOT).as_posix()
    )
    assert (
        link.replacement_production_identity_recipe_ref.resolve(
            repository_root=ROOT, artifact_root=ROOT
        )
        == IDENTITY
    )
    assert link.document_publication_spec_ref.path == DOCUMENT_SPEC.relative_to(ROOT).as_posix()
    assert (
        link.collection_run_spec_ref.resolve(repository_root=ROOT, artifact_root=ROOT)
        == COLLECTION_SPEC
    )
    assert collection.document_run_spec == Path(DOCUMENT_SPEC.name)
    assert collection.document_evidence_mode == "downstream_replay_only"
    assert collection.source_ids == link.selected_source_ids
    assert link.reviewed_navigation is not None
    assert set(link.reviewed_navigation.source_ids) == {
        "deir_appendix_a",
        "deir_appendix_k2_part_1_of_5",
        "deir_main",
    }


def test_gate_c_specs_pass_their_closed_json_schemas() -> None:
    """Validate all three checked-in configuration artifacts offline."""
    pairs = (
        (
            IDENTITY,
            ROOT
            / "benchmarks/er_bench/schemas/document_publication/v2/production_identity.schema.json",
        ),
        (
            DOCUMENT_SPEC,
            ROOT
            / "benchmarks/er_bench/schemas/document_publication/v2/document_run_spec.schema.json",
        ),
        (
            LINK_SPEC,
            ROOT / "benchmarks/er_bench/schemas/document_linking/v1/document_link_run.schema.json",
        ),
        (
            COLLECTION_SPEC,
            ROOT
            / (
                "benchmarks/er_bench/schemas/collection_processing/v2/"
                "collection_run_spec.schema.json"
            ),
        ),
    )
    for value_path, schema_path in pairs:
        value = json.loads(value_path.read_bytes())
        schema = json.loads(schema_path.read_bytes())
        Draft202012Validator(schema).validate(value)


def test_production_identity_avoids_a_run_spec_checksum_cycle() -> None:
    """Bind the run contract in production and the actual run in each candidate."""
    identity = json.loads(IDENTITY.read_bytes())
    artifacts = {
        item["path"] for item in identity["preimage"]["document_process_contract"]["artifacts"]
    }
    assert (
        "benchmarks/er_bench/schemas/document_linking/v1/document_link_run.schema.json" in artifacts
    )
    assert LINK_SPEC.relative_to(ROOT).as_posix() not in artifacts
