"""Hand-calculated fixtures for the frozen automatic metric formulas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from er_commons.automatic_metric_inputs import (
    CitationResolution,
    ReferenceResolution,
    RetrievalResolution,
)
from er_commons.automatic_metrics import MetricRecord, aggregate_metrics, calculate_metrics


def unit(number: int) -> tuple[str, str, str, str]:
    return ("source", "extraction", "section", str(number))


def record(support=(1, 2), context=(), cited=(), invalid=(), retrieval=None):
    return calculate_metrics(
        "invented",
        ReferenceResolution(frozenset(map(unit, support)), frozenset(map(unit, context)), True, ()),
        CitationResolution(frozenset(map(unit, cited)), frozenset(invalid), (), (), True),
        retrieval,
    )


@pytest.mark.parametrize(
    "cited,invalid,expected",
    [
        ((1, 2), (), (1, 1, 1)),
        ((), (), (0, 0, 0)),
        ((1,), (), (1, 0.5, 2 / 3)),
        ((1, 3), (), (0.5, 0.5, 0.5)),
        ((1,), ("bad",), (0.5, 0.5, 0.5)),
        ((1, 2, 3), ("bad",), (0.5, 1, 2 / 3)),
    ],
)
def test_formula_table(cited, invalid, expected):
    result = record(cited=cited, invalid=invalid).citation
    assert (result.precision, result.recall, result.f1) == pytest.approx(expected)


def test_context_neutral_and_support_wins():
    result = record(context=(1, 3), cited=(1, 3))
    assert result.context == [unit(3)]
    assert result.citation.neutral_count == 1
    assert result.citation.precision_denominator == 1
    assert result.citation.precision == 1
    assert result.citation.recall == 0.5
    assert record(context=(3,), cited=(3,)).citation.f1 == 0


def test_missing_empty_and_divergent_retrieval():
    assert record().retrieval.status == "unavailable"
    empty = RetrievalResolution(frozenset(), True)
    result = record(cited=(1, 2), retrieval=empty)
    assert result.retrieval.recall == 0
    assert result.citation.recall == 1
    supplied = RetrievalResolution(frozenset({unit(1), unit(2)}), True)
    result = record(retrieval=supplied)
    assert result.retrieval.recall == 1
    assert result.retrieval.complete == 1
    assert result.citation.recall == 0


def test_empty_support_is_na_and_no_eligible_aggregate_is_null():
    result = record(support=(), cited=(1,))
    assert result.citation.status == result.retrieval.status == "not_applicable"
    assert result.citation.f1 is None
    summary = aggregate_metrics([result])
    assert summary.citation["micro_f1"] is None
    assert summary.retrieval["micro_recall"] is None
    assert summary.citation["not_applicable_cases"] == 1
    assert aggregate_metrics([]).citation["macro_f1"] is None


def test_unavailable_reference_and_citation_infrastructure_are_not_zero():
    result = calculate_metrics(
        "broken",
        ReferenceResolution(frozenset(), frozenset(), False, ("missing source",)),
        CitationResolution(frozenset(), frozenset(), (), (), True),
    )
    assert result.citation.status == "unavailable"
    assert result.retrieval.status == "unavailable"
    result = calculate_metrics(
        "broken",
        ReferenceResolution(frozenset({unit(1)}), frozenset(), True, ()),
        CitationResolution(frozenset(), frozenset(), (), ("missing mapping",), False),
    )
    assert result.citation.precision is None
    assert aggregate_metrics([result]).citation["unavailable_cases"] == 1


def test_pooled_counts_not_mean_f1_and_exclusions_do_not_dilute():
    records = [
        record(support=(1,), cited=(1,)),
        record(support=(1, 2, 3), cited=(1, 4)),
        record(support=()),
    ]
    summary = aggregate_metrics(records).citation
    assert summary["eligible_cases"] == 2
    assert summary["support_count"] == 4
    assert summary["precision_denominator"] == 3
    assert summary["macro_precision"] == 0.75
    assert summary["macro_recall"] == pytest.approx(2 / 3)
    assert summary["macro_f1"] == 0.7
    assert summary["micro_precision"] == pytest.approx(2 / 3)
    assert summary["micro_recall"] == 0.5
    assert summary["micro_f1"] == pytest.approx(4 / 7)


def test_budget_ceiling_does_not_shrink_reference_and_deeper_hits_diagnostic():
    receipt = RetrievalResolution(
        frozenset({unit(1)}),
        True,
        ranked_units=((1, unit(1)), (10, unit(2))),
        unit_budget=1,
        ranked_depth=10,
    )
    result = record(support=(1, 2, 3), retrieval=receipt)
    assert result.retrieval.support_count == 3
    assert result.retrieval.budget_ceiling == pytest.approx(1 / 3)
    assert result.retrieval.recall == pytest.approx(1 / 3)
    assert result.retrieval.recall_at["10"] == pytest.approx(2 / 3)
    assert result.retrieval.complete == 0


def test_counts_and_id_sets_round_trip():
    result = record(cited=(1, 1, 3), invalid=("bad", "bad"))
    restored = MetricRecord.model_validate_json(result.model_dump_json())
    assert restored == result
    assert result.citation.precision_denominator == 3
    assert len(result.invalid_tokens) == 1
    assert aggregate_metrics([restored]) == aggregate_metrics([result])


def test_unobserved_ranked_depth_is_unavailable_with_per_cutoff_denominators():
    shallow = RetrievalResolution(
        frozenset({unit(1)}), True, ranked_units=((1, unit(1)),), ranked_depth=1
    )
    measured = record(retrieval=shallow)
    assert measured.retrieval.recall_at["1"] == 0.5
    assert measured.retrieval.recall_at["3"] is None
    assert measured.retrieval.hits_at["1"] == 1
    summary = aggregate_metrics(
        [measured, record(retrieval=RetrievalResolution(frozenset(), True))]
    )
    assert summary.retrieval["eligible_cases"] == 2
    assert summary.retrieval["eligible_cases_at_1"] == 1
    assert summary.retrieval["support_count_at_1"] == 2
    assert summary.retrieval["eligible_cases_at_3"] == 0
    assert summary.retrieval["micro_recall_at_3"] is None


@pytest.mark.parametrize(
    "changes",
    [
        {"hits": -1},
        {"hits": True},
        {"support_count": "2"},
        {"neutral_count": 1.5},
        {"precision_denominator": 0},
        {"support_count": 0},
        {"hits": 3},
        {"precision": None},
        {"precision": False},
        {"recall": "0.5"},
        {"recall": float("nan")},
        {"f1": float("inf")},
        {"precision": 1.01},
        {"recall": -0.01},
        {"status": "unavailable"},
        {"status": "not_applicable", "precision": None, "recall": None, "f1": None},
    ],
)
def test_persisted_citation_record_rejects_invalid_measurements(changes):
    """Loaded score records must not corrupt population or pooled denominators."""
    payload = record(cited=(1,)).model_dump(mode="json")
    payload["citation"].update(changes)
    with pytest.raises(ValidationError):
        MetricRecord.model_validate(payload)


@pytest.mark.parametrize(
    "changes",
    [
        {"hits": -1},
        {"support_count": True},
        {"hits": 3},
        {"recall": None},
        {"recall": float("nan")},
        {"complete": 0.5},
        {"complete": 1},
        {"budget_ceiling": 1.1},
        {"hits_at": {}},
        {"recall_at": {"1": 0.5}},
        {"hits_at": {"1": 3, "3": None, "5": None, "10": None, "20": None}},
        {"hits_at": {"1": True, "3": None, "5": None, "10": None, "20": None}},
        {"hits_at": {"1": None, "3": None, "5": None, "10": None, "20": None}},
        {"status": "unavailable", "recall": None, "complete": None},
    ],
)
def test_persisted_retrieval_record_rejects_invalid_measurements(changes):
    """Ranked scores require paired availability and safe explicit cutoff counts."""
    retrieval = RetrievalResolution(
        frozenset({unit(1)}), True, ranked_units=((1, unit(1)),), ranked_depth=1
    )
    payload = record(retrieval=retrieval).model_dump(mode="json")
    payload["retrieval"].update(changes)
    with pytest.raises(ValidationError):
        MetricRecord.model_validate(payload)


def test_unavailable_metrics_preserve_partial_counts_without_scores():
    """Unavailable infrastructure can retain observed counts without scoring them."""
    result = calculate_metrics(
        "partial-unavailable",
        ReferenceResolution(frozenset({unit(1)}), frozenset()),
        CitationResolution(frozenset({unit(1)}), frozenset(), available=False),
        RetrievalResolution(frozenset({unit(1)}), False),
    )
    assert result.citation.hits == result.retrieval.hits == 1
    assert result.citation.recall is result.retrieval.recall is None
    assert MetricRecord.model_validate_json(result.model_dump_json()) == result
