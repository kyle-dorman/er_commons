"""Readable behavioral gates for the Task 03F.1 contract validator."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError
from typer.testing import CliRunner

from er_commons.cli import app
from er_commons.corpus_extraction_contract import (
    CorpusExtractionContractError,
    validate_contract_bundle,
    validate_fixture_directory,
    validate_production_identity,
)
from er_commons.corpus_extraction_contract.checks import canonical_sha256
from er_commons.corpus_extraction_contract.fixture_validation import (
    apply_fixture_mutation,
    load_contract_fixtures,
    validate_declared_negative_mutation,
)

ROOT = Path(__file__).parents[1]
SCHEMA_PATH = (
    ROOT
    / "benchmarks"
    / "er_bench"
    / "schemas"
    / "corpus_extraction"
    / "v1"
    / "records.schema.json"
)
FIXTURE_ROOT = ROOT / "benchmarks" / "er_bench" / "fixtures" / "corpus_extraction" / "v1"
FIXTURES = load_contract_fixtures(SCHEMA_PATH, FIXTURE_ROOT)


def bundle() -> dict[str, object]:
    """Return an isolated valid bundle for one focused behavior test."""
    return copy.deepcopy(FIXTURES.bundle)


def assert_contract_error(code: str, value: dict[str, object]) -> CorpusExtractionContractError:
    """Validate one bundle and return its stable, contextual contract failure."""
    with pytest.raises(CorpusExtractionContractError) as raised:
        validate_contract_bundle(value)
    assert raised.value.code == code
    return raised.value


def test_positive_fixtures_validate_without_mutation() -> None:
    original_bundle = copy.deepcopy(FIXTURES.bundle)
    original_identity = copy.deepcopy(FIXTURES.identity)

    FIXTURES.schema_validator.validate(FIXTURES.bundle)
    FIXTURES.schema_validator.validate(FIXTURES.identity)
    validate_contract_bundle(FIXTURES.bundle)
    validate_production_identity(
        FIXTURES.identity,
        expected_source_ids=FIXTURES.expected_source_ids,
        expected_scope=FIXTURES.production_scope_evidence,
        project_root=None,
    )

    assert FIXTURES.bundle == original_bundle
    assert FIXTURES.identity == original_identity


def test_fixture_directory_and_cli_run_the_same_offline_gate() -> None:
    validate_fixture_directory(SCHEMA_PATH, FIXTURE_ROOT)
    result = CliRunner().invoke(
        app,
        [
            "extraction",
            "validate-contract",
            "--schema",
            str(SCHEMA_PATH),
            "--fixtures",
            str(FIXTURE_ROOT),
        ],
    )
    assert result.exit_code == 0
    assert result.stdout == "restartable_extraction_contract=valid\n"


@pytest.mark.parametrize(
    "mutation",
    FIXTURES.mutations,
    ids=[mutation["name"] for mutation in FIXTURES.mutations],
)
def test_every_declared_negative_fixture_fails_as_named(
    mutation: dict[str, object],
) -> None:
    validate_declared_negative_mutation(FIXTURES, mutation)


def test_schema_mutation_still_reports_jsonschema_failure() -> None:
    invalid = bundle()
    apply_fixture_mutation(
        invalid,
        {
            "path": ["document_completions", 0, "raw_docling_status"],
            "value": "PARTIAL_SUCCESS",
        },
    )
    with pytest.raises(ValidationError):
        FIXTURES.schema_validator.validate(invalid)


def test_retryable_attempt_can_precede_a_successful_retry() -> None:
    value = bundle()
    retry_id = "txv1-cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
    retry_events = [
        _event(retry_id, "fixture_alpha", 1, 1, None, "selected", "PENDING"),
        _event(retry_id, "fixture_alpha", 1, 2, "selected", "running", "STARTED"),
        _event(
            retry_id,
            "fixture_alpha",
            1,
            3,
            "running",
            "failed_retryable",
            "FAILURE",
        ),
    ]
    for event in value["state_events"]:
        if event["source_id"] == "fixture_alpha":
            event["attempt"] = 2
    value["state_events"] = [*retry_events, *value["state_events"]]

    validate_contract_bundle(value)


def test_completion_source_must_match_transaction_and_scope() -> None:
    value = bundle()
    value["document_completions"][0]["source"]["source_id"] = "fixture_beta"
    error = assert_contract_error("completion_source", value)
    assert error.subject == value["document_completions"][0]["transaction_id"]


def test_accounting_covers_every_scope_terminal_transaction() -> None:
    value = bundle()
    transaction_id = "txv1-dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
    value["state_events"].extend(
        [
            _event(transaction_id, "fixture_gamma", 1, 1, None, "selected", "PENDING"),
            _event(transaction_id, "fixture_gamma", 1, 2, "selected", "running", "STARTED"),
            _event(
                transaction_id,
                "fixture_gamma",
                1,
                3,
                "running",
                "failed_terminal",
                "FAILURE",
            ),
        ]
    )
    assert_contract_error("scope_transactions", value)


def test_failed_source_cannot_contribute_a_target_index_entry() -> None:
    value = bundle()
    entry = value["target_index"]["entries"][0]
    entry["source_id"] = "fixture_beta"
    entry["source_ordinal"] = 2
    value["target_index"]["entries_sha256"] = canonical_sha256(value["target_index"]["entries"])
    assert_contract_error("index_source", value)


def test_resolution_targets_must_exist_in_the_sealed_index() -> None:
    value = bundle()
    value["resolution_completion"]["resolutions"][0]["candidate_target_ids"] = ["invented-target"]
    assert_contract_error("resolution_target", value)


def test_resolution_source_must_be_an_eligible_candidate() -> None:
    value = bundle()
    value["resolution_completion"]["resolutions"][0]["source_candidate_id"] = (
        "docv1-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    )
    assert_contract_error("resolution_source", value)


def test_production_identity_is_anchored_to_independent_scope_evidence() -> None:
    identity = copy.deepcopy(FIXTURES.identity)
    identity["preimage"]["production_scope"]["ordered_source_ids"][0] = "invented_source"
    digest = canonical_sha256(identity["preimage"])
    identity["identity_sha256"] = digest
    identity["extraction_id"] = f"exv1-{digest}"

    with pytest.raises(CorpusExtractionContractError) as raised:
        validate_production_identity(
            identity,
            expected_source_ids=FIXTURES.expected_source_ids,
            expected_scope=FIXTURES.production_scope_evidence,
        )
    assert raised.value.code == "production_scope"


def test_scope_records_do_not_claim_task04_acceptance() -> None:
    assert FIXTURES.bundle["task04_freezes"] == []
    assert FIXTURES.bundle["handoff"]["task04_status"] == "not_evaluated"


def _event(
    transaction_id: str,
    source_id: str,
    attempt: int,
    sequence: int,
    from_state: str | None,
    to_state: str,
    docling_status: str,
) -> dict[str, object]:
    """Build one explicit state event for lifecycle-focused tests."""
    return {
        "record_type": "document_state_event",
        "schema_version": "er_commons.document_state_event.v1",
        "transaction_id": transaction_id,
        "source_id": source_id,
        "attempt": attempt,
        "sequence": sequence,
        "from_state": from_state,
        "to_state": to_state,
        "raw_docling_status": docling_status,
    }
