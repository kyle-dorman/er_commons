"""Independent Poppler comparison and bounded render-plan evidence for Task 05C."""

from __future__ import annotations

import math
import re
import subprocess
from collections import Counter
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Final

from bs4 import BeautifulSoup

from er_commons.artifact_io import canonical_json_sha256
from er_commons.response_inventory.observations import (
    LineObservation,
    PageObservation,
    observation_to_dict,
)
from er_commons.response_inventory.pilot_policy import (
    POPPLER_PAGE_TIMEOUT_SECONDS,
    QUALIFICATION_RENDER_DPI,
    QUALIFICATION_TOKEN_F1_THRESHOLD,
    TASK05C_FIXED_REVIEW_PAGES,
)

type JsonObject = dict[str, Any]
type CommandRunner = Callable[..., subprocess.CompletedProcess[str]]

_TOKEN_RE: Final = re.compile(r"\w+(?:[-./]\w+)*", re.UNICODE)
_QUALIFICATION_SCHEMA_VERSION: Final = "er_commons.response_inventory.qualification.v1"


def qualify_selected_pages(
    pdf_path: Path,
    observations: Sequence[PageObservation],
    cache_root: Path,
    *,
    runner: CommandRunner = subprocess.run,
) -> JsonObject:
    """Compare and render only already-authorized observations with Poppler."""
    render_root = cache_root / "renders_96dpi"
    render_root.mkdir(parents=True, exist_ok=True)
    page_results: list[JsonObject] = []
    for observation in sorted(observations, key=lambda item: item.physical_page):
        page = observation.physical_page
        bbox_result = _run_poppler(
            runner,
            [
                "pdftotext",
                "-f",
                str(page),
                "-l",
                str(page),
                "-bbox-layout",
                str(pdf_path),
                "-",
            ],
            page=page,
        )
        poppler_text = _bbox_words(bbox_result.stdout)
        token_f1 = token_multiset_f1(observation.raw_text, poppler_text)
        render_prefix = render_root / f"page-{page:04d}"
        _run_poppler(
            runner,
            [
                "pdftoppm",
                "-f",
                str(page),
                "-l",
                str(page),
                "-r",
                str(QUALIFICATION_RENDER_DPI),
                "-gray",
                "-png",
                "-singlefile",
                str(pdf_path),
                str(render_prefix),
            ],
            page=page,
        )
        render_path = render_prefix.with_suffix(".png")
        if not render_path.is_file():
            raise ValueError(f"Poppler did not create the selected-page render: {page}")
        flagged = (
            token_f1 < QUALIFICATION_TOKEN_F1_THRESHOLD
            or observation.title_page
            or observation.revision_markup
            or any(
                line.revision_marks or _line_geometry_is_invalid(observation, line)
                for line in observation.lines
            )
        )
        page_results.append(
            {
                "physical_page": page,
                "pdfium_poppler_token_multiset_f1": round(token_f1, 8),
                "render_path": render_path.relative_to(cache_root).as_posix(),
                "fixed_review_page": page in TASK05C_FIXED_REVIEW_PAGES,
                "flagged_for_review": flagged,
                "visual_disposition": None,
            }
        )
    return {
        "schema_version": _QUALIFICATION_SCHEMA_VERSION,
        "render_dpi": QUALIFICATION_RENDER_DPI,
        "comparison_threshold": QUALIFICATION_TOKEN_F1_THRESHOLD,
        "observation_digest": qualification_observation_digest(observations),
        "selected_page_count": len(page_results),
        "review_page_count": sum(
            item["fixed_review_page"] or item["flagged_for_review"] for item in page_results
        ),
        "pages": page_results,
    }


def qualification_observation_digest(observations: Sequence[PageObservation]) -> str:
    """Bind qualification evidence to the exact ordered page observations."""
    ordered = sorted(observations, key=lambda item: item.physical_page)
    return canonical_json_sha256([observation_to_dict(item) for item in ordered])


def validate_qualification_report(
    report: JsonObject,
    observations: Sequence[PageObservation],
    cache_root: Path,
) -> None:
    """Reject incomplete, stale, or unsafe qualification evidence before reuse."""
    expected_pages = sorted(item.physical_page for item in observations)
    _validate_qualification_header(report, observations, expected_pages)
    pages = _validated_qualification_pages(report, expected_pages)
    resolved_root = cache_root.resolve()
    for item in pages:
        _validate_qualification_page(item, resolved_root)
    review_count = sum(item["fixed_review_page"] or item["flagged_for_review"] for item in pages)
    if report.get("review_page_count") != review_count:
        raise ValueError("qualification review-page count differs from page evidence")


def _validate_qualification_header(
    report: JsonObject,
    observations: Sequence[PageObservation],
    expected_pages: Sequence[int],
) -> None:
    """Validate report-level version, settings, count, and observation identity."""
    if report.get("schema_version") != _QUALIFICATION_SCHEMA_VERSION:
        raise ValueError("qualification report has an unexpected schema version")
    if report.get("render_dpi") != QUALIFICATION_RENDER_DPI:
        raise ValueError(f"qualification report render DPI must be {QUALIFICATION_RENDER_DPI}")
    if report.get("comparison_threshold") != QUALIFICATION_TOKEN_F1_THRESHOLD:
        raise ValueError(
            f"qualification report comparison threshold must be {QUALIFICATION_TOKEN_F1_THRESHOLD}"
        )
    if report.get("selected_page_count") != len(expected_pages):
        raise ValueError("qualification selected-page count differs from observations")
    if report.get("observation_digest") != qualification_observation_digest(observations):
        raise ValueError("qualification report is not bound to the current observations")


def _validated_qualification_pages(
    report: JsonObject, expected_pages: Sequence[int]
) -> list[JsonObject]:
    """Return page rows only after exact ordered coverage is established."""
    pages = report.get("pages")
    if not isinstance(pages, list) or not all(isinstance(item, dict) for item in pages):
        raise ValueError("qualification report pages must be a list of objects")
    reported_pages = [item.get("physical_page") for item in pages]
    if any(isinstance(page, bool) or not isinstance(page, int) for page in reported_pages):
        raise ValueError("qualification physical pages must be integers")
    if reported_pages != expected_pages or len(set(reported_pages)) != len(reported_pages):
        raise ValueError("qualification report does not contain each selected page exactly once")
    return pages


def _validate_qualification_page(item: JsonObject, resolved_root: Path) -> None:
    """Validate one comparison result and its contained nonempty PNG render."""
    page = int(item["physical_page"])
    score = item.get("pdfium_poppler_token_multiset_f1")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1:
        raise ValueError(f"qualification page {page} has an invalid comparison score")
    expected_fixed = page in TASK05C_FIXED_REVIEW_PAGES
    if not isinstance(item.get("fixed_review_page"), bool) or (
        item["fixed_review_page"] is not expected_fixed
    ):
        raise ValueError(f"qualification page {page} has an invalid fixed-review flag")
    if not isinstance(item.get("flagged_for_review"), bool):
        raise ValueError(f"qualification page {page} has an invalid review flag")
    if item.get("visual_disposition") not in {None, "accepted", "requires_followup"}:
        raise ValueError(f"qualification page {page} has an invalid visual disposition")
    relative_render = item.get("render_path")
    if not isinstance(relative_render, str) or not relative_render:
        raise ValueError(f"qualification page {page} lacks a render path")
    relative_path = Path(relative_render)
    render_path = (resolved_root / relative_path).resolve()
    if (
        relative_path.is_absolute()
        or ".." in relative_path.parts
        or not render_path.is_relative_to(resolved_root)
        or render_path.suffix.lower() != ".png"
        or not render_path.is_file()
        or render_path.stat().st_size == 0
    ):
        raise ValueError(f"qualification page {page} render is missing or unsafe")


def _line_geometry_is_invalid(observation: PageObservation, line: LineObservation) -> bool:
    text = observation.raw_text[line.text_start : line.text_end]
    if not text.strip():
        return False
    start = line.character_slot_start
    end = line.character_slot_end
    if (
        start is None
        or end is None
        or start < 0
        or end <= start
        or end > observation.character_slot_count
    ):
        return True
    left, bottom, right, top = line.bbox
    return not (
        all(math.isfinite(value) for value in line.bbox)
        and 0 <= left <= right <= observation.width_points
        and 0 <= bottom <= top <= observation.height_points
    )


def _run_poppler(
    runner: CommandRunner, command: list[str], *, page: int
) -> subprocess.CompletedProcess[str]:
    tool = command[0]
    try:
        return runner(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=POPPLER_PAGE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            f"{tool} timed out after {POPPLER_PAGE_TIMEOUT_SECONDS}s for physical page {page}"
        ) from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "no diagnostic output").strip()
        raise RuntimeError(f"{tool} failed for physical page {page}: {detail}") from error
    except OSError as error:
        raise RuntimeError(f"could not run {tool} for physical page {page}: {error}") from error


def token_multiset_f1(left: str, right: str) -> float:
    """Compare case-folded token multiplicities without assuming reading order."""
    left_counts = Counter(token.casefold() for token in _TOKEN_RE.findall(left))
    right_counts = Counter(token.casefold() for token in _TOKEN_RE.findall(right))
    left_total = sum(left_counts.values())
    right_total = sum(right_counts.values())
    if left_total == 0 and right_total == 0:
        return 1.0
    if left_total == 0 or right_total == 0:
        return 0.0
    overlap = sum((left_counts & right_counts).values())
    precision = overlap / right_total
    recall = overlap / left_total
    return 2 * precision * recall / (precision + recall)


def required_visual_review_pages(report: JsonObject) -> tuple[int, ...]:
    """Return the fixed plus evidence-triggered review set from one report."""
    pages = report.get("pages")
    if not isinstance(pages, list):
        raise ValueError("qualification report lacks page results")
    return tuple(
        int(item["physical_page"])
        for item in pages
        if isinstance(item, dict)
        and (item.get("fixed_review_page") is True or item.get("flagged_for_review") is True)
    )


def flag_record_review_pages(report: JsonObject, records: Sequence[JsonObject]) -> JsonObject:
    """Add pages implicated by unresolved semantic marker evidence to review."""
    page_numbers = {
        str(record["page_id"]): int(record["physical_page"])
        for record in records
        if record.get("record_type") == "page"
    }
    implicated = {
        page_numbers[str(record["page_id"])]
        for record in records
        if record.get("record_type") == "marker_candidate"
        and record.get("disposition") == "needs_review"
        and str(record.get("page_id")) in page_numbers
    }
    pages = report.get("pages")
    if not isinstance(pages, list):
        raise ValueError("qualification report lacks page results")
    for item in pages:
        if not isinstance(item, dict):
            raise ValueError("qualification page result is malformed")
        if int(item["physical_page"]) in implicated:
            item["flagged_for_review"] = True
    report["review_page_count"] = len(required_visual_review_pages(report))
    return report


def apply_visual_dispositions(
    report: JsonObject, dispositions: dict[int, str] | None
) -> tuple[JsonObject, tuple[int, ...]]:
    """Apply explicit human dispositions and return any review pages still open."""
    dispositions = dispositions or {}
    pages = report.get("pages")
    if not isinstance(pages, list):
        raise ValueError("qualification report lacks page results")
    expected = set(required_visual_review_pages(report))
    if set(dispositions) - expected:
        raise ValueError("visual dispositions include pages outside the required review set")
    for item in pages:
        if not isinstance(item, dict):
            raise ValueError("qualification page result is malformed")
        page = int(item["physical_page"])
        disposition = dispositions.get(page)
        if disposition is not None and disposition not in {"accepted", "requires_followup"}:
            raise ValueError(f"unsupported visual disposition for page {page}")
        item["visual_disposition"] = disposition
    unresolved = tuple(
        page
        for page in sorted(expected)
        if next(
            item.get("visual_disposition")
            for item in pages
            if isinstance(item, dict) and int(item["physical_page"]) == page
        )
        != "accepted"
    )
    report["review_complete"] = not unresolved
    report["unresolved_review_pages"] = list(unresolved)
    return report, unresolved


def poppler_versions(*, runner: CommandRunner = subprocess.run) -> dict[str, str]:
    """Capture exact Poppler command versions for the source activity identity."""
    versions: dict[str, str] = {}
    for command in ("pdftotext", "pdftoppm"):
        try:
            result = runner(
                [command, "-v"],
                check=True,
                capture_output=True,
                text=True,
                timeout=POPPLER_PAGE_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise RuntimeError(f"could not query {command} version: {error}") from error
        first_line = (result.stderr or result.stdout).splitlines()
        if not first_line:
            raise ValueError(f"{command} did not report a version")
        versions[command] = first_line[0].strip()
    return versions


def _bbox_words(xhtml: str) -> str:
    soup = BeautifulSoup(xhtml, "html.parser")
    return " ".join(word.get_text() for word in soup.find_all("word"))


__all__ = [
    "apply_visual_dispositions",
    "flag_record_review_pages",
    "poppler_versions",
    "qualification_observation_digest",
    "qualify_selected_pages",
    "required_visual_review_pages",
    "token_multiset_f1",
    "validate_qualification_report",
]
