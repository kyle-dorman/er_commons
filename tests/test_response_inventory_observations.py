from __future__ import annotations

import copy

import pytest

from er_commons.response_inventory.observations import (
    LineObservation,
    PageObservation,
    observation_from_dict,
    observation_to_dict,
)


def _valid_observation() -> dict[str, object]:
    observation = PageObservation(
        physical_page=1,
        raw_text="Heading\n",
        width_points=612.0,
        height_points=792.0,
        rotation=0,
        character_slot_count=8,
        lines=(
            LineObservation(
                line_index=0,
                text_start=0,
                text_end=7,
                bbox=(1.0, 2.0, 3.0, 4.0),
                character_slot_start=0,
                character_slot_end=7,
            ),
        ),
    )
    return observation_to_dict(observation)


def test_observation_cache_round_trip_is_exact() -> None:
    payload = _valid_observation()
    assert observation_to_dict(observation_from_dict(payload)) == payload


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (("labeled_blank", "false"), "must be a boolean"),
        (("physical_page", True), "must be an integer"),
        (("width_points", float("nan")), "finite number"),
    ],
)
def test_observation_cache_rejects_coercible_or_nonfinite_scalars(
    mutation: tuple[str, object], message: str
) -> None:
    payload = _valid_observation()
    payload[mutation[0]] = mutation[1]
    with pytest.raises(ValueError, match=message):
        observation_from_dict(payload)


def test_observation_cache_rejects_invalid_bbox_and_text_interval() -> None:
    payload = _valid_observation()
    lines = copy.deepcopy(payload["lines"])
    assert isinstance(lines, list) and isinstance(lines[0], dict)
    lines[0]["bbox"] = [1.0, 2.0, 3.0]
    payload["lines"] = lines
    with pytest.raises(ValueError, match="bbox must contain four"):
        observation_from_dict(payload)

    payload = _valid_observation()
    lines = copy.deepcopy(payload["lines"])
    assert isinstance(lines, list) and isinstance(lines[0], dict)
    lines[0]["text_end"] = 99
    payload["lines"] = lines
    with pytest.raises(ValueError, match="outside raw_text"):
        observation_from_dict(payload)


def test_observation_cache_rejects_partial_character_slot_interval() -> None:
    payload = _valid_observation()
    lines = copy.deepcopy(payload["lines"])
    assert isinstance(lines, list) and isinstance(lines[0], dict)
    lines[0]["character_slot_end"] = None
    payload["lines"] = lines
    with pytest.raises(ValueError, match="both be present or null"):
        observation_from_dict(payload)
