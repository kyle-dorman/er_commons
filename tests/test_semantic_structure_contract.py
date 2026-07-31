"""Offline schema and cross-record tests for Task 03E.3."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from semantic_structure_support import (
    add_printed_page_alias,
    alias_named,
    fixture_has_no_mentions,
    page_label,
    record_ending_with,
    record_with,
)

from er_commons.semantic_structure import (
    BridgeSourceEvidence,
    SemanticContractError,
    normalize_alias,
)
from er_commons.semantic_structure import (
    validate_semantic_contract as validate_contract,
)

ROOT = Path(__file__).parents[1]
SCHEMA_PATH = (
    ROOT
    / "benchmarks"
    / "er_bench"
    / "schemas"
    / "canonical_extraction"
    / "v2"
    / "semantic_structure.schema.json"
)
FIXTURE_ROOT = ROOT / "benchmarks" / "er_bench" / "fixtures" / "canonical_extraction" / "v2"
SCHEMA = json.loads(SCHEMA_PATH.read_text())
BUNDLE = json.loads((FIXTURE_ROOT / "valid_semantic_structure.json").read_text())
INVALID_MUTATIONS = json.loads((FIXTURE_ROOT / "invalid_semantic_mutations.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)

BRIDGE_EVIDENCE = {
    entry["stable_item_key"]: BridgeSourceEvidence(
        hierarchy_raw_pointer=entry["hierarchy_raw_pointer"],
        baseline_raw_pointer=entry["baseline_raw_pointer"],
        disposition=entry["disposition"],
    )
    for entry in BUNDLE["bridge_entries"]
}


def validate_semantic_contract(
    bundle: dict[str, Any],
    bridge_evidence: dict[str, BridgeSourceEvidence] | None = None,
) -> None:
    """Validate a mutation against the fixture's independently frozen bridge evidence."""
    validate_contract(
        bundle,
        bridge_evidence=BRIDGE_EVIDENCE if bridge_evidence is None else bridge_evidence,
    )


def _mutate(bundle: dict[str, Any], path: list[Any], value: Any) -> None:
    target: Any = bundle
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value


def test_v2_schema_and_positive_fixture_are_valid() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    VALIDATOR.validate(BUNDLE)
    validate_semantic_contract(BUNDLE)


def test_schema_owns_identity_manifest_completion_and_support_report_shapes() -> None:
    assert {
        "semantic_identity_extension",
        "semantic_manifest_extension",
        "semantic_completion",
        "bridge_report",
        "correspondence_report",
        "support_file",
    } <= SCHEMA["$defs"].keys()


@pytest.mark.parametrize(
    "mutation", INVALID_MUTATIONS, ids=[item["name"] for item in INVALID_MUTATIONS]
)
def test_negative_schema_fixtures_fail(mutation: dict[str, Any]) -> None:
    invalid = copy.deepcopy(BUNDLE)
    _mutate(invalid, mutation["path"], mutation["value"])
    with pytest.raises(ValidationError):
        VALIDATOR.validate(invalid)


def test_sparse_levels_and_repeated_heading_aliases_are_representable() -> None:
    top_level = record_ending_with(BUNDLE["sections"], "/sec000003")
    skipped_level = record_ending_with(BUNDLE["sections"], "/sec000004")
    assert top_level["semantic_level"] == 1
    assert skipped_level["semantic_level"] == 3
    repeated = alias_named(BUNDLE, "repeated heading")
    assert repeated["resolution_status"] == "ambiguous"
    assert len(repeated["targets"]) == 2
    validate_semantic_contract(BUNDLE)


def test_alias_records_and_ambiguous_targets_use_deterministic_order() -> None:
    reversed_records = copy.deepcopy(BUNDLE)
    reversed_records["target_aliases"].reverse()
    for sequence, alias in enumerate(reversed_records["target_aliases"], start=1):
        alias["sequence"] = sequence
    with pytest.raises(SemanticContractError, match="deterministic order"):
        validate_semantic_contract(reversed_records)

    reversed_targets = copy.deepcopy(BUNDLE)
    alias_named(reversed_targets, "repeated heading")["targets"].reverse()
    with pytest.raises(SemanticContractError, match="targets are not in document order"):
        validate_semantic_contract(reversed_targets)


def test_ordered_children_are_exact_mixed_content_inverse() -> None:
    invalid = copy.deepcopy(BUNDLE)
    section = record_ending_with(invalid["sections"], "/sec000003")
    section["ordered_child_ids"][1:3] = reversed(section["ordered_child_ids"][1:3])
    with pytest.raises(SemanticContractError, match="ordered section children"):
        validate_semantic_contract(invalid)


def test_section_sequences_and_persisted_order_are_deterministic() -> None:
    wrong_sequence = copy.deepcopy(BUNDLE)
    record_ending_with(wrong_sequence["sections"], "/sec000003")["sequence"] = 99
    with pytest.raises(SemanticContractError, match="contiguous sequence"):
        validate_semantic_contract(wrong_sequence)

    wrong_order = copy.deepcopy(BUNDLE)
    wrong_order["sections"][2], wrong_order["sections"][3] = (
        wrong_order["sections"][3],
        wrong_order["sections"][2],
    )
    for sequence, section in enumerate(wrong_order["sections"], start=1):
        section["sequence"] = sequence
    with pytest.raises(SemanticContractError, match="document order"):
        validate_semantic_contract(wrong_order)


def test_cycles_and_nonincreasing_levels_fail() -> None:
    invalid = copy.deepcopy(BUNDLE)
    child = record_ending_with(invalid["sections"], "/sec000004")
    child["semantic_level"] = 1
    with pytest.raises(SemanticContractError, match="greater than parent"):
        validate_semantic_contract(invalid)

    cycle = copy.deepcopy(BUNDLE)
    parent = record_ending_with(cycle["sections"], "/sec000003")
    child = record_ending_with(cycle["sections"], "/sec000004")
    parent["parent_section_id"] = child["id"]
    parent["section_path_ids"] = [child["id"], parent["id"]]
    with pytest.raises(SemanticContractError):
        validate_semantic_contract(cycle)


def test_semantic_sections_must_descend_from_the_body_root() -> None:
    invalid = copy.deepcopy(BUNDLE)
    semantic = record_ending_with(invalid["sections"], "/sec000003")
    furniture_root = record_with(invalid["sections"], "section_kind", "synthetic_furniture_root")
    semantic["parent_section_id"] = furniture_root["id"]
    semantic["section_path_ids"] = [furniture_root["id"], semantic["id"]]
    with pytest.raises(SemanticContractError, match="descend from the body root"):
        validate_semantic_contract(invalid)


def test_heading_ownership_and_pre_root_toc_furniture_placement_are_strict() -> None:
    wrong_heading = copy.deepcopy(BUNDLE)
    heading = record_ending_with(wrong_heading["content"], "/blk000003")
    heading["semantic_placement"] = "direct_body"
    with pytest.raises(SemanticContractError, match="heading block"):
        validate_semantic_contract(wrong_heading)

    wrong_pre_root = copy.deepcopy(BUNDLE)
    pre_root = record_with(wrong_pre_root["content"], "semantic_placement", "pre_root")
    semantic_section = record_ending_with(wrong_pre_root["sections"], "/sec000003")
    pre_root["section_id"] = semantic_section["id"]
    with pytest.raises(SemanticContractError, match="pre-root"):
        validate_semantic_contract(wrong_pre_root)

    wrong_toc = copy.deepcopy(BUNDLE)
    toc_row = record_with(wrong_toc["content"], "is_toc_row", True)
    semantic_section = record_ending_with(wrong_toc["sections"], "/sec000003")
    toc_row["section_id"] = semantic_section["id"]
    with pytest.raises(SemanticContractError, match="TOC content"):
        validate_semantic_contract(wrong_toc)

    wrong_furniture = copy.deepcopy(BUNDLE)
    furniture = record_with(wrong_furniture["content"], "content_layer", "furniture")
    body_root = record_with(wrong_furniture["sections"], "section_kind", "synthetic_body_root")
    furniture["section_id"] = body_root["id"]
    with pytest.raises(SemanticContractError, match="furniture"):
        validate_semantic_contract(wrong_furniture)

    unowned_heading = copy.deepcopy(BUNDLE)
    body = record_ending_with(unowned_heading["content"], "/blk000004")
    body["semantic_placement"] = "heading_owner"
    with pytest.raises(SemanticContractError, match="heading ownership"):
        validate_semantic_contract(unowned_heading)


def test_content_placement_and_document_scope_cannot_contradict_records() -> None:
    wrong_furniture_placement = copy.deepcopy(BUNDLE)
    furniture = record_with(wrong_furniture_placement["content"], "content_layer", "furniture")
    furniture["semantic_placement"] = "direct_body"
    with pytest.raises(SemanticContractError, match="furniture content has a body placement"):
        validate_semantic_contract(wrong_furniture_placement)

    wrong_section_document = copy.deepcopy(BUNDLE)
    section = record_ending_with(wrong_section_document["sections"], "/sec000003")
    section["document_id"] = section["document_id"].replace("deir_fixture", "other_document")
    with pytest.raises(SemanticContractError, match="section escaped document scope"):
        validate_semantic_contract(wrong_section_document)

    wrong_alias_document = copy.deepcopy(BUNDLE)
    alias = alias_named(wrong_alias_document, "1. introduction")
    alias["document_id"] = alias["document_id"].replace("deir_fixture", "other_document")
    with pytest.raises(SemanticContractError, match="alias escaped document scope"):
        validate_semantic_contract(wrong_alias_document)


def test_tables_and_figures_inherit_sections_but_never_own_headings() -> None:
    invalid = copy.deepcopy(BUNDLE)
    table = next(item for item in invalid["content"] if item["record_type"] == "table")
    table["semantic_placement"] = "heading_owner"
    with pytest.raises(SemanticContractError, match="cannot own semantic headings"):
        validate_semantic_contract(invalid)


def test_page_label_outcomes_cover_pages_without_text_items() -> None:
    assert [item["physical_page_number"] for item in BUNDLE["page_label_observations"]] == list(
        range(1, 223)
    )
    assert page_label(BUNDLE, 3)["resolved_state"] == "unknown"
    invalid = copy.deepcopy(BUNDLE)
    invalid["page_label_observations"].pop(1)
    with pytest.raises(SemanticContractError, match="complete physical-page sequence"):
        validate_semantic_contract(invalid)


def test_page_coverage_is_bound_to_the_accepted_control() -> None:
    truncated = copy.deepcopy(BUNDLE)
    truncated["expected_page_count"] = 3
    truncated["page_label_observations"] = truncated["page_label_observations"][:3]
    with pytest.raises(SemanticContractError, match="accepted control"):
        validate_semantic_contract(truncated)


def test_page_label_state_value_evidence_and_conflict_are_coherent() -> None:
    invalid = copy.deepcopy(BUNDLE)
    page_label(invalid, 3)["resolved_label"] = "3"
    with pytest.raises(SemanticContractError, match="resolution differs.*physical page 3"):
        validate_semantic_contract(invalid)

    invalid = copy.deepcopy(BUNDLE)
    page_label(invalid, 4)["visible_label"]["value"] = "3"
    with pytest.raises(SemanticContractError, match="resolution differs.*physical page 4"):
        validate_semantic_contract(invalid)

    missing_evidence = copy.deepcopy(BUNDLE)
    page_label(missing_evidence, 2)["visible_label"]["evidence_refs"] = []
    with pytest.raises(SemanticContractError, match="no source anchors"):
        validate_semantic_contract(missing_evidence)


@pytest.mark.parametrize(
    ("physical_page", "field", "value"),
    [
        (1, "resolution_basis", "visible_footer_consensus"),
        (2, "resolution_basis", "explicit_pdf_page_labels"),
        (1, "resolved_state", "unknown"),
    ],
)
def test_page_label_precedence_cannot_be_relabelled(
    physical_page: int,
    field: str,
    value: str,
) -> None:
    invalid = copy.deepcopy(BUNDLE)
    page_label(invalid, physical_page)[field] = value
    with pytest.raises(SemanticContractError, match=f"physical page {physical_page}"):
        validate_semantic_contract(invalid)


def test_conflicting_sources_cannot_be_published_as_resolved() -> None:
    invalid = copy.deepcopy(BUNDLE)
    conflict = page_label(invalid, 4)
    conflict["resolved_state"] = "resolved"
    conflict["resolved_label"] = conflict["explicit_pdf_label"]["value"]
    conflict["resolution_basis"] = "explicit_pdf_page_labels"
    with pytest.raises(SemanticContractError, match="physical page 4"):
        validate_semantic_contract(invalid)


def test_alias_normalization_collision_and_toc_target_policy() -> None:
    assert normalize_alias("  Repeated\u00a0Heading ") == "repeated heading"
    invalid = copy.deepcopy(BUNDLE)
    alias_named(invalid, "1. introduction")["normalized_alias"] = "wrong"
    with pytest.raises(SemanticContractError, match="normalization"):
        validate_semantic_contract(invalid)

    invalid = copy.deepcopy(BUNDLE)
    alias_named(invalid, "repeated heading")["resolution_status"] = "unique"
    with pytest.raises(SemanticContractError, match="collision state"):
        validate_semantic_contract(invalid)

    invalid = copy.deepcopy(BUNDLE)
    toc_alias = alias_named(invalid, "1. introduction")
    toc_row = record_with(invalid["content"], "is_toc_row", True)
    toc_alias["targets"][0]["target_id"] = toc_row["id"]
    toc_alias["targets"][0]["target_type"] = "section"
    with pytest.raises(SemanticContractError, match="TOC alias"):
        validate_semantic_contract(invalid)

    wrong_target_type = copy.deepcopy(BUNDLE)
    target = alias_named(wrong_target_type, "repeated heading")["targets"][0]
    target["target_type"] = "table"
    with pytest.raises(SemanticContractError, match="kind and target type"):
        validate_semantic_contract(wrong_target_type)


def test_printed_page_aliases_require_an_existing_resolved_label() -> None:
    valid = copy.deepcopy(BUNDLE)
    add_printed_page_alias(valid, physical_page=2, raw_label="1")
    validate_semantic_contract(valid)

    unresolved = copy.deepcopy(BUNDLE)
    add_printed_page_alias(unresolved, physical_page=3, raw_label="3")
    with pytest.raises(SemanticContractError, match="does not exist with declared type"):
        validate_semantic_contract(unresolved)

    nonexistent = copy.deepcopy(BUNDLE)
    alias = add_printed_page_alias(nonexistent, physical_page=2, raw_label="1")
    alias["targets"][0]["target_id"] = alias["targets"][0]["target_id"].replace(
        "p000002", "p999999"
    )
    with pytest.raises(SemanticContractError, match="does not exist with declared type"):
        validate_semantic_contract(nonexistent)

    wrong_provenance = copy.deepcopy(BUNDLE)
    alias = add_printed_page_alias(wrong_provenance, physical_page=2, raw_label="1")
    alias["targets"][0]["evidence_kind"] = "heading_text"
    with pytest.raises(SemanticContractError, match="invalid provenance"):
        validate_semantic_contract(wrong_provenance)


def test_bridge_requires_coverage_unique_keys_targets_and_exact_producers() -> None:
    missing = copy.deepcopy(BUNDLE)
    missing["bridge_entries"].pop()
    with pytest.raises(SemanticContractError, match="cover"):
        validate_semantic_contract(missing)

    duplicate_key = copy.deepcopy(BUNDLE)
    pre_root = record_with(duplicate_key["bridge_entries"], "stable_item_key", "0" * 64)
    top_heading = record_with(duplicate_key["bridge_entries"], "stable_item_key", "1" * 64)
    top_heading["stable_item_key"] = pre_root["stable_item_key"]
    with pytest.raises(SemanticContractError, match="keys collide"):
        validate_semantic_contract(duplicate_key)

    duplicate_target = copy.deepcopy(BUNDLE)
    pre_root = record_with(duplicate_target["bridge_entries"], "stable_item_key", "0" * 64)
    top_heading = record_with(duplicate_target["bridge_entries"], "stable_item_key", "1" * 64)
    top_heading["canonical_record_ids"] = pre_root["canonical_record_ids"]
    with pytest.raises(SemanticContractError, match="stable key differs"):
        validate_semantic_contract(duplicate_target)

    changed_producer = copy.deepcopy(BUNDLE)
    pre_root = record_with(changed_producer["bridge_entries"], "stable_item_key", "0" * 64)
    pre_root["hierarchy_producer_run_id"] = "prv1-" + "f" * 64
    with pytest.raises(SemanticContractError, match="producer differs"):
        validate_semantic_contract(changed_producer)

    changed_pointers = copy.deepcopy(BUNDLE)
    pre_root = record_with(changed_pointers["bridge_entries"], "stable_item_key", "0" * 64)
    pre_root["hierarchy_raw_pointer"] = "#/wrong/998"
    pre_root["baseline_raw_pointer"] = "#/wrong/999"
    with pytest.raises(SemanticContractError, match="producer correspondence differs"):
        validate_semantic_contract(changed_pointers)


def test_bridge_permitted_replacement_dispositions_are_closed() -> None:
    bridge = copy.deepcopy(BUNDLE)
    entry = copy.deepcopy(record_with(bridge["bridge_entries"], "stable_item_key", "0" * 64))
    entry["stable_item_key"] = "8" * 64
    entry["hierarchy_raw_pointer"] = "#/texts/800"
    entry["baseline_raw_pointer"] = "#/texts/800"
    entry["status"] = "permitted_unmapped"
    entry["canonical_record_ids"] = []
    entry["disposition"] = "canonical_table_replacement_descendant"
    bridge["bridge_entries"].append(entry)
    evidence = dict(BRIDGE_EVIDENCE)
    evidence[entry["stable_item_key"]] = BridgeSourceEvidence(
        hierarchy_raw_pointer=entry["hierarchy_raw_pointer"],
        baseline_raw_pointer=entry["baseline_raw_pointer"],
        disposition=entry["disposition"],
    )
    validate_semantic_contract(bridge, evidence)

    entry["disposition"] = "other"
    with pytest.raises(SemanticContractError, match="not permitted"):
        changed_evidence = dict(evidence)
        changed_evidence[entry["stable_item_key"]] = BridgeSourceEvidence(
            hierarchy_raw_pointer=entry["hierarchy_raw_pointer"],
            baseline_raw_pointer=entry["baseline_raw_pointer"],
            disposition=entry["disposition"],
        )
        validate_semantic_contract(bridge, changed_evidence)

    unbacked = copy.deepcopy(BUNDLE)
    unbacked["bridge_entries"].append(copy.deepcopy(entry))
    with pytest.raises(SemanticContractError, match="source-evidence coverage differs"):
        validate_semantic_contract(unbacked)

    retained = copy.deepcopy(BUNDLE)
    retained_entry = record_with(retained["bridge_entries"], "stable_item_key", "0" * 64)
    retained_entry["status"] = "permitted_unmapped"
    retained_entry["canonical_record_ids"] = []
    retained_entry["disposition"] = "canonical_table_replacement_descendant"
    retained_evidence = dict(BRIDGE_EVIDENCE)
    retained_evidence[retained_entry["stable_item_key"]] = BridgeSourceEvidence(
        hierarchy_raw_pointer=retained_entry["hierarchy_raw_pointer"],
        baseline_raw_pointer=retained_entry["baseline_raw_pointer"],
        disposition=retained_entry["disposition"],
    )
    with pytest.raises(SemanticContractError, match="retained canonical blocks"):
        validate_semantic_contract(retained, retained_evidence)


def test_mapped_bridge_targets_must_be_canonical_blocks() -> None:
    invalid = copy.deepcopy(BUNDLE)
    entry = record_with(invalid["bridge_entries"], "stable_item_key", "0" * 64)
    table = record_with(invalid["content"], "record_type", "table")
    entry["canonical_record_ids"] = [table["id"]]
    with pytest.raises(SemanticContractError, match="not a canonical block"):
        validate_semantic_contract(invalid)

    swapped = copy.deepcopy(BUNDLE)
    first = record_with(swapped["bridge_entries"], "stable_item_key", "0" * 64)
    second = record_with(swapped["bridge_entries"], "stable_item_key", "1" * 64)
    first["canonical_record_ids"], second["canonical_record_ids"] = (
        second["canonical_record_ids"],
        first["canonical_record_ids"],
    )
    with pytest.raises(SemanticContractError, match="stable key differs"):
        validate_semantic_contract(swapped)


def test_control_and_correspondence_fail_closed() -> None:
    control = copy.deepcopy(BUNDLE)
    control["control_provenance"]["semantic_file_set_sha256"] = "0" * 64
    with pytest.raises(SemanticContractError, match="control binding"):
        validate_semantic_contract(control)

    correspondence = copy.deepcopy(BUNDLE)
    correspondence["correspondence_report"]["undeclared_difference_count"] = 1
    with pytest.raises(SemanticContractError, match="undeclared differences"):
        validate_semantic_contract(correspondence)


def test_fixtures_contain_no_cross_reference_mentions() -> None:
    assert BUNDLE["cross_references"] == []
    assert fixture_has_no_mentions(BUNDLE)
