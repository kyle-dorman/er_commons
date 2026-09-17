"""Focused source-free tests for Task 06H substantive evidence proofs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from er_commons.human_review_support.extraction_review.task06h_evidence import (
    map_eligible_figures,
    prove_task04_reuse,
    stable_entity_suffix,
)


def test_stable_entity_suffix_rejects_raw_or_incomplete_ids() -> None:
    assert stable_entity_suffix("exv1-old/block/source/blk000001") == ("block/source/blk000001")
    with pytest.raises(ValueError, match="no stable suffix"):
        stable_entity_suffix("blk000001")


def test_task04_reuse_proves_namespaced_records_by_substance(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    selected = tmp_path / "selected"
    old_id = "docv1-old"
    new_id = "docv1-new"
    _candidate(baseline, "source", old_id, "exv1-old")
    selected_root = _candidate(selected, "source", new_id, "exv1-new")
    completion_sha = _sha256(selected_root / "records/completion_record.json")

    result = prove_task04_reuse(
        [_review_row(old_id)],
        [_source_row(new_id, completion_sha)],
        baseline_publications_root=baseline,
        selected_publications_root=selected,
        accepted_policy_digest="same",
        current_policy_digest="same",
        expected_unchanged=1,
    )

    assert result[0]["correspondence_result"] == "reused_remapped_equivalent"
    assert result[0]["substantive_evidence_equal"] is True
    assert result[0]["page_mapping"]["baseline_id"].startswith("exv1-old/")
    assert result[0]["page_mapping"]["selected_id"].startswith("exv1-new/")


def test_task04_reuse_fails_closed_for_content_or_policy_change(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    selected = tmp_path / "selected"
    old_id = "docv1-old"
    new_id = "docv1-new"
    _candidate(baseline, "source", old_id, "exv1-old")
    selected_root = _candidate(selected, "source", new_id, "exv1-new", text="changed")
    completion_sha = _sha256(selected_root / "records/completion_record.json")

    content_result = prove_task04_reuse(
        [_review_row(old_id)],
        [_source_row(new_id, completion_sha)],
        baseline_publications_root=baseline,
        selected_publications_root=selected,
        accepted_policy_digest="same",
        current_policy_digest="same",
        expected_unchanged=1,
    )
    policy_result = prove_task04_reuse(
        [_review_row(old_id)],
        [_source_row(new_id, completion_sha)],
        baseline_publications_root=baseline,
        selected_publications_root=selected,
        accepted_policy_digest="old",
        current_policy_digest="new",
        expected_unchanged=1,
    )

    assert content_result[0]["correspondence_result"] == "new_review_required"
    assert content_result[0]["substantive_evidence_equal"] is False
    assert policy_result[0]["correspondence_result"] == "new_review_required"
    assert policy_result[0]["policy_compatible"] is False


def test_task04_reuse_closes_page_figure_image_and_asset_metadata(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    selected = tmp_path / "selected"
    old_root = _candidate(baseline, "source", "docv1-old", "exv1-old")
    new_root = _candidate(selected, "source", "docv1-new", "exv1-new")
    _add_visual(old_root, "exv1-old", asset_path="old/content.png")
    _add_visual(new_root, "exv1-new", asset_path="new/content.png")

    result = prove_task04_reuse(
        [_review_row("docv1-old")],
        [_source_row("docv1-new", _sha256(new_root / "records/completion_record.json"))],
        baseline_publications_root=baseline,
        selected_publications_root=selected,
        accepted_policy_digest="same",
        current_policy_digest="same",
        expected_unchanged=1,
    )

    assert result[0]["correspondence_result"] == "reused_remapped_equivalent"
    assert len(result[0]["entity_mappings"]["figures"]) == 1
    assert len(result[0]["entity_mappings"]["images"]) == 1
    assert len(result[0]["entity_mappings"]["assets"]) == 1

    asset_path = new_root / "content/canonical/assets.jsonl"
    asset = json.loads(asset_path.read_text(encoding="utf-8"))
    asset["sha256"] = "b" * 64
    _write_jsonl(asset_path, [asset])
    _reseal(new_root)
    changed = prove_task04_reuse(
        [_review_row("docv1-old")],
        [_source_row("docv1-new", _sha256(new_root / "records/completion_record.json"))],
        baseline_publications_root=baseline,
        selected_publications_root=selected,
        accepted_policy_digest="same",
        current_policy_digest="same",
        expected_unchanged=1,
    )
    assert changed[0]["correspondence_result"] == "new_review_required"


def test_task04_reuse_verifies_selected_completion_and_inventory(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    selected = tmp_path / "selected"
    _candidate(baseline, "source", "docv1-old", "exv1-old")
    selected_root = _candidate(selected, "source", "docv1-new", "exv1-new")
    inventory = selected_root / "records/artifact_inventory.json"
    inventory.write_text('{"files":[],"tampered":true}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="inventory reference differs"):
        prove_task04_reuse(
            [_review_row("docv1-old")],
            [_source_row("docv1-new", _sha256(selected_root / "records/completion_record.json"))],
            baseline_publications_root=baseline,
            selected_publications_root=selected,
            accepted_policy_digest="same",
            current_policy_digest="same",
            expected_unchanged=1,
        )


def test_task04_reuse_returns_finite_ambiguous_mapping_result(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    selected = tmp_path / "selected"
    _candidate(baseline, "source", "docv1-old", "exv1-old")
    selected_root = _candidate(selected, "source", "docv1-new", "exv1-new")
    blocks = selected_root / "content/canonical/blocks.jsonl"
    row = json.loads(blocks.read_text(encoding="utf-8"))
    _write_jsonl(blocks, [row, row])
    _reseal(selected_root)

    result = prove_task04_reuse(
        [_review_row("docv1-old")],
        [_source_row("docv1-new", _sha256(selected_root / "records/completion_record.json"))],
        baseline_publications_root=baseline,
        selected_publications_root=selected,
        accepted_policy_digest="same",
        current_policy_digest="same",
        expected_unchanged=1,
    )

    assert result[0]["correspondence_result"] == "rejected_ambiguous"
    assert result[0]["result_status"] == "finite_result"


def test_eligible_figure_mapping_binds_marker_caption_image_and_page(tmp_path: Path) -> None:
    publications = tmp_path / "selected"
    root = _candidate(publications, "deir_main", "docv1-main", "exv1-new")
    canonical = root / "content/canonical"
    prefix = "exv1-new"
    _write_jsonl(
        canonical / "figures.jsonl",
        [
            {
                "id": f"{prefix}/figure/deir_main/fig000001",
                "caption_block_ids": [f"{prefix}/block/deir_main/blk000001"],
                "image_ids": [f"{prefix}/image/deir_main/img000001"],
                "content_layer": "body",
                "is_toc_row": False,
                "regions": [{"page_id": f"{prefix}/page/deir_main/p000007"}],
            }
        ],
    )
    _write_jsonl(
        canonical / "blocks.jsonl",
        [
            {
                "id": f"{prefix}/block/deir_main/blk000001",
                "canonical_text": "Figure 4.8-5: Exact marker",
                "block_type": "caption",
                "content_layer": "body",
                "is_toc_row": False,
                "regions": [{"page_id": f"{prefix}/page/deir_main/p000007"}],
            }
        ],
    )
    _write_jsonl(
        canonical / "images.jsonl",
        [
            {
                "id": f"{prefix}/image/deir_main/img000001",
                "regions": [{"page_id": f"{prefix}/page/deir_main/p000007"}],
            }
        ],
    )
    _write_jsonl(
        canonical / "pages.jsonl",
        [{"id": f"{prefix}/page/deir_main/p000007", "physical_page_number": 7}],
    )
    _reseal(root)
    decision = _figure_decision("figqualv1-q")

    result = map_eligible_figures(
        {"decisions": [decision]},
        selected_candidate_root=root,
        expected_candidate_id="docv1-main",
        expected_count=1,
    )

    assert result[0]["attachment_status"] == "verified"
    assert result[0]["raw_marker"] == "Figure 4.8-5"
    assert result[0]["stable_figure_suffix"] == "figure/deir_main/fig000001"


def test_eligible_figure_mapping_rejects_truncated_marker(tmp_path: Path) -> None:
    publications = tmp_path / "selected"
    root = _candidate(publications, "deir_main", "docv1-main", "exv1-new")
    canonical = root / "content/canonical"
    prefix = "exv1-new"
    rows = {
        "figures": [
            {
                "id": f"{prefix}/figure/deir_main/fig000001",
                "caption_block_ids": [f"{prefix}/block/deir_main/blk000001"],
                "image_ids": [f"{prefix}/image/deir_main/img000001"],
                "content_layer": "body",
                "is_toc_row": False,
                "regions": [{"page_id": f"{prefix}/page/deir_main/p000007"}],
            }
        ],
        "blocks": [
            {
                "id": f"{prefix}/block/deir_main/blk000001",
                "canonical_text": "Figure 4.8: Wrong truncated marker",
                "block_type": "caption",
                "content_layer": "body",
                "is_toc_row": False,
                "regions": [{"page_id": f"{prefix}/page/deir_main/p000007"}],
            }
        ],
        "images": [
            {
                "id": f"{prefix}/image/deir_main/img000001",
                "regions": [{"page_id": f"{prefix}/page/deir_main/p000007"}],
            }
        ],
        "pages": [{"id": f"{prefix}/page/deir_main/p000007", "physical_page_number": 7}],
    }
    for name, values in rows.items():
        _write_jsonl(canonical / f"{name}.jsonl", values)
    _reseal(root)

    with pytest.raises(ValueError, match="attachment proof failed"):
        map_eligible_figures(
            {"decisions": [_figure_decision("figqualv1-q")]},
            selected_candidate_root=root,
            expected_candidate_id="docv1-main",
            expected_count=1,
        )


def _review_row(candidate_id: str) -> dict[str, object]:
    return {
        "entry_id": "tocpagev1-one",
        "source_id": "source",
        "classification": "unchanged",
        "baseline_evidence": {
            "candidate_id": candidate_id,
            "physical_page": 1,
            "disposition": "toc",
            "entity_ids_by_kind": {
                "blocks": ["exv1-old/block/source/blk000001"],
                "sections": ["exv1-old/section/source/sec000001"],
                "tables": ["exv1-old/table/source/tbl000001"],
            },
        },
    }


def _source_row(candidate_id: str, completion_sha: str) -> dict[str, object]:
    return {
        "logical_source_id": "source",
        "replacement_candidate_id": candidate_id,
        "replacement_completion_ref": {"sha256": completion_sha},
    }


def _candidate(
    publications: Path,
    source_id: str,
    candidate_id: str,
    namespace: str,
    *,
    text: str = "same text",
) -> Path:
    root = publications / "documents" / source_id / candidate_id
    canonical = root / "content/canonical"
    records = root / "records"
    canonical.mkdir(parents=True)
    records.mkdir()
    page_id = f"{namespace}/page/{source_id}/p000001"
    _write_jsonl(
        canonical / "pages.jsonl",
        [
            {
                "id": page_id,
                "extraction_id": namespace,
                "physical_page_number": 1,
                "ordered_content_ids": [f"{namespace}/block/{source_id}/blk000001"],
            }
        ],
    )
    common = {"extraction_id": namespace, "regions": [{"page_id": page_id}]}
    _write_jsonl(
        canonical / "blocks.jsonl",
        [{"id": f"{namespace}/block/{source_id}/blk000001", "canonical_text": text, **common}],
    )
    _write_jsonl(
        canonical / "sections.jsonl",
        [{"id": f"{namespace}/section/{source_id}/sec000001", "title": "section", **common}],
    )
    _write_jsonl(
        canonical / "tables.jsonl",
        [{"id": f"{namespace}/table/{source_id}/tbl000001", "cells": [["value"]], **common}],
    )
    for name in ("figures", "images", "assets"):
        _write_jsonl(canonical / f"{name}.jsonl", [])
    inventory = records / "artifact_inventory.json"
    managed = []
    for name in ("pages", "blocks", "sections", "tables", "figures", "images", "assets"):
        path = canonical / f"{name}.jsonl"
        managed.append(
            {
                "path": path.relative_to(root).as_posix(),
                "byte_size": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    inventory.write_text(json.dumps({"files": managed}) + "\n", encoding="utf-8")
    completion = {
        "candidate_id": candidate_id,
        "completion_last": True,
        "raw_docling_status": "SUCCESS",
        "source": {"source_id": source_id},
        "candidate_inventory": {"sha256": _sha256(inventory)},
    }
    (records / "completion_record.json").write_text(
        json.dumps(completion, sort_keys=True) + "\n", encoding="utf-8"
    )
    return root


def _figure_decision(namespace: str) -> dict[str, object]:
    return {
        "eligibility": "eligible",
        "figure_id": f"{namespace}/figure/deir_main/fig000001",
        "upstream_figure_id": "exv1-old/figure/deir_main/fig000001",
        "caption_block_ids": [f"{namespace}/block/deir_main/blk000001"],
        "image_ids": [f"{namespace}/image/deir_main/img000001"],
        "page_id": f"{namespace}/page/deir_main/p000007",
        "physical_page_number": 7,
        "caption_text": "Figure 4.8-5: Exact marker",
        "raw_marker": "Figure 4.8-5",
        "classification": {
            "figure_content_layer": "body",
            "figure_is_toc_row": False,
            "caption_content_layer": "body",
            "caption_is_toc_row": False,
        },
    }


def _add_visual(root: Path, namespace: str, *, asset_path: str) -> None:
    canonical = root / "content/canonical"
    page_path = canonical / "pages.jsonl"
    page = json.loads(page_path.read_text(encoding="utf-8"))
    page["ordered_content_ids"].append(f"{namespace}/figure/source/fig000001")
    _write_jsonl(page_path, [page])
    region = {"page_id": f"{namespace}/page/source/p000001"}
    _write_jsonl(
        canonical / "figures.jsonl",
        [
            {
                "id": f"{namespace}/figure/source/fig000001",
                "extraction_id": namespace,
                "image_ids": [f"{namespace}/image/source/img000001"],
                "caption_block_ids": [],
                "regions": [region],
            }
        ],
    )
    _write_jsonl(
        canonical / "images.jsonl",
        [
            {
                "id": f"{namespace}/image/source/img000001",
                "extraction_id": namespace,
                "asset_id": f"{namespace}/asset/source/content_image/ast000001",
                "regions": [region],
            }
        ],
    )
    _write_jsonl(
        canonical / "assets.jsonl",
        [
            {
                "id": f"{namespace}/asset/source/content_image/ast000001",
                "extraction_id": namespace,
                "path": asset_path,
                "byte_size": 10,
                "media_type": "image/png",
                "producer": "docling",
                "role": "content_image",
                "sha256": "a" * 64,
            }
        ],
    )
    _reseal(root)


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8"
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reseal(root: Path) -> None:
    """Update the synthetic candidate seals after a deliberate fixture edit."""
    inventory = root / "records/artifact_inventory.json"
    value = json.loads(inventory.read_text(encoding="utf-8"))
    for row in value["files"]:
        path = root / row["path"]
        row["byte_size"] = path.stat().st_size
        row["sha256"] = _sha256(path)
    inventory.write_text(json.dumps(value) + "\n", encoding="utf-8")
    completion = root / "records/completion_record.json"
    record = json.loads(completion.read_text(encoding="utf-8"))
    record["candidate_inventory"]["sha256"] = _sha256(inventory)
    completion.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
