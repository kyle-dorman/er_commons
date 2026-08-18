"""JSON Schema and frozen-evidence tests for hierarchy correction v1."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

import pytest
from hierarchy_correction_support import (
    DEVELOPMENT_CASES,
    INVALID_SCHEMA_MUTATIONS,
    RECORD_SCHEMA,
    VALID_BUNDLE,
    apply_schema_mutation,
)
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from er_commons.hierarchy_correction.digests import canonical_json_sha256


def test_valid_bundle_matches_draft_2020_12_contract() -> None:
    """Validate aggregate shape and its RFC 8785 content identity."""
    Draft202012Validator.check_schema(RECORD_SCHEMA)
    Draft202012Validator(RECORD_SCHEMA).validate(VALID_BUNDLE)
    identity = VALID_BUNDLE["identity"]
    identity_inputs = {key: value for key, value in identity.items() if key != "candidate_id"}
    assert identity["candidate_id"] == f"hcorv1-{canonical_json_sha256(identity_inputs)}"


def test_contract_digests_use_rfc_8785_number_and_key_normalization() -> None:
    """Distinguish the normative digest from ordinary sorted JSON."""
    first = {"z": "é", "number": 1.0, "nested": {"b": False, "a": None}}
    equivalent = {"nested": {"a": None, "b": False}, "number": 1, "z": "é"}
    changed = {"z": "e", "number": 1, "nested": {"a": None, "b": False}}

    assert canonical_json_sha256(first) == canonical_json_sha256(equivalent)
    assert canonical_json_sha256(first) != canonical_json_sha256(changed)


@pytest.mark.parametrize(
    ("definition", "value"),
    [
        ("identity", VALID_BUNDLE["identity"]),
        ("input_inventory", VALID_BUNDLE["input_inventory"]),
        ("feature", VALID_BUNDLE["features"][0]),
        ("toc_entry", VALID_BUNDLE["toc_entries"][0]),
        ("reconciliation", VALID_BUNDLE["reconciliations"][0]),
        ("regime", VALID_BUNDLE["regimes"][0]),
        ("decision", VALID_BUNDLE["decisions"][0]),
        ("hierarchy", VALID_BUNDLE["hierarchy"]),
        (
            "diagnostic",
            {
                "reading_order_index": 1,
                "stable_item_key": VALID_BUNDLE["features"][0]["stable_item_key"],
                "code": "SIBLING_EVIDENCE_CONFLICT",
                "detail": "fixture diagnostic",
            },
        ),
        ("summary", VALID_BUNDLE["summary"]),
        ("metrics", VALID_BUNDLE["metrics"]),
        ("artifact_inventory", VALID_BUNDLE["artifact_inventory"]),
        ("completion", VALID_BUNDLE["completion"]),
    ],
)
def test_each_persisted_record_definition_validates(
    definition: str,
    value: dict[str, Any],
) -> None:
    """Validate each physical record shape, not only the aggregate fixture."""
    Draft202012Validator(
        {
            "$schema": RECORD_SCHEMA["$schema"],
            "$ref": f"#/$defs/{definition}",
            "$defs": RECORD_SCHEMA["$defs"],
        }
    ).validate(value)


def test_document_index_text_may_retain_a_table_parent_pointer() -> None:
    """Accept text descendants when a Docling document index remains text."""
    feature = copy.deepcopy(VALID_BUNDLE["features"][0])
    feature["raw_parent_ref"] = "#/tables/34"

    Draft202012Validator(
        {
            "$schema": RECORD_SCHEMA["$schema"],
            "$ref": "#/$defs/feature",
            "$defs": RECORD_SCHEMA["$defs"],
        }
    ).validate(feature)


def test_failed_attempt_definition_validates() -> None:
    """Keep a schema-valid record for failed, unpublished attempts."""
    attempt = {
        "candidate_id": VALID_BUNDLE["identity"]["candidate_id"],
        "status": "failed",
        "fatal_code": "INPUT_COMPLETION_INVALID",
        "detail": "fixture failure",
    }
    Draft202012Validator(
        {
            "$schema": RECORD_SCHEMA["$schema"],
            "$ref": "#/$defs/attempt_record",
            "$defs": RECORD_SCHEMA["$defs"],
        }
    ).validate(attempt)


def test_picture_caption_disagreement_has_a_fatal_attempt_code() -> None:
    """Keep source-relation disagreement fail-closed before publication."""
    attempt = {
        "candidate_id": VALID_BUNDLE["identity"]["candidate_id"],
        "status": "failed",
        "fatal_code": "PICTURE_CAPTION_RELATION_MISMATCH",
        "detail": "picture caption page differs from owning picture page",
    }
    Draft202012Validator(
        {
            "$schema": RECORD_SCHEMA["$schema"],
            "$ref": "#/$defs/attempt_record",
            "$defs": RECORD_SCHEMA["$defs"],
        }
    ).validate(attempt)


def test_level_gap_is_not_a_fatal_attempt_code() -> None:
    """Keep accepted sparse depth out of the failed-attempt vocabulary."""
    attempt = {
        "candidate_id": VALID_BUNDLE["identity"]["candidate_id"],
        "status": "failed",
        "fatal_code": "HIERARCHY_LEVEL_SKIP",
        "detail": "accepted sparse level",
    }
    with pytest.raises(ValidationError):
        Draft202012Validator(
            {
                "$schema": RECORD_SCHEMA["$schema"],
                "$ref": "#/$defs/attempt_record",
                "$defs": RECORD_SCHEMA["$defs"],
            }
        ).validate(attempt)


@pytest.mark.parametrize(
    "mutation",
    INVALID_SCHEMA_MUTATIONS,
    ids=[case["name"] for case in INVALID_SCHEMA_MUTATIONS],
)
def test_schema_rejects_invalid_mutation(mutation: dict[str, Any]) -> None:
    invalid = apply_schema_mutation(copy.deepcopy(VALID_BUNDLE), mutation)
    with pytest.raises(ValidationError):
        Draft202012Validator(RECORD_SCHEMA).validate(invalid)


def test_development_cases_are_stable_key_bound() -> None:
    """Recompute each reviewed case key from its frozen producer evidence."""
    for case in DEVELOPMENT_CASES["cases"]:
        identity = {
            "text": case["text"],
            "orig": case["orig"],
            "page_no": case["physical_page"],
            "bbox": case["bbox"],
            "charspan": case["charspan"],
        }
        encoded = json.dumps(
            identity,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        assert hashlib.sha256(encoded).hexdigest() == case["stable_item_key"]


def test_development_evidence_supports_each_expected_rule() -> None:
    """Freeze the local evidence used by bullet, ambiguity, transfer, and numbering rules."""
    cases = {case["case_id"]: case for case in DEVELOPMENT_CASES["cases"]}
    for case_id in ("bullet-general-plan-amendment", "bullet-specific-plan"):
        evidence = cases[case_id]["evidence_context"]
        assert evidence["outline_exact"] is False
        assert evidence["toc_exact"] is False
        assert evidence["segment_list_indent_delta_pt"] >= 18

    structural = cases["plain-visible-subheading"]["evidence_context"]
    assert structural["outline_exact"] is False
    assert structural["toc_exact"] is False
    assert structural["shared_heading_level"] == 2
    assert structural["left_delta_previous_pt"] <= 1
    assert structural["left_delta_next_pt"] <= 1
    assert structural["aligned_line_count"] == 1

    transfer = cases["unsupported-style-existing-district"]["evidence_context"]
    assert len(transfer["cluster_item_keys"]) >= 2
    assert transfer["supported_before_level"] + 1 == transfer["supported_after_level"]
    assert transfer["maximum_cluster_to_after_left_delta_pt"] <= 1

    numbering_cases = [
        case
        for case in DEVELOPMENT_CASES["cases"]
        if case["expected_rule_id"] == "R05_APPLY_NUMBERING_REGIME"
    ]
    assert {case["evidence_context"]["regime_start_item_key"] for case in numbering_cases} == {
        "3a80553fe23f770299c2415d0c6aa357e706597132126d3354a29eac123e0bd3"
    }
    assert all(
        case["expected_level"] == case["evidence_context"]["numbering_depth"]
        for case in numbering_cases
    )
