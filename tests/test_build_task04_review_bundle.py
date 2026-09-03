from __future__ import annotations

import json
from importlib.metadata import version
from pathlib import Path

import pytest
from task04_test_support import (
    AcceptingCandidateVerifier,
    FailingRenderer,
    FakeRenderer,
    fake_page_evidence,
    make_synthetic_review_tree,
    synthetic_build_request,
)

from er_commons.document_parsing.content_parsing.routing_geometry import DisplayedPageTransform
from er_commons.human_review_support.task04 import build_review_bundle
from er_commons.human_review_support.task04.geometry import (
    bboxes_overlap,
    canonical_region_display_bbox,
    review_display_bbox,
)
from er_commons.human_review_support.task04.json_io import (
    read_json_object,
    require_list,
    require_mapping,
    require_string,
)
from er_commons.human_review_support.task04.models import (
    BlockEvidence,
    JsonValue,
    PageEvidence,
    ParserAttempt,
    ParserPageEvidence,
    TableEvidence,
    TableParserEvidence,
)
from er_commons.human_review_support.task04.presentation import (
    render_page_comparison,
    render_parser_evidence,
)


def test_build_publishes_valid_separated_selection_and_render_evidence(tmp_path: Path) -> None:
    tree = make_synthetic_review_tree(tmp_path)
    verifier = AcceptingCandidateVerifier()

    output = build_review_bundle(
        synthetic_build_request(tree),
        renderer=FakeRenderer(),
        page_evidence_loader=fake_page_evidence,
        candidate_verifier=verifier,
    )

    selection = _read_json(output / "records/selection_manifest.json")
    inventory = _read_json(output / "records/input_inventory.json")
    manifest = _read_json(output / "records/review_bundle_manifest.json")
    sources = require_list(inventory["sources"], path="$.sources")
    source = require_mapping(sources[0], path="$.sources[0]")
    assert output.name == selection["review_run_id"]
    assert "render_bindings" not in selection
    assert "rendered_pages" not in json.dumps(selection)
    assert manifest["render"] == {
        "renderer": "fake-renderer",
        "renderer_version": "1.2.3",
        "scale": 1.0,
        "rendered_page_count": 1,
    }
    assert manifest["package_versions"] == {
        "er-commons": version("er-commons"),
        "fake-renderer": "1.2.3",
        "jsonschema": version("jsonschema"),
        "Pillow": version("Pillow"),
        "pypdf": version("pypdf"),
        "pypdfium2": version("pypdfium2"),
        "rfc8785": version("rfc8785"),
    }
    identity = require_mapping(manifest["identity"], path="$.identity")
    dependencies = [
        require_mapping(row, path=f"$.identity.dependencies[{index}]")
        for index, row in enumerate(
            require_list(identity["dependencies"], path="$.identity.dependencies")
        )
    ]
    dependency_names = {row["name"] for row in dependencies}
    assert dependency_names == {
        "artifact_io_canonical_hashing",
        "document_publication_records",
        "document_publication_verification",
        "er-commons",
        "fake-renderer",
        "jsonschema",
        "Pillow",
        "pypdf",
        "pypdfium2",
        "rfc8785",
        "routing_displayed_page_transform",
        "task04_assets",
        "task04_package",
        "task04_schemas",
    }
    for dependency in dependencies:
        if dependency["kind"] == "package":
            assert dependency["version"]
            assert dependency["path"] is None
            assert dependency["sha256"] is None
        else:
            assert dependency["path"]
            assert (
                len(require_string(dependency["sha256"], path="$.identity.dependencies[].sha256"))
                == 64
            )
            assert dependency["version"] is None
    assert identity["selected_sources"] == [
        {
            "source_id": "appendix_a",
            "source_pdf_sha256": source["sha256"],
            "candidate_id": f"docv1-{'a' * 64}",
            "completion_sha256": "c" * 64,
            "inventory_sha256": "b" * 64,
        }
    ]
    bindings = require_list(manifest["render_bindings"], path="$.render_bindings")
    items = require_list(selection["items"], path="$.items")
    binding = require_mapping(bindings[0], path="$.render_bindings[0]")
    item = require_mapping(items[0], path="$.items[0]")
    assert binding["review_item_id"] == item["review_item_id"]
    assert source["selected_completion_sha256"] == "c" * 64
    assert source["selected_inventory_sha256"] == "b" * 64
    assert source["source_pdf_sha256"] == source["sha256"]
    assert verifier.sources[0].source_id == "appendix_a"
    assert manifest["mutable_records"] == [
        "records/finding_register.json",
        "records/task03i_handoff.json",
    ]
    managed_paths = {
        require_mapping(row, path=f"$.files[{index}]")["path"]
        for index, row in enumerate(require_list(manifest["files"], path="$.files"))
    }
    assert "records/finding_register.json" not in managed_paths
    assert "records/task03i_handoff.json" not in managed_paths
    assert (output / "html/review.css").is_file()
    assert (output / "html/review.js").is_file()
    assert not any(tree.output_root.joinpath(".tmp").iterdir())


def test_positive_toc_asset_shows_explicit_reviewed_state() -> None:
    asset = Path("src/er_commons/human_review_support/task04/assets/review.js").read_text()

    assert "click to clear" in asset
    assert "button.dataset.runSuffixEntryIds" in asset
    assert "delete tocState[button.dataset.entryId]" in asset
    assert 'requiredElement("#hide-reviewed")' in asset


def test_failed_render_removes_unpublished_staging(tmp_path: Path) -> None:
    tree = make_synthetic_review_tree(tmp_path)

    with pytest.raises(RuntimeError, match="synthetic render failure"):
        build_review_bundle(
            synthetic_build_request(tree),
            renderer=FailingRenderer(),
            page_evidence_loader=fake_page_evidence,
            candidate_verifier=AcceptingCandidateVerifier(),
        )

    assert not list(tree.output_root.glob("reviewv1-*"))
    assert not any(tree.output_root.joinpath(".tmp").iterdir())


def test_review_display_bbox_rotates_native_text_into_landscape_frame() -> None:
    transform = DisplayedPageTransform.create(
        (792.0, 612.0),
        (0.0, 0.0, 612.0, 792.0),
        90,
    )

    assert review_display_bbox(
        [81.184616, 9.787739, 93.525192, 278.870148], transform
    ) == pytest.approx((9.787739, 518.474808, 278.870148, 530.815384))


def test_canonical_display_bbox_does_not_double_rotate_landscape_region() -> None:
    transform = DisplayedPageTransform.create(
        (792.0, 612.0),
        (0.0, 0.0, 612.0, 792.0),
        90,
    )
    region = {
        "bbox": [9.95, 168.32, 263.01, 180.66],
        "page_width": 792.0,
        "page_height": 612.0,
        "rotation_degrees": 0,
    }

    assert canonical_region_display_bbox(region, 792.0, 612.0, transform) == (
        9.95,
        168.32,
        263.01,
        180.66,
    )


def test_parser_presenter_names_every_attempt() -> None:
    evidence = TableParserEvidence(
        pages=(
            ParserPageEvidence(
                physical_page=974,
                route="full_page_numeric",
                detected_table_count=1,
                producer_table_count=1,
                selected_parser_counts=(("camelot_stream", 1),),
                attempts=(ParserAttempt("Camelot Stream", "retained", {"returned": 3}),),
            ),
        ),
        scope="every selected page in this table family",
        page_details_open=False,
    )

    markup = render_parser_evidence(evidence)

    assert "Parsers represented:</strong> Camelot Stream" in markup
    assert "returned 3" in markup
    assert "every selected page in this table family" in markup


def test_page_presenter_puts_table_before_overlapping_text() -> None:
    evidence = PageEvidence(
        physical_page=974,
        width=1224.0,
        height=792.0,
        printed_page_label=None,
        blocks=(BlockEvidence("block-1", "paragraph", "A", (749.0, 700.0, 751.0, 704.0), 1, True),),
        tables=(
            TableEvidence(
                "table-1",
                None,
                "camelot_stream",
                (2, 2),
                ({"row_index": 0, "column_index": 0, "text": "Header"},),
                (40.0, 46.0, 1167.0, 747.0),
                0,
            ),
        ),
    )

    markup = render_page_comparison("page.png", evidence)

    assert markup.index("Header") < markup.index("1 canonical text blocks overlap")
    assert 'class="page-surface" style="--page-ratio: 1.54545455"' in markup


def test_bbox_overlap_rejects_malformed_and_touching_boxes() -> None:
    assert bboxes_overlap((0.0, 0.0, 1.0, 1.0), (0.5, 0.5, 2.0, 2.0))
    assert not bboxes_overlap((0.0, 0.0, 1.0, 1.0), (1.0, 0.0, 2.0, 1.0))
    assert not bboxes_overlap(None, (0.0, 0.0, 1.0, 1.0))


def _read_json(path: Path) -> dict[str, JsonValue]:
    return read_json_object(path)
