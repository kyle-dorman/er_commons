"""Independent semantic-edge evidence checks for Task 05E rules."""

from __future__ import annotations

from typing import Any

from er_commons.response_inventory.contract import (
    _membership_evidence_names_target,
    _mention_evidence_names_target,
)

type JsonObject = dict[str, Any]


def _mention(raw: str) -> tuple[JsonObject, dict[str, JsonObject], dict[str, JsonObject]]:
    mention: JsonObject = {
        "mention_span_id": "span",
        "target_labels": [raw],
    }
    spans = {
        "span": {
            "fragments": [
                {"page_id": "page", "text_end": len(raw)},
            ]
        }
    }
    pages = {"page": {"raw_text": raw + "\x02OSEC-173"}}
    return mention, spans, pages


def test_mention_evidence_rules_reproduce_only_their_bounded_transform() -> None:
    target = {"official_label": "Response M-OSEC-173"}
    mention, spans, pages = _mention("Response M")
    assert _mention_evidence_names_target(
        mention,
        target,
        "u0002_separator_to_hyphen_reference_mention_v1",
        spans,
        pages,
    )
    assert not _mention_evidence_names_target(
        mention,
        {"official_label": "Response M-OSEC-174"},
        "u0002_separator_to_hyphen_reference_mention_v1",
        spans,
        pages,
    )

    combined, spans, pages = _mention("response \r\nX-3.")
    assert _mention_evidence_names_target(
        combined,
        {"official_label": "Response X-3"},
        "collapsed_whitespace_one_terminal_period_casefold_v1",
        spans,
        pages,
    )
    assert not _mention_evidence_names_target(
        combined,
        {"official_label": "Response X-4"},
        "collapsed_whitespace_one_terminal_period_casefold_v1",
        spans,
        pages,
    )


def test_membership_evidence_rules_reject_unreviewed_aliases() -> None:
    assert _membership_evidence_names_target(
        {"target_label": "X-1"},
        {"official_label": "Comment X-1"},
        "typed_comment_suffix_v1",
    )
    assert _membership_evidence_names_target(
        {"target_label": "O-OSEC-106"},
        {"official_label": "Comment M-OSEC-106"},
        "reviewed_o_osec_to_m_osec_membership_alias_v1",
    )
    assert not _membership_evidence_names_target(
        {"target_label": "O-OSEC-107"},
        {"official_label": "Comment M-OSEC-107"},
        "reviewed_o_osec_to_m_osec_membership_alias_v1",
    )
