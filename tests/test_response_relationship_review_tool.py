"""Tests for the read-only, lazy Task 05E review page."""

from __future__ import annotations

from importlib.resources import files
from typing import Any

from er_commons.response_inventory.review_tool import _select_review_items


class _LabelStore:
    """Minimal exact-label lookup used to test bounded case selection."""

    def __init__(self, labels: dict[str, list[str]]) -> None:
        self.labels = labels

    def exact_label_units(self, label: str) -> list[str]:
        return self.labels.get(label, [])


def test_review_selection_contains_only_unresolved_bounded_populations() -> None:
    census: dict[str, Any] = {
        "mention_outcomes": [
            _mention("m1", "general_response", "case_variant"),
            _mention("m2", "general_response", "unsupported_endpoint_kinds"),
            _mention("m3", "response", "other_nonexact"),
            _mention("m4", "general_response", "other_nonexact"),
            _mention("m5", "response", "prose_like"),
            _mention("m6", "response", "whitespace_variant"),
        ],
        "membership_outcomes": [
            _membership("member-resolved", "KNOWN-1"),
            _membership("member-miss", "MISSING-1"),
        ],
    }
    store = _LabelStore({"Comment KNOWN-1": ["unit-known"]})

    items = _select_review_items(census, store)  # type: ignore[arg-type]

    categories = [item["category"] for item in items]
    assert categories == [
        "parent_subanswer",
        "membership_miss",
        "general_response_origin",
        "general_response_origin",
        "other_nonexact",
        "other_nonexact",
    ]
    selected_ids = {
        item["outcome"]["input_id"] for item in items if isinstance(item.get("outcome"), dict)
    }
    assert selected_ids == {"m1", "m2", "m3", "m4", "member-miss"}


def test_static_shell_loads_no_page_images_or_feedback_controls() -> None:
    package = files("er_commons.response_inventory.review_tool_static")
    html = package.joinpath("index.html").read_text(encoding="utf-8")
    script = package.joinpath("app.js").read_text(encoding="utf-8")

    assert "<img" not in html
    assert "<form" not in html
    assert "textarea" not in html
    assert "localStorage" not in script
    assert 'loadJson("data/index.json")' in script
    assert "image.src = button.dataset.url" in script
    assert "data-load-unit" in script
    assert "Gate 1 outcome" not in script
    assert "state.selectedId !== id" in script


def test_reviewed_terminal_exceptions_are_not_reselected() -> None:
    census: dict[str, Any] = {
        "mention_outcomes": [_mention("m1", "response", "reviewed_source_label_typo_unresolved")],
        "membership_outcomes": [],
        "policy": {
            "typed_membership_suffix": True,
            "terminal_unpaired_source_labels": [
                "Comment SA-Caltrans-48",
                "Response SA-Caltrans-48a",
            ],
        },
    }

    assert _select_review_items(census, _LabelStore({})) == []  # type: ignore[arg-type]


def _mention(input_id: str, source_kind: str, reason: str) -> dict[str, str]:
    return {
        "input_id": input_id,
        "source_kind": source_kind,
        "reason": reason,
        "target_label": f"target-{input_id}",
    }


def _membership(input_id: str, target_label: str) -> dict[str, str]:
    return {"input_id": input_id, "target_label": target_label}
