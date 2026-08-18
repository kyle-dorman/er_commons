"""Shared fixtures and named mutations for hierarchy-inference tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[1]
SCHEMA_ROOT = ROOT / "benchmarks/er_bench/schemas/hierarchy_correction/v1"
FIXTURE_ROOT = ROOT / "benchmarks/er_bench/fixtures/hierarchy_correction/v1"

RECORD_SCHEMA = json.loads((SCHEMA_ROOT / "records.schema.json").read_text())
VALID_BUNDLE = json.loads((FIXTURE_ROOT / "valid_bundle.json").read_text())
INVALID_SCHEMA_MUTATIONS = json.loads((FIXTURE_ROOT / "invalid_mutations.json").read_text())
DEVELOPMENT_CASES = json.loads((FIXTURE_ROOT / "development_cases.json").read_text())


def apply_schema_mutation(
    bundle: dict[str, Any],
    mutation: dict[str, Any],
) -> dict[str, Any]:
    """Apply one intentionally schema-invalid fixture change."""
    target: Any = bundle
    for path_part in mutation["path"][:-1]:
        target = target[path_part]
    target[mutation["path"][-1]] = mutation["value"]
    return bundle


def valid_deep_hierarchy_bundle() -> dict[str, Any]:
    """Return a valid three-level hierarchy with two ordered edges."""
    bundle = copy.deepcopy(VALID_BUNDLE)
    root_key = bundle["features"][0]["stable_item_key"]
    level_two_key = bundle["features"][1]["stable_item_key"]
    level_three_key = bundle["features"][2]["stable_item_key"]

    level_two_feature = bundle["features"][1]
    level_two_feature["numbering_kind"] = "none"
    level_two_feature["numbering_token"] = None
    level_two_feature["numbering_depth"] = None
    level_two_decision = bundle["decisions"][1]
    level_two_decision["selected_rule_id"] = "R08_DEFAULT_PRESERVE"
    level_two_decision["eligible_rule_ids"] = ["R08_DEFAULT_PRESERVE"]
    level_two_decision["corrected_role"] = "heading"
    level_two_decision["corrected_level"] = 2
    level_two_decision["outcome"] = "unchanged"
    level_two_decision["evidence"]["numbering_kind"] = "none"
    level_two_decision["evidence"]["numbering_depth"] = None
    level_two_decision["evidence"]["next_list_indent_delta_pt"] = None

    level_three_feature = bundle["features"][2]
    level_three_feature["raw_role"] = "section_header"
    level_three_feature["raw_level"] = 3
    level_three_decision = bundle["decisions"][2]
    level_three_decision["raw_role"] = "section_header"
    level_three_decision["raw_level"] = 3
    level_three_decision["corrected_role"] = "heading"
    level_three_decision["corrected_level"] = 3

    bundle["hierarchy"] = {
        "roots": [root_key],
        "edges": [
            {"parent_key": root_key, "child_key": level_two_key},
            {"parent_key": level_two_key, "child_key": level_three_key},
        ],
        "direct_membership": [
            {
                "item_key": bundle["features"][5]["stable_item_key"],
                "heading_key": level_three_key,
            }
        ],
        "unassigned_content": [],
    }
    bundle["summary"]["heading_count"] = 3
    bundle["summary"]["content_count"] = 1
    _refresh_rule_counts(bundle)
    return bundle


def valid_multiple_roots_bundle() -> dict[str, Any]:
    """Return a valid hierarchy with three roots in reading order."""
    bundle = valid_deep_hierarchy_bundle()
    for feature, decision in zip(
        bundle["features"][1:3],
        bundle["decisions"][1:3],
        strict=True,
    ):
        feature["raw_level"] = 1
        decision["raw_level"] = 1
        decision["corrected_level"] = 1
    bundle["hierarchy"]["roots"] = [
        feature["stable_item_key"] for feature in bundle["features"][:3]
    ]
    bundle["hierarchy"]["edges"] = []
    _refresh_rule_counts(bundle)
    return bundle


def _refresh_rule_counts(bundle: dict[str, Any]) -> None:
    """Refresh derived per-rule summary counts after a valid fixture edit."""
    selected = {rule_id: 0 for rule_id in bundle["summary"]["selected_rule_counts"]}
    eligible_not_selected = {
        rule_id: 0 for rule_id in bundle["summary"]["eligible_not_selected_rule_counts"]
    }
    for decision in bundle["decisions"]:
        selected_rule_id = decision["selected_rule_id"]
        selected[selected_rule_id] += 1
        for eligible_rule_id in decision["eligible_rule_ids"]:
            if eligible_rule_id != selected_rule_id:
                eligible_not_selected[eligible_rule_id] += 1
    bundle["summary"]["selected_rule_counts"] = selected
    bundle["summary"]["eligible_not_selected_rule_counts"] = eligible_not_selected


def semantic_mutation_cases() -> list[tuple[str, dict[str, Any]]]:
    """Return named schema-valid bundles that each violate one policy."""
    cases = []

    def add(name: str, bundle: dict[str, Any]) -> None:
        cases.append((name, bundle))

    duplicate_decision = copy.deepcopy(VALID_BUNDLE)
    duplicate_decision["decisions"].append(copy.deepcopy(duplicate_decision["decisions"][0]))
    add("duplicate_decision", duplicate_decision)

    wrong_membership = copy.deepcopy(VALID_BUNDLE)
    wrong_membership["hierarchy"]["direct_membership"] = []
    add("wrong_membership", wrong_membership)

    ambiguous_heading = copy.deepcopy(VALID_BUNDLE)
    ambiguous_heading["decisions"][0]["outcome"] = "ambiguous"
    add("ambiguous_heading", ambiguous_heading)

    wrong_summary = copy.deepcopy(VALID_BUNDLE)
    wrong_summary["summary"]["heading_count"] = 99
    add("wrong_summary", wrong_summary)

    wrong_selected_rule_counts = copy.deepcopy(VALID_BUNDLE)
    wrong_selected_rule_counts["summary"]["selected_rule_counts"]["R08_DEFAULT_PRESERVE"] += 1
    add("wrong_selected_rule_counts", wrong_selected_rule_counts)

    wrong_eligible_not_selected_counts = copy.deepcopy(VALID_BUNDLE)
    wrong_eligible_not_selected_counts["summary"]["eligible_not_selected_rule_counts"][
        "R08_DEFAULT_PRESERVE"
    ] -= 1
    add("wrong_eligible_not_selected_counts", wrong_eligible_not_selected_counts)

    missing_toc = copy.deepcopy(VALID_BUNDLE)
    missing_toc["toc_entries"] = []
    missing_toc["reconciliations"] = []
    add("missing_toc", missing_toc)

    unknown_evidence = copy.deepcopy(VALID_BUNDLE)
    unknown_evidence["decisions"][0]["evidence"]["source_item_keys"] = ["f" * 64]
    add("unknown_evidence", unknown_evidence)

    self_parented_regime = copy.deepcopy(VALID_BUNDLE)
    self_parented_regime["regimes"][0]["parent_regime_id"] = self_parented_regime["regimes"][0][
        "regime_id"
    ]
    add("self_parented_regime", self_parented_regime)

    reversed_decisions = copy.deepcopy(VALID_BUNDLE)
    reversed_decisions["decisions"].reverse()
    add("reversed_decisions", reversed_decisions)

    duplicate_inventory_path = copy.deepcopy(VALID_BUNDLE)
    duplicate_inventory_path["artifact_inventory"]["files"][1]["path"] = duplicate_inventory_path[
        "artifact_inventory"
    ]["files"][0]["path"]
    add("duplicate_inventory_path", duplicate_inventory_path)

    wrong_inventory_seal = copy.deepcopy(VALID_BUNDLE)
    wrong_inventory_seal["completion"]["artifact_inventory_sha256"] = "f" * 64
    add("wrong_inventory_seal", wrong_inventory_seal)

    wrong_status = copy.deepcopy(VALID_BUNDLE)
    wrong_status["summary"]["status"] = "complete_with_ambiguities"
    wrong_status["completion"]["status"] = "complete_with_ambiguities"
    add("wrong_status", wrong_status)

    wrong_r02_role = copy.deepcopy(VALID_BUNDLE)
    wrong_r02_role["features"][1]["raw_role"] = "list_item"
    wrong_r02_role["decisions"][1]["raw_role"] = "list_item"
    add("wrong_r02_role", wrong_r02_role)

    wrong_r03_action = copy.deepcopy(VALID_BUNDLE)
    wrong_r03_action["decisions"][0]["corrected_role"] = "content"
    wrong_r03_action["decisions"][0]["corrected_level"] = None
    add("wrong_r03_action", wrong_r03_action)

    wrong_r05_evidence = copy.deepcopy(VALID_BUNDLE)
    wrong_r05_evidence["decisions"][0]["selected_rule_id"] = "R05_APPLY_NUMBERING_REGIME"
    wrong_r05_evidence["decisions"][0]["eligible_rule_ids"] = [
        "R05_APPLY_NUMBERING_REGIME",
        "R08_DEFAULT_PRESERVE",
    ]
    wrong_r05_evidence["decisions"][0]["evidence"]["numbering_kind"] = "article"
    add("wrong_r05_evidence", wrong_r05_evidence)

    wrong_r04_target = copy.deepcopy(VALID_BUNDLE)
    wrong_r04_target["decisions"][0]["selected_rule_id"] = "R04_APPLY_EXACT_TOC_ANCHOR"
    wrong_r04_target["decisions"][0]["eligible_rule_ids"] = [
        "R04_APPLY_EXACT_TOC_ANCHOR",
        "R08_DEFAULT_PRESERVE",
    ]
    wrong_r04_target["decisions"][0]["evidence"]["toc_entry_id"] = "toc-ffffffffffffffff"
    add("wrong_r04_target", wrong_r04_target)

    wrong_r08_action = copy.deepcopy(VALID_BUNDLE)
    wrong_r08_action["decisions"][0]["selected_rule_id"] = "R08_DEFAULT_PRESERVE"
    wrong_r08_action["decisions"][0]["eligible_rule_ids"] = ["R08_DEFAULT_PRESERVE"]
    wrong_r08_action["decisions"][0]["corrected_role"] = "content"
    wrong_r08_action["decisions"][0]["corrected_level"] = None
    wrong_r08_action["decisions"][0]["outcome"] = "unchanged"
    add("wrong_r08_action", wrong_r08_action)

    reversed_regime_interval = copy.deepcopy(VALID_BUNDLE)
    reversed_regime_interval["regimes"][0]["start_item_key"] = "5" * 64
    reversed_regime_interval["regimes"][0]["end_item_key"] = "3" * 64
    add("reversed_regime_interval", reversed_regime_interval)

    anchored_r02 = copy.deepcopy(VALID_BUNDLE)
    anchored_r02["features"][1]["outline_state"] = "unique_exact"
    anchored_r02["features"][1]["outline_level"] = 2
    add("anchored_r02", anchored_r02)

    toc_item_escapes_r01 = copy.deepcopy(VALID_BUNDLE)
    toc_feature = toc_item_escapes_r01["features"][3]
    toc_feature["outline_state"] = "unique_exact"
    toc_feature["outline_level"] = 1
    toc_decision = toc_item_escapes_r01["decisions"][3]
    toc_decision["selected_rule_id"] = "R03_APPLY_EXACT_OUTLINE_ANCHOR"
    toc_decision["eligible_rule_ids"] = [
        "R03_APPLY_EXACT_OUTLINE_ANCHOR",
        "R08_DEFAULT_PRESERVE",
    ]
    toc_decision["corrected_role"] = "heading"
    toc_decision["corrected_level"] = 1
    toc_decision["evidence"]["outline_level"] = 1
    toc_item_escapes_r01["hierarchy"]["roots"].append(toc_feature["stable_item_key"])
    toc_item_escapes_r01["summary"]["heading_count"] = 2
    toc_item_escapes_r01["summary"]["excluded_count"] = 0
    add("toc_item_escapes_r01", toc_item_escapes_r01)

    furniture_item_escapes_r01 = copy.deepcopy(VALID_BUNDLE)
    furniture_item_escapes_r01["features"][2]["content_layer"] = "furniture"
    add("furniture_item_escapes_r01", furniture_item_escapes_r01)

    picture_descendant_escapes_r01 = copy.deepcopy(VALID_BUNDLE)
    picture_decision = picture_descendant_escapes_r01["decisions"][4]
    picture_decision["selected_rule_id"] = "R08_DEFAULT_PRESERVE"
    picture_decision["eligible_rule_ids"] = ["R08_DEFAULT_PRESERVE"]
    picture_decision["corrected_role"] = "content"
    picture_decision["outcome"] = "unchanged"
    add("picture_descendant_escapes_r01", picture_descendant_escapes_r01)

    picture_caption_selects_r01 = copy.deepcopy(VALID_BUNDLE)
    caption_decision = picture_caption_selects_r01["decisions"][5]
    caption_decision["selected_rule_id"] = "R01_EXCLUDE_NON_BODY_OR_TOC"
    caption_decision["eligible_rule_ids"] = [
        "R01_EXCLUDE_NON_BODY_OR_TOC",
        "R08_DEFAULT_PRESERVE",
    ]
    caption_decision["corrected_role"] = "excluded"
    caption_decision["outcome"] = "applied"
    add("picture_caption_selects_r01", picture_caption_selects_r01)

    picture_caption_promoted = copy.deepcopy(VALID_BUNDLE)
    caption_feature = picture_caption_promoted["features"][5]
    caption_feature["outline_state"] = "unique_exact"
    caption_feature["outline_level"] = 2
    caption_decision = picture_caption_promoted["decisions"][5]
    caption_decision["selected_rule_id"] = "R03_APPLY_EXACT_OUTLINE_ANCHOR"
    caption_decision["eligible_rule_ids"] = [
        "R03_APPLY_EXACT_OUTLINE_ANCHOR",
        "R08_DEFAULT_PRESERVE",
    ]
    caption_decision["corrected_role"] = "heading"
    caption_decision["corrected_level"] = 2
    caption_decision["outcome"] = "applied"
    caption_decision["evidence"]["outline_level"] = 2
    add("picture_caption_promoted", picture_caption_promoted)

    overlapping_siblings = copy.deepcopy(VALID_BUNDLE)
    child = copy.deepcopy(overlapping_siblings["regimes"][0])
    child["regime_id"] = "reg-1111111111111111"
    child["parent_regime_id"] = overlapping_siblings["regimes"][0]["regime_id"]
    child["start_item_key"] = "4" * 64
    overlapping_siblings["regimes"].append(child)
    sibling = copy.deepcopy(child)
    sibling["regime_id"] = "reg-2222222222222222"
    overlapping_siblings["regimes"].append(sibling)
    add("overlapping_siblings", overlapping_siblings)

    return cases
