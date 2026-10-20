"""Offline confusion-table and historical identity invariants."""

from pathlib import Path

import pytest

from er_commons.reporting_judges import _binary_observations, agreement_from_confusion


def test_invalid_predictions_remain_outside_confusion() -> None:
    """One absent prediction lowers coverage/accuracy without becoming a false label."""
    rows = agreement_from_confusion(
        {"false": {"false": 4, "true": 1}, "true": {"false": 2, "true": 3}}, planned=11
    )
    positive = rows[1]
    assert positive["accuracy_valid_only"] == 7 / 10
    assert positive["accuracy_failure_inclusive"] == 7 / 11
    assert positive["invalid_or_missing"] == 1
    assert positive["precision"] == 3 / 4
    assert positive["recall"] == 3 / 5
    assert positive["f1"] == 6 / 9
    assert positive["coverage"] == 10 / 11


def test_three_class_one_vs_rest_and_macro() -> None:
    """A routing classes retain separate precision, recall and macro-F1."""
    rows = agreement_from_confusion(
        {
            "abstain": {"abstain": 2, "answer": 1, "ambiguous": 0},
            "answer": {"abstain": 0, "answer": 3, "ambiguous": 1},
            "ambiguous": {"abstain": 0, "answer": 1, "ambiguous": 2},
        },
        planned=10,
    )
    assert rows[0]["precision"] == 1
    assert rows[0]["recall"] == 2 / 3
    assert rows[0]["macro_f1_valid_only"] == pytest.approx((4 / 5 + 6 / 9 + 4 / 6) / 3)


def test_empty_class_is_unavailable() -> None:
    """No observed positive support cannot masquerade as perfect accuracy."""
    rows = agreement_from_confusion(
        {"false": {"false": 0, "true": 0}, "true": {"false": 0, "true": 0}}, planned=2
    )
    assert rows[1]["precision"] is None
    assert rows[1]["accuracy_valid_only"] is None
    assert rows[1]["accuracy_failure_inclusive"] == 0


@pytest.mark.parametrize(
    "matrix,planned",
    [
        ({"false": {"false": 1, "true": 0}}, 1),
        ({"true": {"true": -1}}, 1),
        ({"true": {"true": 2}}, 1),
    ],
)
def test_bad_confusion_rejected(matrix: dict[str, dict[str, int]], planned: int) -> None:
    """Summary totals cannot create valid-looking metrics from malformed counts."""
    with pytest.raises(ValueError):
        agreement_from_confusion(matrix, planned=planned)


def test_binary_observation_error_is_not_false_and_identity_retained() -> None:
    """An invalid semantic-looking decision stays unavailable with its epoch."""
    example = {
        "sample_id": "S001",
        "case_id": "C001",
        "expected": True,
        "exposure_stratum": "exact_calibration",
        "decisions": [True, False, None],
        "statuses": ["evaluated", "invalid_output", "missing"],
    }
    rows = _binary_observations([example], {"run_id": "saved", "component": "S"})
    assert [r["valid"] for r in rows] == [True, False, False]
    assert [r["repeat"] for r in rows] == [1, 2, 3]
    assert rows[1]["decision"] is False
    assert rows[1]["sample_id"] == "S001"
    with pytest.raises(ValueError, match="duplicate"):
        _binary_observations([example, example], {})


def test_historical_source_checksum_required(tmp_path: Path) -> None:
    """A changed bound report must not quietly produce refreshed historical metrics."""
    from er_commons.reporting_judges import _read

    source = tmp_path / "summary.json"
    source.write_text('{"valid": 10}')
    with pytest.raises(ValueError, match="checksum mismatch"):
        _read(source, "0" * 64)


def test_repeatability_aligns_correct_negative_labels_and_exact_items() -> None:
    """Correct false decisions count, while repeating wrong labels never counts as correct."""
    from er_commons.reporting_judges import judge_repeatability

    examples = [
        {
            "sample_id": str(i),
            "case_id": "C001",
            "expected": False,
            "exposure_stratum": "synthetic",
            "decisions": [False] * i + [True] * (3 - i),
            "statuses": ["evaluated"] * 3,
        }
        for i in range(4)
    ]
    metadata = {"component": "S", "run_id": "frozen"}
    observations = _binary_observations(examples, metadata)
    items, summaries = judge_repeatability(list(reversed(observations)), metadata)
    assert [item["correct_count"] for item in items] == [0, 1, 2, 3]
    summary = summaries[0]
    assert [summary[f"correct_{i}"] for i in range(4)] == [1, 1, 1, 1]
    assert summary["correct_at_least_once_fraction"] == 3 / 4
    assert summary["correct_all_three_fraction"] == 1 / 4
    assert summary["planned_items"] == 4
    assert summary["observed_correct"] == 6


def test_repeatability_missing_invalid_not_semantic_failure() -> None:
    """Incomplete triples stay unresolved, with known correctness retained separately."""
    from er_commons.reporting_judges import judge_repeatability

    example = {
        "sample_id": "one",
        "case_id": "C001",
        "expected": True,
        "exposure_stratum": "synthetic",
        "decisions": [True, False, True],
        "statuses": ["evaluated", "invalid_output", "evaluated"],
    }
    metadata = {"component": "C", "run_id": "saved"}
    observations = _binary_observations([example], metadata)[:2]
    items, summaries = judge_repeatability(observations, metadata)
    assert items[0]["correct_by_repeat"] == [True, None, None]
    assert items[0]["correct_count"] is None
    assert items[0]["correct_at_least_once"] is None
    assert summaries[0]["unresolved_triples"] == 1
    assert summaries[0]["correct_0"] == 0
    assert summaries[0]["at_least_once_observed_lower_bound"] == 1
    assert summaries[0]["correct_all_three_complete_fraction"] is None


@pytest.mark.parametrize("mutation", ["duplicate", "label", "case", "repeat"])
def test_repeatability_rejects_identity_corruption(mutation: str) -> None:
    """Duplicate slots and changing identities cannot produce plausible repeat counts."""
    from er_commons.reporting_judges import judge_repeatability

    metadata = {"component": "G", "run_id": "saved"}
    example = {
        "sample_id": "point",
        "case_id": "C001",
        "expected": True,
        "exposure_stratum": "synthetic",
        "decisions": [True] * 3,
        "statuses": ["evaluated"] * 3,
    }
    rows = _binary_observations([example], metadata)
    if mutation == "duplicate":
        rows.append(rows[0])
    elif mutation == "label":
        rows[1]["expected"] = False
    elif mutation == "case":
        rows[1]["case_id"] = "C002"
    else:
        rows[1]["repeat"] = 4
    with pytest.raises(ValueError):
        judge_repeatability(rows, metadata)
