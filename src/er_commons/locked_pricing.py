"""The specific user-accepted OpenAI count-fee uncertainty, separate from prices."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def accepted_count_fee(provider: str, rates: dict[str, Any]) -> bool:
    """Accept only the recorded OpenAI counting exception with verified generation."""
    exception = rates.get("count_fee_exception", {})
    return (
        provider == "openai"
        and rates.get("verified") is False
        and rates.get("generation_rates_verified") is True
        and rates.get("count_max_usd") is None
        and exception.get("scope") == "openai_responses_input_tokens_only"
        and exception.get("accepted_by") == "user"
        and exception.get("accepted_on") == "2026-10-20"
        and exception.get("status") == "accepted_unknown_fee"
        and exception.get("planning_allowance_usd") == 0
        and "actual_fee_usd" in exception
        and exception["actual_fee_usd"] is None
    )


def bounded_or_accepted(provider: str, rates: dict[str, Any]) -> bool:
    """Keep all other unknown provider/count pricing blocked."""
    return (
        rates.get("verified") is True and rates.get("count_max_usd") is not None
    ) or accepted_count_fee(provider, rates)


def count_reservation(provider: str, rates: dict[str, Any]) -> Decimal:
    """Return the declared bound or explicitly accepted zero planning allowance."""
    if accepted_count_fee(provider, rates):
        return Decimal(str(rates["count_fee_exception"]["planning_allowance_usd"]))
    if not bounded_or_accepted(provider, rates):
        raise ValueError("Unbounded provider billing: no dispatch permitted")
    return Decimal(str(rates["count_max_usd"]))
