"""Synthetic source-free tests for Task 06G comparison closure."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import er_commons.task06g.comparison as comparison_module
from er_commons.task06g.comparison import (
    _appendix_a_structure_correspondence,
    _publication_files,
    _scope_id_from_checkpoint,
    _verify_or_publish,
    build_task06g_closure,
)
from er_commons.task06g.comparison_links import load_collection_link_evidence
from er_commons.task06g.core import reference

JsonObject = dict[str, Any]


def test_scope_id_uses_verified_collection_checkpoint_outputs() -> None:
    checkpoint = {
        "verified": True,
        "derived_id": "handoffv1-one",
        "recomputed_id": "handoffv1-one",
        "outputs": {"scope_id": "scopev1-one"},
    }
    assert _scope_id_from_checkpoint(checkpoint) == "scopev1-one"
    checkpoint["recomputed_id"] = "handoffv1-two"
    with pytest.raises(ValueError, match="recomputation differs"):
        _scope_id_from_checkpoint(checkpoint)


def _fixture() -> dict[str, object]:
    source_ids = [f"source_{index:02d}" for index in range(1, 36)]
    source_ids[9] = "deir_appendix_f1"
    source_ids[17] = "deir_appendix_a"
    source_ids[24] = "deir_main"
    selected_ids = [
        "feir_appendix_f1" if source_id == "deir_appendix_f1" else source_id
        for source_id in source_ids
    ]
    old_pages = [1] * 35
    old_pages[9] = 75
    old_pages[24] = 48_233
    new_pages = list(old_pages)
    new_pages[9] = 756

    def accounting(ids: list[str], pages: list[int], namespace: str) -> JsonObject:
        return {
            "ordered_sources": [
                {
                    "source_id": source_id,
                    "pdf_page_count": page_count,
                    "sha256": source_id,
                }
                for source_id, page_count in zip(ids, pages, strict=True)
            ],
            "rows": [
                {
                    "source_id": source_id,
                    "candidate_id": f"candidate-{source_id}",
                    "document_completion_ref": {"path": f"{namespace}/{source_id}.json"},
                }
                for source_id in ids
            ],
        }

    def targets(ids: list[str], namespace: str) -> list[JsonObject]:
        return [
            {
                "alias_id": f"{namespace}/alias/{source_id}",
                "lookup_key": f"key-{source_id}",
                "source_id": source_id,
                "source_ordinal": ordinal,
                "target_id": f"{namespace}/section/{source_id}",
                "target_type": "section",
            }
            for ordinal, source_id in enumerate(ids, start=1)
        ]

    def resolutions(namespace: str) -> list[JsonObject]:
        return [
            {
                "candidate_local_sequence": sequence,
                "candidate_targets": [
                    {
                        "target_id": f"{namespace}/section/target-{sequence}",
                        "target_source_id": "source_01",
                        "target_type": "section",
                    }
                ],
                "lookup_key": f"reference-{sequence}",
                "mention_class": "section",
                "mention_id": f"{namespace}/cross-reference/deir_main/xref{sequence:06d}",
                "status": "resolved",
                "unresolved_reason": None,
                "cross_document_evidence": {
                    "catalog_sha256": f"catalog-{namespace}",
                    "source_family_id": "brisbane_baylands_2025_deir",
                    "intended_target_source_ids": ["source_01"],
                    "traversal_rule": "root_report_to_top_level_appendix",
                },
            }
            for sequence in range(1, 73)
        ]

    baseline = {
        "accounting": accounting(source_ids, old_pages, "old"),
        "target_index": {"entry_count": 99_172, "entries": targets(source_ids, "old")},
        "resolution_completion": {
            "mention_input_manifest": {
                "source_family_catalog_ref": {
                    "path": "old-catalog.json",
                    "sha256": "catalog-old",
                    "byte_size": 1,
                }
            },
            "resolutions": resolutions("old"),
        },
    }
    replacement_targets = targets(selected_ids, "new")
    replacement_targets.extend(
        [
            {
                "alias_id": f"new/alias/deir_main/chapter-{marker}",
                "lookup_key": f"chapter {marker}",
                "source_id": "deir_main",
                "source_ordinal": 25,
                "target_id": f"new/section/deir_main/chapter-{marker}",
                "target_type": "section",
            }
            for marker in ("8", "9")
        ]
    )
    replacement_targets.extend(
        {
            "alias_id": f"new/alias/deir_main/figure-{index}",
            "lookup_key": f"figure 4.8-{index}",
            "source_id": "deir_main",
            "source_ordinal": 25,
            "target_id": f"new/figure/deir_main/fig{index:06d}",
            "target_type": "figure",
        }
        for index in range(1, 179)
    )
    replacement = {
        "accounting": accounting(selected_ids, new_pages, "new"),
        "target_index": {"entry_count": 99_354, "entries": replacement_targets},
        "resolution_completion": {
            "mention_input_manifest": {
                "source_family_catalog_ref": {
                    "path": "new-catalog.json",
                    "sha256": "catalog-new",
                    "byte_size": 1,
                }
            },
            "resolutions": resolutions("new"),
        },
    }

    def catalog(ids: list[str], pages: list[int], namespace: str) -> JsonObject:
        return {
            "schema_version": "er_commons.source_family_catalog.v1",
            "catalog_version": "brisbane_baylands_2025_deir_task03h_source_family_v1",
            "source_family_id": "brisbane_baylands_2025_deir",
            "sources": [
                {
                    "document_role": "top_level_appendix",
                    "family_root_source_id": "deir_main",
                    "parent_source_id": "deir_main",
                    "reference_aliases": [f"alias-{index}"],
                    "source": {
                        "source_id": source_id,
                        "pdf_page_count": page_count,
                        "sha256": source_id,
                        "byte_size": index,
                    },
                }
                for index, (source_id, page_count) in enumerate(
                    zip(ids, pages, strict=True), start=1
                )
            ],
        }

    replacement_support = {
        source_id: {"source_candidate_id": f"candidate-{source_id}"}
        for source_id in source_ids
        if source_id not in {"deir_appendix_f1", "deir_appendix_a", "deir_main"}
    }
    repeated = [
        {
            "change_class": "many_to_one_repeated_heading_repair",
            "old_targets": [
                {"section_id": "old/section/deir_appendix_a/a"},
                {"section_id": "old/section/deir_appendix_a/b"},
            ],
            "new_target": {"section_id": "new/section/deir_appendix_a/a"},
            "logical_content_page_extent": extent,
            "content_record_ids_unique": True,
            "policy_version": "repeated_chapter_divider_opening_v2",
            "extent_basis": "record_order_before_immediate_same_level_sibling",
        }
        for extent in ([311, 451], [451, 479], [479, 491], [491, 501])
    ]
    d_rows = [
        {
            "chapter_marker": "06",
            "heading_physical_pages": [311, 312],
            "source_page_extents": [[311, 311], [312, 451]],
            "ordered_child_refs": [["heading", "a", "b", "c"], ["heading", "d", "e", "f"]],
            "following_boundary_raw_text": "07 INFRASTRUCTURE",
            "following_boundary_page": 451,
            "following_boundary_content_order": 5571,
        },
        {
            "chapter_marker": "07",
            "heading_physical_pages": [451, 452],
            "source_page_extents": [[451, 451], [452, 479]],
            "ordered_child_refs": [
                ["heading", "a", "b", "c", "d", "e"],
                ["heading", "f", "g", "h", "i", "j"],
            ],
            "following_boundary_raw_text": "08 PUBLIC FACILITIES FINANCING",
            "following_boundary_page": 479,
            "following_boundary_content_order": 5964,
        },
        {
            "chapter_marker": "08",
            "heading_physical_pages": [479, 480],
            "source_page_extents": [[479, 479], [480, 491]],
            "ordered_child_refs": [["heading", "a", "b"], ["heading", "c", "d"]],
            "following_boundary_raw_text": "09 IMPLEMENTATION",
            "following_boundary_page": 491,
            "following_boundary_content_order": 6179,
        },
        {
            "chapter_marker": "09",
            "heading_physical_pages": [491, 492],
            "source_page_extents": [[491, 491], [492, 501]],
            "ordered_child_refs": [["heading", "a", "b"], ["heading", "c", "d", "e"]],
            "following_boundary_raw_text": "APPENDICES",
            "following_boundary_page": 501,
            "following_boundary_content_order": 6274,
        },
    ]
    repairs = {
        "task06d": {"eligible_decisions": d_rows},
        "task06e": {
            "eligible_decisions": [
                {
                    "chapter_marker": "8",
                    "chapter_title": "Chapter 8 Alternatives",
                    "extent_start_page": 1855,
                    "extent_end_page": 2014,
                },
                {
                    "chapter_marker": "9",
                    "chapter_title": "Chapter 9 Subsequent EIR Analysis and Findings",
                    "extent_start_page": 2015,
                    "extent_end_page": 2084,
                    "following_boundary_page": 2085,
                },
            ]
        },
        "task06f": {
            "candidate_figure_count": 274,
            "eligible_figure_count": 178,
            "rejected_figure_count": 96,
            "unique_alias_count": 178,
            "target_edge_count": 178,
            "ambiguous_alias_count": 0,
            "collision_group_count": 0,
            "review_required_figure_count": 0,
            "decisions": [
                {
                    "eligibility": "eligible",
                    "normalized_alias": f"figure 4.8-{index}",
                    "upstream_figure_id": f"old/figure/deir_main/fig{index:06d}",
                    "reason": "eligible_attached_body_caption",
                }
                for index in range(1, 179)
            ],
            "accepted_target_index_entries": [
                {
                    "lookup_key": f"figure 4.8-{index}",
                    "upstream_target_record_id": f"old/figure/deir_main/fig{index:06d}",
                }
                for index in range(1, 179)
            ],
            "accepted_figure_aliases": [
                {
                    "normalized_alias": f"figure 4.8-{index}",
                    "targets": [{"upstream_target_id": (f"old/figure/deir_main/fig{index:06d}")}],
                }
                for index in range(1, 179)
            ],
        },
    }
    expected = {
        "document_count": 35,
        "page_count": 49_022,
        "task04a_decision_count": 757,
        "task05_mention_count": 511,
        "task05_link_count": 295,
        "task05_nonlink_count": 216,
        "ordinary_reference_count": 5_088,
        "navigation_claim_count": 560,
        "inherited_navigation_link_count": 28,
        "baseline_resolution_decision_count": 72,
    }

    def link_evidence(namespace: str) -> JsonObject:
        evidence = {
            "ordinary": [
                {
                    "id": f"{namespace}/cross-reference/source_01/xref{index:06d}",
                    "source_id": "source_01",
                    "mention_class": "section",
                    "lookup_key": f"section {index}",
                    "candidates": [],
                    "cross_document_evidence": None,
                    "resolution_status": "unresolved",
                    "unresolved_reason": "no_local_alias",
                }
                for index in range(1, 5_089)
            ],
            "navigation": [
                {
                    "source_id": "deir_appendix_k2_part_1_of_5",
                    "navigation_entry_id": f"entry-{index:03d}",
                    "outcome": "resolved_unique" if index <= 410 else "no_text_match",
                    "candidate_target_ids": (
                        [f"{namespace}/section/deir_appendix_k2_part_1_of_5/sec{index:06d}"]
                        if index <= 410
                        else []
                    ),
                    "match_basis": ["exact"] if index <= 410 else [],
                }
                for index in range(1, 561)
            ],
        }
        if namespace == "old":
            evidence["task04c_baseline_targets"] = {
                f"entry-{index:03d}": (f"section/deir_appendix_k2_part_1_of_5/sec{index:06d}")
                for index in range(1, 29)
            }
        return evidence

    return {
        "spec": {
            "expected_fixed_accounting": expected,
            "required_repair_checks": [
                "appendix_a_chapter_06_many_to_one",
                "appendix_a_chapter_07_many_to_one",
                "appendix_a_chapter_08_many_to_one",
                "appendix_a_chapter_09_many_to_one",
                "main_chapter_8_addition",
                "main_chapter_9_addition",
                "main_fc1_274_178_96_zero_collision",
                "figure_4_8_absent",
                "preserved_32_semantic_equality_after_mapping",
            ],
        },
        "baseline": baseline,
        "replacement": replacement,
        "source_slots": {"sources": [{"source_id": item} for item in source_ids]},
        "reviews": {
            "historical_correspondence": [
                {
                    "decision_entry_id": f"decision-{index}",
                    "source_id": "source_01",
                }
                for index in range(757)
            ]
        },
        "mentions": {
            "mentions": [{"mention_id": f"mention-{index}"} for index in range(511)],
            "population_counts": {
                "f1_wrong_source": 66,
                "figure_missing_target": 79,
                "chapter_8_9": 19,
                "appendix_a_duplicate_heading_reference": 2,
            },
        },
        "repairs": repairs,
        "appendix_a_correspondence": {
            "schema_version": "er_commons.recovery.repeated_heading_correspondence.v1",
            "candidate_id": "exv1-" + "a" * 64,
            "decision_ref": {"path": "06d/eligible_decisions.jsonl", "sha256": "b" * 64},
            "records": repeated,
        },
        "main_correspondence": {
            "schema_version": "er_commons.recovery.missing_chapter_correspondence.v1",
            "records": [
                {
                    "chapter_marker": marker,
                    "new_target": {"section_id": f"new/section/deir_main/chapter-{marker}"},
                }
                for marker in ("8", "9")
            ],
        },
        "gate_c": {
            "ordinary_machine": {"population_count": 5_088},
            "navigation": {
                "population_count": 560,
                "resolved_count": 410,
                "unresolved_count": 150,
                "control_population_counts": {"existing_task04c_link": 28},
                "existing_link_invalidation_count": 0,
            },
        },
        "link_evidence": {
            "baseline": link_evidence("old"),
            "replacement": link_evidence("new"),
        },
        "replacement_document_support": replacement_support,
        "source_family_catalogs": {
            "baseline": catalog(source_ids, old_pages, "old"),
            "replacement": catalog(selected_ids, new_pages, "new"),
        },
    }


def _build(fixture: dict[str, object]) -> tuple[dict[str, JsonObject], dict[str, JsonObject]]:
    return build_task06g_closure(**fixture)  # type: ignore[arg-type]


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _repair_loader_fixture(data_root: Path) -> Path:
    """Seal synthetic accepted packets plus a valid but superseded v15 decoy."""
    accepted_main = Path("pipelines/brisbane_baylands/task_06_recovery_v1/06e/qualification_v17")
    roots = {
        "task06d": Path("pipelines/brisbane_baylands/task_06_recovery_v1/06d/qualification_v8"),
        "task06e": accepted_main,
        "task06f": Path("pipelines/brisbane_baylands/task_06_recovery_v1/06f/qualification_v10"),
        "superseded": accepted_main.with_name("qualification_v15"),
    }
    for owner, relative in roots.items():
        root = data_root / relative
        payloads = {"qualification.json": {"packet": owner}}
        if owner == "task06f":
            payloads.update({"target_index_entries.jsonl": {}, "figure_aliases.jsonl": {}})
        else:
            payloads["eligible_decisions.jsonl"] = {"packet": owner, "chapter_marker": "8"}
        for name, value in payloads.items():
            _write_json(root / name, value)
        _write_json(
            root / "inventory.json",
            {"files": [reference(root / name, root=root) for name in payloads]},
        )
        _write_json(
            root / "completion.json",
            {
                "status": "complete",
                "inventory_sha256": reference(root / "inventory.json")["sha256"],
            },
        )
    return data_root / accepted_main


def test_repair_loader_and_provenance_use_exact_accepted_v17(tmp_path: Path) -> None:
    """Neither reading nor emitted provenance may select the sealed v15 decoy."""
    root = _repair_loader_fixture(tmp_path)
    assert comparison_module.REPAIR_ROOTS["task06e"] == root.relative_to(tmp_path)
    repairs = comparison_module._load_repairs(tmp_path)
    assert repairs["task06e"] == {
        "packet": "task06e",
        "eligible_decisions": [{"packet": "task06e", "chapter_marker": "8"}],
    }
    provenance = comparison_module._repair_provenance(tmp_path)["task06e"]
    assert provenance == [
        {"authority": "artifact_root", "role": name, **reference(root / name, root=tmp_path)}
        for name in (
            "completion.json",
            "inventory.json",
            "qualification.json",
            "eligible_decisions.jsonl",
        )
    ]


@pytest.mark.parametrize(
    "name", ["completion.json", "inventory.json", "qualification.json", "eligible_decisions.jsonl"]
)
def test_repair_loader_rejects_each_v17_seal_mutation(tmp_path: Path, name: str) -> None:
    """An intact older packet cannot rescue any broken link in the accepted v17 seals."""
    root = _repair_loader_fixture(tmp_path)
    _write_json(root / name, {"tampered": True})

    with pytest.raises(ValueError, match="accepted task06e"):
        comparison_module._load_repairs(tmp_path)


def test_repair_loader_never_falls_back_to_v15(tmp_path: Path) -> None:
    """Missing current completion is fatal even when the historical packet is complete."""
    root = _repair_loader_fixture(tmp_path)
    (root / "completion.json").unlink()

    with pytest.raises(ValueError, match="qualification_v17/completion.json"):
        comparison_module._load_repairs(tmp_path)


def test_declared_comparison_checks_cover_all_four_appendix_a_repairs() -> None:
    """Keep the checked template, runtime gate, and synthetic contract aligned."""
    template = json.loads(
        (Path(__file__).parents[1] / "configs/task06/v1/task06g_comparison_v1.json").read_text()
    )
    expected = {f"appendix_a_chapter_{marker}_many_to_one" for marker in ("06", "07", "08", "09")}
    assert expected <= comparison_module.EXPECTED_CHECKS
    assert set(template["required_repair_checks"]) == comparison_module.EXPECTED_CHECKS
    assert set(_fixture()["spec"]["required_repair_checks"]) == comparison_module.EXPECTED_CHECKS


def _appendix_loader_fixture(tmp_path: Path) -> tuple[Path, Path, JsonObject, Path]:
    data_root = tmp_path / "data"
    collection_root = data_root / "pipelines/replay/document_publications"
    document_root = collection_root / "documents/deir_appendix_a/docv1-test"
    structure_id = "exv1-" + "a" * 64
    structure_root = data_root / f"pipelines/replay/document_records/{structure_id}"
    correspondence_path = structure_root / "support/repeated_heading_correspondence.json"
    correspondence = _fixture()["appendix_a_correspondence"]
    _write_json(correspondence_path, correspondence)
    correspondence_ref = reference(correspondence_path, root=data_root)
    manifest_path = structure_root / "records/manifest.json"
    _write_json(
        manifest_path,
        {
            "support_files": [
                {
                    "role": "repeated_heading_correspondence",
                    "path": "support/repeated_heading_correspondence.json",
                    "sha256": correspondence_ref["sha256"],
                    "schema_version": "1.0.0",
                }
            ]
        },
    )
    structure_inventory_path = structure_root / "records/artifact_inventory.json"
    _write_json(
        structure_inventory_path,
        {
            "files": [
                {
                    "path": "support/repeated_heading_correspondence.json",
                    "sha256": correspondence_ref["sha256"],
                    "byte_size": correspondence_ref["byte_size"],
                }
            ]
        },
    )
    structure_completion_path = structure_root / "records/completion_record.json"
    _write_json(
        structure_completion_path,
        {
            "extraction_id": structure_id,
            "repeated_heading_correspondence_count": 4,
        },
    )
    identity_path = document_root / "records/document_identity.json"
    _write_json(
        identity_path,
        {
            "candidate_id": "docv1-test",
            "source": {"source_id": "deir_appendix_a"},
            "stage_completions": {
                "structured_document": {
                    "path": structure_completion_path.relative_to(data_root).as_posix(),
                    "sha256": reference(structure_completion_path)["sha256"],
                }
            },
        },
    )
    identity_ref = reference(identity_path, root=document_root)
    candidate_inventory_path = document_root / "records/artifact_inventory.json"
    _write_json(
        candidate_inventory_path,
        {
            "files": [
                {
                    "path": "records/document_identity.json",
                    "sha256": identity_ref["sha256"],
                    "byte_size": identity_ref["byte_size"],
                }
            ]
        },
    )
    document_completion_path = document_root / "records/completion_record.json"
    _write_json(document_completion_path, {"status": "complete"})
    bundle = {
        "accounting": {
            "rows": [
                {
                    "source_id": "deir_appendix_a",
                    "candidate_id": "docv1-test",
                    "candidate_inventory_ref": reference(
                        candidate_inventory_path, root=collection_root
                    ),
                    "document_completion_ref": reference(
                        document_completion_path, root=collection_root
                    ),
                }
            ]
        }
    }
    return data_root, collection_root, bundle, manifest_path


def _link_loader_fixture(tmp_path: Path) -> tuple[Path, Path, JsonObject, Path]:
    data_root = tmp_path / "data"
    collection_root = data_root / "pipelines/replay/document_publications"
    candidate_root = collection_root / "documents/deir_main/docv1-test"
    ordinary_path = candidate_root / "content/canonical/cross_references.jsonl"
    navigation_path = candidate_root / "content/navigation/decisions.jsonl"
    ordinary_path.parent.mkdir(parents=True, exist_ok=True)
    navigation_path.parent.mkdir(parents=True, exist_ok=True)
    ordinary_path.write_text('{"id":"old/cross-reference/deir_main/xref000001"}\n')
    navigation_path.write_text('{"source_id":"deir_main","navigation_entry_id":"entry-1"}\n')
    inventory_path = candidate_root / "records/artifact_inventory.json"
    _write_json(
        inventory_path,
        {
            "files": [
                {
                    "path": relative,
                    "sha256": reference(candidate_root / relative)["sha256"],
                    "byte_size": reference(candidate_root / relative)["byte_size"],
                }
                for relative in (
                    "content/canonical/cross_references.jsonl",
                    "content/navigation/decisions.jsonl",
                )
            ]
        },
    )
    bundle = {
        "accounting": {
            "rows": [
                {
                    "source_id": "deir_main",
                    "candidate_inventory_ref": reference(inventory_path, root=collection_root),
                }
            ]
        }
    }
    return data_root, collection_root, bundle, inventory_path


def test_build_closes_fixed_and_dynamic_populations_without_source_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture()

    def prohibited(*args: object, **kwargs: object) -> None:
        raise AssertionError("builder attempted filesystem or source access")

    monkeypatch.setattr(Path, "read_text", prohibited)
    monkeypatch.setattr(Path, "read_bytes", prohibited)
    correspondence, comparison = _build(fixture)

    assert correspondence["source_correspondence.json"]["counts"] == {
        "total": 35,
        "preserved": 32,
        "repaired": 2,
        "substituted": 1,
    }
    assert comparison["accounting_comparison.json"]["replacement"]["page_count"] == 49_022
    assert comparison["resolution_comparison.json"]["matched_count"] == 72
    resolution_family = comparison["resolution_comparison.json"]["source_family_catalog_rebinding"]
    assert resolution_family["classification"] == "catalog_rebound"
    assert resolution_family["owner"] == "task06c"
    assert resolution_family["affected_resolution_count"] == 72
    assert {
        row["classification"] for row in comparison["resolution_comparison.json"]["comparisons"]
    } == {"unchanged"}
    links = comparison["link_population_comparison.json"]
    assert links["ordinary"]["counts"] == {"unchanged": 5_088}
    assert links["navigation"]["replacement_resolved_count"] == 410
    assert links["navigation"]["replacement_unresolved_count"] == 150
    assert comparison["reference_comparison.json"]["task04d_controls"] == {
        "ordinary_references": 5_088,
        "navigation_claims": 560,
        "navigation_linked": 410,
        "navigation_unresolved": 150,
        "inherited_task04c_links": 28,
        "inherited_task04c_invalidations": 0,
    }
    assert correspondence["review_correspondence.json"]["task04_status"] == "not_evaluated"


def test_builder_rejects_preserved_semantic_drift() -> None:
    fixture = _fixture()
    replacement = fixture["replacement"]
    assert isinstance(replacement, dict)
    target_index = replacement["target_index"]
    assert isinstance(target_index, dict)
    entries = target_index["entries"]
    assert isinstance(entries, list)
    entries[0]["lookup_key"] = "changed"

    with pytest.raises(ValueError, match="preserved document target semantics changed"):
        _build(fixture)


def test_builder_rejects_catalog_rebinding_beyond_final_f1() -> None:
    """Catalog identity drift is accepted only for the sealed slot-10 substitution."""
    fixture = _fixture()
    catalogs = fixture["source_family_catalogs"]
    assert isinstance(catalogs, dict)
    replacement = catalogs["replacement"]
    assert isinstance(replacement, dict)
    sources = replacement["sources"]
    assert isinstance(sources, list)
    sources[0]["reference_aliases"] = ["unowned alias"]

    with pytest.raises(ValueError, match="catalog delta differs from Final F1 slot"):
        _build(fixture)


def test_builder_rejects_resolution_catalog_binding_mismatch() -> None:
    fixture = _fixture()
    replacement = fixture["replacement"]
    assert isinstance(replacement, dict)
    completion = replacement["resolution_completion"]
    assert isinstance(completion, dict)
    rows = completion["resolutions"]
    assert isinstance(rows, list)
    rows[0]["cross_document_evidence"]["catalog_sha256"] = "unsealed"

    with pytest.raises(ValueError, match="replacement resolution catalog binding differs"):
        _build(fixture)


def test_builder_rejects_astra_unauthorized_figure_48_target_and_resolution() -> None:
    fixture = _fixture()
    replacement = fixture["replacement"]
    baseline = fixture["baseline"]
    assert isinstance(replacement, dict) and isinstance(baseline, dict)
    target_index = replacement["target_index"]
    assert isinstance(target_index, dict)
    entries = target_index["entries"]
    assert isinstance(entries, list)
    entries.append(
        {
            "alias_id": "new/alias/deir_main/invented-figure-4-8",
            "lookup_key": "Figure 4.8",
            "source_id": "deir_main",
            "source_ordinal": 25,
            "target_id": "new/figure/deir_main/invented-figure-4-8",
            "target_type": "figure",
        }
    )
    old_resolution = baseline["resolution_completion"]
    new_resolution = replacement["resolution_completion"]
    assert isinstance(old_resolution, dict) and isinstance(new_resolution, dict)
    old_rows = old_resolution["resolutions"]
    new_rows = new_resolution["resolutions"]
    assert isinstance(old_rows, list) and isinstance(new_rows, list)
    old_rows[0]["candidate_targets"] = [
        {
            "target_id": "old/section/source_01/original",
            "target_source_id": "source_01",
            "target_type": "section",
        }
    ]
    new_rows[0]["candidate_targets"] = [
        {
            "target_id": "new/section/deir_main/unrelated",
            "target_source_id": "deir_main",
            "target_type": "section",
        }
    ]

    with pytest.raises(ValueError, match="unowned target-index added"):
        _build(fixture)


def test_builder_accepts_already_local_production_target_ids_for_f1_substitution() -> None:
    fixture = _fixture()
    baseline = fixture["baseline"]
    replacement = fixture["replacement"]
    assert isinstance(baseline, dict) and isinstance(replacement, dict)
    for bundle, source_id in (
        (baseline, "deir_appendix_f1"),
        (replacement, "feir_appendix_f1"),
    ):
        target_index = bundle["target_index"]
        assert isinstance(target_index, dict)
        entries = target_index["entries"]
        assert isinstance(entries, list)
        row = next(item for item in entries if item["source_id"] == source_id)
        row["target_id"] = f"page/{source_id}/p000014"
        row["target_type"] = "page"

    correspondence, _ = _build(fixture)

    f1_delta = next(
        row
        for row in correspondence["target_correspondence.json"]["changed_sources"]
        if row["logical_source_id"] == "deir_appendix_f1"
    )
    assert f1_delta["removed"][0]["target"]["target_id"] == ("page/deir_appendix_f1/p000014")
    assert f1_delta["added"][0]["target"]["target_id"] == ("page/feir_appendix_f1/p000014")
    assert f1_delta["added"][0]["authorizations"][0]["owner"] == "task06c"


def test_builder_rejects_unowned_collection_resolution_change() -> None:
    fixture = _fixture()
    replacement = fixture["replacement"]
    assert isinstance(replacement, dict)
    resolution = replacement["resolution_completion"]
    assert isinstance(resolution, dict)
    rows = resolution["resolutions"]
    assert isinstance(rows, list)
    rows[0]["candidate_targets"] = [
        {
            "target_id": "new/section/deir_main/unrelated",
            "target_source_id": "deir_main",
            "target_type": "section",
        }
    ]

    with pytest.raises(ValueError, match="unowned collection-resolution delta"):
        _build(fixture)


def test_builder_accepts_each_exact_target_authority_class() -> None:
    fixture = _fixture()
    baseline = fixture["baseline"]
    assert isinstance(baseline, dict)
    target_index = baseline["target_index"]
    assert isinstance(target_index, dict)
    entries = target_index["entries"]
    assert isinstance(entries, list)
    entries.append(
        {
            "alias_id": "old/alias/deir_appendix_a/absorbed-b",
            "lookup_key": "appendix-a-absorbed-b",
            "source_id": "deir_appendix_a",
            "source_ordinal": 18,
            "target_id": "old/section/deir_appendix_a/b",
            "target_type": "section",
        }
    )

    correspondence, _ = _build(fixture)
    changed = correspondence["target_correspondence.json"]["changed_sources"]
    by_source = {row["logical_source_id"]: row for row in changed}
    assert by_source["deir_appendix_a"]["removed"][0]["authorizations"][0]["owner"] == "task06d"
    main_added = by_source["deir_main"]["added"]
    assert {item["authorizations"][0]["owner"] for item in main_added} == {
        "task06e",
        "task06f",
    }
    assert (
        len([item for item in main_added if item["authorizations"][0]["owner"] == "task06f"]) == 178
    )
    assert {
        item["authorizations"][0]["owner"]
        for item in by_source["deir_appendix_f1"]["removed"]
        + by_source["deir_appendix_f1"]["added"]
    } == {"task06c"}


@pytest.mark.parametrize(
    ("marker", "chapter_title"),
    [
        ("8", "Chapter 8 Alternatives"),
        ("9", "Chapter 9 Subsequent EIR Analysis and Findings"),
    ],
)
def test_builder_accepts_task06e_sealed_full_title_alias(marker: str, chapter_title: str) -> None:
    """Task 06E full structural titles authorize only their sealed targets."""
    fixture = _fixture()
    replacement = fixture["replacement"]
    assert isinstance(replacement, dict)
    target_index = replacement["target_index"]
    assert isinstance(target_index, dict)
    entries = target_index["entries"]
    assert isinstance(entries, list)
    entries.append(
        {
            "alias_id": f"new/alias/deir_main/chapter-{marker}-full-title",
            "lookup_key": chapter_title.lower(),
            "source_id": "deir_main",
            "source_ordinal": 25,
            "target_id": f"new/section/deir_main/chapter-{marker}",
            "target_type": "section",
        }
    )

    correspondence, _ = _build(fixture)
    changed = correspondence["target_correspondence.json"]["changed_sources"]
    deir_main = next(row for row in changed if row["logical_source_id"] == "deir_main")
    added = next(
        row for row in deir_main["added"] if row["target"]["lookup_key"] == chapter_title.lower()
    )
    assert added["authorizations"][0]["owner"] == "task06e"
    assert added["authorizations"][0]["evidence"]["chapter_title"] == chapter_title


@pytest.mark.parametrize(
    ("target_id", "target_source_id", "target_type", "expected_owner"),
    [
        ("new/section/deir_appendix_a/a", "deir_appendix_a", "section", "task06d"),
        ("new/section/deir_main/chapter-8", "deir_main", "section", "task06e"),
        ("new/figure/deir_main/fig000001", "deir_main", "figure", "task06f"),
    ],
)
def test_builder_accepts_resolution_changes_to_exact_authorized_targets(
    target_id: str, target_source_id: str, target_type: str, expected_owner: str
) -> None:
    fixture = _fixture()
    replacement = fixture["replacement"]
    assert isinstance(replacement, dict)
    resolution = replacement["resolution_completion"]
    assert isinstance(resolution, dict)
    rows = resolution["resolutions"]
    assert isinstance(rows, list)
    row = rows[0]
    row["candidate_targets"] = [
        {
            "target_id": target_id,
            "target_source_id": target_source_id,
            "target_type": target_type,
        }
    ]
    if expected_owner == "task06e":
        row["lookup_key"] = "chapter 8"
        baseline = fixture["baseline"]
        assert isinstance(baseline, dict)
        old_resolution = baseline["resolution_completion"]
        assert isinstance(old_resolution, dict)
        old_rows = old_resolution["resolutions"]
        assert isinstance(old_rows, list)
        old_rows[0]["lookup_key"] = "chapter 8"
    elif expected_owner == "task06f":
        row["lookup_key"] = "figure 4.8-1"
        baseline = fixture["baseline"]
        assert isinstance(baseline, dict)
        old_resolution = baseline["resolution_completion"]
        assert isinstance(old_resolution, dict)
        old_rows = old_resolution["resolutions"]
        assert isinstance(old_rows, list)
        old_rows[0]["lookup_key"] = "figure 4.8-1"

    _, comparison = _build(fixture)
    changed = [
        row
        for row in comparison["resolution_comparison.json"]["comparisons"]
        if row["classification"] == "changed"
    ]
    assert expected_owner in {item["owner"] for item in changed[0]["authorizations"]}


def test_builder_preserves_authorized_unresolved_resolution_outcome() -> None:
    fixture = _fixture()
    baseline = fixture["baseline"]
    replacement = fixture["replacement"]
    assert isinstance(baseline, dict) and isinstance(replacement, dict)
    for bundle in (baseline, replacement):
        completion = bundle["resolution_completion"]
        assert isinstance(completion, dict)
        rows = completion["resolutions"]
        assert isinstance(rows, list)
        rows[0]["lookup_key"] = "chapter 8"
    replacement_completion = replacement["resolution_completion"]
    assert isinstance(replacement_completion, dict)
    replacement_rows = replacement_completion["resolutions"]
    assert isinstance(replacement_rows, list)
    replacement_rows[0]["candidate_targets"] = []
    replacement_rows[0]["status"] = "unresolved"
    replacement_rows[0]["unresolved_reason"] = "no_local_alias"

    _, comparison = _build(fixture)
    changed = [
        row
        for row in comparison["resolution_comparison.json"]["comparisons"]
        if row["classification"] == "changed"
    ]
    assert changed[0]["replacement"]["status"] == "unresolved"
    assert {item["owner"] for item in changed[0]["authorizations"]} == {"task06e"}


def test_builder_rejects_rebuilt_fc1_entity_mismatch() -> None:
    fixture = _fixture()
    replacement = fixture["replacement"]
    assert isinstance(replacement, dict)
    target_index = replacement["target_index"]
    assert isinstance(target_index, dict)
    entries = target_index["entries"]
    assert isinstance(entries, list)
    entries[:] = [
        row
        for row in entries
        if not (
            row.get("source_id") == "deir_main"
            and row.get("target_type") == "figure"
            and row.get("lookup_key") == "figure 4.8-1"
        )
    ]

    with pytest.raises(ValueError, match="FC1 alias/target edges differ"):
        _build(fixture)


def test_builder_rejects_missing_sealed_many_to_one_correspondence() -> None:
    fixture = _fixture()
    fixture["appendix_a_correspondence"] = {}

    with pytest.raises(ValueError, match="repeated-heading correspondence schema differs"):
        _build(fixture)


@pytest.mark.parametrize("marker", ["06", "07", "08", "09"])
def test_builder_requires_each_accepted_repeated_heading_repair(marker: str) -> None:
    """Every accepted Appendix A repair is an independent comparison obligation."""
    fixture = _fixture()
    task06d = fixture["repairs"]["task06d"]
    task06d["eligible_decisions"] = [
        row for row in task06d["eligible_decisions"] if row["chapter_marker"] != marker
    ]

    with pytest.raises(ValueError, match=f"lacks accepted Chapter {marker}"):
        _build(fixture)


@pytest.mark.parametrize("marker", ["06", "07", "08", "09"])
def test_builder_rejects_changed_repeated_heading_boundary(marker: str) -> None:
    """Every chapter's exact record-order boundary remains independently enforced."""
    fixture = _fixture()
    rows = fixture["repairs"]["task06d"]["eligible_decisions"]
    row = next(row for row in rows if row["chapter_marker"] == marker)
    row["following_boundary_content_order"] += 1

    with pytest.raises(ValueError, match=f"Chapter {marker} invariant differs"):
        _build(fixture)


@pytest.mark.parametrize("marker", ["06", "07", "08", "09"])
def test_builder_rejects_omitted_declared_repair_check(marker: str) -> None:
    """The template cannot silently omit one accepted chapter obligation."""
    fixture = _fixture()
    fixture["spec"]["required_repair_checks"].remove(f"appendix_a_chapter_{marker}_many_to_one")

    with pytest.raises(ValueError, match="required repair checks differ"):
        _build(fixture)


def test_builder_rejects_gate_c_population_drift() -> None:
    fixture = _fixture()
    gate_c = fixture["gate_c"]
    assert isinstance(gate_c, dict)
    navigation = gate_c["navigation"]
    assert isinstance(navigation, dict)
    navigation["resolved_count"] = 409

    with pytest.raises(ValueError, match="Gate C control differs"):
        _build(fixture)


def test_builder_rejects_unowned_local_link_delta() -> None:
    fixture = _fixture()
    link_evidence = fixture["link_evidence"]
    assert isinstance(link_evidence, dict)
    replacement = link_evidence["replacement"]
    assert isinstance(replacement, dict)
    ordinary = replacement["ordinary"]
    assert isinstance(ordinary, list)
    baseline = link_evidence["baseline"]
    assert isinstance(baseline, dict)
    baseline_ordinary = baseline["ordinary"]
    assert isinstance(baseline_ordinary, list)
    baseline_ordinary[0]["id"] = "old/cross-reference/deir_main/xref000001"
    baseline_ordinary[0]["source_id"] = "deir_main"
    ordinary[0]["id"] = "new/cross-reference/deir_main/xref000001"
    ordinary[0]["source_id"] = "deir_main"
    ordinary[0]["unresolved_reason"] = "changed_without_repair"

    with pytest.raises(ValueError, match="unowned ordinary-reference delta"):
        _build(fixture)


def test_builder_rejects_incomplete_navigation_population() -> None:
    fixture = _fixture()
    link_evidence = fixture["link_evidence"]
    assert isinstance(link_evidence, dict)
    replacement = link_evidence["replacement"]
    assert isinstance(replacement, dict)
    navigation = replacement["navigation"]
    assert isinstance(navigation, list)
    navigation.pop()

    with pytest.raises(ValueError, match="exactly 560 old and new claims"):
        _build(fixture)


def test_builder_rejects_inherited_task04c_link_loss() -> None:
    fixture = _fixture()
    link_evidence = fixture["link_evidence"]
    assert isinstance(link_evidence, dict)
    replacement = link_evidence["replacement"]
    assert isinstance(replacement, dict)
    navigation = replacement["navigation"]
    assert isinstance(navigation, list)
    navigation[0]["outcome"] = "no_text_match"
    navigation[0]["candidate_target_ids"] = []

    with pytest.raises(ValueError, match="inherited Task 04C navigation link lost"):
        _build(fixture)


def test_builder_itemizes_source_family_catalog_rebinding_separately() -> None:
    fixture = _fixture()
    link_evidence = fixture["link_evidence"]
    assert isinstance(link_evidence, dict)
    for label, digest in (("baseline", "a" * 64), ("replacement", "b" * 64)):
        evidence = link_evidence[label]
        assert isinstance(evidence, dict)
        ordinary = evidence["ordinary"]
        assert isinstance(ordinary, list)
        ordinary[0]["cross_document_evidence"] = {
            "catalog_sha256": digest,
            "intended_target_source_ids": ["deir_appendix_d"],
            "matched_alias": "appendix d",
            "source_family_id": "brisbane_baylands_2025_deir",
            "traversal_rule": "root_report_to_top_level_appendix",
        }

    _, comparison = _build(fixture)

    family = comparison["link_population_comparison.json"]["source_family_bindings"]
    assert family == [
        {
            "mention_key": "cross-reference/source_01/xref000001",
            "classification": "catalog_rebound",
            "owner": "task06c",
            "baseline_catalog_sha256": "a" * 64,
            "replacement_catalog_sha256": "b" * 64,
        }
    ]


def test_builder_treats_final_f1_as_new_source_without_equivalence() -> None:
    fixture = _fixture()
    link_evidence = fixture["link_evidence"]
    assert isinstance(link_evidence, dict)
    baseline = link_evidence["baseline"]
    replacement = link_evidence["replacement"]
    assert isinstance(baseline, dict) and isinstance(replacement, dict)
    old_rows = baseline["ordinary"]
    new_rows = replacement["ordinary"]
    assert isinstance(old_rows, list) and isinstance(new_rows, list)
    old_rows[0]["id"] = "old/cross-reference/deir_appendix_f1/xref000001"
    old_rows[0]["document_id"] = "old/document/deir_appendix_f1"
    old_rows[0].pop("source_id", None)
    new_rows[0]["id"] = "new/cross-reference/feir_appendix_f1/xref000001"
    new_rows[0]["document_id"] = "new/document/feir_appendix_f1"
    new_rows[0].pop("source_id", None)

    _, comparison = _build(fixture)

    changes = [
        row
        for row in comparison["link_population_comparison.json"]["ordinary"]["rows"]
        if row["classification"] != "unchanged"
    ]
    assert [row["classification"] for row in changes] == ["removed", "added"]
    assert all(row["owners"] == ["task06c"] for row in changes)


def test_builder_owns_main_figure_enablement_without_fabricating_a_target() -> None:
    """Task 06F owns the exact unavailable-to-no-local-alias policy transition."""
    fixture = _fixture()
    link_evidence = fixture["link_evidence"]
    assert isinstance(link_evidence, dict)
    baseline = link_evidence["baseline"]
    replacement = link_evidence["replacement"]
    assert isinstance(baseline, dict) and isinstance(replacement, dict)
    old_row = baseline["ordinary"][0]
    new_row = replacement["ordinary"][0]
    for row in (old_row, new_row):
        row["id"] = row["id"].split("/", 1)[0] + "/cross-reference/deir_main/xref000089"
        row["document_id"] = row["id"].split("/", 1)[0] + "/document/deir_main"
        row["mention_class"] = "figure"
        row["resolution_status"] = "unresolved"
        row["candidates"] = []
        row["cross_document_evidence"] = None
    old_row["unresolved_reason"] = "accepted_target_type_unavailable"
    new_row["unresolved_reason"] = "no_local_alias"

    _, comparison = _build(fixture)

    changed = [
        row
        for row in comparison["link_population_comparison.json"]["ordinary"]["rows"]
        if row["classification"] != "unchanged"
    ]
    assert changed == [
        {
            "mention_key": "cross-reference/deir_main/xref000089",
            "classification": "changed",
            "owners": ["task06f"],
            "baseline": {
                "resolution_status": "unresolved",
                "unresolved_reason": "accepted_target_type_unavailable",
                "candidates": [],
                "source_family_semantics": None,
            },
            "replacement": {
                "resolution_status": "unresolved",
                "unresolved_reason": "no_local_alias",
                "candidates": [],
                "source_family_semantics": None,
            },
        }
    ]


def test_appendix_a_loader_binds_document_structure_seal_and_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root, collection_root, bundle, _ = _appendix_loader_fixture(tmp_path)
    verified: list[tuple[Path, str]] = []

    def verify(root: Path, candidate_id: str) -> Path:
        verified.append((root, candidate_id))
        return root / "records/completion_record.json"

    monkeypatch.setattr(comparison_module, "verify_completed_document_structure", verify)
    correspondence, provenance = _appendix_a_structure_correspondence(
        data_root=data_root,
        collection_root=collection_root,
        bundle=bundle,
    )

    assert correspondence["candidate_id"] == "exv1-" + "a" * 64
    assert len(correspondence["records"]) == 4
    assert verified[0][1] == correspondence["candidate_id"]
    assert provenance["appendix_a_repeated_heading_correspondence"]["sha256"]
    assert provenance["appendix_a_repeated_heading_correspondence"]["authority"] == (
        "artifact_root"
    )
    assert provenance["repeated_heading_correspondence_schema"]["sha256"]
    assert provenance["repeated_heading_correspondence_schema"]["authority"] == "repository"


def test_appendix_a_loader_rejects_support_digest_not_owned_by_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root, collection_root, bundle, manifest_path = _appendix_loader_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_bytes())
    manifest["support_files"][0]["sha256"] = "0" * 64
    _write_json(manifest_path, manifest)
    monkeypatch.setattr(
        comparison_module,
        "verify_completed_document_structure",
        lambda root, candidate_id: root / "records/completion_record.json",
    )

    with pytest.raises(ValueError, match="support checksum differs"):
        _appendix_a_structure_correspondence(
            data_root=data_root,
            collection_root=collection_root,
            bundle=bundle,
        )


def test_link_loader_binds_every_consumed_jsonl_to_candidate_inventory(
    tmp_path: Path,
) -> None:
    data_root, collection_root, bundle, _ = _link_loader_fixture(tmp_path)

    evidence, provenance = load_collection_link_evidence(
        data_root=data_root,
        collection_root=collection_root,
        bundle=bundle,
        label="replacement",
    )

    assert len(evidence["ordinary"]) == 1
    assert len(evidence["navigation"]) == 1
    assert {row["role"] for row in provenance["artifacts"]} == {
        "candidate_inventory",
        "ordinary_references",
        "navigation_decisions",
    }
    assert all(row["authority"] == "artifact_root" for row in provenance["artifacts"])


def test_link_loader_rejects_jsonl_digest_drift(tmp_path: Path) -> None:
    data_root, collection_root, bundle, inventory_path = _link_loader_fixture(tmp_path)
    inventory = json.loads(inventory_path.read_bytes())
    inventory["files"][0]["sha256"] = "0" * 64
    _write_json(inventory_path, inventory)
    bundle["accounting"]["rows"][0]["candidate_inventory_ref"] = reference(
        inventory_path, root=collection_root
    )

    with pytest.raises(ValueError, match="differs from its candidate inventory"):
        load_collection_link_evidence(
            data_root=data_root,
            collection_root=collection_root,
            bundle=bundle,
            label="replacement",
        )


def test_completion_last_publication_is_deterministic_and_no_clobber(tmp_path: Path) -> None:
    records = {"result.json": {"schema_version": "example.v1", "status": "passed"}}
    files = _publication_files(records, "comparison")
    root = tmp_path / "comparison_v1"

    _verify_or_publish(root, files)
    _verify_or_publish(root, files)

    inventory = json.loads((root / "artifact_inventory.json").read_bytes())
    completion = json.loads((root / "completion.json").read_bytes())
    assert [item["path"] for item in inventory["files"]] == ["result.json"]
    assert completion["completion_last"] is True
    assert completion["task04_status"] == "not_evaluated"

    (root / "result.json").write_text("changed\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        _verify_or_publish(root, files)
