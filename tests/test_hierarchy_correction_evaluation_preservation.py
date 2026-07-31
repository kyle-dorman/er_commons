"""Focused tests for Task 03E.2 evaluation and preservation evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import er_commons.hierarchy_correction.preservation as preservation_module
from er_commons.hierarchy_correction.evaluation import (
    build_correction_review_inventory,
    evaluate_development_cases,
    evaluate_frozen_outline_numbering_gates,
    inspect_legacy_gate_evidence,
    load_development_cases,
)
from er_commons.hierarchy_correction.preservation import (
    assert_artifacts_preserved,
    snapshot_verified_producer,
    snapshot_verified_task03d1_reference,
)

ROOT = Path(__file__).parents[1]
DEVELOPMENT_CASES_PATH = (
    ROOT / "benchmarks/er_bench/fixtures/hierarchy_correction/v1/development_cases.json"
)


def _decision(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "stable_item_key": case["stable_item_key"],
        "raw_role": case["raw_role"],
        "raw_level": case["raw_level"],
        "corrected_role": case["expected_role"],
        "corrected_level": case["expected_level"],
        "selected_rule_id": case["expected_rule_id"],
        "outcome": case["expected_outcome"],
        "evidence": {"source_item_keys": [case["stable_item_key"]]},
    }


def test_eight_development_cases_require_exact_expected_fields() -> None:
    cases = load_development_cases(DEVELOPMENT_CASES_PATH)
    decisions = tuple(_decision(case) for case in cases)

    passing = evaluate_development_cases(cases=cases, decisions=decisions)
    assert passing["status"] == "pass"
    assert passing["passed_count"] == 8

    changed = [dict(item) for item in decisions]
    changed[3]["corrected_level"] = 6
    failing = evaluate_development_cases(cases=cases, decisions=tuple(changed))
    assert failing["status"] == "reject"
    assert failing["failed_count"] == 1
    assert failing["cases"][3]["mismatch_fields"] == ["corrected_level"]


def test_review_inventory_contains_every_applied_review_rule_in_order() -> None:
    features = tuple(
        {
            "stable_item_key": f"{index + 1:064x}",
            "reading_order_index": index,
            "physical_page": index + 1,
            "text": f"item {index}",
        }
        for index in range(6)
    )
    rules = (
        "R08_DEFAULT_PRESERVE",
        "R05_APPLY_NUMBERING_REGIME",
        "R02_DEMOTE_BULLET_HEADING",
        "R04_APPLY_EXACT_TOC_ANCHOR",
        "R07_TRANSFER_LOCAL_HEADING_LEVEL",
        "R05_APPLY_NUMBERING_REGIME",
    )
    decisions = tuple(
        {
            "stable_item_key": feature["stable_item_key"],
            "raw_role": "section_header",
            "raw_level": 3,
            "corrected_role": "heading",
            "corrected_level": 2,
            "selected_rule_id": rule,
            "outcome": "ambiguous" if index == 5 else "applied",
            "evidence": {"source_item_keys": [feature["stable_item_key"]]},
        }
        for index, (feature, rule) in enumerate(zip(features, rules, strict=True))
    )

    inventory = build_correction_review_inventory(features=features, decisions=decisions)

    assert inventory["record_count"] == 4
    assert [item["selected_rule_id"] for item in inventory["records"]] == list(rules[1:5])
    assert inventory["counts_by_rule"] == {
        "R02_DEMOTE_BULLET_HEADING": 1,
        "R04_APPLY_EXACT_TOC_ANCHOR": 1,
        "R05_APPLY_NUMBERING_REGIME": 1,
        "R07_TRANSFER_LOCAL_HEADING_LEVEL": 1,
    }


def test_legacy_aggregate_report_is_not_misrepresented_as_exact_records(tmp_path: Path) -> None:
    report_path = tmp_path / "bounded_review_report.json"
    report_path.write_text(
        json.dumps(
            {
                "metrics": {
                    "eligible_bookmark_headings_exact": 29,
                    "eligible_bookmark_headings_total": 29,
                    "reviewed_numbered_headings_relative_level_correct": 21,
                    "reviewed_numbered_headings_total": 21,
                }
            }
        )
    )

    evidence = inspect_legacy_gate_evidence(report_path)

    assert evidence["eligible_bookmark_headings_total"] == 29
    assert evidence["reviewed_numbered_headings_total"] == 21
    assert evidence["exact_revalidation_available"] is False
    assert "no stable-key expectations" in evidence["blocker"]


def test_frozen_outline_and_numbering_gates_rederive_item_level_29_and_21() -> None:
    regimes = tuple(
        {
            "regime_id": regime_id,
            "root_level": 1,
        }
        for regime_id in ("reg-initial", "reg-article")
    )
    features: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for index in range(29):
        numbered = index < 23
        regime_id = "reg-initial" if index < 12 else "reg-article"
        depth = 1 if index in {0, 12} else 2
        key = f"{index + 1:064x}"
        feature = {
            "stable_item_key": key,
            "physical_page": 4,
            "content_layer": "body",
            "raw_role": "section_header",
            "outline_state": "unique_exact",
            "outline_level": depth,
            "toc_region": index == 28,
            "numbering_kind": "decimal" if numbered else "none",
            "numbering_depth": depth if numbered else None,
            "regime_id": regime_id,
        }
        features.append(feature)
        decisions.append(
            {
                "stable_item_key": key,
                "selected_rule_id": (
                    "R01_EXCLUDE_NON_BODY_OR_TOC"
                    if index == 28
                    else "R03_APPLY_EXACT_OUTLINE_ANCHOR"
                ),
                "corrected_role": "excluded" if index == 28 else "heading",
                "corrected_level": None if index == 28 else depth,
            }
        )

    report = evaluate_frozen_outline_numbering_gates(
        review_pages=frozenset({4}),
        features=tuple(features),
        decisions=tuple(decisions),
        regimes=regimes,
    )

    assert report["status"] == "pass"
    assert report["outline"]["passed_count"] == 29
    assert report["outline"]["r03_result_count"] == 28
    assert report["outline"]["toc_override_result_count"] == 1
    assert report["numbering"]["eligible_heading_count"] == 23
    assert len(report["numbering"]["excluded_first_by_regime"]) == 2
    assert report["numbering"]["passed_count"] == 21
    assert len(report["numbering"]["results"]) == 21

    decisions[5]["corrected_level"] = 3
    failing = evaluate_frozen_outline_numbering_gates(
        review_pages=frozenset({4}),
        features=tuple(features),
        decisions=tuple(decisions),
        regimes=regimes,
    )
    assert failing["status"] == "reject"
    assert failing["outline"]["passed_count"] == 28
    assert failing["numbering"]["passed_count"] == 20


def test_frozen_gate_rejects_a_changed_evaluation_page_scope() -> None:
    with pytest.raises(ValueError, match="frozen exact-outline count differs"):
        evaluate_frozen_outline_numbering_gates(
            review_pages=frozenset({999}),
            features=(),
            decisions=(),
            regimes=(),
        )


def _managed_root(tmp_path: Path, name: str) -> Path:
    root = tmp_path / name
    records = root / "records"
    records.mkdir(parents=True)
    (records / "completion_record.json").write_text("completion\n")
    (records / "artifact_inventory.json").write_text(
        json.dumps({"files": [{"path": "managed.txt", "byte_size": 7, "sha256": "a" * 64}]})
    )
    (root / "managed.txt").write_text("managed")
    return root


def test_verified_snapshots_cover_both_artifacts_and_detect_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    producer = _managed_root(tmp_path, "producer")
    canonical = _managed_root(tmp_path, "canonical")
    monkeypatch.setattr(
        preservation_module,
        "verify_completed_run",
        lambda root, _identity: root / "records/completion_record.json",
    )
    monkeypatch.setattr(
        preservation_module,
        "verify_completed_candidate",
        lambda root, _identity: root / "records/completion_record.json",
    )

    before = (
        snapshot_verified_producer(producer, "prv1-" + "a" * 64),
        snapshot_verified_task03d1_reference(canonical, "exv1-" + "b" * 64),
    )
    assert_artifacts_preserved(before, before)

    inventory = json.loads((canonical / "records/artifact_inventory.json").read_text())
    inventory["files"][0]["sha256"] = "c" * 64
    (canonical / "records/artifact_inventory.json").write_text(json.dumps(inventory))
    after = (
        snapshot_verified_producer(producer, "prv1-" + "a" * 64),
        snapshot_verified_task03d1_reference(canonical, "exv1-" + "b" * 64),
    )
    with pytest.raises(ValueError, match="task03d1_reference"):
        assert_artifacts_preserved(before, after)
