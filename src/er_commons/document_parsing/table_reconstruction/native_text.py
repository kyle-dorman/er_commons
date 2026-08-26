"""Extract native PDF text tokens in displayed page coordinates."""

from __future__ import annotations

from typing import Any

from er_commons.document_parsing.content_parsing.routing_geometry import (
    DisplayedPageTransform,
)
from er_commons.document_parsing.table_reconstruction.learned_table_types import (
    BoundingBox,
    JsonObject,
)


def native_word_tokens(
    text_page: Any,
    region_bbox: list[float],
    *,
    scale: float,
    transform: DisplayedPageTransform,
) -> list[JsonObject]:
    """Build word-like tokens after rotating native boxes into display space."""
    region_left, region_bottom, region_right, region_top = region_bbox
    tokens: list[JsonObject] = []
    characters: list[tuple[str, BoundingBox]] = []

    def flush_word() -> None:
        if not characters:
            return
        text = "".join(character for character, _box in characters)
        left = min(box[0] for _character, box in characters)
        bottom = min(box[1] for _character, box in characters)
        right = max(box[2] for _character, box in characters)
        top = max(box[3] for _character, box in characters)
        tokens.append(
            {
                "id": len(tokens),
                "text": text,
                "bbox_pdf_points_bottom_left": [left, bottom, right, top],
                "bbox_crop_pixels_top_left": {
                    "l": (left - region_left) * scale,
                    "t": (region_top - top) * scale,
                    "r": (right - region_left) * scale,
                    "b": (region_top - bottom) * scale,
                },
            }
        )
        characters.clear()

    for index in range(text_page.count_chars()):
        character = text_page.get_text_range(index, 1)
        try:
            source_values = [float(value) for value in text_page.get_charbox(index)]
            source_box = (
                source_values[0],
                source_values[1],
                source_values[2],
                source_values[3],
            )
            box = transform.to_displayed_rectangle_unclipped(source_box)
        except Exception:  # PDFium can expose passive characters without geometry.
            flush_word()
            continue
        left, bottom, right, top = box
        center_x = (left + right) / 2
        center_y = (bottom + top) / 2
        inside = region_left <= center_x <= region_right and region_bottom <= center_y <= region_top
        if not inside or not character or character.isspace():
            flush_word()
            continue
        if characters:
            previous_box = characters[-1][1]
            previous_center_y = (previous_box[1] + previous_box[3]) / 2
            starts_new_word = (
                abs(center_y - previous_center_y) > 2.0 or left + 0.5 < previous_box[2]
            )
            if starts_new_word:
                flush_word()
        characters.append((character, box))
    flush_word()
    return tokens


__all__ = ["native_word_tokens"]
