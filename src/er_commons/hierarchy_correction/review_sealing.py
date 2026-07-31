"""Held-out annotation sealing and pre-build verification."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.hierarchy_correction import review_preparation as preparation
from er_commons.hierarchy_correction.candidate_records import stable_json_bytes
from er_commons.hierarchy_correction.digests import canonical_json_sha256
from er_commons.hierarchy_correction.review_evaluation import (
    validate_held_out_review_record,
)
from er_commons.hierarchy_correction.review_preparation import HeldOutReviewContext

JsonRecord = dict[str, Any]


@dataclass(frozen=True)
class HeldOutAnnotationSeal:
    """Verified immutable annotation evidence accepted before any build."""

    annotations_path: Path
    seal_path: Path
    candidate_id: str
    annotation_bundle_sha256: str


def seal_held_out_annotations(
    *, data_root: Path, config_path: Path, completed_template_path: Path
) -> HeldOutAnnotationSeal:
    """Validate completed source annotations and write their no-clobber seal."""
    context = preparation._load_held_out_context(data_root=data_root, config_path=config_path)
    expected_template = (
        context.review_root / "held_out_preparation" / "held_out_annotation_template.json"
    )
    if completed_template_path.resolve() != expected_template.resolve():
        raise ValueError("completed held-out template path differs")
    completed = preparation._load_json_object(completed_template_path)
    if completed.get("record_type") != "held_out_annotation_template":
        raise ValueError("completed held-out input is not the prepared template")
    annotations = dict(completed)
    annotations["record_type"] = "held_out_annotations"
    _validate_annotation_evidence(context, annotations)

    annotations_path = context.review_root / "held_out_annotations.json"
    seal_path = context.review_root / "held_out_annotations.seal.json"
    if annotations_path.exists() or seal_path.exists():
        raise FileExistsError("held-out annotations or seal already exists")
    annotation_bytes = stable_json_bytes(annotations)
    annotation_bundle_sha256 = canonical_json_sha256(annotations)
    render_manifest_path = context.review_root / "held_out_preparation" / "render_manifest.json"
    seal = _seal_record(
        context=context,
        annotations_path=annotations_path,
        annotation_bytes=annotation_bytes,
        annotation_bundle_sha256=annotation_bundle_sha256,
        render_manifest_path=render_manifest_path,
    )
    annotations_created = False
    seal_created = False
    try:
        with annotations_path.open("xb") as stream:
            annotations_created = True
            stream.write(annotation_bytes)
        with seal_path.open("xb") as stream:
            seal_created = True
            stream.write(stable_json_bytes(seal))
    except Exception:
        if annotations_created:
            annotations_path.unlink(missing_ok=True)
        if seal_created:
            seal_path.unlink(missing_ok=True)
        raise
    return HeldOutAnnotationSeal(
        annotations_path=annotations_path,
        seal_path=seal_path,
        candidate_id=context.candidate_id,
        annotation_bundle_sha256=annotation_bundle_sha256,
    )


def verify_sealed_held_out_annotations(
    *, data_root: Path, config_path: Path, candidate_id: str
) -> HeldOutAnnotationSeal:
    """Reverify the complete annotation and render seal before semantic builds."""
    context = preparation._load_held_out_context(data_root=data_root, config_path=config_path)
    if context.candidate_id != candidate_id:
        raise ValueError("held-out annotation candidate identity differs")
    annotations_path = context.review_root / "held_out_annotations.json"
    seal_path = context.review_root / "held_out_annotations.seal.json"
    annotations = preparation._load_json_object(annotations_path)
    seal = preparation._load_json_object(seal_path)
    _validate_annotation_evidence(context, annotations)
    annotation_bytes = annotations_path.read_bytes()
    annotation_bundle_sha256 = canonical_json_sha256(annotations)
    render_manifest_path = context.review_root / "held_out_preparation" / "render_manifest.json"
    expected = _seal_record(
        context=context,
        annotations_path=annotations_path,
        annotation_bytes=annotation_bytes,
        annotation_bundle_sha256=annotation_bundle_sha256,
        render_manifest_path=render_manifest_path,
    )
    if seal != expected:
        raise ValueError("held-out annotation seal differs")
    return HeldOutAnnotationSeal(
        annotations_path=annotations_path,
        seal_path=seal_path,
        candidate_id=candidate_id,
        annotation_bundle_sha256=annotation_bundle_sha256,
    )


def _seal_record(
    *,
    context: HeldOutReviewContext,
    annotations_path: Path,
    annotation_bytes: bytes,
    annotation_bundle_sha256: str,
    render_manifest_path: Path,
) -> JsonRecord:
    """Build the sole compact checksum seal shape."""
    return {
        "record_type": "held_out_annotation_seal",
        "schema_version": "1.0.0",
        "candidate_id": context.candidate_id,
        "annotations_path": annotations_path.name,
        "annotations_file_sha256": hashlib.sha256(annotation_bytes).hexdigest(),
        "annotation_bundle_sha256": annotation_bundle_sha256,
        "render_manifest_path": render_manifest_path.relative_to(context.review_root).as_posix(),
        "render_manifest_sha256": preparation._sha256_file(render_manifest_path),
        "status": "sealed",
    }


def _validate_annotation_evidence(context: HeldOutReviewContext, annotations: JsonRecord) -> None:
    """Bind annotations to source identity, renders, pages, and feature keys."""
    schema = preparation._load_json_object(context.review_schema_path)
    Draft202012Validator(schema).validate(annotations)
    expected_root = {
        "record_type": "held_out_annotations",
        "schema_version": "1.0.0",
        "source_id": context.source_id,
        "source_sha256": context.source_sha256,
        "held_out_manifest_sha256": context.held_out_manifest_sha256,
        "policy_sha256": context.identity["policy_sha256"],
        "code_bundle_sha256": context.identity["code_bundle_sha256"],
        "created_before_corrected_output": True,
        "post_review_tuning_allowed": False,
    }
    for field_name, expected in expected_root.items():
        if annotations.get(field_name) != expected:
            raise ValueError(f"held-out annotation {field_name} differs")
    pages = annotations["pages"]
    if (
        not isinstance(pages, list)
        or tuple(page["physical_page"] for page in pages) != context.selected_pages
    ):
        raise ValueError("held-out annotation page order differs")
    render_manifest = _validate_render_manifest(context)
    render_pages = render_manifest["pages"]
    if not isinstance(render_pages, list):
        raise ValueError("held-out render pages are invalid")
    renders_by_page = {item["physical_page"]: item for item in render_pages}
    for page in pages:
        physical_page = page["physical_page"]
        expected_keys = list(context.eligible_keys_by_page[physical_page])
        if page["eligible_item_keys"] != expected_keys:
            raise ValueError(f"held-out eligible keys differ on page {physical_page}")
        annotation_records = page["annotations"]
        if [item["stable_item_key"] for item in annotation_records] != expected_keys:
            raise ValueError(f"held-out annotation key order differs on page {physical_page}")
        if page["source_render_sha256"] != renders_by_page[physical_page]["sha256"]:
            raise ValueError(f"held-out source render differs on page {physical_page}")
    validate_held_out_review_record(annotations, expected_pages=set(context.selected_pages))


def _validate_render_manifest(context: HeldOutReviewContext) -> JsonRecord:
    """Recompute every deterministic render path and byte checksum."""
    root = context.review_root / "held_out_preparation"
    manifest = preparation._load_json_object(root / "render_manifest.json")
    expected_header = {
        "record_type": "held_out_source_render_manifest",
        "schema_version": "1.0.0",
        "candidate_id": context.candidate_id,
        "source_id": context.source_id,
        "source_sha256": context.source_sha256,
        "held_out_manifest_sha256": context.held_out_manifest_sha256,
        "engine": "pypdfium2",
        "engine_version": version("pypdfium2"),
        "settings": preparation._render_settings(),
    }
    for field_name, expected in expected_header.items():
        if manifest.get(field_name) != expected:
            raise ValueError(f"held-out render manifest {field_name} differs")
    pages = manifest.get("pages")
    if (
        not isinstance(pages, list)
        or tuple(item.get("physical_page") for item in pages if isinstance(item, dict))
        != context.selected_pages
    ):
        raise ValueError("held-out render page order differs")
    for item in pages:
        page = item["physical_page"]
        expected_name = f"source-p{page:05d}.png"
        if item.get("path") != expected_name:
            raise ValueError(f"held-out render path differs on page {page}")
        path = root / expected_name
        if preparation._sha256_file(path) != item.get("sha256"):
            raise ValueError(f"held-out render checksum differs on page {page}")
    verification_root = Path(
        tempfile.mkdtemp(prefix=".held-out-render-verification-", dir=context.review_root)
    )
    try:
        expected = preparation._render_source_pages(context, verification_root)
        if expected != manifest:
            raise ValueError("held-out renders differ from deterministic source rendering")
    finally:
        shutil.rmtree(verification_root, ignore_errors=True)
    return manifest
