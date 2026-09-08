"""Human-readable Task 05C selection and qualification policy.

Keep exact pilot decisions here so generic receipt, parser, and validation code
does not become the accidental owner of document-specific scope.
"""

from __future__ import annotations

from typing import Final

type PageRange = tuple[int, int]

TASK05C_PILOT_RANGES: Final[tuple[PageRange, ...]] = (
    (1, 5),
    (23, 25),
    (31, 44),
    (82, 92),
    (154, 158),
    (171, 175),
    (179, 185),
    (368, 372),
    (551, 555),
    (575, 577),
    (668, 671),
    (684, 691),
    (720, 726),
    (738, 744),
)
TASK05C_RIGHT_CENSORED_RANGE: Final[PageRange] = (368, 372)

# The contract combines range edges, dense high-risk ranges, and a small set of
# representative layouts. Evidence-triggered pages are added at runtime.
_FULL_REVIEW_RANGES: Final[tuple[PageRange, ...]] = ((368, 372), (551, 555), (668, 671))
_REPRESENTATIVE_REVIEW_PAGES: Final[frozenset[int]] = frozenset(
    {2, 4, 38, 39, 83, 84, 721, 722, 744}
)
TASK05C_FIXED_REVIEW_PAGES: Final[frozenset[int]] = frozenset(
    {
        *(page for first, last in TASK05C_PILOT_RANGES for page in (first, last)),
        *(page for first, last in _FULL_REVIEW_RANGES for page in range(first, last + 1)),
        *_REPRESENTATIVE_REVIEW_PAGES,
    }
)

# These values are evidence gates, not parser heuristics. F1 below the threshold
# requests human review; it never rewrites source text automatically.
QUALIFICATION_RENDER_DPI: Final[int] = 96
QUALIFICATION_TOKEN_F1_THRESHOLD: Final[float] = 0.98
POPPLER_PAGE_TIMEOUT_SECONDS: Final[int] = 120

__all__ = [
    "POPPLER_PAGE_TIMEOUT_SECONDS",
    "QUALIFICATION_RENDER_DPI",
    "QUALIFICATION_TOKEN_F1_THRESHOLD",
    "TASK05C_FIXED_REVIEW_PAGES",
    "TASK05C_PILOT_RANGES",
    "TASK05C_RIGHT_CENSORED_RANGE",
]
