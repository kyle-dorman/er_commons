"""The accepted counting uncertainty cannot relax any unrelated billing gate."""

import copy
import json
from pathlib import Path

import pytest

from er_commons.locked_pricing import accepted_count_fee, count_reservation
from er_commons.locked_run import pricing_blockers


def pricing():
    """Read the explicit authorization metadata, never any provider credentials."""
    return json.loads(Path("configs/task13_pricing_v1.json").read_text())


def test_recorded_exception_allows_preflight_without_claiming_free():
    rates = pricing()
    assert pricing_blockers(rates) == []
    assert rates["openai"]["verified"] is False
    assert rates["openai"]["count_max_usd"] is None
    assert count_reservation("openai", rates["openai"]) == 0


@pytest.mark.parametrize("mutation", ["provider", "generation", "scope", "authorization", "actual"])
def test_exception_is_narrow(mutation):
    rates = copy.deepcopy(pricing()["openai"])
    provider = "openai"
    if mutation == "provider":
        provider = "anthropic"
    elif mutation == "generation":
        rates["generation_rates_verified"] = False
    elif mutation == "scope":
        rates["count_fee_exception"]["scope"] = "all_requests"
    elif mutation == "authorization":
        rates["count_fee_exception"]["accepted_by"] = "agent"
    else:
        rates["count_fee_exception"]["actual_fee_usd"] = 0
    assert not accepted_count_fee(provider, rates)
    with pytest.raises(ValueError, match="Unbounded"):
        count_reservation(provider, rates)
