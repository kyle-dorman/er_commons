"""Coverage-aware post-run classification metrics with an explicit failed-output category."""

from __future__ import annotations

from typing import Any

Label = bool | int


def classification_metrics(
    expected: list[Label], predicted: list[Label | None], *, classes: tuple[Label, ...]
) -> dict[str, Any]:
    """Count missing outputs as errors and false negatives, never fabricated predictions.

    Macro-F1 averages the declared classes, with zero for a class whose F1
    denominator is zero. An entirely ineligible population has no metrics.
    """
    if not classes or len({(type(value), value) for value in classes}) != len(classes):
        raise ValueError("Require distinct nonempty classes")
    if any(type(value) not in {bool, int} for value in classes):
        raise ValueError("Classes must be strict boolean or integer labels")
    if len({type(value) for value in classes}) != 1:
        raise ValueError("Classes must share one strict label type")
    if len(expected) != len(predicted):
        raise ValueError("Expected and predicted populations differ")
    allowed = {(type(value), value) for value in classes}
    if any((type(value), value) not in allowed for value in expected):
        raise ValueError("Expected label is outside declared classes")
    if any(value is not None and (type(value), value) not in allowed for value in predicted):
        raise ValueError("Prediction is outside declared classes")
    returned = sum(value is not None for value in predicted)
    correct = sum(target == guess for target, guess in zip(expected, predicted, strict=True))
    per_class = []
    valid_f1 = []
    for label in classes:
        tp = sum(
            target == label and guess == label
            for target, guess in zip(expected, predicted, strict=True)
        )
        fp = sum(
            target != label and guess == label
            for target, guess in zip(expected, predicted, strict=True)
        )
        fn = sum(
            target == label and guess != label
            for target, guess in zip(expected, predicted, strict=True)
        )
        missing = sum(
            target == label and guess is None
            for target, guess in zip(expected, predicted, strict=True)
        )
        denominator = 2 * tp + fp + fn
        valid_denominator = denominator - missing
        valid_f1.append(2 * tp / valid_denominator if valid_denominator else 0.0)
        per_class.append(
            {
                "label": label,
                "support": sum(target == label for target in expected),
                "true_positive": tp,
                "false_positive": fp,
                "false_negative": fn,
                "failed": missing,
                "f1": 2 * tp / denominator if denominator else 0.0,
            }
        )
    return {
        "eligible": len(expected),
        "returned": returned,
        "failed": len(expected) - returned,
        "correct": correct,
        "coverage": returned / len(expected) if expected else None,
        "accuracy": correct / len(expected) if expected else None,
        "macro_f1": sum(row["f1"] for row in per_class) / len(classes) if expected else None,
        "classes": list(classes),
        "per_class": per_class,
        "valid_only": {
            "denominator": returned,
            "accuracy": correct / returned if returned else None,
            "macro_f1": sum(valid_f1) / len(classes) if returned else None,
        },
    }
