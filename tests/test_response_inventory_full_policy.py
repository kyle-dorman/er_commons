"""Source-free tests for Task 05D structural accounting and review policy."""

from __future__ import annotations

from copy import deepcopy

from er_commons.response_inventory.full_policy import (
    TASK05D_CONTROL_PAGES,
    build_structural_accounting,
    lower_median,
    select_full_review_population,
)
from er_commons.response_inventory.observations import LineObservation, PageObservation


def test_lower_median_uses_the_contract_index() -> None:
    assert lower_median([1]) == 1
    assert lower_median([1, 2]) == 1
    assert lower_median([1, 2, 3, 4]) == 2


def test_fixed_controls_include_dense_boundaries() -> None:
    assert {368, 369, 370, 371, 372}.issubset(TASK05D_CONTROL_PAGES)
    assert {551, 552, 553, 554, 555}.issubset(TASK05D_CONTROL_PAGES)
    assert {668, 669, 670, 671}.issubset(TASK05D_CONTROL_PAGES)
    assert {1, 2, 4, 38, 39, 83, 84, 721, 722, 744}.issubset(TASK05D_CONTROL_PAGES)


def test_review_population_mapping_and_digest_are_exact_and_order_independent() -> None:
    records = [
        {
            "record_type": "page",
            "page_id": f"p{page}",
            "physical_page": page,
            "page_state": "body",
            "raw_text": "text",
        }
        for page in (100, 101, 102)
    ]
    qualification = {
        "pages": [
            {"physical_page": page, "review_reasons": [], "pdfium_poppler_token_multiset_f1": 1.0}
            for page in (100, 101, 102)
        ]
    }
    observations = [
        PageObservation(
            physical_page=page,
            raw_text="text",
            width_points=100,
            height_points=100,
            rotation=0,
            character_slot_count=4,
            lines=(LineObservation(0, 0, 4, (0, 0, 10, 10), 0, 4),),
        )
        for page in (100, 101, 102)
    ]
    first = select_full_review_population(
        deepcopy(qualification), records, observations, accepted_signature_digests=frozenset()
    )
    shuffled = select_full_review_population(
        deepcopy(qualification),
        list(reversed(records)),
        list(reversed(observations)),
        accepted_signature_digests=frozenset(),
    )
    assert first["review_population"] == [
        {
            "physical_page": page,
            "page_id": f"p{page}",
            "reasons": ["new_structural_signature", "page_state_sample:body"],
        }
        for page in (100, 101, 102)
    ]
    assert shuffled["review_population"] == first["review_population"]
    assert shuffled["review_population_digest"] == first["review_population_digest"]


def test_structural_accounting_derives_duplicate_and_gap_findings() -> None:
    records = [
        {
            "record_type": "page",
            "page_id": "pagev1-a",
            "physical_page": 1,
            "page_state": "unit_start",
        },
        {
            "record_type": "page",
            "page_id": "pagev1-b",
            "physical_page": 2,
            "page_state": "unit_start",
        },
        {
            "record_type": "source_span",
            "span_id": "spanv1-a",
            "fragments": [{"page_id": "pagev1-a"}],
        },
        {
            "record_type": "source_span",
            "span_id": "spanv1-b",
            "fragments": [{"page_id": "pagev1-b"}],
        },
        {
            "record_type": "source_unit",
            "unit_id": "unitv1-a",
            "unit_kind": "comment",
            "official_label": "Comment A-1",
            "span_ids": ["spanv1-a"],
        },
        {
            "record_type": "source_unit",
            "unit_id": "unitv1-b",
            "unit_kind": "comment",
            "official_label": "Comment A-3",
            "span_ids": ["spanv1-b"],
        },
        {
            "record_type": "source_unit",
            "unit_id": "unitv1-c",
            "unit_kind": "comment",
            "official_label": "Comment A-3",
            "span_ids": ["spanv1-b"],
        },
    ]
    report = build_structural_accounting(records)
    kinds = {finding["finding_kind"] for finding in report["label_findings"]}
    assert kinds == {"duplicate_label", "sequence_gap"}
    assert report["suspected_omissions"][0]["missing_numbers"] == [2]


def test_structural_accounting_retains_diagnostic_instances_and_pages() -> None:
    records = [
        {
            "record_type": "page",
            "page_id": "pagev1-a",
            "physical_page": 1,
            "page_state": "unit_start",
        },
        {
            "record_type": "page",
            "page_id": "pagev1-b",
            "physical_page": 2,
            "page_state": "unit_start",
        },
        {
            "record_type": "marker_candidate",
            "marker_id": "markerv1-a",
            "page_id": "pagev1-a",
            "marker_kind": "comment",
            "disposition": "unit_start",
        },
        {
            "record_type": "marker_candidate",
            "marker_id": "markerv1-b",
            "page_id": "pagev1-b",
            "marker_kind": "comment",
            "disposition": "unit_start",
        },
        {
            "record_type": "source_span",
            "span_id": "spanv1-a",
            "fragments": [{"page_id": "pagev1-a"}, {"page_id": "pagev1-b"}],
        },
        {
            "record_type": "source_unit",
            "unit_id": "unitv1-a",
            "unit_kind": "comment",
            "official_label": "Comment A-1",
            "start_marker_id": "markerv1-a",
            "span_ids": ["spanv1-a"],
        },
        {
            "record_type": "diagnostic",
            "diagnostic_id": "diagnosticv1-a",
            "code": "source_response_heading_absent",
            "subject_ids": ["unitv1-a"],
            "evidence_ids": ["markerv1-a", "markerv1-b", "spanv1-a"],
        },
    ]

    report = build_structural_accounting(records)

    assert report["schema_version"] == ("er_commons.response_inventory.structural_accounting.v2")
    assert report["diagnostic_codes"] == {"source_response_heading_absent": 1}
    assert report["diagnostic_instances"] == [
        {
            "diagnostic_id": "diagnosticv1-a",
            "code": "source_response_heading_absent",
            "subject_ids": ["unitv1-a"],
            "evidence_ids": ["markerv1-a", "markerv1-b", "spanv1-a"],
            "physical_pages": [1, 2],
        }
    ]
