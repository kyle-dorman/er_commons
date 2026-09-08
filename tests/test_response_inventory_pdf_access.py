"""Source-free unit tests for bounded PDF observation helpers."""

from er_commons.response_inventory import pdf_access
from er_commons.response_inventory.observations import LineObservation
from er_commons.response_inventory.pdf_access import (
    _has_bold_section_heading,
    _has_large_image,
    _has_styled_figure_table_heading,
    _line_intervals,
    _line_observations,
    _revision_marks,
    _rule_flags,
    _union_boxes,
)


def _line(*, end: int, bold: bool = False) -> LineObservation:
    return LineObservation(
        line_index=0,
        text_start=0,
        text_end=end,
        bbox=(72.0, 500.0, 180.0, 514.0),
        character_slot_start=0,
        character_slot_end=end,
        bold=bold,
        italic=False,
        solid_rule=False,
        dotted_rule=False,
        revision_marks=(),
    )


class _FakeImage:
    def __init__(self, bounds: tuple[float, float, float, float]) -> None:
        self._bounds = bounds

    def get_bounds(self) -> tuple[float, float, float, float]:
        return self._bounds


class _FakePage:
    def __init__(self, image_bounds: tuple[tuple[float, float, float, float], ...]) -> None:
        self._images = tuple(_FakeImage(bounds) for bounds in image_bounds)

    def get_objects(self, *, filter: list[int]) -> tuple[_FakeImage, ...]:
        del filter
        return self._images


class _FakeSearch:
    def __init__(self, count: int) -> None:
        self._count = count

    def get_next(self) -> tuple[int, int]:
        return 0, self._count

    def close(self) -> None:
        pass


class _FakeTextPageWithoutBoxes:
    def search(self, query: str, **_: object) -> _FakeSearch:
        return _FakeSearch(len(query))

    def get_charbox(self, index: int) -> tuple[float, float, float, float]:
        raise RuntimeError(f"no box for character {index}")

    def get_textobj(self, index: int) -> None:
        del index
        return None


def test_line_intervals_preserve_raw_unicode_offsets() -> None:
    text = "Comment A-1\r\nβ response\nlast"
    intervals = list(_line_intervals(text))
    assert [text[start:end] for start, end in intervals] == ["Comment A-1", "β response", "last"]


def test_rule_evidence_distinguishes_solid_and_dashed_paths() -> None:
    text_box = (72.0, 500.0, 180.0, 514.0)
    assert _rule_flags(text_box, (((72.0, 498.0, 180.0, 499.0), False),)) == (True, False)
    assert _rule_flags(text_box, (((72.0, 498.0, 180.0, 499.0), True),)) == (False, True)
    assert _rule_flags(text_box, (((300.0, 498.0, 400.0, 499.0), False),)) == (
        False,
        False,
    )


def test_revision_marks_remain_separate_from_marker_rules() -> None:
    text_box = (72.0, 500.0, 180.0, 514.0)
    crossing = (((72.0, 507.0, 180.0, 507.5), False),)
    assert _revision_marks(text_box, crossing, False, False) == ("strikethrough",)
    assert _revision_marks(text_box, crossing, True, False) == ()


def test_revision_marks_require_located_character_geometry() -> None:
    page_fallback_box = (0.0, 0.0, 612.0, 792.0)
    crossing = (((72.0, 400.0, 180.0, 400.5), False),)
    assert (
        _revision_marks(
            page_fallback_box,
            crossing,
            False,
            False,
            has_character_geometry=False,
        )
        == ()
    )


def test_missing_charboxes_do_not_turn_page_bounds_into_rule_evidence() -> None:
    page_box = (0.0, 0.0, 612.0, 792.0)
    rules = (((72.0, 400.0, 180.0, 400.5), False),)
    line = next(_line_observations("Heading", _FakeTextPageWithoutBoxes(), rules, page_box))

    assert line.bbox == page_box
    assert not line.solid_rule
    assert not line.dotted_rule
    assert line.revision_marks == ()


def test_union_boxes_uses_pdf_point_extents() -> None:
    assert _union_boxes(((2.0, 3.0, 4.0, 5.0), (1.0, 4.0, 8.0, 9.0))) == (
        1.0,
        3.0,
        8.0,
        9.0,
    )


def test_front_matter_title_and_contents_rules_are_explicit() -> None:
    title = "Final Environmental Impact Report Prepared for Lead Agency Prepared by Consultant"
    assert all(pattern.search(title) for pattern in pdf_access._TITLE_PAGE_REQUIRED_RE)
    assert pdf_access._SECTION_RE.match("CONTENTS (APPENDIX B)")
    assert not all(
        pattern.search("Project contents") for pattern in pdf_access._TITLE_PAGE_REQUIRED_RE
    )


def test_section_openers_require_structural_text_and_bold_evidence() -> None:
    contents = "CONTENTS (VOLUME 4 OF 5)"
    running_header = "RESPONSES TO COMMENTS"
    ordinary_bold_text = "Some unrelated bold sentence"

    assert _has_bold_section_heading(contents, (_line(end=len(contents), bold=True),))
    assert not _has_bold_section_heading(running_header, (_line(end=len(running_header)),))
    assert not _has_bold_section_heading(
        ordinary_bold_text, (_line(end=len(ordinary_bold_text), bold=True),)
    )
    numbered = "12.1.3 REGIONAL AGENCIES"
    assert _has_bold_section_heading(numbered, (_line(end=len(numbered), bold=True),))


def test_running_context_requires_response_vocabulary() -> None:
    assert pdf_access._RUNNING_CONTEXT_RE.search(
        "13.2 Responses to Organizations | 13.2.8 Letter O-EXAMPLE"
    )
    assert not pdf_access._RUNNING_CONTEXT_RE.search("13.2 Ordinary narrative")


def test_figure_table_heading_requires_style_not_prose_prefix() -> None:
    heading = "Figure 4-2 PROJECT OVERVIEW"
    prose = "Figure 4-2 shows the project overview in context."

    assert _has_styled_figure_table_heading(heading, (_line(end=len(heading), bold=True),))
    assert not _has_styled_figure_table_heading(prose, (_line(end=len(prose)),))


def test_dense_table_listing_is_recognized_without_heading_style() -> None:
    first = "Table 8-1: First entry"
    second = "Table 8-2: Second entry"
    text = f"{first}\n{second}"
    lines = (
        _line(end=len(first)),
        LineObservation(
            line_index=1,
            text_start=len(first) + 1,
            text_end=len(text),
            bbox=(72.0, 480.0, 180.0, 494.0),
        ),
    )
    assert _has_styled_figure_table_heading(text, lines)


def test_large_embedded_image_uses_clipped_page_area_ratio() -> None:
    page_box = (0.0, 0.0, 100.0, 100.0)
    assert _has_large_image(_FakePage(((10.0, 10.0, 60.0, 60.0),)), page_box)
    assert not _has_large_image(_FakePage(((10.0, 10.0, 20.0, 20.0),)), page_box)
    assert not _has_large_image(_FakePage(((95.0, 95.0, 200.0, 200.0),)), page_box)
