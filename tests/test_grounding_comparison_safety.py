"""Invented exact-counter, cap and durable-receipt boundary regressions."""

import json
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from er_commons.artifact_io import stable_json_sha256
from er_commons.grounding_comparison_safety import (
    CounterReceipt,
    RunBudget,
    amount,
    begin_attempt,
    complete_attempt,
    estimate_cost,
    preflight,
    reuse_attempt,
    worst_case_cost,
)

REQUEST = {"model": "fixture", "state": "Invented evidence", "schema": {"support": "boolean"}}
CONDITION = {"endpoint": "fixture://invented", "model": "fixture", "version": 1}


def receipt(**updates: object) -> CounterReceipt:
    """Bind the full invented request, never a benchmark or live counter."""
    return CounterReceipt.model_validate(
        {
            "request_sha256": stable_json_sha256(REQUEST),
            "condition_sha256": stable_json_sha256(CONDITION),
            "input_tokens": 100,
            "state_longest_tokens": 90,
            "provenance": "invented",
            "exact": True,
            **updates,
        }
    )


def qualified(**updates: object) -> dict:
    """Supply fixture qualification through the trusted adapter-only argument."""
    return preflight(
        REQUEST,
        CONDITION,
        receipt(),
        context_limit=120,
        output_reserve=20,
        qualified_counter_provenance="invented",
        **updates,
    )


def test_exact_count_full_binding_and_limit_boundary() -> None:
    """A count exactly at capacity passes; any changed field invalidates its receipt."""
    assert qualified()["dispatch_allowed"]
    for request in ({**REQUEST, "schema": {}}, {**REQUEST, "model": "other"}):
        assert (
            preflight(
                request,
                CONDITION,
                receipt(),
                context_limit=120,
                output_reserve=20,
                qualified_counter_provenance="invented",
            )["status"]
            == "counter_binding_mismatch"
        )
    assert (
        preflight(
            REQUEST,
            {**CONDITION, "version": 2},
            receipt(),
            context_limit=120,
            output_reserve=20,
            qualified_counter_provenance="invented",
        )["status"]
        == "counter_binding_mismatch"
    )
    assert (
        preflight(
            REQUEST,
            CONDITION,
            receipt(),
            context_limit=119,
            output_reserve=20,
            qualified_counter_provenance="invented",
        )["status"]
        == "context_overflow"
    )


def test_receipt_file_cannot_self_qualify() -> None:
    """Exact-looking receipt data is insufficient without a trusted qualified adapter."""
    assert (
        preflight(REQUEST, CONDITION, receipt(), context_limit=120, output_reserve=20)["status"]
        == "context_unverified"
    )
    assert (
        preflight(
            REQUEST,
            CONDITION,
            receipt(exact=False),
            context_limit=120,
            output_reserve=20,
            qualified_counter_provenance="invented",
        )["status"]
        == "counter_binding_mismatch"
    )
    assert (
        preflight(REQUEST, CONDITION, None, context_limit=None, output_reserve=20)["status"]
        == "context_unverified"
    )


def test_independent_body_and_state_question_limits() -> None:
    """Independent provider restrictions cannot be replaced by the total token ceiling."""
    assert qualified(state_longest_limit=90)["dispatch_allowed"]
    assert qualified(state_longest_limit=89)["status"] == "state_question_overflow"
    assert qualified(body_limit=1)["status"] == "request_body_overflow"
    assert (
        preflight(
            REQUEST,
            CONDITION,
            receipt(state_longest_tokens=None),
            context_limit=120,
            output_reserve=20,
            state_longest_limit=90,
            qualified_counter_provenance="invented",
        )["status"]
        == "context_unverified"
    )


@pytest.mark.parametrize("bad", [True, -1, 2.5, "100"])
def test_counter_rejects_coercion(bad: object) -> None:
    """Token counts must be strict integers rather than truth values or estimates."""
    with pytest.raises(ValidationError):
        receipt(input_tokens=bad)


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-1", True, 0.1])
def test_currency_is_finite_exact_nonnegative(bad: object) -> None:
    """Malformed decimal prices cannot disable positive cap checks."""
    with pytest.raises(ValueError):
        amount(bad)  # type: ignore[arg-type]


def test_disjoint_cache_pricing_and_worst_case_write_premium() -> None:
    """Cache writes use full write rate; reservations include the larger write price."""
    rates = {"input": "2", "output": "8", "cache_read": ".2", "cache_write": "2.5"}
    assert estimate_cost(
        1000, 100, rates, cache_read_tokens=200, cache_write_tokens=300
    ) == Decimal(".00259")
    assert worst_case_cost(1000, 100, rates) == Decimal(".0033")
    with pytest.raises(ValueError, match="Missing"):
        estimate_cost(1000, 1, {})
    with pytest.raises(ValueError, match="exceed"):
        estimate_cost(100, 0, rates, cache_read_tokens=101)


def test_reservations_before_dispatch_are_cumulative_and_never_refunded() -> None:
    """Even a failed call consumes its request, output and potentially billed currency."""
    budget = RunBudget(".01", 2, 20, 60)
    first = budget.reserve(".004", 10)
    assert first["request_number"] == 1
    second = budget.reserve(".006", 10)
    assert (
        second["total_currency_reserved"] == ".010" or second["total_currency_reserved"] == "0.010"
    )
    with pytest.raises(ValueError, match="request_cap"):
        budget.reserve(0, 0)
    assert budget.requests_reserved == 2


@pytest.mark.parametrize(
    "kwargs,cost,output,error",
    [
        ({"currency_cap": "0.01"}, ".011", 1, "currency_cap"),
        ({"output_cap": 1}, ".001", 2, "output_cap"),
        ({"started": 0}, ".001", 1, "wall_clock_cap"),
    ],
)
def test_cap_failure_leaves_no_reservation(
    kwargs: dict, cost: str, output: int, error: str
) -> None:
    """Failed admission must not partially mutate a later request's available budget."""
    budget = RunBudget(
        **{"currency_cap": ".1", "request_cap": 2, "output_cap": 20, "wall_seconds": 60, **kwargs}
    )
    with pytest.raises(ValueError, match=error):
        budget.reserve(cost, output)
    assert budget.requests_reserved == 0 and budget.currency_reserved == 0


def test_positive_paid_cap_required_and_free_local_allowed() -> None:
    """A local zero-cost run still requires finite request, output and time bounds."""
    with pytest.raises(ValueError):
        RunBudget(0, 1, 1, 1)
    assert RunBudget(0, 1, 1, 1, paid=False).reserve(0, 1)["cost_reserved"] == "0"
    for cap in (float("inf"), float("nan"), 0):
        with pytest.raises(ValueError):
            RunBudget(1, 1, 1, cap)


def test_intent_blocks_uncertain_replay_and_seal_allows_matching_reuse(tmp_path: Path) -> None:
    """A crash after intent is not a permission to resend a possibly billed request."""
    directory = tmp_path / "attempt"
    assert reuse_attempt(directory, REQUEST, CONDITION) is None
    reservation = RunBudget(1, 1, 10, 60).reserve(".01", 10)
    begin_attempt(directory, REQUEST, CONDITION, qualified(), reservation)
    with pytest.raises(ValueError, match="Uncertain"):
        reuse_attempt(directory, REQUEST, CONDITION)
    with pytest.raises(FileExistsError):
        begin_attempt(directory, REQUEST, CONDITION, qualified(), reservation)
    response = {"usage": {"input_tokens": 100}, "result": True}
    complete_attempt(directory, response)
    assert reuse_attempt(directory, REQUEST, CONDITION) == response
    with pytest.raises(ValueError, match="mismatch"):
        reuse_attempt(directory, REQUEST, {**CONDITION, "version": 2})
    with pytest.raises(FileExistsError):
        complete_attempt(directory, response)
    (directory / "response.json").write_text(json.dumps({"result": False}))
    with pytest.raises(ValueError, match="mismatch"):
        reuse_attempt(directory, REQUEST, CONDITION)


def test_http_body_limit_excludes_envelope_but_count_binding_includes_it() -> None:
    """Protocol body caps exclude adapter metadata, but counts bind the endpoint too."""
    envelope = {"endpoint": "fixture://invented/" + "x" * 100, "body": {"state": "tiny"}}
    count = receipt(request_sha256=stable_json_sha256(envelope))
    assert preflight(
        envelope,
        CONDITION,
        count,
        context_limit=120,
        output_reserve=20,
        body_limit=16,
        qualified_counter_provenance="invented",
    )["dispatch_allowed"]
    assert not preflight(
        {**envelope, "endpoint": "different"},
        CONDITION,
        count,
        context_limit=120,
        output_reserve=20,
        qualified_counter_provenance="invented",
    )["dispatch_allowed"]


def test_config_pricing_preserves_decimal_spelling_and_conservative_rates() -> None:
    """Reviewed JSON numeric prices map to exact currency without inventing unknown fees."""
    from er_commons.grounding_comparison_safety import rates_for_condition

    pricing = {
        "input_per_million": 0.1,
        "conservative_input_per_million": 0.275,
        "output_per_million": 0.5,
        "cache_read_per_million": None,
        "cache_write_per_million": 0.125,
    }
    conservative = rates_for_condition(pricing)
    assert conservative["input"] == Decimal("0.275")
    assert "cache_read" not in conservative
    assert rates_for_condition(pricing, conservative=False)["input"] == Decimal("0.1")
    assert worst_case_cost(1000, 100, conservative) == Decimal(".000325")
    for bad in (float("nan"), True, -1):
        with pytest.raises(ValueError):
            rates_for_condition({"input_per_million": bad})


def test_remaining_deadline_is_finite_and_applies_to_dispatch_timeout() -> None:
    """Restored or malformed deadlines cannot remove the native timeout boundary."""
    budget = RunBudget(1, 1, 1, 60)
    assert 0 < budget.remaining_seconds() <= 60
    budget.started = float("nan")
    with pytest.raises(ValueError, match="wall_clock_cap"):
        budget.remaining_seconds()


@pytest.mark.parametrize(
    "filename", ["intent.json", "request.json", "response.json", "completion.json"]
)
def test_nonobject_saved_receipts_fail_closed(tmp_path: Path, filename: str) -> None:
    """Malformed receipt shapes fail deliberately instead of crashing with attribute errors."""
    from er_commons.grounding_comparison_safety import AttemptReceiptError

    directory = tmp_path / "attempt"
    begin_attempt(directory, REQUEST, CONDITION, qualified(), {"request_number": 1})
    complete_attempt(directory, {"result": True})
    (directory / filename).write_text("[]")
    with pytest.raises(AttemptReceiptError, match="objects"):
        reuse_attempt(directory, REQUEST, CONDITION)
