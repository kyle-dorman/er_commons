"""Focused unit tests for source-backed structural inference rules."""

from __future__ import annotations

import pytest

from er_commons.response_inventory.source_structure import (
    MissingResponseHeading,
    missing_response_heading_gaps,
    paired_response_style_comment_marker_ids,
)


def _page(text: str = "Comment A-1\nResponse A-1") -> dict[str, object]:
    return {
        "record_type": "page",
        "page_id": "p1",
        "activity_id": "act",
        "physical_page": 1,
        "raw_text": text,
    }


def _marker(
    identity: str, kind: str, label: str, start: int, **changes: object
) -> dict[str, object]:
    row: dict[str, object] = {
        "record_type": "marker_candidate",
        "marker_id": identity,
        "page_id": "p1",
        "marker_kind": kind,
        "disposition": "unit_start",
        "observed_label": label,
        "text_start": start,
        "text_end": start + len(label),
        "line_initial": True,
        "style_evidence": {"bold": False, "italic": True, "solid_rule": False, "dotted_rule": True},
    }
    row.update(changes)
    return row


def test_paired_response_style_promotes_exact_adjacent_pair() -> None:
    records = [
        _page(),
        _marker("m1", "comment", "Comment A-1", 0, disposition="needs_review"),
        _marker("m2", "response", "Response A-1", 12),
    ]
    assert paired_response_style_comment_marker_ids(records) == frozenset({"m1"})


@pytest.mark.parametrize(
    "mutation",
    [
        {"line_initial": False},
        {
            "style_evidence": {
                "bold": True,
                "italic": True,
                "solid_rule": False,
                "dotted_rule": True,
            }
        },
        {
            "style_evidence": {
                "bold": False,
                "italic": False,
                "solid_rule": False,
                "dotted_rule": True,
            }
        },
        {
            "style_evidence": {
                "bold": False,
                "italic": True,
                "solid_rule": True,
                "dotted_rule": True,
            }
        },
        {
            "style_evidence": {
                "bold": False,
                "italic": True,
                "solid_rule": False,
                "dotted_rule": False,
            }
        },
    ],
)
def test_paired_response_style_rejects_style_and_position_mutations(
    mutation: dict[str, object],
) -> None:
    records = [
        _page(),
        _marker("m1", "comment", "Comment A-1", 0, disposition="needs_review", **mutation),
        _marker("m2", "response", "Response A-1", 12),
    ]
    assert paired_response_style_comment_marker_ids(records) == frozenset()


def test_paired_response_style_rejects_mismatch_intervening_unit_and_submission() -> None:
    base = [_page(), _marker("m1", "comment", "Comment A-1", 0, disposition="needs_review")]
    assert (
        paired_response_style_comment_marker_ids(
            [*base, _marker("m2", "response", "Response A-2", 12)]
        )
        == frozenset()
    )
    assert (
        paired_response_style_comment_marker_ids(
            [
                *base,
                _marker("mx", "comment", "Comment X-1", 10),
                _marker("m2", "response", "Response A-1", 12),
            ]
        )
        == frozenset()
    )
    assert (
        paired_response_style_comment_marker_ids(
            [
                *base,
                _marker("ms", "submission", "Submission", 10, disposition="section_opener"),
                _marker("m2", "response", "Response A-1", 12),
            ]
        )
        == frozenset()
    )


def _unit(
    identity: str, kind: str, label: str, marker: str, submission: str = "s1"
) -> dict[str, object]:
    return {
        "record_type": "source_unit",
        "unit_id": identity,
        "activity_id": "act",
        "unit_kind": kind,
        "official_label": label,
        "start_marker_id": marker,
        "submission_id": submission,
        "span_ids": [f"span-{identity}"],
    }


def _gap_records(
    *,
    include_response_one: bool = False,
    second_submission: str = "s1",
    second_label: str = "Comment A-2",
) -> list[dict[str, object]]:
    records = [
        _page(""),
        _marker("m1", "comment", "Comment A-1", 0),
        _marker("m2", "comment", second_label, 20),
        _marker("mr2", "response", "Response A-2", 30),
        _unit("u1", "comment", "Comment A-1", "m1"),
        _unit("u2", "comment", second_label, "m2", second_submission),
        _unit("ur2", "response", "Response A-2", "mr2"),
    ]
    if include_response_one:
        records.extend(
            [
                _marker("mr1", "response", "Response A-1", 10),
                _unit("ur1", "response", "Response A-1", "mr1"),
            ]
        )
    return records


def test_missing_heading_reports_exact_single_gap_and_evidence() -> None:
    assert missing_response_heading_gaps(_gap_records(), "act") == (
        MissingResponseHeading("act", "u1", ("m1", "m2", "span-u1")),
    )


@pytest.mark.parametrize(
    "records",
    [
        _gap_records(include_response_one=True),
        _gap_records(second_submission="s2"),
        _gap_records(second_label="Comment A-3"),
        [row for row in _gap_records() if row.get("unit_id") != "ur2"],
    ],
)
def test_missing_heading_rejects_present_or_unproven_boundaries(
    records: list[dict[str, object]],
) -> None:
    assert missing_response_heading_gaps(records, "act") == ()


def test_missing_heading_returns_multiple_ordered_gaps() -> None:
    records = [
        row
        for row in _gap_records()
        if row.get("marker_id") != "mr2" and row.get("unit_id") != "ur2"
    ]
    records.extend(
        [
            _marker("m3", "comment", "Comment A-3", 40),
            _marker("mr3", "response", "Response A-3", 50),
            _unit("u3", "comment", "Comment A-3", "m3"),
            _unit("ur3", "response", "Response A-3", "mr3"),
        ]
    )
    gaps = missing_response_heading_gaps(records, "act")
    assert [gap.comment_unit_id for gap in gaps] == ["u1", "u2"]
