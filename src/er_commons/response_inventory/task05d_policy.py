"""Shared immutable scope and warning policy for Task 05D."""

from __future__ import annotations

from typing import Final

TASK05D_RANGE: Final = (1, 744)
TASK05D_PAGE_COUNT: Final = TASK05D_RANGE[1] - TASK05D_RANGE[0] + 1
TASK05D_ALLOWED_WARNING_CODES: Final = ("source_response_heading_absent",)

__all__ = [
    "TASK05D_ALLOWED_WARNING_CODES",
    "TASK05D_PAGE_COUNT",
    "TASK05D_RANGE",
]
