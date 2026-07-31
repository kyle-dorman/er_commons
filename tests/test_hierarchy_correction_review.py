"""Held-out annotation and evidence-comparison tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from hierarchy_correction_support import (
    REVIEW_SCHEMA,
    VALID_BUNDLE,
    valid_annotation_bundle,
)
from jsonschema import Draft202012Validator
from PIL import Image
from pypdf import PdfWriter

import er_commons.hierarchy_correction.review_preparation as review_preparation
from er_commons.hierarchy_correction import (
    HierarchyCorrectionContractError,
    build_held_out_evaluation,
    validate_held_out_review_record,
)
from er_commons.hierarchy_correction.review import (
    HeldOutReviewContext,
    prepare_held_out_review,
    seal_held_out_annotations,
    verify_sealed_held_out_annotations,
)


def test_annotation_bundle_has_complete_page_coverage() -> None:
    """Validate schema plus exact annotation coverage and order."""
    annotations = valid_annotation_bundle()
    Draft202012Validator(REVIEW_SCHEMA).validate(annotations)
    validate_held_out_review_record(annotations, expected_pages={73})


def test_evaluation_is_derived_from_annotations_and_candidate() -> None:
    """Build, schema-check, and recount one passing held-out evaluation."""
    evaluation = build_held_out_evaluation(valid_annotation_bundle(), VALID_BUNDLE)
    Draft202012Validator(REVIEW_SCHEMA).validate(evaluation)
    validate_held_out_review_record(evaluation)
    assert evaluation["mismatches"] == []
    assert evaluation["status"] == "pass"


@pytest.mark.parametrize(
    "field_name",
    ["source_sha256", "policy_sha256", "code_bundle_sha256"],
)
def test_annotations_must_match_candidate_identity(field_name: str) -> None:
    """Reject evidence sealed for another source, policy, or code bundle."""
    annotations = copy.deepcopy(valid_annotation_bundle())
    candidate_digest = VALID_BUNDLE["identity"][field_name]
    annotations[field_name] = ("0" if candidate_digest[0] != "0" else "1") * 64

    with pytest.raises(HierarchyCorrectionContractError, match=field_name):
        build_held_out_evaluation(annotations, VALID_BUNDLE)


def test_prepare_and_seal_source_only_heldout_is_ordered_and_no_clobber(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Render only frozen pages, require complete keys, and reverify every byte."""
    source_path = tmp_path / "source.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_blank_page(width=612, height=792)
    with source_path.open("wb") as stream:
        writer.write(stream)
    schema_path = (
        Path(__file__).parents[1]
        / "benchmarks/er_bench/schemas/hierarchy_correction/v1/review.schema.json"
    )
    candidate_id = f"hcorv1-{'a' * 64}"
    context = HeldOutReviewContext(
        candidate_id=candidate_id,
        identity={"policy_sha256": "b" * 64, "code_bundle_sha256": "c" * 64},
        review_root=tmp_path / "review" / candidate_id,
        source_path=source_path,
        source_id="source",
        source_sha256="d" * 64,
        held_out_manifest_sha256="e" * 64,
        selected_pages=(2, 1),
        eligible_keys_by_page={2: ("2" * 64,), 1: ("1" * 64, "3" * 64)},
        review_schema_path=schema_path,
    )
    monkeypatch.setattr(review_preparation, "_load_held_out_context", lambda **_kwargs: context)

    template_path = prepare_held_out_review(data_root=tmp_path, config_path=tmp_path / "x")
    preparation = template_path.parent
    manifest = json.loads((preparation / "render_manifest.json").read_bytes())
    assert [item["physical_page"] for item in manifest["pages"]] == [2, 1]
    assert [item["path"] for item in manifest["pages"]] == [
        "source-p00002.png",
        "source-p00001.png",
    ]
    assert manifest["settings"]["scale"] == 2.0
    assert manifest["settings"]["dpi"] == 144
    assert manifest["settings"]["pixel_mode"] == "RGB"
    assert manifest["settings"]["alpha"] is False
    with Image.open(preparation / "source-p00002.png") as rendered:
        assert rendered.mode == "RGB"
        assert rendered.size == (1224, 1584)
    with pytest.raises(FileExistsError, match="preparation already exists"):
        prepare_held_out_review(data_root=tmp_path, config_path=tmp_path / "x")

    completed = json.loads(template_path.read_bytes())
    assert [page["eligible_item_keys"] for page in completed["pages"]] == [
        ["2" * 64],
        ["1" * 64, "3" * 64],
    ]
    for page in completed["pages"]:
        for annotation in page["annotations"]:
            annotation.update(
                {
                    "expected_boundary": False,
                    "expected_level": None,
                    "expected_parent_key": None,
                    "expected_regime_action": "none",
                    "source_ambiguous": False,
                    "note": "source-only review",
                }
            )
    template_path.write_text(json.dumps(completed))
    seal = seal_held_out_annotations(
        data_root=tmp_path,
        config_path=tmp_path / "x",
        completed_template_path=template_path,
    )
    assert seal.annotations_path.name == "held_out_annotations.json"
    assert seal.seal_path.name == "held_out_annotations.seal.json"
    assert (
        verify_sealed_held_out_annotations(
            data_root=tmp_path,
            config_path=tmp_path / "x",
            candidate_id=candidate_id,
        ).annotation_bundle_sha256
        == seal.annotation_bundle_sha256
    )
    with pytest.raises(FileExistsError, match="annotations or seal already exists"):
        seal_held_out_annotations(
            data_root=tmp_path,
            config_path=tmp_path / "x",
            completed_template_path=template_path,
        )


def test_seal_rejects_changed_source_render(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Never accept an annotation after its source-only render bytes change."""
    source_path = tmp_path / "source.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with source_path.open("wb") as stream:
        writer.write(stream)
    candidate_id = f"hcorv1-{'a' * 64}"
    context = HeldOutReviewContext(
        candidate_id=candidate_id,
        identity={"policy_sha256": "b" * 64, "code_bundle_sha256": "c" * 64},
        review_root=tmp_path / "review" / candidate_id,
        source_path=source_path,
        source_id="source",
        source_sha256="d" * 64,
        held_out_manifest_sha256="e" * 64,
        selected_pages=(1,),
        eligible_keys_by_page={1: ("1" * 64,)},
        review_schema_path=(
            Path(__file__).parents[1]
            / "benchmarks/er_bench/schemas/hierarchy_correction/v1/review.schema.json"
        ),
    )
    monkeypatch.setattr(review_preparation, "_load_held_out_context", lambda **_kwargs: context)
    template_path = prepare_held_out_review(data_root=tmp_path, config_path=tmp_path / "x")
    completed = json.loads(template_path.read_bytes())
    completed["pages"][0]["annotations"][0].update(
        {
            "expected_boundary": False,
            "expected_regime_action": "none",
            "source_ambiguous": False,
        }
    )
    template_path.write_text(json.dumps(completed))
    (template_path.parent / "source-p00001.png").write_bytes(b"changed")

    with pytest.raises(ValueError, match="render checksum differs"):
        seal_held_out_annotations(
            data_root=tmp_path,
            config_path=tmp_path / "x",
            completed_template_path=template_path,
        )
