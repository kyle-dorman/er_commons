"""Strict v2 workflow contracts and explicit read-only legacy boundaries."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from pydantic import ValidationError

from er_commons.collection_processing.compatibility_v1 import load_scope_run_spec_v1
from er_commons.collection_processing.config import (
    CollectionRunSpec,
    load_collection_run_spec,
)
from er_commons.collection_processing.contract_validation import (
    validate_collection_contract_fixtures,
)
from er_commons.document_publication.compatibility_v1 import (
    load_document_run_spec_v1,
)
from er_commons.document_publication.config import (
    DocumentRunSpec,
    load_document_run_spec,
)
from er_commons.document_publication.production_identity import validate_production_identity

ROOT = Path(__file__).parents[1]
DOCUMENT_FIXTURE = ROOT / (
    "benchmarks/er_bench/fixtures/document_publication/v2/document_run_spec.json"
)
DOCUMENT_SCHEMA = ROOT / (
    "benchmarks/er_bench/schemas/document_publication/v2/document_run_spec.schema.json"
)
DOCUMENT_IDENTITY = ROOT / (
    "benchmarks/er_bench/fixtures/document_publication/v2/production_identity.json"
)
DOCUMENT_IDENTITY_SCHEMA = ROOT / (
    "benchmarks/er_bench/schemas/document_publication/v2/production_identity.schema.json"
)
COLLECTION_FIXTURE = ROOT / (
    "benchmarks/er_bench/fixtures/collection_processing/v2/collection_run_spec.json"
)
COLLECTION_SCHEMA = ROOT / (
    "benchmarks/er_bench/schemas/collection_processing/v2/collection_run_spec.schema.json"
)
COLLECTION_RECORDS_SCHEMA = ROOT / (
    "benchmarks/er_bench/schemas/collection_processing/v2/records.schema.json"
)
INVALID_LEGACY_RECORDS = ROOT / (
    "benchmarks/er_bench/fixtures/collection_processing/negative_v2/invalid_legacy_vocabulary.json"
)
V1_DOCUMENT = ROOT / "configs/brisbane_baylands_2025_deir_task03g2_document_v1.json"
V1_COLLECTION = ROOT / "configs/brisbane_baylands_2025_deir_task03g2_scope_v1.json"
V1_IDENTITY = ROOT / (
    "benchmarks/er_bench/fixtures/corpus_extraction/v1_1/production_identity_preimage.json"
)


@pytest.mark.parametrize(
    ("fixture_path", "schema_path"),
    [(DOCUMENT_FIXTURE, DOCUMENT_SCHEMA), (COLLECTION_FIXTURE, COLLECTION_SCHEMA)],
)
def test_v2_config_fixture_matches_checked_schema(fixture_path: Path, schema_path: Path) -> None:
    """Keep checked examples and their strict JSON Schemas synchronized."""
    schema = json.loads(schema_path.read_bytes())
    fixture = json.loads(fixture_path.read_bytes())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(fixture)


def test_v2_models_load_only_v2_operation_vocabulary() -> None:
    """V2 loaders accept the checked examples and expose directional names."""
    document, _ = load_document_run_spec(DOCUMENT_FIXTURE)
    collection, _ = load_collection_run_spec(COLLECTION_FIXTURE)

    assert isinstance(document, DocumentRunSpec)
    assert document.document_processes[0].configs.record_mapping.name == "record_mapping.json"
    assert isinstance(collection, CollectionRunSpec)
    assert collection.source_family_catalog_relative_path.name == "source_family.json"


def test_v2_document_identity_is_native_and_digest_bound() -> None:
    """The current document recipe neither reads nor impersonates the v1.1 identity."""
    schema = json.loads(DOCUMENT_IDENTITY_SCHEMA.read_bytes())
    identity = json.loads(DOCUMENT_IDENTITY.read_bytes())
    Draft202012Validator(schema).validate(identity)

    validated = validate_production_identity(identity, expected_scope_kind="fixture")

    assert validated.value == identity["extraction_id"]


def test_v2_document_identity_rejects_the_historical_recipe() -> None:
    """Current execution never accepts a v1.1 recipe through an implicit adapter."""
    historical = json.loads(V1_IDENTITY.read_bytes())

    with pytest.raises(ValueError, match="schema is not v2"):
        validate_production_identity(historical, expected_scope_kind="fixture")


def test_v2_models_reject_v1_keys_without_aliases() -> None:
    """Legacy bytes cannot cross the executable v2 boundary implicitly."""
    with pytest.raises(ValidationError):
        DocumentRunSpec.model_validate_json(V1_DOCUMENT.read_bytes())
    with pytest.raises(ValidationError):
        CollectionRunSpec.model_validate_json(V1_COLLECTION.read_bytes())


@pytest.mark.parametrize(
    "disposition",
    [
        {"source_id": "alpha", "authority": "bounded_acceptance"},
        {
            "source_id": "alpha",
            "authority": "machine_validation",
            "authorization_relative_path": "reviews/alpha.json",
        },
    ],
)
def test_document_schema_rejects_authority_without_matching_evidence(
    disposition: dict[str, object],
) -> None:
    """The portable schema encodes the hierarchy authority/evidence invariant."""
    schema = json.loads(DOCUMENT_SCHEMA.read_bytes())
    fixture = json.loads(DOCUMENT_FIXTURE.read_bytes())
    fixture["hierarchy_dispositions"] = [disposition]

    errors = list(Draft202012Validator(schema).iter_errors(fixture))

    assert errors


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["document_processes"].append(value["document_processes"][0]),
        lambda value: value["hierarchy_dispositions"][0].update(source_id="other"),
        lambda value: value["resource_policy"].update(
            docling_timeout_seconds=20,
            outer_process_deadline_seconds=20,
        ),
    ],
)
def test_document_model_enforces_cross_field_semantics(
    mutation: Callable[[dict[str, Any]], None],
) -> None:
    """Cross-array and deadline semantics are an explicit typed-validation layer."""
    fixture = json.loads(DOCUMENT_FIXTURE.read_bytes())
    mutation(fixture)

    with pytest.raises(ValidationError):
        DocumentRunSpec.model_validate(fixture)


def test_v1_readers_are_version_specific_and_read_only() -> None:
    """Historical evidence remains readable without becoming a v2 recipe."""
    document, document_sha = load_document_run_spec_v1(V1_DOCUMENT)
    collection, collection_sha = load_scope_run_spec_v1(V1_COLLECTION)

    assert document.schema_version == "er_commons.document_run_spec.v1"
    assert collection.schema_version == "er_commons.scope_run_spec.v1"
    assert len(document_sha) == len(collection_sha) == 64
    with pytest.raises(ValidationError):
        load_document_run_spec_v1(DOCUMENT_FIXTURE)
    with pytest.raises(ValidationError):
        load_scope_run_spec_v1(COLLECTION_FIXTURE)


def test_current_collection_contract_has_one_offline_fixture_gate() -> None:
    """The public v2 validator does not route through the historical v1.1 contract."""
    assert (
        validate_collection_contract_fixtures(
            COLLECTION_SCHEMA,
            COLLECTION_FIXTURE.parent,
        )
        == 1
    )


def test_v2_record_schema_rejects_legacy_stage_identity_vocabulary() -> None:
    """Legacy names and ordering policy cannot cross the current write boundary."""
    schema = json.loads(COLLECTION_RECORDS_SCHEMA.read_bytes())
    invalid_records = json.loads(INVALID_LEGACY_RECORDS.read_bytes())

    for case in invalid_records:
        validator = Draft202012Validator(
            {
                "$ref": f"#/$defs/{case['definition']}",
                "$defs": schema["$defs"],
            }
        )
        assert list(validator.iter_errors(case["record"])), case["definition"]
