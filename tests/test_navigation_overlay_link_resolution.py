"""Tests for the Task 04D navigation adapter over shared resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from er_commons.artifact_io import write_jsonl
from er_commons.document_records.document_references.exact_resolution import ExactAliasEvidence
from er_commons.document_records.document_references.linking_policy import (
    load_document_linking_policy,
)
from er_commons.navigation_overlay.link_resolution import (
    resolve_toc_heading as _resolve_toc_heading,
)
from er_commons.navigation_overlay.task04d_reconciliation import (
    Task04DDocumentIndex,
    load_task04d_document_index,
)
from er_commons.navigation_overlay.task04d_reconciliation import (
    reconcile_task04d_entry as _reconcile_task04d_entry,
)

ROOT = Path(__file__).parents[1]


def _policy():
    return load_document_linking_policy(
        ROOT / "configs/linking_policies/document_linking_v1.json",
        schema_path=ROOT
        / "benchmarks/er_bench/schemas/document_linking/v1/linking_policy.schema.json",
    )


def resolve_toc_heading(**kwargs: Any):
    return _resolve_toc_heading(policy=_policy(), **kwargs)


def reconcile_task04d_entry(*args: Any, **kwargs: Any):
    return _reconcile_task04d_entry(*args, policy=_policy(), **kwargs)


def _alias(
    text: str,
    target_id: str = "target-1",
    *,
    alias_id: str = "alias-1",
    page_id: str = "page-1",
    parent_id: str | None = None,
) -> ExactAliasEvidence:
    return ExactAliasEvidence(
        lookup_keys=(text,),
        target_type="section",
        alias_id=alias_id,
        target_id=target_id,
        target_page_ids=(page_id,),
        parent_target_id=parent_id,
    )


@pytest.mark.parametrize(
    ("toc", "body"),
    [
        (
            "0.4.3 Expression of Unique Natural Settings",
            "0.4.3 Expression of Unique Natural Settings.",
        ),
        ("0.5.3 Active Transportation & Transit", "0.5.3 Active Transportation and Transit"),
        ("3.4.2 Residential Flex Space", "3.4.2 Residential Flex-Space"),
        ("3.6.5 Duplex/Single Family", "3.6.5 Duplex / Single Family"),
        ("8.3.4 Financing/Enhanced Infrastructure", "8.3.4 Financing/ Enhanced Infrastructure"),
        ("8.3.9 Traffi c Reduction", "8.3.9 Traffic Reduction"),
        (
            "9.3.3 Conditions, Covenants and Restrictions",
            "9.3.3 Conditions, Covenants, and Restrictions",
        ),
    ],
)
def test_accepted_mechanical_heading_fallbacks_resolve_uniquely(toc: str, body: str) -> None:
    decision = resolve_toc_heading(
        raw_entry_text=toc,
        terminal_destination_token=None,
        target_type="section",
        aliases=(_alias(body),),
    )

    assert [candidate.target_id for candidate in decision.candidates] == ["target-1"]


@pytest.mark.parametrize(
    ("toc", "body"),
    [
        (
            "2.2.1 Development Requirements of the Specifi c Plan",
            "GOAL 2.2.1: Development Requirements of the Specific Plan",
        ),
        (
            "3.2.1 Create a Mixed-Use District",
            "GOAL 3.2.1: Create a Mixed-Use District.",
        ),
        (
            "3.2.2 Commercial Development that is Benefi cial to City Residents",
            "GOAL 3.2.2: Commercial Development that is Beneficial to City Residents",
        ),
        (
            "2.2.2 Preserve the City’s Character",
            "GOAL 2.2.2: Preserve the City's Character.",
        ),
    ],
)
def test_goal_prefix_composes_with_accepted_typographic_fallbacks(toc: str, body: str) -> None:
    decision = resolve_toc_heading(
        raw_entry_text=toc,
        terminal_destination_token=None,
        target_type="section",
        aliases=(_alias(body),),
    )

    assert [candidate.target_id for candidate in decision.candidates] == ["target-1"]
    assert any(basis.startswith("goal_prefix") for basis in decision.match_basis)


@pytest.mark.parametrize(
    "raw_entry",
    (
        "4.2.1 Soil Conditions 38",
        "4.2.1 Soil Conditions........38",
        "4.2.1 Soil Conditions . . . 38",
    ),
)
def test_confirmed_terminal_destination_is_removed_before_full_heading_match(
    raw_entry: str,
) -> None:
    decision = resolve_toc_heading(
        raw_entry_text=raw_entry,
        terminal_destination_token="38",
        target_type="section",
        aliases=(_alias("4.2.1 Soil Conditions", page_id="page-38"),),
        destination_page_ids=("page-38",),
    )

    assert [candidate.target_id for candidate in decision.candidates] == ["target-1"]
    assert decision.destination_page_intersection_applied is True


def test_hyphenated_destination_after_unspaced_leader_is_removed() -> None:
    decision = resolve_toc_heading(
        raw_entry_text="4.1 Introduction...4.1-1",
        terminal_destination_token="4.1-1",
        target_type="section",
        aliases=(_alias("4.1 Introduction", page_id="page-4.1-1"),),
        destination_page_ids=("page-4.1-1",),
    )

    assert [candidate.target_id for candidate in decision.candidates] == ["target-1"]


def test_parent_scope_uses_only_an_explicit_resolved_parent() -> None:
    aliases = (
        _alias("a. Purpose", "child-a", parent_id="parent-a"),
        _alias("a. Purpose", "child-b", alias_id="alias-2", parent_id="parent-b"),
    )
    unscoped = resolve_toc_heading(
        raw_entry_text="a. Purpose",
        terminal_destination_token=None,
        target_type="section",
        aliases=aliases,
    )
    scoped = resolve_toc_heading(
        raw_entry_text="a. Purpose",
        terminal_destination_token=None,
        target_type="section",
        aliases=aliases,
        resolved_parent_target_ids=("parent-b",),
    )

    assert len(unscoped.candidates) == 2
    assert [candidate.target_id for candidate in scoped.candidates] == ["child-b"]


@pytest.mark.parametrize(
    ("toc", "body"),
    [
        ("2.6.4 Nonconforming Stuctures", "2.6.4 Nonconforming Structures"),
        ("3.6.10 Amenities", "3.6.10 Amenity"),
        ("7.10.1 Communications System", "7.10.1 Communications Systems"),
        ("3.3.4 Active Ground Floor Uses", "3.3.4 Objective Development Standards"),
    ],
)
def test_unaccepted_typo_plural_and_conflicting_wording_stay_unresolved(
    toc: str, body: str
) -> None:
    decision = resolve_toc_heading(
        raw_entry_text=toc,
        terminal_destination_token=None,
        target_type="section",
        aliases=(_alias(body),),
    )

    assert decision.candidates == ()


def test_section_fallbacks_are_not_authorized_for_figures() -> None:
    for target_type in ("figure",):
        decision = resolve_toc_heading(
            raw_entry_text="Table 4-1: Active Transportation & Transit",
            terminal_destination_token=None,
            target_type=target_type,
            aliases=(
                ExactAliasEvidence(
                    lookup_keys=("Table 4-1: Active Transportation and Transit",),
                    target_type=target_type,
                    alias_id="alias-1",
                    target_id="target-1",
                ),
            ),
        )
        assert decision.candidates == ()


def test_task04d_reconciler_integrates_no_page_goal_fallback() -> None:
    entry = {
        "toc_text_entry_id": "entry-1",
        "source_id": "appendix-a",
        "candidate_id": "candidate-1",
        "raw_text": "2.2.1 Development Requirements of the Specifi c Plan",
        "marker_kind": "section",
        "terminal_destination_token": None,
    }
    index = Task04DDocumentIndex(
        exact_aliases=(_alias("GOAL 2.2.1: Development Requirements of the Specific Plan"),),
        destination_page_ids={},
    )

    record = reconcile_task04d_entry(entry, index)

    assert record["outcome"] == "resolved_unique"
    assert record["target_ids"] == ["target-1"]
    assert record["match_basis"] == ["goal_prefix+split_fi_ligature"]


def test_task04d_reconciler_reports_destination_target_page_mismatch() -> None:
    entry = {
        "toc_text_entry_id": "entry-1",
        "source_id": "deir-main",
        "candidate_id": "candidate-1",
        "raw_text": "4.2.1 Soil Conditions 39",
        "marker_kind": "section",
        "terminal_destination_token": "39",
    }
    index = Task04DDocumentIndex(
        exact_aliases=(_alias("4.2.1 Soil Conditions", page_id="page-38"),),
        destination_page_ids={"39": ("page-39",)},
    )

    record = reconcile_task04d_entry(entry, index)

    assert record["outcome"] == "destination_target_page_mismatch"
    assert record["target_ids"] == []
    assert record["resolver_outcome"] == "destination_page_mismatch"
    assert record["scoped_text_candidate_count"] == 1


def test_document_index_loads_typed_section_and_page_evidence(tmp_path) -> None:
    document_root = _write_document_index_fixture(tmp_path)

    index = load_task04d_document_index(document_root)

    assert len(index.exact_aliases) == 1
    assert index.exact_aliases[0].target_id == "heading-without-id-type-coupling"
    assert index.exact_aliases[0].target_page_ids == ("page-1",)
    assert index.destination_page_ids == {"1": ("page-1",)}


def test_document_index_rejects_incomplete_canonical_evidence(tmp_path) -> None:
    document_root = _write_document_index_fixture(tmp_path)
    missing = document_root / "content/canonical/figures.jsonl"
    missing.unlink()

    with pytest.raises(ValueError, match=r"canonical evidence is incomplete.*figures\.jsonl"):
        load_task04d_document_index(document_root)


def _write_document_index_fixture(tmp_path):
    document_root = tmp_path / "document"
    canonical = document_root / "content/canonical"
    canonical.mkdir(parents=True)
    write_jsonl(canonical / "pages.jsonl", [{"id": "page-1", "printed_page_label": "1"}])
    write_jsonl(
        canonical / "blocks.jsonl",
        [
            {
                "id": "heading-block-1",
                "content_layer": "body",
                "is_toc_row": False,
                "semantic_placement": "body_content",
                "regions": [{"page_id": "page-1"}],
            }
        ],
    )
    write_jsonl(
        canonical / "sections.jsonl",
        [
            {
                "id": "heading-without-id-type-coupling",
                "heading_block_id": "heading-block-1",
                "content_layer": "body",
                "is_toc_row": False,
                "semantic_placement": "body_content",
                "parent_section_id": None,
            }
        ],
    )
    write_jsonl(canonical / "tables.jsonl", [])
    write_jsonl(canonical / "figures.jsonl", [])
    write_jsonl(
        canonical / "target_aliases.jsonl",
        [
            {
                "id": "section-alias-1",
                "alias_kind": "section",
                "normalized_alias": "1.1 Introduction",
                "targets": [
                    {
                        "target_id": "heading-without-id-type-coupling",
                        "target_type": "section",
                    }
                ],
            },
            {
                "id": "page-alias-1",
                "alias_kind": "printed_page",
                "normalized_alias": "1",
                "targets": [{"target_id": "page-1", "target_type": "page"}],
            },
        ],
    )
    return document_root
