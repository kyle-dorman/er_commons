"""Offline tests for the Task 03B canonical extraction contract."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry
from referencing.jsonschema import DRAFT202012

from er_commons.canonical_extraction import (
    ContractError,
    make_record_id,
    pdf_bbox_to_render_pixels,
    validate_bundle_integrity,
)
from er_commons.canonical_extraction.bundle import BundleView
from er_commons.canonical_extraction.layout import RECORD_COLLECTIONS
from er_commons.canonical_extraction.policies.bundle import source_release_matches_documents

ROOT = Path(__file__).parents[1]
SCHEMA_PATH = (
    ROOT
    / "benchmarks"
    / "er_bench"
    / "schemas"
    / "canonical_extraction"
    / "v1"
    / "records.schema.json"
)
FIXTURE_ROOT = ROOT / "benchmarks" / "er_bench" / "fixtures" / "canonical_extraction" / "v1"
SCHEMA = json.loads(SCHEMA_PATH.read_text())
BUNDLE = json.loads((FIXTURE_ROOT / "valid_bundle.json").read_text())
INVALID_MUTATIONS = json.loads((FIXTURE_ROOT / "invalid_mutations.json").read_text())
REGISTRY = Registry().with_resource(SCHEMA["$id"], DRAFT202012.create_resource(SCHEMA))
VALIDATOR = Draft202012Validator(SCHEMA, registry=REGISTRY)
DEFINITION_BY_COLLECTION = {
    "identity": "extraction_identity",
    "manifest": "manifest",
    **{
        collection.bundle_key: collection.record_type.replace("-", "_")
        for collection in RECORD_COLLECTIONS
    },
}


def definition_validator(definition: str) -> Draft202012Validator:
    """Build a validator for one definition without network resolution."""
    return Draft202012Validator(
        {"$ref": f"{SCHEMA['$id']}#/$defs/{definition}"},
        registry=REGISTRY,
    )


def selected_record(bundle: dict[str, Any], collection: str, index: int | None) -> Any:
    """Return the mutation target described by an invalid fixture."""
    value = bundle[collection]
    return value if index is None else value[index]


def apply_mutation(bundle: dict[str, Any], mutation: dict[str, Any]) -> Any:
    """Apply one small invalid-fixture mutation and return its record."""
    record = selected_record(bundle, mutation["collection"], mutation["index"])
    target = record
    for part in mutation["path"][:-1]:
        target = target[part]
    target[mutation["path"][-1]] = mutation["value"]
    return record


def test_schema_bundle_and_every_valid_record() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    VALIDATOR.validate(BUNDLE)
    for collection in RECORD_COLLECTIONS:
        definition = collection.record_type.replace("-", "_")
        validator = definition_validator(definition)
        for record in BUNDLE[collection.bundle_key]:
            validator.validate(record)
    definition_validator("manifest").validate(BUNDLE["manifest"])
    definition_validator("extraction_identity").validate(BUNDLE["identity"])
    assert (
        BUNDLE["identity"]["canonical_contract"]["schema_bundle_sha256"]
        == hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest()
    )


@pytest.mark.parametrize(
    "mutation",
    INVALID_MUTATIONS,
    ids=[case["name"] for case in INVALID_MUTATIONS],
)
def test_invalid_fixtures_fail_their_record_schema(mutation: dict[str, Any]) -> None:
    invalid = copy.deepcopy(BUNDLE)
    record = apply_mutation(invalid, mutation)
    definition = DEFINITION_BY_COLLECTION[mutation["collection"]]
    with pytest.raises(ValidationError):
        definition_validator(definition).validate(record)


def test_valid_fixture_referential_integrity_and_mapping_cardinalities() -> None:
    validate_bundle_integrity(BUNDLE)
    cardinalities = {
        len(item["canonical_table_ids"]) for item in BUNDLE["table_stage_observations"]
    }
    assert cardinalities == {0, 1, 2}


def test_record_ids_are_reproducible_and_use_explicit_prefixes() -> None:
    extraction_id = BUNDLE["manifest"]["extraction_id"]
    expected = BUNDLE["pages"][0]["id"]
    assert make_record_id(extraction_id, "page", "deir_fixture", "p000001") == expected
    assert make_record_id(extraction_id, "page", "deir_fixture", "p000001") == expected
    assert make_record_id(extraction_id, "table-family", "deir_fixture", "fam000001").endswith(
        "/table-family/deir_fixture/fam000001"
    )
    assert make_record_id(extraction_id, "figure", "deir_fixture", "fig000001").endswith(
        "/figure/deir_fixture/fig000001"
    )
    with pytest.raises(ContractError, match="invalid figure local key"):
        make_record_id(extraction_id, "figure", "deir_fixture", "f000001")


def test_document_and_child_record_id_shapes_are_distinct() -> None:
    extraction_id = BUNDLE["manifest"]["extraction_id"]
    document_id = make_record_id(extraction_id, "document", "deir_fixture")
    assert document_id.endswith("/document/deir_fixture")

    with pytest.raises(ContractError, match="do not accept a local key"):
        make_record_id(
            extraction_id,
            "document",
            "deir_fixture",
            "deir_fixture",
        )
    with pytest.raises(ContractError, match="require a local key"):
        make_record_id(extraction_id, "page", "deir_fixture")


def test_record_id_collisions_are_rejected() -> None:
    duplicate = copy.deepcopy(BUNDLE)
    duplicate["blocks"][1]["id"] = duplicate["blocks"][0]["id"]
    with pytest.raises(ContractError, match="duplicate record IDs"):
        validate_bundle_integrity(duplicate)


def test_record_collections_keep_canonical_sequence_order() -> None:
    unordered = copy.deepcopy(BUNDLE)
    unordered["tables"].reverse()
    with pytest.raises(ContractError, match="tables sequence"):
        validate_bundle_integrity(unordered)

    sequence_gap = copy.deepcopy(BUNDLE)
    sequence_gap["tables"][1]["sequence"] = 99
    with pytest.raises(ContractError, match="tables sequence"):
        validate_bundle_integrity(sequence_gap)


def test_regions_must_stay_within_page_bounds() -> None:
    out_of_bounds = copy.deepcopy(BUNDLE)
    out_of_bounds["blocks"][0]["regions"][0]["bbox"][2] = 700.0
    with pytest.raises(ContractError, match="out-of-bounds region"):
        validate_bundle_integrity(out_of_bounds)


def test_coordinate_transform_is_explicit_and_invertible() -> None:
    rendered = pdf_bbox_to_render_pixels((72.0, 400.0, 180.0, 430.0), 792.0, 2.0)
    assert rendered == (144.0, 724.0, 360.0, 784.0)
    left, top, right, bottom = rendered
    assert (left / 2.0, 792.0 - bottom / 2.0, right / 2.0, 792.0 - top / 2.0) == (
        72.0,
        400.0,
        180.0,
        430.0,
    )


def test_partial_document_cannot_finalize_table_families() -> None:
    partial = copy.deepcopy(BUNDLE)
    partial["documents"][0]["document_scope_complete"] = False
    with pytest.raises(ContractError, match="partial document"):
        validate_bundle_integrity(partial)


def test_source_edition_override_must_propagate_exactly() -> None:
    mismatch = copy.deepcopy(BUNDLE)
    mismatch["pages"][0]["source_edition_override"] = None
    with pytest.raises(ContractError, match="source-edition override"):
        validate_bundle_integrity(mismatch)


def test_referential_integrity_rejects_unknown_targets() -> None:
    broken = copy.deepcopy(BUNDLE)
    broken["cross_references"][0]["target_record_ids"] = [
        make_record_id(
            BUNDLE["manifest"]["extraction_id"],
            "section",
            "deir_fixture",
            "sec999999",
        )
    ]
    with pytest.raises(ContractError, match="unknown references"):
        validate_bundle_integrity(broken)


def test_record_id_type_must_match_its_collection() -> None:
    wrong_type = copy.deepcopy(BUNDLE)
    wrong_type["blocks"][0]["id"] = wrong_type["blocks"][0]["id"].replace("/block/", "/table/")
    with pytest.raises(ContractError, match="wrong-type record ID"):
        validate_bundle_integrity(wrong_type)


def test_reference_type_must_match_the_relationship() -> None:
    wrong_reference_type = copy.deepcopy(BUNDLE)
    wrong_reference_type["pages"][0]["routing_observation_id"] = wrong_reference_type["blocks"][0][
        "id"
    ]
    with pytest.raises(ContractError, match="wrong-type reference"):
        validate_bundle_integrity(wrong_reference_type)


def test_table_and_family_membership_must_be_symmetric() -> None:
    wrong_family = copy.deepcopy(BUNDLE)
    wrong_family["tables"][0]["table_family_id"] = wrong_family["table_families"][1]["id"]
    with pytest.raises(ContractError, match="family membership differs"):
        validate_bundle_integrity(wrong_family)


def test_identity_payload_is_content_bound_to_its_digest() -> None:
    mismatched = copy.deepcopy(BUNDLE)
    mismatched["identity"]["source_release"]["ordered_model_corpus"][0]["pdf_page_count"] = 2
    with pytest.raises(ContractError, match="identity and manifest digest"):
        validate_bundle_integrity(mismatched)


def test_materialization_scope_selects_documents_from_full_release() -> None:
    release_source_ids = [
        source["source_id"]
        for source in BUNDLE["identity"]["source_release"]["ordered_model_corpus"]
    ]
    selected_source_ids = BUNDLE["identity"]["materialization_scope"]["ordered_source_ids"]
    assert release_source_ids == ["deir_fixture", "deir_unselected_fixture"]
    assert selected_source_ids == ["deir_fixture"]
    validate_bundle_integrity(BUNDLE)

    unknown_source = copy.deepcopy(BUNDLE)
    unknown_source["identity"]["materialization_scope"]["ordered_source_ids"] = [
        "deir_unselected_fixture"
    ]
    with pytest.raises(ContractError, match="materialization scope differs"):
        source_release_matches_documents(BundleView(unknown_source))

    missing_release_source = copy.deepcopy(BUNDLE)
    missing_release_source["identity"]["source_release"]["ordered_model_corpus"] = [
        missing_release_source["identity"]["source_release"]["ordered_model_corpus"][1]
    ]
    with pytest.raises(ContractError, match="unknown release sources"):
        source_release_matches_documents(BundleView(missing_release_source))

    checksum_mismatch = copy.deepcopy(BUNDLE)
    checksum_mismatch["documents"][0]["source_sha256"] = "0" * 64
    with pytest.raises(ContractError, match="differs from release source"):
        source_release_matches_documents(BundleView(checksum_mismatch))


def test_materialization_scope_binds_ordered_producer_runs() -> None:
    mismatched = copy.deepcopy(BUNDLE)
    mismatched["identity"]["materialization_scope"]["producer_runs"][0]["source_id"] = (
        "deir_unselected_fixture"
    )
    with pytest.raises(ContractError, match="producer run order"):
        source_release_matches_documents(BundleView(mismatched))


def test_dirty_code_is_allowed_only_for_non_release_candidates() -> None:
    non_release = copy.deepcopy(BUNDLE["identity"])
    non_release["project_code"]["git_dirty"] = True
    definition_validator("extraction_identity").validate(non_release)

    release = copy.deepcopy(non_release)
    release["materialization_scope"]["scope_kind"] = "corpus"
    release["materialization_scope"]["release_status"] = "release_candidate"
    with pytest.raises(ValidationError):
        definition_validator("extraction_identity").validate(release)

    release["project_code"]["git_dirty"] = False
    definition_validator("extraction_identity").validate(release)


def test_geometry_coordinate_combinations_and_rotations_are_strict() -> None:
    invalid = copy.deepcopy(BUNDLE["blocks"][0]["regions"][0])
    invalid["coordinate_space"] = "canonical_pdf"
    invalid["origin"] = "top_left"
    with pytest.raises(ValidationError):
        definition_validator("region").validate(invalid)

    rotated = copy.deepcopy(BUNDLE["blocks"][0]["regions"][0])
    rotated["rotation_degrees"] = 90
    rotated["affine_transform"] = None
    with pytest.raises(ValidationError):
        definition_validator("region").validate(rotated)


def test_statuses_cannot_imply_outputs_that_do_not_exist() -> None:
    failed_stage = copy.deepcopy(BUNDLE["table_stage_observations"][1])
    failed_stage["status"] = "failed"
    with pytest.raises(ValidationError):
        definition_validator("table_stage_observation").validate(failed_stage)

    failed_conversion = copy.deepcopy(BUNDLE["conversion_observations"][0])
    failed_conversion["status"] = "failed"
    with pytest.raises(ValidationError):
        definition_validator("conversion_observation").validate(failed_conversion)


def test_canonical_text_changes_require_declared_normalization() -> None:
    invented = copy.deepcopy(BUNDLE)
    invented["blocks"][0]["canonical_text"] = "Invented text"
    with pytest.raises(ContractError, match="unexplained canonical text"):
        validate_bundle_integrity(invented)


def test_table_shape_must_match_its_cells() -> None:
    wrong_shape = copy.deepcopy(BUNDLE)
    wrong_shape["tables"][0]["shape"] = [2, 2]
    with pytest.raises(ContractError, match="cell count differs"):
        validate_bundle_integrity(wrong_shape)


def test_every_canonical_content_record_requires_a_raw_mapping() -> None:
    missing_mapping = copy.deepcopy(BUNDLE)
    missing_mapping["raw_mappings"] = []
    missing_mapping["manifest"]["record_files"][-1]["record_count"] = 0
    with pytest.raises(ContractError, match="missing raw mappings"):
        validate_bundle_integrity(missing_mapping)


def test_human_review_fields_are_rejected_at_any_depth() -> None:
    nested_review = copy.deepcopy(BUNDLE)
    nested_review["routing_observations"][0]["native_text_features"]["reviewer"] = "human"
    with pytest.raises(ContractError, match="human-review field"):
        validate_bundle_integrity(nested_review)


def test_section_hierarchy_cannot_contain_cycles() -> None:
    cycle = copy.deepcopy(BUNDLE)
    cycle["sections"][0]["parent_section_id"] = cycle["sections"][0]["id"]
    with pytest.raises(ContractError, match="hierarchy cycle"):
        validate_bundle_integrity(cycle)


def test_cross_reference_status_must_match_its_targets() -> None:
    false_resolution = copy.deepcopy(BUNDLE)
    false_resolution["cross_references"][0]["resolution_status"] = "resolved"
    with pytest.raises(ContractError, match="exactly one target"):
        validate_bundle_integrity(false_resolution)


def test_raw_link_stage_must_match_its_asset_producer() -> None:
    wrong_producer = copy.deepcopy(BUNDLE)
    wrong_producer["blocks"][0]["raw_links"][0]["producer"] = "pdfium_router"
    with pytest.raises(ContractError, match="producer differs"):
        validate_bundle_integrity(wrong_producer)


def test_review_derivatives_are_not_canonical_assets() -> None:
    review_asset = copy.deepcopy(BUNDLE["assets"][0])
    review_asset["role"] = "page_render"
    with pytest.raises(ValidationError):
        definition_validator("asset").validate(review_asset)


def test_task03d_producer_asset_roles_are_canonical() -> None:
    roles = {asset["role"] for asset in BUNDLE["assets"]}
    assert {
        "clean_table_json",
        "clean_table_cells_json",
        "table_family_assignments_jsonl",
        "table_families_json",
    } <= roles
