"""Check fixed selection, response-only traversal, and cycle-safe closure."""

from typing import Any

import pytest

from er_commons.pilot_context_repair import refresh_cases


def _fixture() -> tuple[
    list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]
]:
    """Build one comment with a cycle and an unrelated general-membership edge."""
    sample = [
        {
            "comment_id": "c",
            "comment_label": "Comment c",
            "number": 7,
            "portion": "coverage",
            "selection_reason": "original reason",
            "sampling_general_response_ids": [],
            "direct_response_ids": ["r1"],
            "context_unit_ids": ["c", "r1"],
            "relationship_ids": ["direct"],
        }
    ]
    sources = []
    for uid, kind in [
        ("c", "comment"),
        ("r1", "response"),
        ("r2", "response"),
        ("g", "general_response"),
        ("other", "comment"),
    ]:
        sources.extend(
            [
                {
                    "record_type": "source_unit",
                    "unit_id": uid,
                    "unit_kind": kind,
                    "official_label": uid,
                    "span_ids": ["s-" + uid],
                },
                {
                    "record_type": "source_span",
                    "span_id": "s-" + uid,
                    "fragments": [{"page_id": "p-" + uid, "text_start": 0, "text_end": len(uid)}],
                },
                {"record_type": "page", "page_id": "p-" + uid, "physical_page": 1, "raw_text": uid},
            ]
        )
    edges = [
        {
            "edge_id": name,
            "source_unit_id": source,
            "target_unit_id": target,
            "relation_type": relation,
        }
        for name, source, target, relation in [
            ("direct", "c", "r1", "comment_response"),
            ("next", "r1", "r2", "response_response"),
            ("cycle", "r2", "r1", "response_response"),
            ("general", "r2", "g", "response_general_response"),
            ("membership", "g", "other", "general_response_comment"),
        ]
    ]
    views = [
        {
            "root_unit_id": "c",
            "view_id": "v-new",
            "ordered_unit_ids": ["c", "r1"],
            "edge_ids": ["direct"],
        }
    ]
    return sample, sources, edges, views


def test_cycle_deduplication_and_fixed_selection() -> None:
    """Only response-directed edges extend context; selection fields stay exact."""
    old, sources, edges, views = _fixture()
    cases, context, changes = refresh_cases(old, sources, edges, [], views)
    for key in (
        "number",
        "comment_id",
        "portion",
        "selection_reason",
        "sampling_general_response_ids",
    ):
        assert cases[0][key] == old[0][key]
    assert cases[0]["context_unit_ids"] == ["c", "r1", "r2", "g"]
    assert len(context) == 4
    assert changes[0]["added_context_unit_ids"] == ["g", "r2"]
    assert "membership" not in cases[0]["relationship_ids"]
    assert old[0]["context_unit_ids"] == ["c", "r1"]


def test_response_edge_to_comment_is_rejected() -> None:
    """An invalid graph cannot introduce another sampled or unsampled comment."""
    old, sources, edges, views = _fixture()
    edges[-1]["relation_type"] = "general_response_response"
    with pytest.raises(ValueError, match="non-response"):
        refresh_cases(old, sources, edges, [], views)


def test_changed_direct_response_stops_refresh() -> None:
    """The bounded linking repair cannot silently replace direct response bindings."""
    old, sources, edges, views = _fixture()
    edges[0]["target_unit_id"] = "r2"
    with pytest.raises(ValueError, match="Direct response changed"):
        refresh_cases(old, sources, edges, [], views)
