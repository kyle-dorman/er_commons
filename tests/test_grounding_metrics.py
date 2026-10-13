"""Hand-calculated coverage metrics keep failed outputs in accuracy and F1."""

import pytest

from er_commons.grounding_metrics import classification_metrics


def test_missing_output_counts_as_error_and_true_class_false_negative() -> None:
    """A missing negative prediction lowers full-panel F1 despite perfect returned outputs."""
    result = classification_metrics(
        [False, False, True], [False, None, True], classes=(False, True)
    )
    assert result["eligible"] == 3
    assert result["returned"] == 2
    assert result["failed"] == 1
    assert result["accuracy"] == pytest.approx(2 / 3)
    assert result["macro_f1"] == pytest.approx((2 / 3 + 1) / 2)
    assert result["per_class"][0]["false_negative"] == 1
    assert result["per_class"][1]["false_positive"] == 0
    assert result["valid_only"] == {"denominator": 2, "accuracy": 1.0, "macro_f1": 1.0}


def test_wrong_and_missing_multiclass_outputs_have_distinct_accounting() -> None:
    """Wrong predictions add a false positive; missing predictions invent no class."""
    result = classification_metrics([0, 1, 2, 2], [0, 2, 2, None], classes=(0, 1, 2))
    assert result["accuracy"] == 0.5
    assert result["macro_f1"] == pytest.approx((1 + 0 + 0.5) / 3)
    assert result["per_class"][2]["false_positive"] == 1
    assert result["per_class"][2]["false_negative"] == 1
    assert result["valid_only"]["macro_f1"] == pytest.approx((1 + 0 + 2 / 3) / 3)


def test_absent_classes_are_fixed_and_empty_population_is_not_perfect() -> None:
    """The report states fixed classes rather than silently changing macro denominators."""
    single_class = classification_metrics([2], [2], classes=(0, 1, 2))
    assert single_class["macro_f1"] == pytest.approx(1 / 3)
    empty = classification_metrics([], [], classes=(False, True))
    assert empty["accuracy"] is empty["macro_f1"] is None
    missing = classification_metrics([False, True], [None, None], classes=(False, True))
    assert missing["accuracy"] == missing["macro_f1"] == 0.0
    assert missing["valid_only"]["accuracy"] is None


@pytest.mark.parametrize(
    "expected,predicted,classes",
    [
        ([True], [1], (False, True)),
        ([1], [True], (0, 1, 2)),
        ([1], [], (0, 1, 2)),
        ([3], [None], (0, 1, 2)),
        ([1], [1], (True, 1)),
    ],
)
def test_metrics_reject_coercion_and_misaligned_populations(expected, predicted, classes) -> None:
    """Booleans cannot impersonate numeric scores, or unknown labels disappear."""
    with pytest.raises(ValueError):
        classification_metrics(expected, predicted, classes=classes)
