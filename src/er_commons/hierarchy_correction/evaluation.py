"""Evidence-backed development-case and correction-inventory evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

JsonRecord = dict[str, Any]
REVIEWED_CHANGE_RULES = frozenset(
    {
        "R02_DEMOTE_BULLET_HEADING",
        "R04_APPLY_EXACT_TOC_ANCHOR",
        "R05_APPLY_NUMBERING_REGIME",
        "R07_TRANSFER_LOCAL_HEADING_LEVEL",
    }
)
NON_BULLET_NUMBERING_KINDS = frozenset({"decimal", "article", "upper_alpha", "upper_roman"})


def load_development_cases(path: Path, *, expected_count: int | None = 8) -> tuple[JsonRecord, ...]:
    """Load one checksum-bound case bundle with caller-declared cardinality."""
    payload = json.loads(path.read_bytes())
    if not isinstance(payload, dict) or not isinstance(payload.get("cases"), list):
        raise ValueError("development-case file must contain a cases array")
    cases = tuple(payload["cases"])
    if expected_count is not None and len(cases) != expected_count:
        raise ValueError(f"expected exactly {expected_count} development cases, found {len(cases)}")
    if not cases:
        raise ValueError("development cases must not be empty")
    keys = [case["stable_item_key"] for case in cases]
    if len(set(keys)) != len(keys):
        raise ValueError("development cases contain duplicate stable keys")
    return cases


def evaluate_development_cases(
    *,
    cases: tuple[JsonRecord, ...],
    decisions: tuple[JsonRecord, ...],
) -> JsonRecord:
    """Compare every frozen case to exact role, level, rule, and outcome fields."""
    if len(cases) != 8:
        raise ValueError(f"expected exactly eight development cases, found {len(cases)}")
    return evaluate_expected_cases(cases=cases, decisions=decisions)


def evaluate_expected_cases(
    *,
    cases: tuple[JsonRecord, ...],
    decisions: tuple[JsonRecord, ...],
) -> JsonRecord:
    """Compare a caller-bounded case set to its four exact expected fields."""
    decisions_by_key = {item["stable_item_key"]: item for item in decisions}
    if len(decisions_by_key) != len(decisions):
        raise ValueError("candidate decisions contain duplicate stable keys")
    results: list[JsonRecord] = []
    for case in cases:
        key = case["stable_item_key"]
        decision = decisions_by_key.get(key)
        expected = {
            "corrected_role": case["expected_role"],
            "corrected_level": case["expected_level"],
            "selected_rule_id": case["expected_rule_id"],
            "outcome": case["expected_outcome"],
        }
        actual = None if decision is None else {field: decision.get(field) for field in expected}
        mismatches = (
            ["missing_decision"]
            if actual is None
            else [field for field, value in expected.items() if actual[field] != value]
        )
        results.append(
            {
                "case_id": case["case_id"],
                "stable_item_key": key,
                "expected": expected,
                "actual": actual,
                "mismatch_fields": mismatches,
                "passed": not mismatches,
            }
        )
    failed_count = sum(not item["passed"] for item in results)
    return {
        "status": "pass" if failed_count == 0 else "reject",
        "case_count": len(results),
        "passed_count": len(results) - failed_count,
        "failed_count": failed_count,
        "cases": results,
    }


def build_correction_review_inventory(
    *,
    features: tuple[JsonRecord, ...],
    decisions: tuple[JsonRecord, ...],
) -> JsonRecord:
    """List every applied demotion, TOC promotion, numbering, and transfer change."""
    features_by_key = {item["stable_item_key"]: item for item in features}
    records: list[JsonRecord] = []
    counts = {rule_id: 0 for rule_id in sorted(REVIEWED_CHANGE_RULES)}
    for decision in decisions:
        rule_id = decision["selected_rule_id"]
        if rule_id not in REVIEWED_CHANGE_RULES or decision["outcome"] != "applied":
            continue
        key = decision["stable_item_key"]
        if key not in features_by_key:
            raise ValueError(f"review-inventory decision has no feature: {key}")
        feature = features_by_key[key]
        counts[rule_id] += 1
        records.append(
            {
                "reading_order_index": feature["reading_order_index"],
                "stable_item_key": key,
                "physical_page": feature["physical_page"],
                "text": feature["text"],
                "raw_role": decision["raw_role"],
                "raw_level": decision["raw_level"],
                "corrected_role": decision["corrected_role"],
                "corrected_level": decision["corrected_level"],
                "selected_rule_id": rule_id,
                "evidence": decision["evidence"],
            }
        )
    records.sort(key=lambda item: (item["reading_order_index"], item["stable_item_key"]))
    return {
        "record_count": len(records),
        "counts_by_rule": counts,
        "records": records,
    }


def evaluate_frozen_outline_numbering_gates(
    *,
    review_pages: frozenset[int],
    features: tuple[JsonRecord, ...],
    decisions: tuple[JsonRecord, ...],
    regimes: tuple[JsonRecord, ...],
    expected_outline_count: int = 29,
    expected_outline_r03_count: int = 28,
    expected_outline_toc_override_count: int = 1,
    expected_numbered_heading_count: int = 23,
    expected_numbering_relation_count: int = 21,
) -> JsonRecord:
    """Rederive Task 03E's 29/21 gates from source-bound item evidence.

    The caller supplies the frozen page set as evaluation evidence. Runtime
    hierarchy predicates remain independent of physical page numbers.
    """
    decisions_by_key = {item["stable_item_key"]: item for item in decisions}
    regimes_by_id = {item["regime_id"]: item for item in regimes}
    if len(decisions_by_key) != len(decisions):
        raise ValueError("candidate decisions contain duplicate stable keys")
    if len(regimes_by_id) != len(regimes):
        raise ValueError("candidate regimes contain duplicate regime IDs")

    reviewed = [item for item in features if item["physical_page"] in review_pages]
    outline_features = [
        item
        for item in reviewed
        if item["content_layer"] == "body"
        and item["raw_role"] == "section_header"
        and item["outline_state"] == "unique_exact"
    ]
    if len(outline_features) != expected_outline_count:
        raise ValueError(
            "frozen exact-outline count differs: "
            f"expected={expected_outline_count}, actual={len(outline_features)}"
        )
    toc_outline_features = [item for item in outline_features if item["toc_region"]]
    if len(toc_outline_features) != expected_outline_toc_override_count:
        raise ValueError(
            "frozen TOC-outline override count differs: "
            f"expected={expected_outline_toc_override_count}, "
            f"actual={len(toc_outline_features)}"
        )
    if len(outline_features) - len(toc_outline_features) != expected_outline_r03_count:
        raise ValueError(
            "frozen R03 outline count differs: "
            f"expected={expected_outline_r03_count}, "
            f"actual={len(outline_features) - len(toc_outline_features)}"
        )
    outline_results: list[JsonRecord] = []
    for feature in outline_features:
        key = feature["stable_item_key"]
        decision = decisions_by_key.get(key)
        toc_override = bool(feature["toc_region"])
        passed = bool(
            decision is not None
            and (
                (
                    toc_override
                    and decision["selected_rule_id"] == "R01_EXCLUDE_NON_BODY_OR_TOC"
                    and decision["corrected_role"] == "excluded"
                    and decision["corrected_level"] is None
                )
                or (
                    not toc_override
                    and decision["selected_rule_id"] == "R03_APPLY_EXACT_OUTLINE_ANCHOR"
                    and decision["corrected_role"] == "heading"
                    and decision["corrected_level"] == feature["outline_level"]
                )
            )
        )
        outline_results.append(
            {
                "stable_item_key": key,
                "physical_page": feature["physical_page"],
                "expected_level": feature["outline_level"],
                "actual_level": decision and decision["corrected_level"],
                "actual_rule_id": decision and decision["selected_rule_id"],
                "expected_resolution": "R01_TOC_OVERRIDE" if toc_override else "R03_LEVEL",
                "passed": passed,
            }
        )

    numbered_features = [
        item
        for item in reviewed
        if item["content_layer"] == "body"
        and item["raw_role"] == "section_header"
        and item["numbering_kind"] in NON_BULLET_NUMBERING_KINDS
        and isinstance(item["numbering_depth"], int)
    ]
    if len(numbered_features) != expected_numbered_heading_count:
        raise ValueError(
            "frozen numbered-heading count differs: "
            f"expected={expected_numbered_heading_count}, actual={len(numbered_features)}"
        )
    first_numbered_by_regime: dict[str, str] = {}
    for feature in numbered_features:
        first_numbered_by_regime.setdefault(feature["regime_id"], feature["stable_item_key"])
    base_level_by_regime: dict[str, int] = {}
    for regime_id, key in first_numbered_by_regime.items():
        decision = decisions_by_key.get(key)
        level = decision and decision["corrected_level"]
        if (
            decision is not None
            and isinstance(level, int)
            and decision["corrected_role"] == "heading"
        ):
            base_level_by_regime[regime_id] = level
            continue
        first_feature = next(item for item in numbered_features if item["stable_item_key"] == key)
        regime = regimes_by_id.get(regime_id)
        if regime is None:
            raise ValueError(f"first reviewed numbered heading has unknown regime: {key}")
        base_level_by_regime[regime_id] = (
            regime["root_level"] + first_feature["numbering_depth"] - 1
        )
    relation_features = [
        item
        for item in numbered_features
        if first_numbered_by_regime[item["regime_id"]] != item["stable_item_key"]
    ]
    if len(relation_features) != expected_numbering_relation_count:
        raise ValueError(
            "frozen numbering-relation count differs: "
            f"expected={expected_numbering_relation_count}, actual={len(relation_features)}"
        )
    numbering_results: list[JsonRecord] = []
    for feature in relation_features:
        key = feature["stable_item_key"]
        decision = decisions_by_key.get(key)
        regime = regimes_by_id.get(feature["regime_id"])
        if regime is None:
            raise ValueError(f"numbering relation references unknown regime: {key}")
        actual_relative_depth = None
        if decision is not None and isinstance(decision["corrected_level"], int):
            actual_relative_depth = (
                decision["corrected_level"] - base_level_by_regime[feature["regime_id"]] + 1
            )
        passed = bool(
            decision is not None
            and decision["corrected_role"] == "heading"
            and actual_relative_depth == feature["numbering_depth"]
        )
        numbering_results.append(
            {
                "stable_item_key": key,
                "physical_page": feature["physical_page"],
                "regime_id": feature["regime_id"],
                "expected_relative_depth": feature["numbering_depth"],
                "actual_relative_depth": actual_relative_depth,
                "actual_rule_id": decision and decision["selected_rule_id"],
                "passed": passed,
            }
        )

    outline_passed = sum(item["passed"] for item in outline_results)
    numbering_passed = sum(item["passed"] for item in numbering_results)
    passed = (
        outline_passed == expected_outline_count
        and numbering_passed == expected_numbering_relation_count
    )
    return {
        "status": "pass" if passed else "reject",
        "review_pages": sorted(review_pages),
        "outline": {
            "expected_count": expected_outline_count,
            "expected_r03_count": expected_outline_r03_count,
            "expected_toc_override_count": expected_outline_toc_override_count,
            "r03_result_count": sum(
                item["expected_resolution"] == "R03_LEVEL" for item in outline_results
            ),
            "toc_override_result_count": sum(
                item["expected_resolution"] == "R01_TOC_OVERRIDE" for item in outline_results
            ),
            "passed_count": outline_passed,
            "results": outline_results,
        },
        "numbering": {
            "eligible_heading_count": len(numbered_features),
            "excluded_first_by_regime": [
                {
                    "regime_id": regime_id,
                    "stable_item_key": key,
                    "corrected_base_level": base_level_by_regime[regime_id],
                }
                for regime_id, key in first_numbered_by_regime.items()
            ],
            "expected_relation_count": expected_numbering_relation_count,
            "passed_count": numbering_passed,
            "results": numbering_results,
        },
    }


def inspect_legacy_gate_evidence(path: Path) -> JsonRecord:
    """Report whether Task 03E retained item-level 29/21 expectations.

    Aggregate success counts are useful provenance, but cannot independently
    verify a new candidate's exact stable keys and levels.
    """
    payload = json.loads(path.read_bytes())
    metrics = payload.get("metrics", {}) if isinstance(payload, dict) else {}
    item_records = payload.get("reviewed_item_expectations") if isinstance(payload, dict) else None
    return {
        "path": path.as_posix(),
        "eligible_bookmark_headings_exact": metrics.get("eligible_bookmark_headings_exact"),
        "eligible_bookmark_headings_total": metrics.get("eligible_bookmark_headings_total"),
        "reviewed_numbered_headings_relative_level_correct": metrics.get(
            "reviewed_numbered_headings_relative_level_correct"
        ),
        "reviewed_numbered_headings_total": metrics.get("reviewed_numbered_headings_total"),
        "item_level_expectations_available": isinstance(item_records, list),
        "exact_revalidation_available": isinstance(item_records, list),
        "blocker": (
            None
            if isinstance(item_records, list)
            else "legacy report retains aggregate 29/21 counts but no stable-key expectations"
        ),
    }
