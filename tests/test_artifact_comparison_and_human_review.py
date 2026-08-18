from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path

import pytest

from er_commons.artifact_comparison import compare_candidate_files, compare_table_evidence
from er_commons.human_review_support import (
    GeneratedReviewManifest,
    GeneratedReviewOutput,
    RenderPlan,
    RenderRecipe,
    ReviewArtifactInput,
    ReviewSelection,
    build_hierarchy_authorization_review,
    write_generated_review_manifest,
    write_hierarchy_authorization_review,
)


def _jsonl(path: Path, records: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def test_candidate_comparison_is_read_only_and_explicit_about_ignored_files(tmp_path: Path) -> None:
    before, after = tmp_path / "before", tmp_path / "after"
    before.mkdir()
    after.mkdir()
    (before / "records.jsonl").write_text("same\n")
    (after / "records.jsonl").write_text("same\n")
    (before / "identity.json").write_text("old\n")
    (after / "identity.json").write_text("new\n")
    result = compare_candidate_files(before, after, ignored_paths=frozenset({"identity.json"}))
    assert result["equivalent"] is True


def test_candidate_comparison_normalizes_only_declared_identifiers(tmp_path: Path) -> None:
    before, after = tmp_path / "before", tmp_path / "after"
    before.mkdir()
    after.mkdir()
    (before / "record.json").write_text('{"run_id":"prv1-old","value":3}\n')
    (after / "record.json").write_text('{"run_id":"prv1-new","value":3}\n')

    result = compare_candidate_files(
        before,
        after,
        identifier_replacements=(
            ("prv1-old", "{producer_run_id}"),
            ("prv1-new", "{producer_run_id}"),
        ),
    )

    assert result["equivalent"] is True


def test_table_comparison_covers_pages_tables_families_and_regions(tmp_path: Path) -> None:
    before, after = tmp_path / "before", tmp_path / "after"
    page = {
        "physical_pdf_page": 1,
        "route": "layout_regions",
        "complex_page": True,
        "ruling_region_count": 2,
        "table_count": 1,
        "footer": None,
        "footer_owner_table_id": None,
    }
    table = {
        "table_id": "t1",
        "physical_pdf_page": 1,
        "page_table_index": 1,
        "route": "layout_regions",
        "parser": "camelot_lattice",
        "parser_order": 1,
        "region_id": "r1",
        "bbox_pdf_points_bottom_left": [0, 0, 1, 1],
        "shape_raw": [1, 1],
        "shape_clean": [1, 1],
        "columns_pdf_points": [],
        "cleanup": {},
        "header_matrix": [],
        "clean_csv": {"sha256": "a"},
    }
    assignment = {"table_id": "t1", "family_id": "f1", "footer_owned": False}
    for root in (before, after):
        _jsonl(root / "pages.jsonl", [page])
        _jsonl(root / "tables.jsonl", [table])
        _jsonl(root / "family_assignments.jsonl", [assignment])
    assert compare_table_evidence(before, after)["exact_semantic_match"] is True


def test_requested_page_comparison_excludes_other_page_family_assignments(tmp_path: Path) -> None:
    before, after = tmp_path / "before", tmp_path / "after"
    pages = [
        {
            "physical_pdf_page": page,
            "route": "r",
            "complex_page": False,
            "ruling_region_count": 0,
            "table_count": 1,
            "footer": None,
            "footer_owner_table_id": None,
        }
        for page in (1, 2)
    ]
    tables = [
        {
            "table_id": f"t{page}",
            "physical_pdf_page": page,
            "page_table_index": 1,
            "route": "r",
            "parser": "p",
            "parser_order": 1,
            "region_id": f"r{page}",
            "bbox_pdf_points_bottom_left": [0, 0, 1, 1],
            "shape_raw": [1, 1],
            "shape_clean": [1, 1],
            "columns_pdf_points": [],
            "cleanup": {},
            "header_matrix": [],
            "clean_csv": {"sha256": "a"},
        }
        for page in (1, 2)
    ]
    for root in (before, after):
        _jsonl(root / "pages.jsonl", pages)
        _jsonl(root / "tables.jsonl", tables)
    _jsonl(
        before / "family_assignments.jsonl",
        [
            {"table_id": "t1", "family_id": "same", "footer_owned": False},
            {"table_id": "t2", "family_id": "old", "footer_owned": False},
        ],
    )
    _jsonl(
        after / "family_assignments.jsonl",
        [
            {"table_id": "t1", "family_id": "same", "footer_owned": False},
            {"table_id": "t2", "family_id": "new", "footer_owned": False},
        ],
    )

    requested = compare_table_evidence(before, after, physical_pages=frozenset({1}))
    exact = compare_table_evidence(before, after)

    assert requested["exact_semantic_match"] is True
    assert exact["exact_semantic_match"] is False


def test_review_manifest_is_disposable_and_checksummed(tmp_path: Path) -> None:
    output = tmp_path / "page.png"
    output.write_bytes(b"render")
    path = write_generated_review_manifest(
        tmp_path,
        manifest=GeneratedReviewManifest(
            selection=ReviewSelection("exv1-test", "source", (1,), ("page", "table")),
            recipe=RenderRecipe(
                renderer="review-render",
                renderer_version="1.2.3",
                arguments=("--page", "1"),
                inputs=(ReviewArtifactInput("source_pdf", "sources/source.pdf", "a" * 64),),
            ),
            outputs=(GeneratedReviewOutput(output, 1, "page"),),
        ),
    )
    manifest = json.loads(path.read_text())
    assert manifest["schema_version"] == "er_commons.requested_review_manifest.v1"
    assert manifest["disposition"] == "disposable_outside_candidate_identity"
    assert manifest["files"][0]["path"] == "page.png"
    assert manifest["files"][0]["physical_page"] == 1
    assert manifest["recipe"]["renderer_version"] == "1.2.3"


def test_requested_and_generated_review_models_share_one_validated_selection(
    tmp_path: Path,
) -> None:
    selection = ReviewSelection("candidate", "source", (1, 3), ("page", "table"))
    recipe = RenderRecipe(
        "renderer",
        "1",
        ("--page", "1"),
        (ReviewArtifactInput("pdf", "source.pdf", "a" * 64),),
    )
    plan = RenderPlan("scope", (selection,))
    manifest = GeneratedReviewManifest(
        selection,
        recipe,
        (GeneratedReviewOutput(tmp_path / "page.png", 1, "page"),),
    )

    assert plan.selections[0] is selection
    assert manifest.selection is selection
    with pytest.raises(ValueError, match="output page was not selected"):
        GeneratedReviewManifest(
            selection,
            recipe,
            (GeneratedReviewOutput(tmp_path / "page-2.png", 2, "page"),),
        )


def test_hierarchy_authorization_review_is_exact_and_non_authoritative(
    tmp_path: Path,
) -> None:
    previous = {
        "candidate": {"identity": {"candidate_id": "hcorv1-old", "config_sha256": "a"}},
        "scope": {"source_id": "appendix_p", "corpus_wide_acceptance": False},
        "limitations": ["known_limit"],
    }
    report = build_hierarchy_authorization_review(
        candidate_identity={"candidate_id": "hcorv1-new", "config_sha256": "b"},
        prior_authorization=previous,
        policy_sha256="c" * 64,
        expected_semantic_sha256="d" * 64,
        observed_semantic_sha256="d" * 64,
        expected_counts={"features": 3},
        observed_counts={"features": 3},
    )
    path = write_hierarchy_authorization_review(tmp_path / "review.json", report)
    persisted = json.loads(path.read_text())

    assert persisted["review_status"] == "ready_for_user_review"
    assert persisted["publication_authority"] is False
    assert persisted["task04_status"] == "not_evaluated"
    assert [item["field"] for item in persisted["identity_changes"]] == [
        "candidate_id",
        "config_sha256",
    ]
