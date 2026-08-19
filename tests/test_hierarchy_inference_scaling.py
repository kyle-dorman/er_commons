"""Deterministic scaling guards for hierarchy-inference feature traversals."""

from __future__ import annotations

import gc
import time
from typing import Any

import er_commons.hierarchy_inference.numbering_scopes as numbering_scopes
from er_commons.hierarchy_inference.correction_policy import build_rule_decisions


def _feature(
    order: int,
    text: str,
    *,
    role: str = "text",
    page: int = 1,
    outline_state: str = "absent",
) -> dict[str, Any]:
    return {
        "stable_item_key": f"{order + 1:064x}",
        "raw_self_ref": f"#/texts/{order}",
        "raw_parent_ref": "#/body",
        "text": text,
        "orig": text,
        "normalized_text": text.casefold(),
        "reading_order_index": order,
        "content_layer": "body",
        "raw_role": role,
        "raw_level": 1 if role == "section_header" else None,
        "physical_page": page,
        "page_width": 612.0,
        "page_height": 792.0,
        "bbox": {
            "l": 72.0,
            "t": 720.0,
            "r": 300.0,
            "b": 700.0,
            "coord_origin": "BOTTOMLEFT",
        },
        "charspan": [0, len(text)],
        "line_count": 1,
        "left_pt": 72.0,
        "height_pt": 20.0,
        "toc_region": False,
        "numbering_kind": "none",
        "numbering_token": None,
        "numbering_depth": None,
        "outline_state": outline_state,
        "outline_level": 2 if outline_state == "unique_exact" else None,
        "layout_state": "unique_aligned",
        "printed_page_label": None,
    }


def _numbering_fixture(blocks: int) -> tuple[list[dict[str, Any]], tuple[dict[str, Any], ...]]:
    features: list[dict[str, Any]] = []
    outlines: list[dict[str, Any]] = []
    for block in range(blocks):
        order = block * 4
        page = block + 1
        title = f"Appendix {block}"
        features.extend(
            [
                _feature(order, "2 Previous", role="section_header", page=page),
                _feature(
                    order + 1,
                    title,
                    role="section_header",
                    page=page,
                    outline_state="unique_exact",
                ),
                _feature(order + 2, "Article 1. Parties", role="section_header", page=page),
                _feature(order + 3, "Body", page=page),
            ]
        )
        outlines.append(
            {
                "outline_id": f"outline-{block:08d}",
                "parent_outline_id": "root",
                "title": title,
                "normalized_title": title.casefold(),
                "physical_page": page,
                "raw_depth": 2,
                "source_root_depth": 1,
                "effective_level": 2,
            }
        )
    return features, tuple(outlines)


def test_numbering_parse_work_doubles_linearly(monkeypatch: Any) -> None:
    original = numbering_scopes.parse_numbering

    def calls_for(blocks: int) -> int:
        calls = 0

        def counted(*args: Any, **kwargs: Any) -> Any:
            nonlocal calls
            calls += 1
            return original(*args, **kwargs)

        monkeypatch.setattr(numbering_scopes, "parse_numbering", counted)
        features, outlines = _numbering_fixture(blocks)
        result = numbering_scopes.build_numbering_regimes(features, outlines)
        assert len(result.regimes) == blocks + 1
        assert calls == 5 * blocks - 1
        return calls

    small = calls_for(250)
    large = calls_for(500)

    assert large == 2 * small + 1


def _decision_seconds(size: int) -> float:
    features = tuple(_feature(index, f"body {index}") for index in range(size))
    regime_id = "reg-0123456789abcdef"
    scoped = tuple({**item, "regime_id": regime_id} for item in features)
    regimes = (
        {
            "regime_id": regime_id,
            "parent_regime_id": None,
            "root_level": 1,
            "start_item_key": scoped[0]["stable_item_key"],
            "end_item_key": None,
            "outline_anchor_key": None,
            "page_label_reset": False,
        },
    )
    gc.collect()
    was_enabled = gc.isenabled()
    gc.disable()
    started = time.perf_counter()
    try:
        result = build_rule_decisions(
            features=scoped,
            toc_entries=(),
            reconciliations=(),
            regimes=regimes,
        )
    finally:
        if was_enabled:
            gc.enable()
    assert len(result.decisions) == size
    return time.perf_counter() - started


def test_rule_decision_doubling_stays_below_gate_b_limit() -> None:
    _decision_seconds(1_000)
    small = min(_decision_seconds(8_000) for _ in range(2))
    large = min(_decision_seconds(16_000) for _ in range(2))

    assert large / small < 2.5
