"""Focused source-free tests for Task 04C Gate C reconciliation."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from er_commons.artifact_io import (
    canonical_json_sha256,
    file_reference,
    json_bytes,
    sha256_file,
)
from er_commons.navigation_overlay.reconciliation import (
    ACCEPTED_GATE_B_ID,
    GateCReconciliationRequest,
    _accounting,
    _DocumentIndex,
    _normalize_numeric_marker,
    _publish,
    _reconcile_entry,
    _specification,
    _validate_ambiguity_population,
    _validate_candidate_files,
    _validate_gate_a_closure,
)


def _entry(raw_text: str, terminal: str | None) -> dict[str, object]:
    return {
        "toc_text_entry_id": "navtocentryv1-" + "3" * 24,
        "toc_text_page_id": "navtocpagev1-" + "4" * 24,
        "source_page_id": "ex/page/p000007",
        "physical_page": 7,
        "entry_index": 0,
        "raw_text": raw_text,
        "terminal_destination_token": terminal,
    }


def _index() -> _DocumentIndex:
    target_id = "ex/section/sec000001"
    target_alias = {
        "id": "ex/target-alias/alias000001",
        "eligible_targets": [{"target_id": target_id}],
    }
    page_alias = {
        "id": "ex/target-alias/alias000002",
        "eligible_targets": [{"target_id": "ex/page/p000038"}],
    }
    return _DocumentIndex(
        target_aliases={("section", "4.2.1"): [target_alias]},
        entities={},
        entity_pages={target_id: ("ex/page/p000038",)},
        destination_aliases={"38": [page_alias]},
        physical_by_page_id={"ex/page/p000007": 7},
    )


def test_numeric_marker_normalization_is_narrow() -> None:
    assert _normalize_numeric_marker(" 04 . 02 . 1 ") == "04.02.1"
    assert _normalize_numeric_marker("4") is None
    assert _normalize_numeric_marker("4-2-1") is None


def test_resolved_entry_uses_existing_alias_and_creates_only_link() -> None:
    row, link = _reconcile_entry(
        source_id="source",
        candidate_id="docv1-" + "2" * 64,
        entry=_entry("4 . 2 . 1 Soil ........ 38", "38"),
        index=_index(),
        link_view_id=None,
    )
    assert row["entry_outcome"] == "resolved_unique"
    assert row["normalized_marker"] == "4.2.1"
    assert row["target_alias_count"] == 1
    assert row["link_overlay_id"] is not None
    assert link is not None
    assert link["existing_body_alias_id"] == "ex/target-alias/alias000001"
    assert "alias_overlay_id" not in link


def test_printed_page_disambiguates_multiple_body_targets() -> None:
    index = _index()
    target_id = "ex/section/sec000001"
    competing_id = "ex/section/sec000002"
    alias = index.target_aliases[("section", "4.2.1")][0]
    alias["eligible_targets"].append({"target_id": competing_id})
    index.entity_pages[competing_id] = ("ex/page/p000099",)
    index.destination_aliases["38"][0]["eligible_targets"].append({"target_id": "ex/page/p000077"})

    row, link = _reconcile_entry(
        source_id="source",
        candidate_id="docv1-" + "2" * 64,
        entry=_entry("4.2.1 Soil ........ 38", "38"),
        index=index,
        link_view_id=None,
    )

    assert row["distinct_target_ids"] == [target_id, competing_id]
    assert row["page_consistent_target_ids"] == [target_id]
    assert row["page_disambiguation_applied"] is True
    assert row["destination_page_count"] == 2
    assert row["entry_outcome"] == "resolved_unique"
    assert link is not None
    assert link["target_id"] == target_id
    assert link["resolution_method"] == (
        "existing_body_alias_and_printed_page_candidate_intersection"
    )


def test_page_intersection_stays_ambiguous_when_two_targets_remain() -> None:
    index = _index()
    competing_id = "ex/section/sec000002"
    index.target_aliases[("section", "4.2.1")][0]["eligible_targets"].append(
        {"target_id": competing_id}
    )
    index.entity_pages[competing_id] = ("ex/page/p000038",)

    row, link = _reconcile_entry(
        source_id="source",
        candidate_id="docv1-" + "2" * 64,
        entry=_entry("4.2.1 Soil ........ 38", "38"),
        index=index,
        link_view_id=None,
    )

    assert row["entry_outcome"] == "ambiguous_target_alias"
    assert len(row["page_consistent_target_ids"]) == 2
    assert link is None


def test_page_intersection_rejects_zero_compatible_targets() -> None:
    index = _index()
    index.entity_pages["ex/section/sec000001"] = ("ex/page/p000099",)

    row, link = _reconcile_entry(
        source_id="source",
        candidate_id="docv1-" + "2" * 64,
        entry=_entry("4.2.1 Soil ........ 38", "38"),
        index=index,
        link_view_id=None,
    )

    assert row["entry_outcome"] == "destination_target_page_mismatch"
    assert row["page_consistent_target_ids"] == []
    assert link is None


def test_second_supported_marker_fails_closed_before_linking() -> None:
    row, link = _reconcile_entry(
        source_id="source",
        candidate_id="docv1-" + "2" * 64,
        entry=_entry("4.2.1 Soil Table 2: merged OCR content 38", "38"),
        index=_index(),
        link_view_id=None,
    )
    assert row["supported_marker_count"] == 2
    assert row["entry_outcome"] == "unsupported_entry_shape"
    assert link is None


def test_production_accounting_is_fail_closed() -> None:
    with pytest.raises(ValueError, match="production accounting differs"):
        _accounting([], [], [], [], [])


def test_ambiguity_population_must_equal_gate_a_closure() -> None:
    entries = [{"reference_id": f"xref-{index}"} for index in range(725)]
    closure = {
        "inherited_ambiguous_links": {
            "all_ids": [f"xref-{index}" for index in range(725)],
            "outside_closure_ids": [f"xref-{index}" for index in range(725)],
        }
    }
    _validate_ambiguity_population(entries, closure)
    entries[-1] = {"reference_id": "substituted-xref"}
    with pytest.raises(ValueError, match="differs from the Gate A closure"):
        _validate_ambiguity_population(entries, closure)


def test_gate_a_closure_rejects_nonzero_alias_or_link_scope() -> None:
    closure = {
        "inherited_ambiguous_links": {
            "in_closure_ids": [],
            "outside_closure_ids": [str(index) for index in range(725)],
        },
        "accounting": {
            "affected_alias_count": 1,
            "affected_link_count": 0,
            "affected_collection_resolution_count": 0,
            "inherited_ambiguous_link_in_closure_count": 0,
            "inherited_ambiguous_link_outside_closure_count": 725,
        },
    }
    with pytest.raises(ValueError, match="ambiguity closure differs"):
        _validate_gate_a_closure(closure)


def test_candidate_inventory_size_check_rejects_changed_canonical_input(
    tmp_path: Path,
) -> None:
    publication = tmp_path / "task03j/document_publications"
    document = publication / "documents/source/docv1-test"
    relative_files = (
        "records/document_identity.json",
        "content/canonical/pages.jsonl",
        "content/canonical/sections.jsonl",
        "content/canonical/blocks.jsonl",
        "content/canonical/tables.jsonl",
        "content/canonical/target_aliases.jsonl",
        "content/observations/page_labels.jsonl",
    )
    for relative in relative_files:
        path = document / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")
    inventory = {
        "files": [file_reference(document / relative, root=document) for relative in relative_files]
    }
    inventory_path = document / "records/artifact_inventory.json"
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_bytes(json_bytes(inventory))
    candidate = {
        "candidate_inventory": {
            "path": inventory_path.relative_to(publication).as_posix(),
            "sha256": sha256_file(inventory_path),
        },
        "canonical_records": cast(list[dict[str, object]], inventory["files"][:5]),
    }
    (document / "content/canonical/pages.jsonl").write_bytes(b"changed")
    request = GateCReconciliationRequest(
        data_root=tmp_path,
        repo_root=tmp_path,
        task03j_root=tmp_path / "task03j",
    )
    with pytest.raises(ValueError, match="changed or unsealed"):
        _validate_candidate_files(request, candidate)


def _accepted_accounting() -> dict[str, object]:
    return {
        "confirmed_navigation_table_count": 15,
        "toc_text_page_count": 15,
        "toc_text_entry_count": 560,
        "toc_entry_reconciliation_count": 560,
        "toc_entry_outcome_counts": {
            "empty_entry": 0,
            "unsupported_entry_shape": 216,
            "unsupported_target_type": 87,
            "no_target_alias": 120,
            "ambiguous_target_alias": 0,
            "no_unique_destination_page": 108,
            "destination_target_page_mismatch": 1,
            "resolved_unique": 28,
        },
        "resolved_toc_entry_count": 28,
        "unresolved_toc_entry_count": 532,
        "alias_overlay_addition_count": 0,
        "link_overlay_addition_count": 28,
        "existing_alias_invalidation_count": 0,
        "existing_link_invalidation_count": 0,
        "inherited_ambiguous_disposition_count": 725,
        "inherited_ambiguous_in_affected_closure_count": 0,
        "inherited_ambiguous_outside_affected_closure_count": 725,
    }


def test_publication_reuses_identical_and_rejects_tamper(tmp_path: Path) -> None:
    preimage = {"schema_version": "er_commons.navigation_overlay.v1.link_identity_preimage"}
    link_view_id = f"navlinkv1-{canonical_json_sha256(preimage)}"
    specification = _specification(
        link_view_id,
        preimage,
        {},
        _accepted_accounting(),
        object(),  # type: ignore[arg-type]
    )
    schema_root = (
        Path(__file__).parents[1] / "benchmarks/er_bench/schemas/navigation_overlay/v1/gate_c"
    )
    first = _publish(
        tmp_path,
        link_view_id,
        [],
        [],
        [],
        [],
        [],
        specification,
        _accepted_accounting(),
        schema_root,
    )
    second = _publish(
        tmp_path,
        link_view_id,
        [],
        [],
        [],
        [],
        [],
        specification,
        _accepted_accounting(),
        schema_root,
    )
    assert first == second
    assert (first / "alias_overlay.jsonl").read_bytes() == b""
    assert ACCEPTED_GATE_B_ID in (first / "navigation_link_manifest.json").read_text()
    (first / "link_overlay.jsonl").write_text("tampered\n")
    with pytest.raises(FileExistsError, match="refusing to reuse changed"):
        _publish(
            tmp_path,
            link_view_id,
            [],
            [],
            [],
            [],
            [],
            specification,
            _accepted_accounting(),
            schema_root,
        )
