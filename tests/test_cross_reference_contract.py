"""Gate B schema and fixture tests for Task 03E.5.

These checks validate the frozen contract without implementing production
mention detection, target-index construction, or candidate materialization.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from er_commons.cross_reference_contract import (
    CrossReferenceContractError,
    validate_cross_reference_contract,
)

ROOT = Path(__file__).parents[1]
SCHEMA_PATH = (
    ROOT
    / "benchmarks"
    / "er_bench"
    / "schemas"
    / "canonical_extraction"
    / "v3"
    / "cross_references.schema.json"
)
FIXTURE_ROOT = ROOT / "benchmarks" / "er_bench" / "fixtures" / "canonical_extraction" / "v3"
SCHEMA = json.loads(SCHEMA_PATH.read_text())
DEVELOPMENT = json.loads((FIXTURE_ROOT / "development_cases.json").read_text())
FROZEN_REVIEW = json.loads((FIXTURE_ROOT / "frozen_review_cases.json").read_text())
CONTRACT = json.loads((FIXTURE_ROOT / "valid_cross_reference_contract.json").read_text())
INVALID_MUTATIONS = json.loads((FIXTURE_ROOT / "invalid_mutations.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)
UPSTREAM_ALIAS_EVIDENCE = copy.deepcopy(CONTRACT["upstream_alias_evidence"])
TARGET_EVIDENCE_BLOCKS = copy.deepcopy(CONTRACT["target_evidence_blocks"])
TARGET_RECORDS = copy.deepcopy(CONTRACT["target_records"])
PHYSICAL_PAGE_NUMBERS = {
    CONTRACT["source_blocks"][0]["regions"][0]["page_id"]: 1,
    CONTRACT["target_records"][0]["page_ids"][0]: 2,
}


def _lookup(value: Any, path: list[Any]) -> Any:
    target = value
    for part in path:
        target = target[part]
    return target


def _mutate(value: dict[str, Any], mutation: dict[str, Any]) -> None:
    target: Any = value
    for part in mutation["path"][:-1]:
        target = target[part]
    replacement = (
        copy.deepcopy(_lookup(value, mutation["copy_from"]))
        if "copy_from" in mutation
        else mutation["value"]
    )
    target[mutation["path"][-1]] = replacement


def _validate_expected_status(mention: dict[str, Any]) -> None:
    count = mention["candidate_count"]
    status = mention["resolution_status"]
    reason = mention["unresolved_reason"]
    expected = "unresolved" if count == 0 else "resolved" if count == 1 else "ambiguous"
    if status != expected:
        raise CrossReferenceContractError("fixture status disagrees with candidate count")
    if (status == "unresolved") != (reason is not None):
        raise CrossReferenceContractError("fixture unresolved reason disagrees with status")
    if len(mention["target_types"]) != count:
        raise CrossReferenceContractError("fixture target-type count disagrees with candidates")


def validate_inventory(inventory: dict[str, Any]) -> None:
    """Validate checksum, span, order, and expected-status fixture invariants."""
    seen_names: set[str] = set()
    seen_blocks: set[int] = set()
    for case in inventory["cases"]:
        if case["name"] in seen_names or case["source"]["block_sequence"] in seen_blocks:
            raise CrossReferenceContractError("fixture case or source block is duplicated")
        seen_names.add(case["name"])
        seen_blocks.add(case["source"]["block_sequence"])

        source = case["source"]
        text = source["canonical_text"]
        if hashlib.sha256(text.encode()).hexdigest() != source["text_sha256"]:
            raise CrossReferenceContractError("fixture source checksum drifted")

        previous_key: tuple[int, int] | None = None
        for expected in [*case["expected_mentions"], *case["expected_diagnostics"]]:
            start, end = expected["source_charspan"]
            if start >= end or text[start:end] != expected["raw_text"]:
                raise CrossReferenceContractError("fixture span does not reproduce literal text")
            key = (start, end)
            if previous_key is not None and key < previous_key:
                raise CrossReferenceContractError("fixture spans are not in source order")
            previous_key = key
            if "candidate_count" in expected:
                _validate_expected_status(expected)


def validate_contract_fixture(bundle: dict[str, Any]) -> None:
    """Exercise the responsibility-owned validator with frozen external evidence."""
    validate_cross_reference_contract(
        bundle,
        upstream_alias_evidence=UPSTREAM_ALIAS_EVIDENCE,
        target_evidence_blocks=TARGET_EVIDENCE_BLOCKS,
        target_records=TARGET_RECORDS,
        physical_page_numbers=PHYSICAL_PAGE_NUMBERS,
    )


def test_v3_schema_and_positive_fixtures_are_valid() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    for fixture in (DEVELOPMENT, FROZEN_REVIEW, CONTRACT):
        VALIDATOR.validate(fixture)
    validate_inventory(DEVELOPMENT)
    validate_inventory(FROZEN_REVIEW)
    validate_contract_fixture(CONTRACT)


def test_schema_owns_new_records_support_and_correspondence_shapes() -> None:
    assert {
        "cross_reference",
        "candidate",
        "target_index_entry",
        "target_record",
        "upstream_alias_evidence",
        "canonical_target_alias",
        "target_index_support",
        "summary_support",
        "preservation_support",
        "support_file",
        "identity_extension",
        "manifest_extension",
        "completion",
        "publication_policy",
    } <= SCHEMA["$defs"].keys()


def test_development_and_frozen_review_sources_are_disjoint() -> None:
    development_blocks = {case["source"]["block_sequence"] for case in DEVELOPMENT["cases"]}
    frozen_blocks = {case["source"]["block_sequence"] for case in FROZEN_REVIEW["cases"]}
    assert development_blocks.isdisjoint(frozen_blocks)
    assert {260, 274, 280, 320, 405, 575, 736, 1537, 1594} <= frozen_blocks


def test_table_and_figure_precision_boundary_is_frozen() -> None:
    development = {case["name"]: case for case in DEVELOPMENT["cases"]}
    frozen = {case["name"]: case for case in FROZEN_REVIEW["cases"]}

    table_mentions = [
        development["table_body_mention_with_verified_target_alias"]["expected_mentions"][0],
        frozen["table_generalizes_through_verified_target_alias"]["expected_mentions"][0],
    ]
    assert all(item["resolution_status"] == "resolved" for item in table_mentions)
    assert all(
        item["evidence_kinds"] == ["verified_same_page_table_label"] for item in table_mentions
    )
    assert [item["target_page_distances"] for item in table_mentions] == [[1], [5]]

    external_table = frozen["qualified_external_table_reference_stays_unresolved"][
        "expected_mentions"
    ][0]
    assert external_table["candidate_count"] == 0
    assert external_table["unresolved_reason"] == "qualified_external_table_reference"

    figure = frozen["figure_remains_unresolved_without_target_evidence"]["expected_mentions"][0]
    assert figure["candidate_count"] == 0
    assert figure["unresolved_reason"] == "accepted_target_type_unavailable"


def test_multiple_alias_rows_for_one_target_remain_one_candidate() -> None:
    section = CONTRACT["cross_references"][0]
    assert section["resolution_status"] == "resolved"
    assert len(section["candidates"]) == 1
    assert len(section["candidates"][0]["alias_record_ids"]) == 2
    assert len(section["candidates"][0]["upstream_alias_record_ids"]) == 2


@pytest.mark.parametrize(
    "mutation", INVALID_MUTATIONS, ids=[item["name"] for item in INVALID_MUTATIONS]
)
def test_invalid_mutations_fail(mutation: dict[str, Any]) -> None:
    invalid = copy.deepcopy(CONTRACT)
    _mutate(invalid, mutation)
    if mutation["kind"] == "schema":
        with pytest.raises(ValidationError):
            VALIDATOR.validate(invalid)
    else:
        with pytest.raises(CrossReferenceContractError):
            validate_contract_fixture(invalid)


def test_external_evidence_cannot_be_self_authenticated() -> None:
    invalid = copy.deepcopy(CONTRACT)
    invalid["target_evidence_blocks"][0]["canonical_text"] = "Table 9"
    with pytest.raises(CrossReferenceContractError, match="external evidence"):
        validate_contract_fixture(invalid)


def test_fabricated_upstream_figure_alias_is_rejected() -> None:
    invalid = copy.deepcopy(CONTRACT)
    invalid["target_index"][1]["alias_origin"] = "upstream_v2"
    invalid["target_index"][1]["target_type"] = "figure"
    invalid["target_index"][1]["upstream_alias_record_id"] = (
        "exv1-2222222222222222222222222222222222222222222222222222222222222222/"
        "target-alias/deir_fixture/fakefigure"
    )
    with pytest.raises(CrossReferenceContractError, match="external upstream aliases"):
        validate_contract_fixture(invalid)


def test_synthetic_fixture_cannot_claim_full_candidate_preservation() -> None:
    invalid = copy.deepcopy(CONTRACT)
    invalid["fixture_scope"] = "full_candidate"
    with pytest.raises(ValidationError):
        VALIDATOR.validate(invalid)


def test_table_candidate_outside_five_page_window_is_rejected() -> None:
    target_page_id = CONTRACT["target_records"][0]["page_ids"][0]
    distant_pages = {**PHYSICAL_PAGE_NUMBERS, target_page_id: 7}
    with pytest.raises(CrossReferenceContractError, match="five-page target window"):
        validate_cross_reference_contract(
            CONTRACT,
            upstream_alias_evidence=UPSTREAM_ALIAS_EVIDENCE,
            target_evidence_blocks=TARGET_EVIDENCE_BLOCKS,
            target_records=TARGET_RECORDS,
            physical_page_numbers=distant_pages,
        )


def test_v1_and_v2_cross_reference_boundaries_remain_strict() -> None:
    v1_schema = json.loads(
        (
            ROOT
            / "benchmarks"
            / "er_bench"
            / "schemas"
            / "canonical_extraction"
            / "v1"
            / "records.schema.json"
        ).read_text()
    )
    v2_schema = json.loads(
        (
            ROOT
            / "benchmarks"
            / "er_bench"
            / "schemas"
            / "canonical_extraction"
            / "v2"
            / "semantic_structure.schema.json"
        ).read_text()
    )
    assert v1_schema["$defs"]["cross_reference"]["allOf"][1]["additionalProperties"] is False
    assert v2_schema["$defs"]["fixture_bundle"]["properties"]["cross_references"] == {"const": []}
