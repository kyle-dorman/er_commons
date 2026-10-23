"""Strict coverage projection and failure contracts, without live inference."""

import json

import pytest

from er_commons import required_support_coverage as core
from er_commons.judge_context import baylands_overview

PACKET = {
    "question": "What is required?",
    "required_reference_point": {"point_id": "R7", "text": "Both A and B."},
    "candidate_supporting_points": [
        {"point_id": "S2", "text": "A."},
        {"point_id": "S8", "text": "B."},
    ],
}


def test_exact_projection_and_context() -> None:
    """Preserve nonsequential canonical IDs and the agreed context envelope."""
    assert core.validate_input(PACKET) == PACKET
    assert core.system_prompt() == (
        core.PROMPT_PATH.read_text().rstrip("\n") + "\n\nPROJECT OVERVIEW\n" + baylands_overview()
    )
    with pytest.raises(ValueError):
        core.validate_input({**PACKET, "candidate_conclusion": "hidden"})
    with pytest.raises(ValueError):
        core.validate_input(
            {
                **PACKET,
                "candidate_supporting_points": [
                    PACKET["candidate_supporting_points"][0],
                    PACKET["candidate_supporting_points"][0],
                ],
            }
        )


@pytest.mark.parametrize("covered,ids", [(True, ["S2", "S8"]), (False, [])])
def test_valid_decision(covered: bool, ids: list[str]) -> None:
    """Accept distributed witnesses and empty negative witnesses."""
    result = {"covered": covered, "supporting_point_ids": ids, "reason": "Brief reason."}
    assert core.parse_output(json.dumps(result), payload=PACKET) == result


@pytest.mark.parametrize(
    "covered,ids",
    [
        (True, []),
        (False, ["S2"]),
        (True, ["S9"]),
        (True, ["S2", "S2"]),
        (1, ["S2"]),
        ("true", ["S2"]),
        (True, [{}]),
    ],
)
def test_invalid_witnesses(covered: object, ids: list[object]) -> None:
    """Reject inconsistent, unknown, repeated or non-string witness IDs."""
    with pytest.raises(ValueError):
        core.parse_output(
            json.dumps({"covered": covered, "supporting_point_ids": ids, "reason": "Reason"}),
            payload=PACKET,
        )


def test_duplicate_json_and_empty_support() -> None:
    """Never repair duplicate keys or fabricate coverage for an empty input."""
    with pytest.raises(ValueError, match="Duplicate"):
        core.parse_output(
            '{"covered":true,"covered":false,"supporting_point_ids":[],"reason":"x"}',
            payload=PACKET,
        )
    empty = {**PACKET, "candidate_supporting_points": []}
    assert core.validate_input(empty) == empty
    with pytest.raises(ValueError):
        core.parse_output(
            '{"covered":true,"supporting_point_ids":["S2"],"reason":"x"}', payload=empty
        )
