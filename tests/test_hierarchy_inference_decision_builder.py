"""Synthetic policy tests for pure hierarchy-inference builders."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

from er_commons.hierarchy_inference.correction_policy import build_rule_decisions
from er_commons.hierarchy_inference.hierarchy import derive_expected_hierarchy
from er_commons.hierarchy_inference.hierarchy_projection import build_corrected_hierarchy
from er_commons.hierarchy_inference.rules import _calibrated_numbering_levels


def _feature(index: int, **updates: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "stable_item_key": f"{index + 1:064x}",
        "raw_self_ref": f"#/texts/{index}",
        "raw_parent_ref": "#/body",
        "text": f"text {index}",
        "orig": f"text {index}",
        "normalized_text": f"text {index}",
        "reading_order_index": index,
        "content_layer": "body",
        "raw_role": "text",
        "raw_level": None,
        "physical_page": 1,
        "page_width": 612.0,
        "page_height": 792.0,
        "bbox": {"l": 72.0, "t": 720.0, "r": 300.0, "b": 700.0, "coord_origin": "BOTTOMLEFT"},
        "charspan": [0, 6],
        "line_count": 1,
        "left_pt": 72.0,
        "height_pt": 20.0,
        "regime_id": "reg-0123456789abcdef",
        "toc_region": False,
        "numbering_kind": "none",
        "numbering_token": None,
        "numbering_depth": None,
        "outline_state": "absent",
        "outline_level": None,
        "layout_state": "unique_aligned",
        "printed_page_label": "1",
    }
    record.update(updates)
    return record


def _regime() -> tuple[dict[str, Any], ...]:
    return (
        {
            "regime_id": "reg-0123456789abcdef",
            "parent_regime_id": None,
            "root_level": 1,
            "start_item_key": f"{1:064x}",
            "end_item_key": None,
            "outline_anchor_key": None,
            "page_label_reset": False,
        },
    )


def _build(features: tuple[dict[str, Any], ...]):
    return build_rule_decisions(
        features=features,
        toc_entries=(),
        reconciliations=(),
        regimes=_regime(),
    )


def test_picture_owned_policy_excludes_non_caption_but_preserves_caption_content() -> None:
    non_caption = _feature(0, raw_parent_ref="#/pictures/0")
    caption = _feature(
        1,
        raw_parent_ref="#/pictures/0",
        raw_role="caption",
        toc_region=True,
    )

    result = _build((non_caption, caption))

    assert result.decisions[0]["selected_rule_id"] == "R01_EXCLUDE_NON_BODY_OR_TOC"
    assert result.decisions[0]["corrected_role"] == "excluded"
    assert result.decisions[0]["eligible_rule_ids"] == [
        "R01_EXCLUDE_NON_BODY_OR_TOC",
        "R08_DEFAULT_PRESERVE",
    ]
    assert result.decisions[1]["selected_rule_id"] == "R08_DEFAULT_PRESERVE"
    assert result.decisions[1]["corrected_role"] == "content"
    assert result.decisions[1]["eligible_rule_ids"] == ["R08_DEFAULT_PRESERVE"]


def test_outline_precedence_keeps_complete_eligible_list_and_bullet_demotes() -> None:
    anchored = _feature(
        0,
        raw_role="section_header",
        raw_level=4,
        numbering_kind="decimal",
        numbering_token="1",
        numbering_depth=1,
        outline_state="unique_exact",
        outline_level=1,
    )
    bullet = _feature(
        1,
        raw_role="section_header",
        raw_level=2,
        numbering_kind="bullet",
        numbering_token="•",
        left_pt=72.0,
    )
    list_item = _feature(2, raw_role="list_item", left_pt=90.0)

    result = _build((anchored, bullet, list_item))

    assert result.decisions[0]["selected_rule_id"] == "R03_APPLY_EXACT_OUTLINE_ANCHOR"
    assert result.decisions[0]["corrected_level"] == 1
    assert result.decisions[0]["eligible_rule_ids"] == [
        "R03_APPLY_EXACT_OUTLINE_ANCHOR",
        "R05_APPLY_NUMBERING_REGIME",
        "R08_DEFAULT_PRESERVE",
    ]
    assert result.decisions[1]["selected_rule_id"] == "R02_DEMOTE_BULLET_HEADING"
    assert result.decisions[1]["outcome"] == "applied"
    assert result.decisions[1]["evidence"]["next_list_indent_delta_pt"] == 18.0
    assert all(item["eligible_rule_ids"][-1] == "R08_DEFAULT_PRESERVE" for item in result.decisions)


def test_structural_sibling_and_numbering_jump_are_fail_closed_ambiguities() -> None:
    features = (
        _feature(0, raw_role="section_header", raw_level=1),
        _feature(1, raw_role="text", normalized_text="before"),
        _feature(2, raw_role="text", normalized_text="candidate"),
        _feature(3, raw_role="text", normalized_text="after"),
        _feature(4, raw_role="section_header", raw_level=1),
        _feature(
            5,
            raw_role="section_header",
            raw_level=3,
            numbering_kind="decimal",
            numbering_token="1.1.1",
            numbering_depth=3,
        ),
    )

    result = _build(features)
    sibling = result.decisions[2]
    jump = result.decisions[5]

    assert sibling["selected_rule_id"] == "R06_FLAG_STRUCTURAL_AMBIGUITY"
    assert sibling["outcome"] == "ambiguous"
    assert sibling["corrected_role"] == "content"
    assert jump["selected_rule_id"] == "R05_APPLY_NUMBERING_REGIME"
    assert jump["outcome"] == "ambiguous"
    assert jump["corrected_role"] == "content"
    assert [item["code"] for item in result.ambiguities] == [
        "SIBLING_EVIDENCE_CONFLICT",
        "NUMBERING_JUMP_UNSUPPORTED",
    ]


def test_indexed_heading_neighbors_preserve_exact_decision_evidence() -> None:
    features = (
        _feature(0),
        _feature(1, raw_role="section_header", raw_level=1),
        _feature(2),
        _feature(3),
        _feature(4, raw_role="section_header", raw_level=2),
        _feature(5),
    )

    result = _build(features)

    for index, decision in enumerate(result.decisions):
        previous = next(
            (
                item["stable_item_key"]
                for item in reversed(features[:index])
                if item["raw_role"] == "section_header"
            ),
            None,
        )
        following = next(
            (
                item["stable_item_key"]
                for item in features[index + 1 :]
                if item["raw_role"] == "section_header"
            ),
            None,
        )
        assert decision["evidence"]["previous_heading_key"] == previous
        assert decision["evidence"]["next_heading_key"] == following


def test_previous_numbered_level_index_never_crosses_regimes() -> None:
    second_regime = "reg-fedcba9876543210"
    regimes = (
        _regime()[0],
        {
            **_regime()[0],
            "regime_id": second_regime,
            "start_item_key": f"{3:064x}",
        },
    )
    features = (
        _feature(
            0,
            raw_role="section_header",
            raw_level=2,
            numbering_kind="decimal",
            numbering_token="1.1",
            numbering_depth=2,
        ),
        _feature(1),
        _feature(
            2,
            regime_id=second_regime,
            raw_role="section_header",
            raw_level=1,
            numbering_kind="decimal",
            numbering_token="1",
            numbering_depth=1,
        ),
    )

    result = build_rule_decisions(
        features=features,
        toc_entries=(),
        reconciliations=(),
        regimes=regimes,
    )

    assert result.decisions[2]["outcome"] == "applied"
    assert result.decisions[2]["corrected_level"] == 1


def test_indexed_local_transfer_preserves_cluster_semantics() -> None:
    features = (
        _feature(
            0,
            raw_role="section_header",
            raw_level=1,
            outline_state="unique_exact",
            outline_level=1,
        ),
        _feature(1, raw_role="section_header", raw_level=5, left_pt=90.0),
        _feature(2, raw_role="section_header", raw_level=5, left_pt=90.5),
        _feature(
            3,
            raw_role="section_header",
            raw_level=2,
            numbering_kind="decimal",
            numbering_token="2",
            numbering_depth=1,
            outline_state="unique_exact",
            outline_level=2,
            left_pt=90.0,
        ),
    )

    result = _build(features)

    assert [item["selected_rule_id"] for item in result.decisions[1:3]] == [
        "R07_TRANSFER_LOCAL_HEADING_LEVEL",
        "R07_TRANSFER_LOCAL_HEADING_LEVEL",
    ]
    assert [item["corrected_level"] for item in result.decisions[1:3]] == [2, 2]
    assert [item["evidence"]["transferred_level"] for item in result.decisions[1:3]] == [2, 2]


def test_supported_unnumbered_heading_does_not_bridge_transfer_intervals() -> None:
    features = (
        _feature(
            0,
            raw_role="section_header",
            raw_level=1,
            outline_state="unique_exact",
            outline_level=1,
        ),
        _feature(1, raw_role="section_header", raw_level=5, left_pt=90.0),
        _feature(
            2,
            raw_role="section_header",
            raw_level=2,
            outline_state="unique_exact",
            outline_level=2,
            left_pt=90.0,
        ),
        _feature(3, raw_role="section_header", raw_level=3, left_pt=90.0),
        _feature(
            4,
            raw_role="section_header",
            raw_level=3,
            outline_state="unique_exact",
            outline_level=3,
            left_pt=90.0,
        ),
    )

    result = _build(features)

    assert result.decisions[1]["selected_rule_id"] == "R08_DEFAULT_PRESERVE"
    assert result.decisions[2]["eligible_rule_ids"] == [
        "R03_APPLY_EXACT_OUTLINE_ANCHOR",
        "R08_DEFAULT_PRESERVE",
    ]


def test_r05_calibrates_from_nearest_immutable_outline_anchor() -> None:
    features = (
        _feature(
            0,
            raw_role="section_header",
            raw_level=3,
            text="6 Introduction",
            numbering_kind="decimal",
            numbering_token="6",
            numbering_depth=1,
            outline_state="unique_exact",
            outline_level=3,
        ),
        _feature(
            1,
            raw_role="section_header",
            raw_level=4,
            text="6.2 Supply",
            numbering_kind="decimal",
            numbering_token="6.2",
            numbering_depth=2,
        ),
        _feature(
            2,
            raw_role="section_header",
            raw_level=4,
            text="6.2.3 Scenario",
            numbering_kind="decimal",
            numbering_token="6.2.3",
            numbering_depth=3,
        ),
    )

    result = _build(features)

    assert [item["corrected_level"] for item in result.decisions] == [3, 4, 5]
    assert [item["selected_rule_id"] for item in result.decisions] == [
        "R03_APPLY_EXACT_OUTLINE_ANCHOR",
        "R05_APPLY_NUMBERING_REGIME",
        "R05_APPLY_NUMBERING_REGIME",
    ]
    assert all(item["outcome"] == "applied" for item in result.decisions)

    validator_levels = _calibrated_numbering_levels(
        cast(
            Any,
            SimpleNamespace(
                features=features,
                regimes_by_id={_regime()[0]["regime_id"]: _regime()[0]},
                exact_reconciliations_by_toc={},
                toc_entries_by_id={},
            ),
        )
    )
    assert [validator_levels[item["stable_item_key"]] for item in features] == [3, 4, 5]


def test_hierarchy_uses_per_regime_stack_and_exact_content_membership() -> None:
    features = (
        _feature(0),
        _feature(1, raw_role="section_header", raw_level=1),
        _feature(2),
        _feature(3, raw_role="section_header", raw_level=2),
        _feature(4),
        _feature(5, raw_role="section_header", raw_level=1),
    )
    decisions = _build(features).decisions

    result = build_corrected_hierarchy(
        features=features,
        decisions=decisions,
        regimes=_regime(),
    )
    hierarchy = result.hierarchy

    assert hierarchy["roots"] == [features[1]["stable_item_key"], features[5]["stable_item_key"]]
    assert hierarchy["edges"] == [
        {
            "parent_key": features[1]["stable_item_key"],
            "child_key": features[3]["stable_item_key"],
        }
    ]
    assert hierarchy["direct_membership"] == [
        {
            "item_key": features[2]["stable_item_key"],
            "heading_key": features[1]["stable_item_key"],
        },
        {
            "item_key": features[4]["stable_item_key"],
            "heading_key": features[3]["stable_item_key"],
        },
    ]
    assert hierarchy["unassigned_content"] == [features[0]["stable_item_key"]]
    assert result.warnings == ()


def test_hierarchy_preserves_sparse_levels_and_emits_review_warnings() -> None:
    features = (
        _feature(0, raw_role="section_header", raw_level=2),
        _feature(1, raw_role="section_header", raw_level=5),
    )
    decisions = _build(features).decisions

    result = build_corrected_hierarchy(
        features=features,
        decisions=decisions,
        regimes=_regime(),
    )

    assert result.hierarchy["roots"] == [features[0]["stable_item_key"]]
    assert result.hierarchy["edges"] == [
        {
            "parent_key": features[0]["stable_item_key"],
            "child_key": features[1]["stable_item_key"],
        }
    ]
    assert [item["detail"] for item in result.warnings] == [
        "sparse hierarchy root: regime_root_level=1, child_level=2, "
        "missing_intermediate_level_count = 1",
        "sparse hierarchy edge: parent_level=2, child_level=5, "
        "missing_intermediate_level_count = 2",
    ]
    assert all(item["code"] == "RAW_HEADING_DEPTH_UNSUPPORTED" for item in result.warnings)


def test_nested_regime_exit_clears_stale_parent_stack() -> None:
    """A peer end boundary must not resume an enclosing pre-regime heading."""
    outer_id = "reg-outer"
    nested_id = "reg-nested"
    features = (
        _feature(0, regime_id=outer_id, raw_role="section_header", raw_level=2),
        _feature(1, regime_id=nested_id, raw_role="section_header", raw_level=1),
        _feature(2, regime_id=outer_id, raw_role="section_header", raw_level=3),
    )
    decisions = tuple(
        {
            "stable_item_key": feature["stable_item_key"],
            "corrected_role": "heading",
            "corrected_level": feature["raw_level"],
        }
        for feature in features
    )
    regimes = (
        {
            "regime_id": outer_id,
            "parent_regime_id": None,
            "root_level": 1,
            "start_item_key": features[0]["stable_item_key"],
            "end_item_key": None,
            "outline_anchor_key": None,
            "page_label_reset": False,
        },
        {
            "regime_id": nested_id,
            "parent_regime_id": outer_id,
            "root_level": 1,
            "start_item_key": features[1]["stable_item_key"],
            "end_item_key": features[2]["stable_item_key"],
            "outline_anchor_key": features[0]["stable_item_key"],
            "page_label_reset": True,
        },
    )

    result = build_corrected_hierarchy(
        features=features,
        decisions=decisions,
        regimes=regimes,
    )
    expected = derive_expected_hierarchy(
        cast(
            Any,
            SimpleNamespace(
                features=features,
                decisions_by_key={item["stable_item_key"]: item for item in decisions},
                regimes=regimes,
                regimes_by_id={item["regime_id"]: item for item in regimes},
            ),
        )
    )

    assert result.hierarchy["roots"] == [
        features[0]["stable_item_key"],
        features[1]["stable_item_key"],
        features[2]["stable_item_key"],
    ]
    assert result.hierarchy["edges"] == []
    assert expected.roots == tuple(result.hierarchy["roots"])
    assert expected.edges == ()
