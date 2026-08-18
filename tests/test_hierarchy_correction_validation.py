"""Cross-record policy tests for hierarchy correction v1."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from hierarchy_correction_support import (
    VALID_BUNDLE,
    semantic_mutation_cases,
    valid_deep_hierarchy_bundle,
    valid_multiple_roots_bundle,
)

from er_commons.hierarchy_correction import (
    HierarchyCorrectionContractError,
    validate_hierarchy_correction_bundle,
)

SEMANTIC_MUTATION_CASES = semantic_mutation_cases()


def test_valid_bundle_passes_every_cross_record_policy() -> None:
    """Exercise the complete ordered policy registry on the positive fixture."""
    validate_hierarchy_correction_bundle(VALID_BUNDLE)


def test_every_decision_records_r08_as_the_final_eligible_rule() -> None:
    """Keep the always-eligible fallback visible even when an earlier rule wins."""
    for decision in VALID_BUNDLE["decisions"]:
        assert decision["eligible_rule_ids"][-1] == "R08_DEFAULT_PRESERVE"
        if decision["selected_rule_id"] == "R08_DEFAULT_PRESERVE":
            assert decision["eligible_rule_ids"] == ["R08_DEFAULT_PRESERVE"]


def test_missing_r08_eligibility_fails_closed() -> None:
    """Reject an audit list that omits the always-eligible fallback."""
    bundle = copy.deepcopy(VALID_BUNDLE)
    bundle["decisions"][0]["eligible_rule_ids"].pop()

    with pytest.raises(HierarchyCorrectionContractError, match="R08 eligibility absent"):
        validate_hierarchy_correction_bundle(bundle)


def test_environment_record_is_checksum_managed() -> None:
    """Keep reproducibility evidence inside the exact sealed candidate set."""
    paths = {item["path"] for item in VALID_BUNDLE["artifact_inventory"]["files"]}
    assert "records/environment.json" in paths


def test_environment_record_cannot_escape_the_managed_inventory() -> None:
    """Reject a same-size inventory that substitutes an unmanaged record."""
    bundle = copy.deepcopy(VALID_BUNDLE)
    environment = next(
        item
        for item in bundle["artifact_inventory"]["files"]
        if item["path"] == "records/environment.json"
    )
    environment["path"] = "records/unmanaged.json"

    with pytest.raises(
        HierarchyCorrectionContractError,
        match="artifact inventory paths differ",
    ):
        validate_hierarchy_correction_bundle(bundle)


def test_picture_owned_non_caption_text_must_select_r01() -> None:
    """Preserve picture text evidence while excluding it from hierarchy."""
    bundle = copy.deepcopy(VALID_BUNDLE)
    decision = bundle["decisions"][4]
    decision["selected_rule_id"] = "R08_DEFAULT_PRESERVE"
    decision["eligible_rule_ids"] = ["R08_DEFAULT_PRESERVE"]
    decision["corrected_role"] = "content"
    decision["outcome"] = "unchanged"

    with pytest.raises(HierarchyCorrectionContractError, match="R01 eligibility differs"):
        validate_hierarchy_correction_bundle(bundle)


def test_picture_owned_caption_remains_r08_content() -> None:
    """Keep an explicit caption as content without treating it as excluded text."""
    caption_feature = VALID_BUNDLE["features"][5]
    caption_decision = VALID_BUNDLE["decisions"][5]
    assert caption_feature["raw_parent_ref"] == "#/pictures/0"
    assert caption_feature["raw_role"] == "caption"
    assert caption_decision["selected_rule_id"] == "R08_DEFAULT_PRESERVE"
    assert caption_decision["corrected_role"] == "content"


def test_picture_owned_caption_ignores_an_incidental_outline_title_match() -> None:
    """Keep caption ownership authoritative over same-text PDF outline entries."""
    bundle = copy.deepcopy(VALID_BUNDLE)
    caption_feature = bundle["features"][5]
    caption_feature["outline_state"] = "unique_exact"
    caption_feature["outline_level"] = 2

    validate_hierarchy_correction_bundle(bundle)


def test_picture_owned_caption_cannot_be_promoted_by_an_anchor() -> None:
    """Reject outline evidence that would turn a picture caption into a heading."""
    bundle = copy.deepcopy(VALID_BUNDLE)
    feature = bundle["features"][5]
    feature["outline_state"] = "unique_exact"
    feature["outline_level"] = 2
    decision = bundle["decisions"][5]
    decision["selected_rule_id"] = "R03_APPLY_EXACT_OUTLINE_ANCHOR"
    decision["eligible_rule_ids"] = [
        "R03_APPLY_EXACT_OUTLINE_ANCHOR",
        "R08_DEFAULT_PRESERVE",
    ]
    decision["corrected_role"] = "heading"
    decision["corrected_level"] = 2
    decision["outcome"] = "applied"
    decision["evidence"]["outline_level"] = 2

    with pytest.raises(HierarchyCorrectionContractError, match="picture caption rule differs"):
        validate_hierarchy_correction_bundle(bundle)


def test_picture_owned_text_cannot_be_a_toc_reconciliation_target() -> None:
    """Keep picture descendants outside the body-heading target set."""
    bundle = copy.deepcopy(VALID_BUNDLE)
    picture_key = bundle["features"][5]["stable_item_key"]
    bundle["reconciliations"][0]["candidate_keys"] = [picture_key]
    bundle["reconciliations"][0]["target_key"] = picture_key

    with pytest.raises(
        HierarchyCorrectionContractError,
        match="reconciliation candidate is not body content",
    ):
        validate_hierarchy_correction_bundle(bundle)


def test_numeric_toc_token_cannot_retain_terminal_period() -> None:
    """Independently enforce canonical numeric marker storage."""
    bundle = copy.deepcopy(VALID_BUNDLE)
    entry = bundle["toc_entries"][0]
    entry["title_with_marker_normalized"] = "1.01. example heading"
    entry["numbering_token"] = "1.01."

    with pytest.raises(
        HierarchyCorrectionContractError,
        match="numeric TOC token retains terminal punctuation",
    ):
        validate_hierarchy_correction_bundle(bundle)


def test_strict_toc_match_cannot_claim_canonical_basis() -> None:
    """Keep match-basis provenance independently reproducible."""
    bundle = copy.deepcopy(VALID_BUNDLE)
    bundle["reconciliations"][0]["match_basis"] = "typographic_canonical"

    with pytest.raises(HierarchyCorrectionContractError, match="canonical TOC match differs"):
        validate_hierarchy_correction_bundle(bundle)


def test_strict_toc_match_cannot_carry_native_pdf_evidence() -> None:
    """Keep independent native evidence exclusive to its declared tier."""
    bundle = copy.deepcopy(VALID_BUNDLE)
    bundle["reconciliations"][0]["native_pdf_evidence"] = {
        "physical_page": 1,
        "bbox": dict(bundle["features"][0]["bbox"]),
        "normalized_text": "example heading",
        "outline_ids": [],
    }

    with pytest.raises(HierarchyCorrectionContractError, match="non-native TOC match"):
        validate_hierarchy_correction_bundle(bundle)


@pytest.mark.parametrize(
    "invalid_bundle",
    [bundle for _, bundle in SEMANTIC_MUTATION_CASES],
    ids=[name for name, _ in SEMANTIC_MUTATION_CASES],
)
def test_named_semantic_mutation_fails(
    invalid_bundle: dict[str, Any],
) -> None:
    """Make the failing responsibility visible in the pytest case name."""
    with pytest.raises(HierarchyCorrectionContractError):
        validate_hierarchy_correction_bundle(invalid_bundle)


def test_hierarchy_edges_must_remain_in_reading_order() -> None:
    """Reject a relationship set serialized in the wrong edge order."""
    bundle = valid_deep_hierarchy_bundle()
    validate_hierarchy_correction_bundle(bundle)
    bundle["hierarchy"]["edges"].reverse()

    with pytest.raises(HierarchyCorrectionContractError, match="edges differ"):
        validate_hierarchy_correction_bundle(bundle)


def test_hierarchy_roots_must_remain_in_reading_order() -> None:
    """Reject root keys serialized in an order different from decisions."""
    bundle = valid_multiple_roots_bundle()
    validate_hierarchy_correction_bundle(bundle)
    bundle["hierarchy"]["roots"].reverse()

    with pytest.raises(HierarchyCorrectionContractError, match="roots differ"):
        validate_hierarchy_correction_bundle(bundle)


def test_sparse_root_is_valid_only_with_exact_review_warning() -> None:
    """Treat a preserved level gap as evidence rather than a fatal hierarchy error."""
    bundle = copy.deepcopy(VALID_BUNDLE)
    feature = bundle["features"][0]
    decision = bundle["decisions"][0]
    feature["outline_level"] = 3
    decision["corrected_level"] = 3
    decision["evidence"]["outline_level"] = 3
    warning = {
        "reading_order_index": feature["reading_order_index"],
        "stable_item_key": feature["stable_item_key"],
        "code": "RAW_HEADING_DEPTH_UNSUPPORTED",
        "detail": "sparse hierarchy root: regime_root_level=1, child_level=3, "
        "missing_intermediate_level_count = 2",
    }
    bundle["warnings"] = [warning]
    bundle["summary"]["warning_count"] = 1

    validate_hierarchy_correction_bundle(bundle)

    bundle["warnings"][0]["detail"] = "gap hidden"
    with pytest.raises(HierarchyCorrectionContractError, match="sparse hierarchy warnings differ"):
        validate_hierarchy_correction_bundle(bundle)
