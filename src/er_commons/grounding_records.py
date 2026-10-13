"""Pure saved-sample boundaries and diagnostic aggregation, independent of Inspect."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SavedGroundingSample(BaseModel):
    """A saved packet with labels restricted to analysis rather than grader input."""

    model_config = ConfigDict(strict=True, extra="forbid")
    sample_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    scope: Literal["invented_fixture", "development"]
    packet: dict[str, Any]
    expected_score: int | None = Field(ge=0, le=2)
    category: str = Field(min_length=1)
    control: bool = False
    stage_expectations: dict[str, Any] | None = None


def observed_token_counts(records: list[dict[str, Any]], field: str) -> list[int]:
    """Retain only observed nonnegative integer measurements from native objects."""
    counts = []
    for record in records:
        if record.get("reused"):
            continue
        native = record.get("native")
        output = native.get("output") if isinstance(native, dict) else None
        value = output.get(field) if isinstance(output, dict) else None
        if type(value) is int and value >= 0:
            counts.append(value)
    return counts


def summarize_records(records: list[dict[str, Any]]) -> dict[str, float | int | None]:
    """Expose all denominators; numeric confusion excludes failures and N/A."""
    scored = [r for r in records if r["status"] == "scored"]
    na = [r for r in records if r["status"] == "not_applicable"]
    comparable = [r for r in scored if r["expected_score"] is not None]
    valid = scored + na
    expected_na = [r for r in valid if r["expected_score"] is None]
    proposed_errors = [r for r in scored if r["expected_score"] in (0, 1)]
    controls = [r for r in valid if r["control"]]
    count = len(scored)
    input_counts = observed_token_counts(records, "prompt_eval_count")
    output_counts = observed_token_counts(records, "eval_count")
    summary: dict[str, float | int | None] = {
        "expected": len(records),
        "attempted": sum(r["attempts"] > 0 for r in records),
        "new": sum(r["attempts"] > 0 for r in records),
        "reused": sum(r.get("reused", False) for r in records),
        "scored": count,
        "not_applicable": len(na),
        "failed": len(records) - len(valid),
        "context_blocked": sum(r["status"].startswith("context_") for r in records),
        "schema_failed": sum(r["status"] == "schema_error" for r in records),
        "retries": sum(max(0, r["attempts"] - 1) for r in records),
        "valid_findings": len(valid),
        "grounding_mean": sum(r["score"] for r in scored) / count if count else None,
        "synthetic_numeric_comparable": len(comparable),
        "synthetic_exact_agreement": (
            sum(r["score"] == r["expected_score"] for r in comparable) / len(comparable)
            if comparable
            else None
        ),
        "synthetic_ordinal_absolute_error": (
            sum(abs(r["score"] - r["expected_score"]) for r in comparable) / len(comparable)
            if comparable
            else None
        ),
        "expected_na_valid": len(expected_na),
        "unexpected_na": sum(r["expected_score"] is not None for r in na),
        "numeric_expected_valid_denominator": sum(r["expected_score"] is not None for r in valid),
        "native_input_tokens": sum(input_counts) if input_counts else None,
        "native_input_measured_samples": len(input_counts),
        "native_output_tokens": sum(output_counts) if output_counts else None,
        "native_output_measured_samples": len(output_counts),
        "na_agreement": (
            sum(r["status"] == "not_applicable" for r in expected_na) / len(expected_na)
            if expected_na
            else None
        ),
        "false_supported_count": sum(r["score"] == 2 for r in proposed_errors),
        "false_supported_denominator": len(proposed_errors),
        "control_rejected_count": sum(r["score"] != 2 for r in controls),
        "control_valid_denominator": len(controls),
        "control_scored_denominator": sum(r["status"] == "scored" for r in controls),
        "elapsed_seconds": sum(r["elapsed_seconds"] for r in records),
    }
    for score in range(3):
        summary[f"score_{score}"] = sum(r["score"] == score for r in scored)
        for expected in range(3):
            summary[f"confusion_expected_{expected}_judge_{score}"] = sum(
                r["score"] == score and r["expected_score"] == expected for r in comparable
            )
    question_means = []
    for case_id in sorted({r["case_id"] for r in scored}):
        rows = [r for r in scored if r["case_id"] == case_id]
        question_means.append(sum(r["score"] for r in rows) / len(rows))
    summary["question_balanced_grounding_mean"] = (
        sum(question_means) / len(question_means) if question_means else None
    )
    question_rates = []
    for case_id in sorted({r["case_id"] for r in records}):
        rows = [r for r in comparable if r["case_id"] == case_id]
        if rows:
            question_rates.append(sum(r["score"] == r["expected_score"] for r in rows) / len(rows))
    summary["question_balanced_agreement"] = (
        sum(question_rates) / len(question_rates) if question_rates else None
    )
    summary["question_agreement_denominator"] = len(question_rates)
    for field in ("case_id", "category"):
        for label in sorted({r.get(field, "unspecified") for r in records}):
            rows = [r for r in records if r.get(field, "unspecified") == label]
            eligible = [r for r in rows if r["status"] == "scored"]
            prefix = f"by_{field}_{label}"
            summary[f"{prefix}_expected"] = len(rows)
            summary[f"{prefix}_scored"] = len(eligible)
            summary[f"{prefix}_mean"] = (
                sum(r["score"] for r in eligible) / len(eligible) if eligible else None
            )
    return summary
