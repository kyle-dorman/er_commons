"""Gate A behavioral tests for the corrected corpus contract."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.corpus_extraction_contract_v1_1 import CorpusExtractionContractError
from er_commons.corpus_extraction_contract_v1_1.fixture_validation import (
    validate_fixture_directory,
)
from er_commons.corpus_extraction_contract_v1_1.identity import build_index_id
from er_commons.corpus_extraction_contract_v1_1.synthetic_fixture import (
    build_valid_fixture,
)
from er_commons.corpus_extraction_contract_v1_1.validation import (
    validate_contract_bundle,
)

ROOT = Path(__file__).parents[1]
SCHEMA_PATH = ROOT / "benchmarks/er_bench/schemas/corpus_extraction/v1_1/records.schema.json"
FIXTURE_ROOT = ROOT / "benchmarks/er_bench/fixtures/corpus_extraction/v1_1"
SCHEMA = json.loads(SCHEMA_PATH.read_text())
VALIDATOR = Draft202012Validator(SCHEMA)


def test_positive_fixture_proves_required_gate_a_cases() -> None:
    fixture = build_valid_fixture()
    VALIDATOR.validate(fixture.bundle)
    validate_contract_bundle(fixture.bundle, fixture.artifacts)

    accounting = fixture.bundle["accounting"]
    assert accounting["counts"] == {
        "total": 4,
        "complete": 2,
        "complete_with_warnings": 1,
        "failed_terminal": 1,
    }
    manifest = fixture.bundle["resolution_completion"]["mention_input_manifest"]
    assert [row["eligible_mention_count"] for row in manifest["candidates"]] == [5, 0, 0]
    resolutions = fixture.bundle["resolution_completion"]["resolutions"]
    assert {row["status"] for row in resolutions} == {"resolved", "ambiguous", "unresolved"}
    assert [row["unresolved_reason"] for row in resolutions if row["status"] == "unresolved"] == [
        "target_source_failed",
        "target_not_in_scope",
        "target_unavailable",
    ]
    attempts = fixture.bundle["corpus_stage_attempts"]
    assert {row["disposition"] for row in attempts} >= {
        "complete",
        "failed_retryable",
        "cancelled",
    }
    assert fixture.bundle["handoff"]["status"] == "blocked"
    assert fixture.bundle["task04_freezes"] == []


def test_checked_fixture_directory_is_a_single_offline_gate() -> None:
    validate_fixture_directory(SCHEMA_PATH, FIXTURE_ROOT)


def test_eligible_mentions_are_derived_from_independent_stage_one_bytes() -> None:
    fixture = build_valid_fixture()
    invalid = copy.deepcopy(fixture.bundle)
    candidate = invalid["resolution_completion"]["mention_input_manifest"]["candidates"][0]
    candidate["eligible_mentions"].pop()
    candidate["eligible_mention_count"] = 3
    invalid["resolution_completion"]["resolutions"].pop()

    with pytest.raises(CorpusExtractionContractError) as raised:
        validate_contract_bundle(invalid, fixture.artifacts)
    assert raised.value.code == "artifact_join"


def test_changed_stage_one_bytes_fail_the_exact_reference() -> None:
    fixture = build_valid_fixture()
    reference = fixture.bundle["resolution_completion"]["mention_input_manifest"]["candidates"][0][
        "cross_references_ref"
    ]
    fixture.artifacts.values[reference["path"]] += b"{}\n"

    with pytest.raises(CorpusExtractionContractError) as raised:
        validate_contract_bundle(fixture.bundle, fixture.artifacts)
    assert raised.value.code == "artifact_digest"


def test_index_identity_is_order_independent_but_field_sensitive() -> None:
    fixture = build_valid_fixture()
    preimage = fixture.bundle["target_index"]["identity_preimage"]
    assert (
        build_index_id(dict(reversed(list(preimage.items()))))
        == fixture.bundle["target_index"]["index_id"]
    )
    changed = copy.deepcopy(preimage)
    changed["entry_count"] += 1
    assert build_index_id(changed) != fixture.bundle["target_index"]["index_id"]


def test_schema_requires_closed_byte_sized_references() -> None:
    fixture = build_valid_fixture()
    invalid = copy.deepcopy(fixture.bundle)
    del invalid["accounting"]["rows"][0]["terminal_event_ref"]["byte_size"]
    assert not VALIDATOR.is_valid(invalid)
