"""Tests for rotation-aware PDF routing geometry."""

from __future__ import annotations

import pytest

from er_commons.document_parsing.content_parsing.routing_geometry import (
    DisplayedPageTransform,
    measure_routing_geometry,
)


@pytest.mark.parametrize(
    ("rotation", "displayed_size"),
    [(0, (100.0, 200.0)), (90, (200.0, 100.0)), (180, (100.0, 200.0)), (270, (200.0, 100.0))],
)
def test_equivalent_canvas_coverage_is_rotation_invariant(
    rotation: int, displayed_size: tuple[float, float]
) -> None:
    """Displayed rotation cannot change coverage measured in PDF canvas axes."""
    result = measure_routing_geometry(
        displayed_size,
        (10.0, 20.0, 110.0, 220.0),
        rotation,
        [(20.0, 40.0, 100.0, 200.0)],
    )

    assert result["text_width_fraction"] == pytest.approx(0.8)
    assert result["text_height_fraction"] == pytest.approx(0.8)
    assert result["routing_coordinate_system"] == "displayed_pdf_points_bottom_left"


def test_quarter_turn_swaps_asymmetric_canvas_spans() -> None:
    result = measure_routing_geometry(
        (200.0, 100.0),
        (0.0, 0.0, 100.0, 200.0),
        90,
        [(10.0, 50.0, 90.0, 150.0)],
    )

    assert result["text_width_fraction"] == pytest.approx(0.5)
    assert result["text_height_fraction"] == pytest.approx(0.8)


@pytest.mark.parametrize(
    ("rotation", "displayed_size", "expected"),
    [
        (0, (100.0, 200.0), (10.0, 20.0, 30.0, 40.0)),
        (90, (200.0, 100.0), (20.0, 70.0, 40.0, 90.0)),
        (180, (100.0, 200.0), (70.0, 160.0, 90.0, 180.0)),
        (270, (200.0, 100.0), (160.0, 10.0, 180.0, 30.0)),
    ],
)
def test_unclipped_display_transform_has_exact_inverse(
    rotation: int,
    displayed_size: tuple[float, float],
    expected: tuple[float, float, float, float],
) -> None:
    transform = DisplayedPageTransform.create(
        displayed_size,
        (10.0, 20.0, 110.0, 220.0),
        rotation,
    )
    source = (20.0, 40.0, 40.0, 60.0)

    displayed = transform.to_displayed_rectangle_unclipped(source)

    assert displayed == expected
    assert transform.to_source_rectangle_unclipped(displayed) == source


def test_empty_text_has_zero_coverage() -> None:
    result = measure_routing_geometry((100.0, 200.0), (0.0, 0.0, 100.0, 200.0), 0, [])

    assert result["text_width_fraction"] == 0.0
    assert result["text_height_fraction"] == 0.0


def test_off_canvas_text_is_clipped_to_visible_page_geometry() -> None:
    result = measure_routing_geometry(
        (100.0, 200.0),
        (0.0, 0.0, 100.0, 200.0),
        0,
        [(-25.0, 50.0, 25.0, 100.0), (120.0, 250.0, 140.0, 280.0)],
    )

    assert result["text_width_fraction"] == pytest.approx(0.25)
    assert result["text_height_fraction"] == pytest.approx(0.25)


@pytest.mark.parametrize(
    ("displayed_size", "bbox", "rotation", "rectangles", "message"),
    [
        ((100.0, 200.0), (0.0, 0.0, 100.0, 200.0), 45, [], "unsupported"),
        ((200.0, 100.0), (0.0, 0.0, 100.0, 200.0), 0, [], "disagrees"),
        ((100.0, 200.0), (0.0, 0.0, 100.0, 200.0), 0, [(1.0, 1.0, 1.0, 2.0)], "non-positive"),
    ],
)
def test_invalid_geometry_fails_closed(
    displayed_size: tuple[float, float],
    bbox: tuple[float, float, float, float],
    rotation: int,
    rectangles: list[tuple[float, float, float, float]],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        measure_routing_geometry(displayed_size, bbox, rotation, rectangles)
