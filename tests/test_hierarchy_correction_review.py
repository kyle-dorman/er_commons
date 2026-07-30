"""Held-out annotation and evidence-comparison tests."""

from __future__ import annotations

import copy

import pytest
from hierarchy_correction_support import (
    REVIEW_SCHEMA,
    VALID_BUNDLE,
    valid_annotation_bundle,
)
from jsonschema import Draft202012Validator

from er_commons.hierarchy_correction import (
    HierarchyCorrectionContractError,
    build_held_out_evaluation,
    validate_held_out_review_record,
)


def test_annotation_bundle_has_complete_page_coverage() -> None:
    """Validate schema plus exact annotation coverage and order."""
    annotations = valid_annotation_bundle()
    Draft202012Validator(REVIEW_SCHEMA).validate(annotations)
    validate_held_out_review_record(annotations, expected_pages={73})


def test_evaluation_is_derived_from_annotations_and_candidate() -> None:
    """Build, schema-check, and recount one passing held-out evaluation."""
    evaluation = build_held_out_evaluation(valid_annotation_bundle(), VALID_BUNDLE)
    Draft202012Validator(REVIEW_SCHEMA).validate(evaluation)
    validate_held_out_review_record(evaluation)
    assert evaluation["mismatches"] == []
    assert evaluation["status"] == "pass"


@pytest.mark.parametrize(
    "field_name",
    ["source_sha256", "policy_sha256", "code_bundle_sha256"],
)
def test_annotations_must_match_candidate_identity(field_name: str) -> None:
    """Reject evidence sealed for another source, policy, or code bundle."""
    annotations = copy.deepcopy(valid_annotation_bundle())
    candidate_digest = VALID_BUNDLE["identity"][field_name]
    annotations[field_name] = ("0" if candidate_digest[0] != "0" else "1") * 64

    with pytest.raises(HierarchyCorrectionContractError, match=field_name):
        build_held_out_evaluation(annotations, VALID_BUNDLE)
