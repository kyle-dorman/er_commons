"""Offline positive and declared-negative validation for Gate A fixtures."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.corpus_extraction_contract_v1_1.checks import fail
from er_commons.corpus_extraction_contract_v1_1.errors import CorpusExtractionContractError
from er_commons.corpus_extraction_contract_v1_1.identity import validate_production_identity
from er_commons.corpus_extraction_contract_v1_1.model import JsonObject
from er_commons.corpus_extraction_contract_v1_1.synthetic_fixture import build_valid_fixture
from er_commons.corpus_extraction_contract_v1_1.validation import validate_contract_bundle


def validate_fixture_directory(schema_path: Path, fixture_root: Path) -> None:
    """Validate the generated positive corpus, identity recipe, and negatives."""
    schema = _read_object(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    fixture = build_valid_fixture()
    validator.validate(fixture.bundle)
    validate_contract_bundle(fixture.bundle, fixture.artifacts)

    identity = _read_object(fixture_root / "production_identity_preimage.json")
    preimage = identity["preimage"]
    if not isinstance(preimage, dict):
        fail("fixture_shape", "production identity preimage is not an object")
    revision = preimage.get("contract_revision")
    evidence_name = (
        "task03g2_production_scope_evidence.json"
        if revision == "task_03g2_representative_pilot_v1"
        else "production_scope_evidence.json"
    )
    scope_evidence = _read_object(fixture_root / evidence_name)
    production_scope = preimage.get("production_scope")
    if not isinstance(production_scope, dict):
        fail("fixture_shape", "production identity scope is not an object")
    expected_source_ids = production_scope.get("ordered_source_ids")
    if not isinstance(expected_source_ids, list):
        fail("fixture_shape", "production identity source IDs are not a list")
    validator.validate(identity)
    validate_production_identity(
        identity,
        expected_source_ids=expected_source_ids,
        expected_scope=scope_evidence,
    )

    mutations = json.loads((fixture_root / "invalid_mutations.json").read_bytes())
    if not isinstance(mutations, list):
        fail("fixture_shape", "invalid mutations fixture is not a list")
    for mutation in mutations:
        _validate_negative(validator, fixture.bundle, fixture.artifacts, mutation)


def _validate_negative(
    validator: Draft202012Validator,
    bundle: JsonObject,
    artifacts: object,
    mutation: JsonObject,
) -> None:
    invalid = copy.deepcopy(bundle)
    _apply_mutation(invalid, mutation)
    name = str(mutation["name"])
    if mutation["kind"] == "schema":
        if validator.is_valid(invalid):
            fail("negative_fixture", "schema mutation passed", subject=name)
        return
    try:
        validate_contract_bundle(invalid, artifacts)  # type: ignore[arg-type]
    except CorpusExtractionContractError as error:
        if error.code != mutation["expected_error_code"]:
            fail(
                "negative_fixture",
                f"expected {mutation['expected_error_code']}, observed {error.code}",
                subject=name,
            )
    else:
        fail("negative_fixture", "contract mutation passed", subject=name)


def _apply_mutation(value: JsonObject, mutation: JsonObject) -> None:
    path = mutation["path"]
    parent = _follow(value, path[:-1])
    key = path[-1]
    if mutation.get("operation") == "remove":
        del parent[key]
    else:
        parent[key] = copy.deepcopy(mutation["value"])


def _follow(value: Any, path: list[str | int]) -> Any:
    current = value
    for part in path:
        current = current[part]
    return current


def _read_object(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        fail("fixture_shape", "fixture root is not an object", subject=path.as_posix())
    return value
