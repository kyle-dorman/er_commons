"""Source-free tests for deterministic response source-unit construction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.response_inventory import build_record_id, validate_record_bundle
from er_commons.response_inventory.observations import LineObservation, PageObservation
from er_commons.response_inventory.producer import _classify_page_state, build_source_records

type JsonObject = dict[str, Any]

SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "benchmarks/er_bench/schemas/response_inventory/v1/records.schema.json"
)


def _activity(page_ranges: list[list[int]], *, stage: str = "05c") -> JsonObject:
    record: JsonObject = {
        "schema_version": "er_commons.response_inventory.v1",
        "record_type": "activity",
        "stage": stage,
        "source_id": "feir_volume_4",
        "page_ranges": page_ranges,
        "config_sha256": "0" * 64,
        "schema_sha256": "1" * 64,
        "code_sha256": "2" * 64,
        "tool_versions": {"pypdfium2": "5.12.1"},
        "input_refs": [
            {
                "role": "source_record",
                "identity": "source-record",
                "authority": "artifact_root",
                "path": "datasets/source_manifest.json",
            },
            {
                "role": "task05a_completion",
                "identity": "3" * 64,
                "authority": "artifact_root",
                "path": "pipelines/task05a_completion.json",
            },
        ],
    }
    record["activity_id"] = build_record_id(record)
    return record


def _lines(text: str, styles: dict[int, dict[str, bool]]) -> tuple[LineObservation, ...]:
    observations: list[LineObservation] = []
    offset = 0
    for index, value in enumerate(text.splitlines(keepends=True)):
        content = value.rstrip("\r\n")
        end = offset + len(content)
        style = styles.get(index, {})
        observations.append(
            LineObservation(
                line_index=index,
                text_start=offset,
                text_end=end,
                bbox=(72.0, 700.0 - 20 * index, 500.0, 714.0 - 20 * index),
                character_slot_start=offset,
                character_slot_end=end,
                bold=style.get("bold", False),
                italic=style.get("italic", False),
                solid_rule=style.get("solid_rule", False),
                dotted_rule=style.get("dotted_rule", False),
            )
        )
        offset += len(value)
    return tuple(observations)


def test_builds_closed_units_continuation_and_raw_reference() -> None:
    first_text = "Comment A-1\nA concern.\nResponse A-1\nSee Draft EIR Section 3.1.\n"
    second_text = "Continued response.\n"
    pages = [
        PageObservation(
            physical_page=1,
            raw_text=first_text,
            width_points=612,
            height_points=792,
            rotation=0,
            character_slot_count=len(first_text),
            lines=_lines(
                first_text,
                {
                    0: {"bold": True, "solid_rule": True},
                    2: {"italic": True, "dotted_rule": True},
                },
            ),
        ),
        PageObservation(
            physical_page=2,
            raw_text=second_text,
            width_points=612,
            height_points=792,
            rotation=0,
            character_slot_count=len(second_text),
            lines=_lines(second_text, {}),
            closes_open_unit=True,
        ),
    ]

    records = build_source_records(_activity([[1, 2]]), pages)

    units = [record for record in records if record["record_type"] == "source_unit"]
    assert [unit["unit_kind"] for unit in units] == ["comment", "response"]
    assert len([record for record in records if record["record_type"] == "page_continuation"]) == 1
    mentions = [record for record in records if record["record_type"] == "reference_mention"]
    assert [(item["reference_domain"], item["target_labels"]) for item in mentions] == [
        ("draft_eir", ["Draft EIR Section 3.1"])
    ]
    states = [record["page_state"] for record in records if record["record_type"] == "page"]
    assert states == ["mixed_markers", "continuation"]


def test_right_censored_response_is_diagnostic_not_complete_unit() -> None:
    text = "Response M-OSEC-137\nThe response continues.\n"
    page = PageObservation(
        physical_page=372,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=_lines(text, {0: {"italic": True, "dotted_rule": True}}),
    )

    records = build_source_records(_activity([[372, 372]]), [page])

    assert not [record for record in records if record["record_type"] == "source_unit"]
    diagnostics = [record for record in records if record["record_type"] == "diagnostic"]
    assert len(diagnostics) == 1
    assert diagnostics[0]["code"] == "unit_boundary_ambiguous"
    assert diagnostics[0]["terminal"] is True


def test_open_boundary_diagnostic_uses_activity_stage() -> None:
    text = "Response A-1\nThe response continues.\n"
    page = PageObservation(
        physical_page=1,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=_lines(text, {0: {"italic": True, "dotted_rule": True}}),
    )

    records = build_source_records(_activity([[1, 1]], stage="05d"), [page])

    diagnostic = next(record for record in records if record["record_type"] == "diagnostic")
    assert diagnostic["stage"] == "05d"


def test_gr9_creates_placement_exception_but_no_unit() -> None:
    text = "General Response 9 is routed to Chapter 16 in Volume 5.\n"
    page = PageObservation(
        physical_page=38,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=_lines(text, {}),
    )

    records = build_source_records(_activity([[38, 38]]), [page])

    assert (
        len([record for record in records if record["record_type"] == "source_placement_exception"])
        == 1
    )
    assert not [record for record in records if record["record_type"] == "source_unit"]


@pytest.mark.parametrize(
    "pages",
    [
        ["General Response 9 appears in the contents. Chapter 16 discusses methods.\n"],
        ["General Response 9 appears in the contents.\n", "Volume 5 discusses methods.\n"],
        ["General Response 9 appears here.\n\nVolume 5 discusses methods.\n"],
    ],
)
def test_gr9_unrelated_route_mentions_do_not_create_placement_exception(
    pages: list[str],
) -> None:
    observations = [
        PageObservation(
            physical_page=index,
            raw_text=text,
            width_points=612,
            height_points=792,
            rotation=0,
            character_slot_count=len(text),
            lines=_lines(text, {}),
            section_opener=True,
        )
        for index, text in enumerate(pages, start=1)
    ]

    records = build_source_records(_activity([[1, len(pages)]]), observations)

    assert not [
        record for record in records if record["record_type"] == "source_placement_exception"
    ]


def test_gr9_cross_page_route_requires_shared_topic_context() -> None:
    texts = [
        "General Response 9: Maximum Building Heights and Tower Buildings\n",
        "Refer to Chapter 16, Response Addressing Maximum Building Heights and Tower Buildings.\n",
    ]
    pages = [
        PageObservation(
            physical_page=index,
            raw_text=text,
            width_points=612,
            height_points=792,
            rotation=0,
            character_slot_count=len(text),
            lines=_lines(text, {}),
            section_opener=True,
        )
        for index, text in enumerate(texts, start=1)
    ]

    records = build_source_records(_activity([[1, 2]]), pages)

    exceptions = [
        record for record in records if record["record_type"] == "source_placement_exception"
    ]
    assert len(exceptions) == 1
    evidence_ids = set(exceptions[0]["evidence_ids"])
    evidence_pages = {
        fragment["page_id"]
        for record in records
        if record.get("span_id") in evidence_ids
        for fragment in record["fragments"]
    }
    assert len(evidence_pages) == 2


def test_gr9_and_plain_gr_contents_entries_never_become_units() -> None:
    text = "General Response 9\nGeneral Response 3\nResponse A-1\nDone.\n"
    page = PageObservation(
        physical_page=38,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=_lines(
            text,
            {
                0: {"bold": True},
                2: {"italic": True, "dotted_rule": True},
            },
        ),
        closes_open_unit=True,
    )

    records = build_source_records(_activity([[38, 38]]), [page])

    units = [record for record in records if record["record_type"] == "source_unit"]
    assert [(unit["unit_kind"], unit["official_label"]) for unit in units] == [
        ("response", "Response A-1")
    ]
    candidates = [record for record in records if record["record_type"] == "marker_candidate"]
    assert [
        (record["observed_label"], record["disposition"])
        for record in candidates
        if record["marker_kind"] == "general_response"
    ] == [
        ("General Response 9", "section_opener"),
        ("General Response 3", "needs_review"),
    ]


@pytest.mark.parametrize(
    "heading",
    [
        "13.2.2 GENERAL RESPONSE 2: EXAMPLE HEADING",
        "13.2.2 GENERAL RESPONSE 2: HIGH\x02SPEED RAIL FACILITY",
        "4.1 GENERAL RESPONSE NO. 4: LAND USE AND TRANSPORTATION",
    ],
)
def test_numbered_uppercase_general_response_heading_survives_missing_font_style(
    heading: str,
) -> None:
    text = f"{heading}\nBody.\n"
    page = PageObservation(
        physical_page=1,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=_lines(text, {}),
        closes_open_unit=True,
    )
    records = build_source_records(_activity([[1, 1]]), [page])
    units = [record for record in records if record["record_type"] == "source_unit"]
    assert [(unit["unit_kind"], unit["official_label"]) for unit in units] == [
        (
            "general_response",
            "GENERAL RESPONSE 2" if "RESPONSE 2" in heading else "GENERAL RESPONSE NO. 4",
        )
    ]


@pytest.mark.parametrize(
    "heading",
    [
        "13.2.2 GENERAL RESPONSE 2 ........ 13-5",
        "13.2.2 GENERAL RESPONSE 2: TRANSPORTATION 13-5",
        "13.2.2 GENERAL RESPONSE 2",
        "13.2.2 GENERAL RESPONSE 2: Mixed Case Contents Entry 13-5",
    ],
)
def test_numbered_uppercase_general_response_fallback_rejects_nonheadings(
    heading: str,
) -> None:
    text = f"{heading}\n"
    page = PageObservation(
        physical_page=1,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=_lines(text, {}),
        section_opener=True,
        closes_open_unit=True,
    )

    records = build_source_records(_activity([[1, 1]]), [page])

    assert not [record for record in records if record["record_type"] == "source_unit"]
    candidate = next(
        record
        for record in records
        if record["record_type"] == "marker_candidate"
        and record["marker_kind"] == "general_response"
    )
    assert candidate["disposition"] == "needs_review"


def test_submission_closes_gr_and_scopes_following_unit_and_membership() -> None:
    text = (
        "   General Response 3\n"
        "a. Comments\n"
        "Comment Letter: O-Joint-1\n"
        "13.7.4 LETTER M-SFPUC\n"
        "Submitted by: City and County of San Francisco\n"
        "Comment M-SFPUC-1\n"
        "Body.\n"
    )
    page = PageObservation(
        physical_page=100,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=_lines(
            text,
            {
                0: {"bold": True},
                5: {"bold": True, "solid_rule": True},
            },
        ),
        closes_open_unit=True,
    )

    records = build_source_records(_activity([[100, 100]]), [page])

    submissions = [record for record in records if record["record_type"] == "submission"]
    assert len(submissions) == 1
    assert submissions[0]["submission_kind"] == "letter"
    assert submissions[0]["official_code"] == "M-SFPUC"
    commenters = [record for record in records if record["record_type"] == "commenter"]
    assert [record["source_label"] for record in commenters] == ["City and County of San Francisco"]
    assert submissions[0]["commenter_ids"] == [commenters[0]["commenter_id"]]

    units = [record for record in records if record["record_type"] == "source_unit"]
    general_response = next(unit for unit in units if unit["unit_kind"] == "general_response")
    comment = next(unit for unit in units if unit["unit_kind"] == "comment")
    assert general_response["submission_id"] is None
    assert comment["submission_id"] == submissions[0]["submission_id"]
    general_response_span = next(
        record
        for record in records
        if record["record_type"] == "source_span"
        and record["span_id"] == general_response["span_ids"][0]
    )
    assert general_response_span["fragments"][0]["text_start"] == text.index("General Response 3")
    assert general_response_span["fragments"][0]["text_end"] == text.index("13.7.4 LETTER")
    memberships = [record for record in records if record["record_type"] == "membership_claim"]
    assert [record["target_label"] for record in memberships] == ["O-Joint-1"]
    validate_record_bundle(records, json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


def test_numbered_transcript_is_a_submission_boundary() -> None:
    text = "13.10.1 TRANSCRIPT PC-NL\nResponse PC-NL-1\nBody.\n"
    page = PageObservation(
        physical_page=200,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=_lines(text, {1: {"italic": True, "dotted_rule": True}}),
        closes_open_unit=True,
    )

    records = build_source_records(_activity([[200, 200]]), [page])

    submission = next(record for record in records if record["record_type"] == "submission")
    unit = next(record for record in records if record["record_type"] == "source_unit")
    assert submission["submission_kind"] == "meeting"
    assert submission["official_code"] == "PC-NL"
    assert submission["commenter_ids"] == []
    assert unit["submission_id"] == submission["submission_id"]


def test_submission_opener_requires_uppercase_hyphenated_official_code() -> None:
    text = "Letter Code\nLetter M-mixed\nLetter ORG\nLetter AB-CD/EF\nLetter AB-12\n"
    page = PageObservation(
        physical_page=1,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=_lines(text, {}),
        section_opener=True,
    )

    records = build_source_records(_activity([[1, 1]]), [page])

    submissions = [record for record in records if record["record_type"] == "submission"]
    assert [record["official_code"] for record in submissions] == ["AB-12"]


def test_numbered_general_response_needs_bold_heading_evidence() -> None:
    text = (
        "12.4.2 General Response 4\n"
        "12.4.3 General Response 5\n"
        "See General Response 6 for details.\n"
        "12.4.9 General Response 9\n"
    )
    page = PageObservation(
        physical_page=1,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=_lines(text, {0: {"bold": True}, 3: {"bold": True}}),
        closes_open_unit=True,
    )

    records = build_source_records(_activity([[1, 1]]), [page])

    units = [record for record in records if record["record_type"] == "source_unit"]
    assert [(record["unit_kind"], record["official_label"]) for record in units] == [
        ("general_response", "General Response 4")
    ]
    candidates = [
        record
        for record in records
        if record["record_type"] == "marker_candidate"
        and record["marker_kind"] == "general_response"
    ]
    assert [(record["observed_label"], record["disposition"]) for record in candidates] == [
        ("General Response 4", "unit_start"),
        ("General Response 5", "needs_review"),
        ("General Response 6", "inline_reference"),
        ("General Response 9", "section_opener"),
    ]


def test_roster_row_materializes_commenter_and_links_matching_submission() -> None:
    roster_text = (
        "SA-Caltrans State Transportation Agency\n"
        "ZX-TEAM Example Review Coalition\n"
        "QX-7 Seventh District\n"
        "Letter Code\n"
    )
    submission_text = "14.2 LETTER SA-CALTRANS\nResponse SA-CALTRANS-1\nDone.\n"
    pages = [
        PageObservation(
            physical_page=1,
            raw_text=roster_text,
            width_points=612,
            height_points=792,
            rotation=0,
            character_slot_count=len(roster_text),
            lines=_lines(roster_text, {}),
        ),
        PageObservation(
            physical_page=2,
            raw_text=submission_text,
            width_points=612,
            height_points=792,
            rotation=0,
            character_slot_count=len(submission_text),
            lines=_lines(submission_text, {1: {"italic": True, "dotted_rule": True}}),
            closes_open_unit=True,
        ),
    ]

    records = build_source_records(_activity([[1, 2]]), pages)

    commenters = [record for record in records if record["record_type"] == "commenter"]
    assert [record["source_label"] for record in commenters] == [
        "State Transportation Agency",
        "Example Review Coalition",
        "Seventh District",
    ]
    submission = next(record for record in records if record["record_type"] == "submission")
    assert submission["commenter_ids"] == [commenters[0]["commenter_id"]]
    span_ids = {record["span_id"] for record in records if record["record_type"] == "source_span"}
    assert commenters[0]["opener_span_id"] in span_ids


def test_isolated_code_like_prose_and_numeric_page_label_are_not_roster_rows() -> None:
    text = (
        "13-650 Final Environmental Impact Report\nES-6 discusses cumulative effects in detail.\n"
    )
    page = PageObservation(
        physical_page=1,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=_lines(text, {}),
        section_opener=True,
    )

    records = build_source_records(_activity([[1, 1]]), [page])

    assert not [record for record in records if record["record_type"] == "commenter"]


def test_general_response_comment_letter_bullet_emits_each_membership() -> None:
    text = "General Response 2\nComment Letter:\nAA-1, BB-TEAM-2; C3-7\nBody.\n"
    page = PageObservation(
        physical_page=1,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=_lines(text, {0: {"bold": True}}),
        closes_open_unit=True,
    )

    records = build_source_records(_activity([[1, 1]]), [page])

    memberships = [record for record in records if record["record_type"] == "membership_claim"]
    assert [record["target_label"] for record in memberships] == [
        "AA-1",
        "BB-TEAM-2",
        "C3-7",
    ]


def test_labeled_blank_precedes_nonempty_running_header_state() -> None:
    text = "Final Environmental Impact Report\nIntentionally Blank\n"
    page = PageObservation(
        physical_page=1,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=_lines(text, {}),
        labeled_blank=True,
        section_opener=True,
    )

    records = build_source_records(_activity([[1, 1]]), [page])

    page_record = next(record for record in records if record["record_type"] == "page")
    assert page_record["page_state"] == "labeled_blank"


def test_unknown_nonempty_page_requires_explicit_state() -> None:
    text = "Unclassified body text.\n"
    page = PageObservation(
        physical_page=1,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=_lines(text, {}),
    )

    try:
        build_source_records(_activity([[1, 1]]), [page])
    except ValueError as error:
        assert "unclassified nonempty page" in str(error)
    else:  # pragma: no cover - failure branch
        raise AssertionError("unclassified nonempty page should fail")


def test_nonunit_section_content_can_continue_on_an_adjacent_page() -> None:
    opener_text = "12.1 REGIONAL AGENCIES\n"
    body_text = "Association of Bay Area Governments\n"
    pages = [
        PageObservation(
            physical_page=1,
            raw_text=opener_text,
            width_points=612,
            height_points=792,
            rotation=0,
            character_slot_count=len(opener_text),
            lines=_lines(opener_text, {0: {"bold": True}}),
            section_opener=True,
        ),
        PageObservation(
            physical_page=2,
            raw_text=body_text,
            width_points=612,
            height_points=792,
            rotation=0,
            character_slot_count=len(body_text),
            lines=_lines(body_text, {}),
            closes_open_unit=True,
        ),
    ]
    records = build_source_records(_activity([[1, 2]]), pages)
    states = [record["page_state"] for record in records if record["record_type"] == "page"]
    assert states == ["section_opener", "continuation"]


def test_running_header_context_explains_a_range_edge_continuation() -> None:
    text = "13.2 Responses to Organizations | 13.2.8 Letter O-EXAMPLE\nBody text.\n"
    page = PageObservation(
        physical_page=10,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=_lines(text, {}),
        running_header_context=True,
        closes_open_unit=True,
    )
    records = build_source_records(_activity([[10, 10]]), [page])
    state = next(record for record in records if record["record_type"] == "page")
    assert state["page_state"] == "continuation"


@pytest.mark.parametrize(
    ("page_flags", "marker_count", "section_evidence", "open_unit", "open_structure", "expected"),
    [
        ({"labeled_blank": True, "title_page": True}, 2, True, True, True, "labeled_blank"),
        (
            {"title_page": True, "revision_markup": True},
            2,
            True,
            True,
            True,
            "layout_exception",
        ),
        (
            {"revision_markup": True, "figure_or_table": True},
            2,
            True,
            True,
            True,
            "revision_markup",
        ),
        ({"figure_or_table": True}, 2, True, True, True, "figure_or_table"),
        ({"raw_text": ""}, 2, True, True, True, "blank"),
        ({}, 2, True, True, True, "mixed_markers"),
        ({}, 1, True, True, True, "unit_start"),
        ({"zero_comment_section": True}, 0, True, True, True, "zero_comment_section"),
        ({"section_opener": True}, 0, False, True, True, "section_opener"),
        ({}, 0, True, True, True, "section_opener"),
        ({}, 0, False, True, False, "continuation"),
        ({}, 0, False, False, True, "continuation"),
        ({"running_header_context": True}, 0, False, False, False, "continuation"),
    ],
)
def test_page_state_precedence_is_explicit(
    page_flags: dict[str, object],
    marker_count: int,
    section_evidence: bool,
    open_unit: bool,
    open_structure: bool,
    expected: str,
) -> None:
    raw_text = str(page_flags.get("raw_text", "Body text.\n"))
    observation_flags = {key: value for key, value in page_flags.items() if key != "raw_text"}
    page = PageObservation(
        physical_page=1,
        raw_text=raw_text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(raw_text),
        lines=_lines(raw_text, {}),
        **observation_flags,  # type: ignore[arg-type]
    )

    state = _classify_page_state(
        page,
        accepted_marker_count=marker_count,
        section_evidence=section_evidence,
        open_unit=open_unit,
        open_structure=open_structure,
    )

    assert state == expected


def test_rejects_missing_or_duplicate_page_scope() -> None:
    page = PageObservation(
        physical_page=1,
        raw_text="",
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=0,
        lines=(),
    )
    activity = _activity([[1, 2]])

    try:
        build_source_records(activity, [page])
    except ValueError as error:
        assert "do not close" in str(error)
    else:  # pragma: no cover - failure branch
        raise AssertionError("missing activity page should fail")
