"""Deterministic reference-set arithmetic, independent of Inspect and model calls."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.automatic_metric_inputs import (
    CanonicalUnit,
    CitationResolution,
    ReferenceResolution,
    RetrievalResolution,
)

MetricStatus = Literal["eligible", "not_applicable", "unavailable"]
CUTOFFS = (1, 3, 5, 10, 20)
Count = Annotated[int, Field(strict=True, ge=0)]
UnitScore = Annotated[float, Field(strict=True, ge=0, le=1, allow_inf_nan=False)]


class RecordModel(BaseModel):
    """Reject accidental fields in persisted metric records."""

    model_config = ConfigDict(extra="forbid")


def _validate_status(status: MetricStatus, support_count: int) -> None:
    """Known support is nonempty for eligibility and empty for N/A."""
    if status == "eligible" and not support_count:
        raise ValueError("Eligible metrics require nonempty support")
    if status == "not_applicable" and support_count:
        raise ValueError("Not-applicable metrics require empty support")


class CitationMetrics(RecordModel):
    """Raw citation counts and nullable scores with explicit eligibility."""

    status: MetricStatus
    hits: Count
    support_count: Count
    precision_denominator: Count
    neutral_count: Count
    precision: UnitScore | None
    recall: UnitScore | None
    f1: UnitScore | None

    @model_validator(mode="after")
    def validate_measurement(self) -> Self:
        """Reject counts and eligibility states that cannot describe a measurement."""
        _validate_status(self.status, self.support_count)
        if self.hits > min(self.support_count, self.precision_denominator):
            raise ValueError("Citation hits exceed a scoring denominator")
        scores = (self.precision, self.recall, self.f1)
        if any((value is not None) != (self.status == "eligible") for value in scores):
            raise ValueError("Citation scores must be present exactly when eligible")
        return self


class RetrievalMetrics(RecordModel):
    """Actual delivery scores and separately identified ranked diagnostics."""

    status: MetricStatus
    hits: Count
    support_count: Count
    recall: UnitScore | None
    complete: UnitScore | None
    budget_ceiling: UnitScore | None
    recall_at: dict[str, UnitScore | None]
    hits_at: dict[str, Count | None]

    @model_validator(mode="after")
    def validate_measurement(self) -> Self:
        """Keep primary eligibility and optional ranked populations reconstructable."""
        _validate_status(self.status, self.support_count)
        if self.hits > self.support_count:
            raise ValueError("Retrieval hits exceed the support denominator")
        eligible = self.status == "eligible"
        if any((value is not None) != eligible for value in (self.recall, self.complete)):
            raise ValueError("Retrieval scores must be present exactly when eligible")
        if self.complete is not None and self.complete != float(self.hits == self.support_count):
            raise ValueError("Complete-case indicator disagrees with retrieval counts")
        if not eligible and self.budget_ceiling is not None:
            raise ValueError("Ineligible retrieval cannot have a budget ceiling")
        expected = set(map(str, CUTOFFS))
        if set(self.recall_at) != expected or set(self.hits_at) != expected:
            raise ValueError("Ranked diagnostics require exactly the supported cutoff keys")
        for cutoff in map(str, CUTOFFS):
            hits, recall = self.hits_at[cutoff], self.recall_at[cutoff]
            if (hits is None) != (recall is None):
                raise ValueError("Ranked hit counts and recall must have matching availability")
            if hits is not None and (not eligible or hits > self.support_count):
                raise ValueError("Ranked hits require eligibility and cannot exceed support")
        return self


class MetricRecord(RecordModel):
    """Reconstructable per-case metric result; never a judge/model input."""

    schema_version: Literal["task09d.metric_record.v1"] = "task09d.metric_record.v1"
    case_id: str
    support: list[CanonicalUnit]
    context: list[CanonicalUnit]
    cited: list[CanonicalUnit]
    retrieved: list[CanonicalUnit]
    invalid_tokens: list[str]
    citation_attempts: list[dict[str, Any]]
    diagnostics: list[str]
    receipt: dict[str, Any] | None
    citation: CitationMetrics
    retrieval: RetrievalMetrics


class MetricSummary(RecordModel):
    """Separate population counts, pooled counts and nullable aggregate scores."""

    schema_version: Literal["task09d.metric_summary.v1"] = "task09d.metric_summary.v1"
    citation: dict[str, float | int | None] = Field(default_factory=dict)
    retrieval: dict[str, float | int | None] = Field(default_factory=dict)


def _status(available: bool, support_count: int) -> MetricStatus:
    """Unknown reference infrastructure takes precedence over empty-set N/A."""
    if not available:
        return "unavailable"
    return "eligible" if support_count else "not_applicable"


def _ratio(numerator: int, denominator: int) -> float:
    """Apply the contract's measured-empty zero rule, only for eligible cases."""
    return numerator / denominator if denominator else 0.0


def _f1(precision: float, recall: float) -> float:
    """Compute harmonic mean, with the specified both-zero convention."""
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def calculate_metrics(
    case_id: str,
    references: ReferenceResolution,
    citations: CitationResolution,
    retrieval: RetrievalResolution | None = None,
) -> MetricRecord:
    """Calculate independent canonical-set metrics without inferring retrieval."""
    support = references.support
    context = references.context - support
    cited = citations.units
    returned = retrieval.units if retrieval is not None else frozenset()
    support_count = len(support)
    citation_status = _status(references.available and citations.available, support_count)
    retrieval_status = _status(
        references.available and retrieval is not None and retrieval.available, support_count
    )
    # An explicitly known empty reference set is N/A even if no receipt exists.
    if references.available and not support_count:
        citation_status = retrieval_status = "not_applicable"
    citation_hits = len(cited & support)
    precision_denominator = len(cited - context) + len(citations.invalid_tokens)
    precision = recall = f1 = None
    if citation_status == "eligible":
        precision = _ratio(citation_hits, precision_denominator)
        recall = _ratio(citation_hits, support_count)
        f1 = _f1(precision, recall)
    retrieval_hits = len(returned & support)
    retrieval_recall = complete = budget_ceiling = None
    recall_at: dict[str, float | None] = dict.fromkeys(map(str, CUTOFFS))
    hits_at: dict[str, int | None] = dict.fromkeys(map(str, CUTOFFS))
    if retrieval_status == "eligible" and retrieval is not None:
        retrieval_recall = _ratio(retrieval_hits, support_count)
        complete = float(retrieval_hits == support_count)
        if retrieval.unit_budget is not None:
            budget_ceiling = min(retrieval.unit_budget, support_count) / support_count
        for cutoff in CUTOFFS:
            if cutoff > retrieval.ranked_depth and not retrieval.ranking_exhausted:
                continue
            ranked = {unit for rank, unit in retrieval.ranked_units if rank <= cutoff}
            hits_at[str(cutoff)] = len(ranked & support)
            recall_at[str(cutoff)] = len(ranked & support) / support_count
    diagnostics = [*references.diagnostics, *citations.diagnostics]
    diagnostics.extend(
        retrieval.diagnostics if retrieval is not None else ["retrieval_receipt_absent"]
    )
    return MetricRecord(
        case_id=case_id,
        support=sorted(support),
        context=sorted(context),
        cited=sorted(cited),
        retrieved=sorted(returned),
        invalid_tokens=sorted(citations.invalid_tokens),
        citation_attempts=list(citations.attempts),
        diagnostics=diagnostics,
        receipt=retrieval.receipt if retrieval is not None else None,
        citation=CitationMetrics(
            status=citation_status,
            hits=citation_hits,
            support_count=support_count,
            precision_denominator=precision_denominator,
            neutral_count=len(cited & context),
            precision=precision,
            recall=recall,
            f1=f1,
        ),
        retrieval=RetrievalMetrics(
            status=retrieval_status,
            hits=retrieval_hits,
            support_count=support_count,
            recall=retrieval_recall,
            complete=complete,
            budget_ceiling=budget_ceiling,
            recall_at=recall_at,
            hits_at=hits_at,
        ),
    )


def _mean(values: Sequence[float | None]) -> float | None:
    """Average explicitly present measurements; no framework zero substitution."""
    present = [value for value in values if value is not None]
    return sum(present) / len(present) if present else None


def _population(statuses: Sequence[MetricStatus]) -> dict[str, float | int | None]:
    """Expose all exclusions alongside eligible population size."""
    return {
        "total_cases": len(statuses),
        "eligible_cases": statuses.count("eligible"),
        "unavailable_cases": statuses.count("unavailable"),
        "not_applicable_cases": statuses.count("not_applicable"),
    }


def aggregate_metrics(records: Sequence[MetricRecord]) -> MetricSummary:
    """Pool eligible raw counts and recompute micro F1 from pooled P/R."""
    citation = _population([record.citation.status for record in records])
    cs = [record.citation for record in records if record.citation.status == "eligible"]
    hits = sum(row.hits for row in cs)
    support = sum(row.support_count for row in cs)
    denominator = sum(row.precision_denominator for row in cs)
    micro_precision = _ratio(hits, denominator) if cs else None
    micro_recall = _ratio(hits, support) if cs else None
    citation.update(
        hits=hits,
        support_count=support,
        precision_denominator=denominator,
        neutral_count=sum(row.neutral_count for row in cs),
        macro_precision=_mean([row.precision for row in cs]),
        macro_recall=_mean([row.recall for row in cs]),
        macro_f1=_mean([row.f1 for row in cs]),
        micro_precision=micro_precision,
        micro_recall=micro_recall,
        micro_f1=(
            _f1(micro_precision, micro_recall)
            if micro_precision is not None and micro_recall is not None
            else None
        ),
    )
    retrieval = _population([record.retrieval.status for record in records])
    rs = [record.retrieval for record in records if record.retrieval.status == "eligible"]
    retrieval_hits = sum(row.hits for row in rs)
    retrieval_support = sum(row.support_count for row in rs)
    retrieval.update(
        hits=retrieval_hits,
        support_count=retrieval_support,
        macro_recall=_mean([row.recall for row in rs]),
        micro_recall=_ratio(retrieval_hits, retrieval_support) if rs else None,
        complete_cases=sum(row.complete == 1 for row in rs),
        complete_case_recall=_mean([row.complete for row in rs]),
        macro_budget_ceiling=_mean([row.budget_ceiling for row in rs]),
        budget_ceiling_cases=sum(row.budget_ceiling is not None for row in rs),
    )
    for cutoff in CUTOFFS:
        eligible_at = [row for row in rs if row.hits_at[str(cutoff)] is not None]
        hits_at = sum(row.hits_at[str(cutoff)] or 0 for row in eligible_at)
        support_at = sum(row.support_count for row in eligible_at)
        retrieval[f"eligible_cases_at_{cutoff}"] = len(eligible_at)
        retrieval[f"hits_at_{cutoff}"] = hits_at
        retrieval[f"support_count_at_{cutoff}"] = support_at
        retrieval[f"macro_recall_at_{cutoff}"] = _mean(
            [row.recall_at[str(cutoff)] for row in eligible_at]
        )
        retrieval[f"micro_recall_at_{cutoff}"] = (
            _ratio(hits_at, support_at) if eligible_at else None
        )
    return MetricSummary(citation=citation, retrieval=retrieval)
