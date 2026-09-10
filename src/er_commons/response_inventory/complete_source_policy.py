"""Accepted historical complete-source scope and warning policy.

The 1-744 bounds describe the accepted corpus recipe, not a generic source default."""

from __future__ import annotations

from typing import Final

ACCEPTED_COMPLETE_RANGE: Final = (1, 744)
ACCEPTED_COMPLETE_PAGE_COUNT: Final = ACCEPTED_COMPLETE_RANGE[1] - ACCEPTED_COMPLETE_RANGE[0] + 1
ACCEPTED_WARNING_CODES: Final = ("source_response_heading_absent",)

__all__ = [
    "ACCEPTED_WARNING_CODES",
    "ACCEPTED_COMPLETE_PAGE_COUNT",
    "ACCEPTED_COMPLETE_RANGE",
]
