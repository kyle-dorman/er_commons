from __future__ import annotations

import pytest

from er_commons.human_review_support.task04.models import (
    PageProfile,
    TableFamilyCandidate,
    WarningInstance,
)
from er_commons.human_review_support.task04.page_selection import (
    select_content_pages,
    select_nearby_content_page,
    select_table_families,
)
from er_commons.human_review_support.task04.warning_policy import (
    build_warning_classes,
    normalize_warning_message,
)


def test_page_selection_uses_content_bearing_pages_in_each_document_region() -> None:
    candidates = [PageProfile(page) for page in range(1, 10)]
    candidates[1] = PageProfile(2, body_text_chars=900, body_block_count=8)
    candidates[4] = PageProfile(5, body_text_chars=1_100, body_block_count=10)
    candidates[7] = PageProfile(8, body_text_chars=800, body_block_count=7)

    assert [item.physical_page for item in select_content_pages(candidates)] == [2, 5, 8]


def test_page_selection_replaces_an_empty_short_document_slice() -> None:
    candidates = [
        PageProfile(1, body_text_chars=60, body_block_count=1),
        PageProfile(2),
        PageProfile(3, body_text_chars=1_700, body_block_count=9),
        PageProfile(4, body_text_chars=1_300, body_block_count=8),
    ]

    assert [item.physical_page for item in select_content_pages(candidates)] == [1, 4, 3]


def test_nearby_page_selection_rejects_invalid_radius() -> None:
    with pytest.raises(ValueError, match="radius"):
        select_nearby_content_page([PageProfile(1)], 1, radius=-1)


def test_warning_sampling_collapses_pass_through_labels_but_retains_structure() -> None:
    instances = [
        WarningInstance("a", "producer", "producer_warning", "same warning"),
        WarningInstance("a", "canonicalization", "canonicalization_warning", "same warning"),
        WarningInstance("b", "producer", "producer_warning", "same warning"),
        WarningInstance("b", "canonicalization", "canonicalization_warning", "same warning"),
    ]

    warning = build_warning_classes(instances)[0]

    assert warning.occurrence_count == 2
    assert warning.raw_occurrence_count == 4
    assert warning.owners == ("canonicalization", "producer")
    assert warning.codes == ("canonicalization_warning", "producer_warning")


def test_warning_normalization_groups_instance_specific_pdf_values() -> None:
    first = (
        "WARNING: page object 782 0 stream 783 0 (content, offset 923): treating object "
        "as null because of error during parsing: overflow/underflow converting "
        "-674134905482582579616054562442867519324885678286666262159422773635563127 "
        "to 64-bit integer"
    )
    second = (
        "WARNING: page object 792 0 stream 793 0 (content, offset 5498): treating object "
        "as null because of error during parsing: overflow/underflow converting "
        "134826981096516515923210912488573503864977135657333252431884554727112625 "
        "to 64-bit integer"
    )

    assert normalize_warning_message(first) == normalize_warning_message(second)


def test_warning_normalization_preserves_known_class_semantics() -> None:
    assert normalize_warning_message("invalid provenance records: 246") == (
        "invalid provenance records: <count>"
    )
    assert (
        normalize_warning_message("routed pages with zero reconstructed tables: [1, 5, 172]")
        == "routed pages with zero reconstructed tables: <page-list>"
    )
    assert (
        normalize_warning_message("WARNING: /tmp/a.pdf Resources is missing or invalid; repairing")
        == "Resources is missing or invalid; repairing"
    )


def test_table_selection_uses_six_main_and_two_multipage_families_per_appendix() -> None:
    candidates = [TableFamilyCandidate("main", f"m{i}", page_count=10 - i) for i in range(8)]
    candidates.extend(
        [
            TableFamilyCandidate("appendix_a", "a1", 4),
            TableFamilyCandidate("appendix_a", "a2", 2),
            TableFamilyCandidate("appendix_a", "a3", 1),
            TableFamilyCandidate("appendix_c", "c1", 3),
        ]
    )

    selected = select_table_families(candidates, main_source_id="main")

    assert [item.family_id for item in selected if item.source_id == "main"] == [
        "m0",
        "m1",
        "m2",
        "m3",
        "m4",
        "m5",
    ]
    assert [(item.source_id, item.family_id) for item in selected if item.source_id != "main"] == [
        ("appendix_a", "a1"),
        ("appendix_a", "a2"),
        ("appendix_c", "c1"),
    ]
