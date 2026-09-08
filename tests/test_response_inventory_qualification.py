"""Source-free tests for Task 05C comparison and review selection."""

from __future__ import annotations

import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from er_commons.response_inventory.observations import LineObservation, PageObservation
from er_commons.response_inventory.qualification import (
    apply_visual_dispositions,
    flag_record_review_pages,
    qualify_selected_pages,
    required_visual_review_pages,
    token_multiset_f1,
    validate_qualification_report,
)


def test_token_multiset_f1_ignores_case_and_order_but_not_missing_tokens() -> None:
    assert token_multiset_f1("Response A-1 text", "text response a-1") == 1.0
    assert 0 < token_multiset_f1("one two three", "one two") < 1
    assert token_multiset_f1("", "") == 1.0
    assert token_multiset_f1("one", "") == 0.0


def test_review_pages_combine_fixed_and_flagged_evidence() -> None:
    report = {
        "pages": [
            {"physical_page": 1, "fixed_review_page": True, "flagged_for_review": False},
            {"physical_page": 2, "fixed_review_page": False, "flagged_for_review": True},
            {"physical_page": 3, "fixed_review_page": False, "flagged_for_review": False},
        ]
    }
    assert required_visual_review_pages(report) == (1, 2)


def test_visual_review_must_explicitly_accept_every_required_page() -> None:
    report = {
        "pages": [
            {"physical_page": 1, "fixed_review_page": True, "flagged_for_review": False},
            {"physical_page": 2, "fixed_review_page": False, "flagged_for_review": True},
            {"physical_page": 3, "fixed_review_page": False, "flagged_for_review": False},
        ]
    }
    updated, unresolved = apply_visual_dispositions(report, {1: "accepted"})
    assert unresolved == (2,)
    assert updated["review_complete"] is False
    updated, unresolved = apply_visual_dispositions(report, {1: "accepted", 2: "accepted"})
    assert unresolved == ()
    assert updated["review_complete"] is True


def test_unresolved_marker_candidate_adds_its_page_to_review() -> None:
    report = {
        "pages": [{"physical_page": 7, "fixed_review_page": False, "flagged_for_review": False}]
    }
    records: list[dict[str, object]] = [
        {"record_type": "page", "page_id": "pagev1-x", "physical_page": 7},
        {
            "record_type": "marker_candidate",
            "page_id": "pagev1-x",
            "disposition": "needs_review",
        },
    ]
    updated = flag_record_review_pages(report, records)
    assert required_visual_review_pages(updated) == (7,)
    assert updated["review_page_count"] == 1


def test_nonempty_line_without_character_geometry_requires_review(tmp_path: Path) -> None:
    observation = _observation_without_geometry(6)

    def fake_runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if command[0] == "pdftoppm":
            Path(command[-1]).with_suffix(".png").write_bytes(b"synthetic-png")
            stdout = ""
        else:
            stdout = "<doc><word>source</word><word>text</word></doc>"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    report = qualify_selected_pages(
        tmp_path / "source.pdf", [observation], tmp_path / "qualification", runner=fake_runner
    )

    assert report["pages"][0]["flagged_for_review"] is True
    validate_qualification_report(report, [observation], tmp_path / "qualification")


def test_qualification_validation_rejects_incomplete_stale_and_missing_render(
    tmp_path: Path,
) -> None:
    observation = _observation_without_geometry(6)
    cache_root = tmp_path / "qualification"

    def fake_runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if command[0] == "pdftoppm":
            Path(command[-1]).with_suffix(".png").write_bytes(b"synthetic-png")
            stdout = ""
        else:
            stdout = "<doc><word>source</word><word>text</word></doc>"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    report = qualify_selected_pages(
        tmp_path / "source.pdf", [observation], cache_root, runner=fake_runner
    )

    incomplete = deepcopy(report)
    incomplete["pages"] = []
    with pytest.raises(ValueError, match="each selected page exactly once"):
        validate_qualification_report(incomplete, [observation], cache_root)

    stale = deepcopy(report)
    stale["observation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="current observations"):
        validate_qualification_report(stale, [observation], cache_root)

    wrong_settings = deepcopy(report)
    wrong_settings["render_dpi"] = 150
    with pytest.raises(ValueError, match="render DPI"):
        validate_qualification_report(wrong_settings, [observation], cache_root)

    invalid_score = deepcopy(report)
    invalid_score["pages"][0]["pdfium_poppler_token_multiset_f1"] = "perfect"
    with pytest.raises(ValueError, match="invalid comparison score"):
        validate_qualification_report(invalid_score, [observation], cache_root)

    render_path = cache_root / str(report["pages"][0]["render_path"])
    render_path.unlink()
    with pytest.raises(ValueError, match="render is missing or unsafe"):
        validate_qualification_report(report, [observation], cache_root)


def test_poppler_timeout_names_tool_page_and_bound(tmp_path: Path) -> None:
    observation = _observation_without_geometry(6)

    def timeout_runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(command, timeout=120)

    with pytest.raises(
        RuntimeError,
        match=r"pdftotext timed out after 120s for physical page 6",
    ):
        qualify_selected_pages(
            tmp_path / "source.pdf",
            [observation],
            tmp_path / "qualification",
            runner=timeout_runner,
        )


def _observation_without_geometry(page: int) -> PageObservation:
    text = "source text"
    return PageObservation(
        physical_page=page,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=(
            LineObservation(
                line_index=0,
                text_start=0,
                text_end=len(text),
                bbox=(0, 0, 612, 792),
            ),
        ),
    )
