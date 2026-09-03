from __future__ import annotations

import json
from pathlib import Path

import pytest

from er_commons.human_review_support.task04 import toc_page_shapes
from er_commons.human_review_support.task04.final_pass import final_review_policy
from er_commons.human_review_support.task04.toc_census import build_toc_census
from er_commons.human_review_support.task04.toc_decisions import load_toc_decisions
from er_commons.human_review_support.task04.toc_models import (
    contiguous_page_runs,
    parse_toc_censuses,
)
from er_commons.human_review_support.task04.toc_page_shapes import (
    decided_not_toc_run_suffixes,
)
from er_commons.human_review_support.task04.toc_review_selection import (
    basic_project_information_pages,
    build_positive_toc_items,
    build_toc_review_selection,
    intentional_blank_pages,
    recognized_toc_run_suffixes,
)
from er_commons.human_review_support.task04.toc_table_filters import (
    is_two_column_decimal_table,
    left_column,
)


def test_final_policy_freezes_source_free_boundary() -> None:
    policy = final_review_policy()

    assert policy["pass"] == "task03j_final"
    assert policy["toc_candidate_census"]["adjacency_rule"] == (
        "include_immediate_physical_neighbors_of_each_seed_page"
    )
    assert policy["approval_boundary"]["gate_c"] == (
        "explicit_approval_required_before_pdf_reads_or_renders"
    )


def test_toc_census_unions_signals_raw_index_and_adjacency(tmp_path: Path) -> None:
    candidate = tmp_path / "documents" / ("docv1-" + "a" * 64)
    canonical = candidate / "content/canonical"
    observations = candidate / "content/observations"
    canonical.mkdir(parents=True)
    observations.mkdir(parents=True)
    _jsonl(
        canonical / "pages.jsonl",
        [
            _page("p1", 1),
            _page("p2", 2),
            _page("p3", 3),
            _page("p4", 4),
            _page("p5", 5),
        ],
    )
    _jsonl(
        canonical / "blocks.jsonl",
        [
            _block("b1", "Contents", "p1", block_type="heading"),
            _block("b2", "1. Introduction........ 7", "p2", is_toc_row=True),
        ],
    )
    _jsonl(
        canonical / "sections.jsonl",
        [{"id": "s1", "parent_section_id": None, "heading_block_id": "b1", "section_kind": "body"}],
    )
    _jsonl(
        canonical / "tables.jsonl",
        [
            _table("t1", "p2", "s1", "toc_content", True),
            _table("t2", "p3", None, "body", False),
        ],
    )
    _jsonl(
        canonical / "assets.jsonl",
        [{"id": "asset1", "path": "raw.json", "role": "raw_docling_json"}],
    )
    _jsonl(
        canonical / "target_aliases.jsonl",
        [
            {
                "id": "alias1",
                "resolution_status": "ambiguous",
                "alias_kind": "section",
                "normalized_alias": "one",
                "raw_values": ["One"],
                "targets": [],
            }
        ],
    )
    _jsonl(canonical / "cross_references.jsonl", [])
    _jsonl(observations / "routing.jsonl", [])
    _jsonl(
        observations / "table_stage.jsonl",
        [
            {
                "id": "stage1",
                "page_id": "p4",
                "unmapped_reason": "document_index_not_canonical_table",
                "source_region_raw_link": {"object_pointer": "#/tables/0"},
            }
        ],
    )
    (tmp_path / "raw.json").write_text(
        json.dumps(
            {
                "tables": [
                    {
                        "label": "document_index",
                        "prov": [{"page_no": 4}],
                        "children": [{"$ref": "#/groups/1"}],
                    }
                ]
            }
        )
    )

    census = build_toc_census(
        candidate,
        source_id="source",
        source_ordinal=1,
        data_root=tmp_path,
    )

    by_page = {item["physical_page"]: item for item in census["candidate_pages"]}
    assert set(by_page) == {1, 2, 3, 4, 5}
    assert "canonical_toc_block" in by_page[2]["signals"]
    assert "adjacent_navigation_run" in by_page[5]["signals"]
    assert "raw_docling_document_index" in by_page[4]["signals"]
    assert census["summary"]["ambiguous_toc_alias_count"] == 1
    assert census["summary"]["substantive_table_control_count"] == 1


def test_toc_review_excludes_known_toc_and_bounds_each_signal_stratum() -> None:
    rows = [
        {
            "candidate_page_id": f"tocpagev1-source-p{page:05d}",
            "physical_page": page,
            "signals": signals,
            "adjacent_only": False,
            "substantive_table_control": False,
        }
        for page, signals in [
            (1, ["canonical_toc_block"]),
            (2, ["page_furniture_or_heading"]),
            (3, ["page_furniture_or_heading"]),
            (4, ["page_furniture_or_heading"]),
            (5, ["page_furniture_or_heading"]),
            (6, ["ambiguous_reference_link"]),
        ]
    ]
    selection = build_toc_review_selection(
        [
            {
                "source_id": "source",
                "source_ordinal": 1,
                "candidate_id": "docv1-candidate",
                "candidate_pages": rows,
            }
        ],
        "reviewv1-task03j-final-test",
        "a" * 64,
    )

    assert [item.physical_pages[0] for item in selection.items] == [2, 4, 5, 6]
    assert selection.population["recognized_toc_page_count_excluded"] == 1
    assert selection.population["selected_toc_review_page_count"] == 4


def test_numeric_two_column_and_repeated_left_column_filters() -> None:
    numeric = _canonical_table(["0.01", "0.25", "1.75"])
    repeated = _canonical_table(["Page 1", "Page 2", "Page 3"])

    assert is_two_column_decimal_table(numeric)
    assert not is_two_column_decimal_table(repeated)
    assert left_column(repeated) == ("a", "b", "c")
    assert left_column(repeated) == left_column(_canonical_table(["Different", "Values", "Here"]))


def test_obvious_navigation_heading_vocabulary() -> None:
    pattern = toc_page_shapes.OBVIOUS_NAVIGATION_HEADING_RE

    for heading in (
        "Contents",
        "Table of Contents (Continued)",
        "List of Figures",
        "List of Tables",
        "List of Appendices",
        "List of Attachments",
        "List of Support Exhibits",
        "Appendices",
        "Tables",
        "Figures",
        "Attachments",
    ):
        assert pattern.search(heading)
    assert not pattern.search("Basic Project Information")


def test_exported_toc_decisions_load_by_stable_page_id(tmp_path: Path) -> None:
    path = tmp_path / "toc_review_decisions.json"
    path.write_text(
        json.dumps(
            {
                "entries": [
                    {"entry_id": "tocpagev1-stable", "disposition": "toc"},
                    {"entry_id": "tocpagev1-other", "disposition": "not_toc"},
                ]
            }
        )
    )

    assert load_toc_decisions(path) == {
        "tocpagev1-stable": "toc",
        "tocpagev1-other": "not_toc",
    }


def test_toc_census_boundary_reports_the_bad_field() -> None:
    malformed = [
        {
            "source_id": "source",
            "source_ordinal": 1,
            "candidate_id": "candidate",
            "candidate_pages": [
                {
                    "candidate_page_id": "tocpagev1-test",
                    "physical_page": "not-an-integer",
                    "signals": [],
                }
            ],
        }
    ]

    with pytest.raises(ValueError) as captured:
        parse_toc_censuses(malformed)

    assert "toc_candidate_census[0].candidate_pages[0].physical_page" in str(captured.value)


def test_contiguous_page_runs_have_a_named_ordered_boundary() -> None:
    census = parse_toc_censuses(
        [
            {
                "source_id": "source",
                "candidate_pages": [
                    {
                        "candidate_page_id": f"tocpagev1-{page}",
                        "physical_page": page,
                        "signals": ["canonical_toc_block"],
                    }
                    for page in [5, 2, 1, 8]
                ],
            }
        ]
    )[0]

    runs = contiguous_page_runs(census.pages)

    assert [[page.physical_page for page in run] for run in runs] == [[1, 2], [5], [8]]


def test_imported_positive_stays_visible_without_reopening_its_run() -> None:
    rows = [
        {
            "candidate_page_id": f"tocpagev1-{name}",
            "physical_page": page,
            "signals": ["page_furniture_or_heading"],
            "adjacent_only": False,
            "substantive_table_control": False,
        }
        for page, name in [(1, "positive"), (2, "negative"), (3, "pending")]
    ]
    selection = build_toc_review_selection(
        [
            {
                "source_id": "source",
                "source_ordinal": 1,
                "candidate_id": "candidate",
                "candidate_pages": rows,
            }
        ],
        "reviewv1-test",
        "a" * 64,
        full_page_table_pages={("source", 1), ("source", 2), ("source", 3)},
        prior_decisions={"tocpagev1-positive": "toc", "tocpagev1-negative": "not_toc"},
    )

    assert [item.population["candidate_page_id"] for item in selection.items] == [
        "tocpagev1-positive",
    ]
    assert selection.population["imported_positive_page_count_included"] == 1
    assert selection.population["prior_decision_page_count_excluded"] == 1


def test_full_page_table_decision_keeps_same_run_representative_visible() -> None:
    rows = [
        {
            "candidate_page_id": f"tocpagev1-{page}",
            "physical_page": page,
            "signals": ["page_furniture_or_heading"],
            "adjacent_only": False,
            "substantive_table_control": False,
        }
        for page in [1, 2, 3]
    ]
    selection = build_toc_review_selection(
        [
            {
                "source_id": "source",
                "source_ordinal": 1,
                "candidate_id": "candidate",
                "candidate_pages": rows,
            }
        ],
        "reviewv1-test",
        "a" * 64,
        full_page_table_pages={("source", 1), ("source", 2), ("source", 3)},
        prior_decisions={"tocpagev1-1": "not_toc"},
    )

    assert [item.population["candidate_page_id"] for item in selection.items] == ["tocpagev1-1"]


def test_positive_review_selects_recognized_toc_runs() -> None:
    rows = [
        {
            "candidate_page_id": "tocpagev1-block",
            "physical_page": 1,
            "signals": ["canonical_toc_block"],
        },
        {
            "candidate_page_id": "tocpagev1-placement",
            "physical_page": 3,
            "signals": ["canonical_toc_placement"],
        },
        {
            "candidate_page_id": "tocpagev1-candidate",
            "physical_page": 2,
            "signals": ["page_furniture_or_heading"],
        },
    ]

    selection = build_positive_toc_items(
        [
            {
                "source_id": "source",
                "source_ordinal": 1,
                "candidate_id": "candidate",
                "candidate_pages": rows,
            }
        ],
        "reviewv1-test",
        "a" * 64,
    )

    assert [item.population["candidate_page_id"] for item in selection.items] == [
        "tocpagev1-block",
        "tocpagev1-placement",
    ]


def test_positive_review_excludes_safe_prefix_and_selects_each_unresolved_page() -> None:
    rows = [
        {
            "candidate_page_id": f"tocpagev1-{page}",
            "physical_page": page,
            "signals": ["canonical_toc_block"],
        }
        for page in [1, 2, 3, 5, 6]
    ]
    selection = build_positive_toc_items(
        [
            {
                "source_id": "source",
                "source_ordinal": 1,
                "candidate_id": "candidate",
                "candidate_pages": rows,
            }
        ],
        "reviewv1-test",
        "a" * 64,
        excluded_heading_pages={("source", 1), ("source", 6)},
        navigation_shaped_pages={("source", 2), ("source", 3)},
    )

    assert [item.physical_pages[0] for item in selection.items] == [5, 6]
    assert selection.population == {
        "machine_positive_page_count": 5,
        "fully_excluded_navigation_run_count": 1,
        "fully_excluded_navigation_run_page_count": 3,
        "navigation_prefix_page_count": 3,
        "split_after_navigation_prefix_run_count": 0,
        "long_run_guardrail_representative_count": 0,
        "intentional_blank_review_page_count_excluded": 0,
        "auto_false_positive_page_count_excluded": 0,
        "maximum_fully_excluded_run_page_count": 5,
        "selected_positive_review_page_count": 2,
    }


def test_positive_review_surfaces_first_page_after_navigation_prefix() -> None:
    rows = [
        {
            "candidate_page_id": f"tocpagev1-{page}",
            "physical_page": page,
            "signals": ["canonical_toc_block"],
        }
        for page in range(100, 108)
    ]

    selection = build_positive_toc_items(
        [
            {
                "source_id": "source",
                "source_ordinal": 1,
                "candidate_id": "candidate",
                "candidate_pages": rows,
            }
        ],
        "reviewv1-test",
        "a" * 64,
        excluded_heading_pages={("source", 100)},
        navigation_shaped_pages={("source", 101), ("source", 102)},
    )

    assert [item.physical_pages[0] for item in selection.items] == [103, 104, 105, 106, 107]
    assert selection.population["split_after_navigation_prefix_run_count"] == 1
    assert selection.items[0].population["positive_run"] == {
        "start_page": 100,
        "end_page": 107,
        "page_count": 8,
        "navigation_prefix_page_count": 3,
        "selection_basis": "first_page_after_navigation_prefix",
        "suffix_entry_ids": [
            "tocpagev1-103",
            "tocpagev1-104",
            "tocpagev1-105",
            "tocpagev1-106",
            "tocpagev1-107",
        ],
    }


def test_positive_review_never_fully_excludes_run_longer_than_five_pages() -> None:
    rows = [
        {
            "candidate_page_id": f"tocpagev1-{page}",
            "physical_page": page,
            "signals": ["canonical_toc_block", "raw_docling_document_index"],
        }
        for page in range(1, 7)
    ]

    selection = build_positive_toc_items(
        [
            {
                "source_id": "source",
                "source_ordinal": 1,
                "candidate_id": "candidate",
                "candidate_pages": rows,
            }
        ],
        "reviewv1-test",
        "a" * 64,
        excluded_heading_pages={("source", 1)},
    )

    assert [item.physical_pages[0] for item in selection.items] == [2]
    assert selection.population["long_run_guardrail_representative_count"] == 1


def test_positive_review_bypasses_intentional_blank_representative() -> None:
    rows = [
        {
            "candidate_page_id": f"tocpagev1-{page}",
            "physical_page": page,
            "signals": ["canonical_toc_block"],
        }
        for page in range(1, 5)
    ]

    selection = build_positive_toc_items(
        [
            {
                "source_id": "source",
                "source_ordinal": 1,
                "candidate_id": "candidate",
                "candidate_pages": rows,
            }
        ],
        "reviewv1-test",
        "a" * 64,
        excluded_heading_pages={("source", 1)},
        excluded_review_pages={("source", 2)},
    )

    assert [item.physical_pages[0] for item in selection.items] == [3, 4]
    assert selection.population["intentional_blank_review_page_count_excluded"] == 1


def test_positive_review_bypasses_auto_false_positive_representative() -> None:
    rows = [
        {
            "candidate_page_id": f"tocpagev1-{page}",
            "physical_page": page,
            "signals": ["canonical_toc_block"],
        }
        for page in range(1, 5)
    ]

    selection = build_positive_toc_items(
        [
            {
                "source_id": "source",
                "source_ordinal": 1,
                "candidate_id": "candidate",
                "candidate_pages": rows,
            }
        ],
        "reviewv1-test",
        "a" * 64,
        excluded_heading_pages={("source", 1)},
        navigation_shaped_pages={("source", 2), ("source", 3)},
        auto_false_positive_pages={("source", 4)},
    )

    assert selection.items == ()
    assert selection.population["auto_false_positive_page_count_excluded"] == 1


def test_intentional_blank_page_detection_requires_only_blank_notice(tmp_path: Path) -> None:
    candidate = tmp_path / "docv1-test"
    canonical = candidate / "content/canonical"
    canonical.mkdir(parents=True)
    page1 = "exv1-test/page/source/p000001"
    page2 = "exv1-test/page/source/p000002"
    _jsonl(canonical / "pages.jsonl", [_page(page1, 1), _page(page2, 2)])
    _jsonl(
        canonical / "blocks.jsonl",
        [
            _block("blank", "This page has been left blank intentionally.", page1),
            _block("body", "Introduction", page2, block_type="heading"),
        ],
    )

    assert intentional_blank_pages({"source": candidate}) == {("source", 1)}


def test_basic_project_information_pages_match_numbered_heading_only(tmp_path: Path) -> None:
    candidate = tmp_path / "docv1-test"
    canonical = candidate / "content/canonical"
    canonical.mkdir(parents=True)
    page1 = "exv1-test/page/source/p000001"
    page2 = "exv1-test/page/source/p000002"
    _jsonl(canonical / "pages.jsonl", [_page(page1, 1), _page(page2, 2)])
    _jsonl(
        canonical / "blocks.jsonl",
        [
            _block("body-heading", "1. Basic Project Information", page1, block_type="heading"),
            _block("body-text", "Basic Project Information", page2),
        ],
    )

    assert basic_project_information_pages({"source": candidate}) == {("source", 1)}


def test_recognized_toc_run_suffixes_stop_at_run_end() -> None:
    rows = [
        {
            "candidate_page_id": f"tocpagev1-{page}",
            "physical_page": page,
            "signals": ["canonical_toc_block"],
        }
        for page in [1, 2, 3, 5, 6]
    ]

    pages, entry_ids = recognized_toc_run_suffixes(
        [
            {
                "source_id": "source",
                "source_ordinal": 1,
                "candidate_id": "candidate",
                "candidate_pages": rows,
            }
        ],
        {("source", 2)},
    )

    assert pages == {("source", 2), ("source", 3)}
    assert entry_ids == {"tocpagev1-2", "tocpagev1-3"}


def test_not_toc_decision_expands_through_only_its_positive_run() -> None:
    rows = [
        {
            "candidate_page_id": f"tocpagev1-{page}",
            "physical_page": page,
            "signals": ["canonical_toc_block"],
        }
        for page in [1, 2, 3, 5, 6]
    ]

    pages, entry_ids = decided_not_toc_run_suffixes(
        [{"source_id": "source", "candidate_pages": rows}],
        {"tocpagev1-2": "not_toc", "tocpagev1-5": "toc"},
    )

    assert pages == {("source", 2), ("source", 3)}
    assert entry_ids == {"tocpagev1-2", "tocpagev1-3"}


def _canonical_table(second_column: list[str]) -> dict[str, object]:
    cells = []
    for row, value in enumerate(second_column):
        cells.extend(
            [
                {"row_index": row, "column_index": 0, "text": chr(65 + row)},
                {"row_index": row, "column_index": 1, "text": value},
            ]
        )
    return {"shape": [len(second_column), 2], "cells": cells}


def _page(page_id: str, physical: int) -> dict[str, object]:
    return {
        "id": page_id,
        "physical_page_number": physical,
        "printed_page_label": None,
        "ordered_content_ids": [],
    }


def _block(
    block_id: str,
    text: str,
    page_id: str,
    *,
    block_type: str = "paragraph",
    is_toc_row: bool = False,
) -> dict[str, object]:
    return {
        "id": block_id,
        "canonical_text": text,
        "block_type": block_type,
        "is_toc_row": is_toc_row,
        "semantic_placement": "body",
        "regions": [{"page_id": page_id}],
    }


def _table(
    table_id: str,
    page_id: str,
    section_id: str | None,
    placement: str,
    is_toc_row: bool,
) -> dict[str, object]:
    return {
        "id": table_id,
        "section_id": section_id,
        "table_family_id": None,
        "semantic_placement": placement,
        "is_toc_row": is_toc_row,
        "cells": [{"text": "Body table"}],
        "regions": [{"page_id": page_id}],
    }


def _jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + ("\n" if rows else ""))
