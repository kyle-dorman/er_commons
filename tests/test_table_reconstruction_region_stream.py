"""Tests for the source-faithful region-bounded Stream fallback."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pandas as pd  # type: ignore[import-untyped]
import pytest

from er_commons.document_parsing.content_parsing.routing_geometry import (
    DisplayedPageTransform,
)
from er_commons.document_parsing.table_reconstruction import (
    region_stream_fallback,
    region_stream_geometry,
    region_stream_text,
)
from er_commons.document_parsing.table_reconstruction.learned_table_types import JsonObject
from er_commons.document_parsing.table_reconstruction.native_text import native_word_tokens


@dataclass
class FakeCell:
    x1: float
    y1: float
    x2: float
    y2: float


class FakeTable:
    """Minimal well-formed Camelot table used at the parser boundary."""

    shape = (2, 2)
    order = 1
    _bbox = (0.0, 0.0, 100.0, 100.0)
    cols = [(0.0, 50.0), (50.0, 100.0)]
    rows = [(100.0, 50.0), (50.0, 0.0)]
    cells = [
        [FakeCell(0, 50, 50, 100), FakeCell(50, 50, 100, 100)],
        [FakeCell(0, 0, 50, 50), FakeCell(50, 0, 100, 50)],
    ]
    df = pd.DataFrame([["Header", "Value"], ["Alpha", "1"]])
    parsing_report = {"accuracy": 99.0, "whitespace": 0.0}


class OvershootingTable(FakeTable):
    """Stream grid whose rightmost cells extend beyond the requested region."""

    cols = [(0.0, 50.0), (50.0, 100.75)]
    cells = [
        [FakeCell(0, 50, 50, 100), FakeCell(50, 50, 100.75, 100)],
        [FakeCell(0, 0, 50, 50), FakeCell(50, 0, 100.75, 50)],
    ]


class FakeTextPage:
    def count_chars(self) -> int:
        return 1

    def get_text_range(self, _index: int, _count: int) -> str:
        return "A"

    def get_charbox(self, _index: int) -> tuple[float, float, float, float]:
        return (10.0, 30.0, 20.0, 40.0)


def _detection() -> dict[str, object]:
    return {
        "render_scale": 2.0,
        "minimum_region_match_iou": 0.5,
        "minimum_region_stream_native_text_coverage": 0.9,
        "maximum_region_stream_bbox_overshoot_points": 1.5,
    }


def _clean_rows(
    rows: list[list[str]], _cleanup: dict[str, Any]
) -> tuple[list[list[str]], dict[str, Any]]:
    return rows, {}


def _table_rows(table: FakeTable) -> list[list[str]]:
    return cast(list[list[str]], table.df.values.tolist())


def _apply(
    monkeypatch: pytest.MonkeyPatch,
    *,
    ruled: bool = False,
) -> tuple[list[JsonObject], JsonObject]:
    if not ruled:
        monkeypatch.setattr(
            region_stream_fallback,
            "read_region_tables",
            lambda *_args, **_kwargs: [FakeTable()],
        )
    monkeypatch.setattr(
        region_stream_text,
        "native_tokens",
        lambda *_args, **_kwargs: [
            {"id": index, "text": text}
            for index, text in enumerate(("Header", "Value", "Alpha", "1"))
        ],
    )
    evidence = {
        "region_matches": [{"region_id": "layout_001", "matched": False, "matched_iou": 0.0}]
    }
    candidates = region_stream_fallback.apply_region_stream_fallbacks(
        pdf_path=Path("not-opened.pdf"),
        page_number=1,
        page_size=(100.0, 100.0),
        opencv_ruled_regions=(
            [{"bbox_pdf_points_bottom_left": [0.0, 0.0, 10.0, 10.0]}] if ruled else []
        ),
        accepted_candidates=[],
        parser_evidence=evidence,
        layout_regions=[
            {
                "region_id": "layout_001",
                "bbox_pdf_points_bottom_left": [0.0, 0.0, 100.0, 100.0],
            }
        ],
        detection=_detection(),
        cleanup={},
        table_rows=_table_rows,
        clean_rows=_clean_rows,
    )
    return candidates, evidence


def test_native_tokens_are_rotated_into_display_coordinates() -> None:
    transform = DisplayedPageTransform.create(
        (200.0, 100.0),
        (0.0, 0.0, 100.0, 200.0),
        90,
    )

    tokens = native_word_tokens(
        FakeTextPage(),
        [25.0, 75.0, 45.0, 95.0],
        scale=2.0,
        transform=transform,
    )

    assert len(tokens) == 1
    assert tokens[0]["bbox_pdf_points_bottom_left"] == [30.0, 80.0, 40.0, 90.0]


def test_accepts_one_exact_text_conserving_stream_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidates, evidence = _apply(monkeypatch)

    assert len(candidates) == 1
    assert candidates[0]["parser"] == "camelot_stream"
    assert evidence["region_matches"][0]["matched"] is True
    attempt = evidence["region_stream_attempts"][0]
    assert attempt["status"] == "accepted"
    assert attempt["measurements"]["native_text_coverage"] == 1.0
    assert attempt["measurements"]["duplicated_native_character_count"] == 0


def test_discretionary_pdf_hyphen_matches_rendered_stream_hyphen() -> None:
    table = FakeTable()
    table.df = pd.DataFrame([["projects affordable to low-", "income households"]])
    tokens = [
        {"text": "projects affordable to low\ufffe"},
        {"text": "income households"},
    ]

    measurements = region_stream_text.text_measurements(table, tokens)

    assert measurements["native_text_coverage"] == 1.0
    assert measurements["duplicated_native_character_count"] == 0


def test_stream_cannot_invent_an_ordinary_hyphen() -> None:
    table = FakeTable()
    table.df = pd.DataFrame([["low-", "income"]])

    measurements = region_stream_text.text_measurements(table, [{"text": "lowincome"}])

    assert measurements["native_text_coverage"] == 1.0
    assert measurements["duplicated_native_character_count"] == 1


def test_stream_noncharacter_is_not_treated_as_a_native_discretionary_hyphen() -> None:
    table = FakeTable()
    table.df = pd.DataFrame([["low\ufffe", "income"]])

    measurements = region_stream_text.text_measurements(table, [{"text": "low-income"}])

    assert measurements["native_text_coverage"] < 1.0
    assert measurements["duplicated_native_character_count"] == 1


def test_ruled_overlap_abstains_before_invoking_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Stream must not run for a ruled region")

    monkeypatch.setattr(region_stream_fallback, "read_region_tables", fail_if_called)
    candidates, evidence = _apply(monkeypatch, ruled=True)

    assert candidates == []
    assert evidence["region_matches"][0]["matched"] is False
    assert evidence["region_stream_attempts"][0]["reason"] == "ruled_region_overlap"


def test_small_cell_bbox_overshoot_is_accepted() -> None:
    issue, overshoot = region_stream_geometry.geometry_issue(
        OvershootingTable(),
        page_size=(101.0, 100.0),
        region_bbox=[0.0, 0.0, 100.0, 100.0],
        maximum_cell_overshoot=1.5,
    )

    assert issue is None
    assert overshoot == 0.75


def test_large_cell_bbox_overshoot_has_explicit_reason() -> None:
    issue, overshoot = region_stream_geometry.geometry_issue(
        OvershootingTable(),
        page_size=(101.0, 100.0),
        region_bbox=[0.0, 0.0, 100.0, 100.0],
        maximum_cell_overshoot=0.5,
    )

    assert issue == "cell_bbox_exceeds_region"
    assert overshoot == 0.75
