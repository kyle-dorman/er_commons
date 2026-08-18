"""Tests for source-agnostic table routing."""

from er_commons.document_parsing.content_parsing.routing import (
    NumericTableThresholds,
    StrictTableThresholds,
    classify_page,
)

STRICT = StrictTableThresholds.model_validate(
    {
        "minimum_text_width_fraction": 0.70,
        "minimum_text_height_fraction": 0.75,
        "minimum_nonempty_line_count": 80,
        "minimum_nonspace_characters_per_square_point": 0.02,
        "minimum_digit_fraction": 0.35,
    }
)
NUMERIC = NumericTableThresholds.model_validate(
    {
        "minimum_text_width_fraction": 0.70,
        "minimum_nonempty_line_count": 20,
        "minimum_nonspace_characters_per_square_point": 0.005,
        "minimum_digit_fraction": 0.50,
    }
)


def _features(**updates: float | int) -> dict[str, float | int]:
    values: dict[str, float | int] = {
        "text_width_fraction": 0.5,
        "text_height_fraction": 0.5,
        "nonempty_line_count": 10,
        "nonspace_characters_per_square_point": 0.001,
        "digit_fraction": 0.1,
    }
    values.update(updates)
    return values


def test_numeric_signal_routes_any_source_to_full_page_stream() -> None:
    result = classify_page(
        _features(
            text_width_fraction=0.8,
            nonempty_line_count=20,
            nonspace_characters_per_square_point=0.006,
            digit_fraction=0.6,
        ),
        [],
        STRICT,
        NUMERIC,
    )
    assert result["route"] == "full_page_numeric"


def test_layout_table_region_is_the_general_fallback() -> None:
    result = classify_page(_features(), [[1.0, 2.0, 3.0, 4.0]], STRICT, NUMERIC)
    assert result["route"] == "layout_regions"


def test_page_without_signal_or_layout_table_skips_table_parser() -> None:
    result = classify_page(_features(), [], STRICT, NUMERIC)
    assert result["route"] == "no_table_route"


def test_dense_partial_page_routes_without_weakening_other_strict_signals() -> None:
    result = classify_page(
        _features(
            page_rotation_degrees=90,
            text_width_fraction=0.8,
            text_height_fraction=0.4,
            nonempty_line_count=90,
            nonspace_characters_per_square_point=0.03,
            digit_fraction=0.4,
        ),
        [],
        STRICT,
        NUMERIC,
    )
    assert result["route"] == "full_page_numeric"
    assert result["dense_partial_table"] is True
    assert result["strict_table_dominant"] is False


def test_rotated_page_without_all_other_strict_signals_does_not_route() -> None:
    result = classify_page(
        _features(
            page_rotation_degrees=90,
            text_width_fraction=0.8,
            text_height_fraction=0.4,
            nonempty_line_count=90,
            nonspace_characters_per_square_point=0.03,
            digit_fraction=0.2,
        ),
        [],
        STRICT,
        NUMERIC,
    )
    assert result["route"] == "no_table_route"
    assert result["dense_partial_table"] is False


def test_unrotated_dense_partial_page_uses_the_same_policy() -> None:
    result = classify_page(
        _features(
            page_rotation_degrees=0,
            text_width_fraction=0.8,
            text_height_fraction=0.4,
            nonempty_line_count=90,
            nonspace_characters_per_square_point=0.03,
            digit_fraction=0.4,
        ),
        [],
        STRICT,
        NUMERIC,
    )
    assert result["route"] == "full_page_numeric"
    assert result["dense_partial_table"] is True


def test_too_short_dense_fragment_does_not_route() -> None:
    result = classify_page(
        _features(
            page_rotation_degrees=90,
            text_width_fraction=0.8,
            text_height_fraction=0.2,
            nonempty_line_count=90,
            nonspace_characters_per_square_point=0.03,
            digit_fraction=0.4,
        ),
        [],
        STRICT,
        NUMERIC,
    )
    assert result["route"] == "no_table_route"
    assert result["dense_partial_table"] is False
