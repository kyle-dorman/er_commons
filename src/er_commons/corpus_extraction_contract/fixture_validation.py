"""Offline loading and negative testing of the checked contract fixtures."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.corpus_extraction_contract.checks import fail
from er_commons.corpus_extraction_contract.errors import CorpusExtractionContractError
from er_commons.corpus_extraction_contract.identity import validate_production_identity
from er_commons.corpus_extraction_contract.model import JsonObject


@dataclass(frozen=True)
class ContractFixtures:
    """The schema, positive examples, and declared negative mutations."""

    schema_validator: Draft202012Validator
    bundle: JsonObject
    identity: JsonObject
    mutations: tuple[JsonObject, ...]
    project_root: Path
    expected_source_ids: list[str]
    production_scope_evidence: JsonObject


def load_contract_fixtures(schema_path: Path, fixture_root: Path) -> ContractFixtures:
    """Load checked JSON files and independently derive the production source order."""
    project_root = _find_project_root(schema_path)
    schema = _read_object(schema_path)
    Draft202012Validator.check_schema(schema)
    source_spec = _read_object(
        project_root / "configs" / "brisbane_baylands_2025_deir_sources_v1.json"
    )
    source_ids = [
        source["source_id"] for source in source_spec["sources"] if source["role"] == "model_corpus"
    ]
    mutations = json.loads((fixture_root / "invalid_mutations.json").read_bytes())
    if not isinstance(mutations, list):
        fail("fixture_shape", "invalid mutations fixture is not a list")
    return ContractFixtures(
        schema_validator=Draft202012Validator(schema),
        bundle=_read_object(fixture_root / "valid_contract_bundle.json"),
        identity=_read_object(fixture_root / "production_identity_preimage.json"),
        mutations=tuple(mutations),
        project_root=project_root,
        expected_source_ids=source_ids,
        production_scope_evidence=_read_object(fixture_root / "production_scope_evidence.json"),
    )


def validate_fixture_directory(schema_path: Path, fixture_root: Path) -> None:
    """Validate both positive fixtures and every declared negative mutation."""
    from er_commons.corpus_extraction_contract.validation import validate_contract_bundle

    fixtures = load_contract_fixtures(schema_path, fixture_root)
    fixtures.schema_validator.validate(fixtures.bundle)
    fixtures.schema_validator.validate(fixtures.identity)
    validate_contract_bundle(fixtures.bundle)
    validate_production_identity(
        fixtures.identity,
        expected_source_ids=fixtures.expected_source_ids,
        expected_scope=fixtures.production_scope_evidence,
        # v1 is immutable historical evidence after the versioned v1.1 successor.
        # Its digest and scope remain valid; current checked bytes belong to v1.1.
        project_root=None,
    )
    for mutation in fixtures.mutations:
        validate_declared_negative_mutation(fixtures, mutation)


def validate_declared_negative_mutation(
    fixtures: ContractFixtures,
    mutation: JsonObject,
) -> None:
    """Require one named mutation to fail at its declared validation boundary."""
    from er_commons.corpus_extraction_contract.validation import validate_contract_bundle

    original = (
        fixtures.identity if mutation["fixture"] == "production_identity" else fixtures.bundle
    )
    invalid = copy.deepcopy(original)
    apply_fixture_mutation(invalid, mutation)
    if mutation["kind"] == "schema":
        if fixtures.schema_validator.is_valid(invalid):
            fail("negative_fixture", "schema mutation passed", subject=mutation["name"])
        return
    try:
        if mutation["fixture"] == "production_identity":
            validate_production_identity(invalid)
        else:
            validate_contract_bundle(invalid)
    except CorpusExtractionContractError as error:
        if error.code != mutation["expected_error_code"]:
            fail(
                "negative_fixture",
                f"expected {mutation['expected_error_code']}, observed {error.code}",
                subject=mutation["name"],
            )
    else:
        fail("negative_fixture", "contract mutation passed", subject=mutation["name"])


def apply_fixture_mutation(value: JsonObject, mutation: JsonObject) -> None:
    """Apply the small JSON-path mutation language used by negative fixtures."""
    path = mutation["path"]
    parent = _follow_path(value, path[:-1])
    key = path[-1]
    if mutation.get("operation", "replace") == "remove":
        del parent[key]
        return
    replacement = (
        copy.deepcopy(_follow_path(value, mutation["copy_from"]))
        if "copy_from" in mutation
        else copy.deepcopy(mutation["value"])
    )
    parent[key] = replacement


def _follow_path(value: Any, path: list[str | int]) -> Any:
    current = value
    for part in path:
        current = current[part]
    return current


def _read_object(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        fail("fixture_shape", "fixture root is not an object", subject=path.as_posix())
    return value


def _find_project_root(path: Path) -> Path:
    for parent in (path.resolve(), *path.resolve().parents):
        if (parent / "pyproject.toml").is_file():
            return parent
    fail("fixture_path", "could not find project root", subject=path.as_posix())
