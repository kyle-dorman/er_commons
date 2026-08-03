"""Source-only held-out context, rendering, and template preparation."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium  # type: ignore[import-untyped]

from er_commons.document_extraction.hierarchy.document import stable_text_key
from er_commons.hierarchy_correction.candidate_identity import build_candidate_identity
from er_commons.hierarchy_correction.candidate_records import stable_json_bytes
from er_commons.hierarchy_correction.code_inventory import owned_code_paths
from er_commons.hierarchy_correction.configuration import load_hierarchy_correction_config
from er_commons.hierarchy_correction.features import traverse_provenance_text
from er_commons.hierarchy_correction.inputs import load_hierarchy_correction_inputs
from er_commons.hierarchy_correction.quality_config import load_quality_gate_config

JsonRecord = dict[str, Any]
RENDER_SCALE = 2.0
RENDER_DPI = 144


@dataclass(frozen=True)
class HeldOutReviewContext:
    """Verified source-only inputs needed to prepare or seal held-out review."""

    candidate_id: str
    identity: JsonRecord
    review_root: Path
    source_path: Path
    source_id: str
    source_sha256: str
    held_out_manifest_sha256: str
    selected_pages: tuple[int, ...]
    eligible_keys_by_page: dict[int, tuple[str, ...]]
    review_schema_path: Path


def prepare_held_out_review(*, data_root: Path, config_path: Path) -> Path:
    """Render frozen source pages and write one no-clobber annotation template."""
    context = _load_held_out_context(data_root=data_root, config_path=config_path)
    preparation_root = context.review_root / "held_out_preparation"
    if preparation_root.exists():
        raise FileExistsError(f"held-out preparation already exists: {preparation_root}")
    context.review_root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".held-out-preparation-", dir=context.review_root))
    try:
        render_manifest = _render_source_pages(context, staging)
        template = _annotation_template(context, render_manifest)
        template_path = staging / "held_out_annotation_template.json"
        template_path.write_bytes(stable_json_bytes(template))
        staging.rename(preparation_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return preparation_root / "held_out_annotation_template.json"


def _load_held_out_context(*, data_root: Path, config_path: Path) -> HeldOutReviewContext:
    """Verify source inputs and compute identity without building semantic output."""
    project_root = Path(__file__).resolve().parents[3]
    config, config_sha256 = load_hierarchy_correction_config(config_path)
    quality_config, _quality_digest = load_quality_gate_config(
        project_root / config.quality_gate_config_relative_path
    )
    inputs = load_hierarchy_correction_inputs(data_root, config)
    identity = build_candidate_identity(
        config=config,
        config_sha256=config_sha256,
        inputs=inputs,
        policy_path=project_root / config.policy_relative_path,
        schema_path=project_root / config.schema_relative_path,
        project_root=project_root,
        owned_code_paths=owned_code_paths(project_root),
    )
    manifest_path = project_root / quality_config.held_out_manifest.path
    manifest = _load_json_object(manifest_path)
    if (
        manifest.get("source_id") != config.source.source_id
        or manifest.get("source_sha256") != config.source.expected_sha256
        or manifest.get("producer_run_id") != config.producer_run_id
    ):
        raise ValueError("held-out manifest source identity differs")
    selected_pages = tuple(manifest.get("unique_selected_pages", ()))
    if not selected_pages or not all(isinstance(page, int) and page > 0 for page in selected_pages):
        raise ValueError("held-out manifest selected pages are invalid")
    keys_by_page: dict[int, list[str]] = {page: [] for page in selected_pages}
    for entry in traverse_provenance_text(inputs.document):
        provenance = entry.item["prov"][0]
        page = provenance["page_no"]
        if page in keys_by_page:
            keys_by_page[page].append(stable_text_key(entry.item))
    if any(not keys_by_page[page] for page in selected_pages):
        raise ValueError("held-out page has no provenance-bearing text")
    return HeldOutReviewContext(
        candidate_id=identity["candidate_id"],
        identity=identity,
        review_root=data_root / config.review_artifact_relative_root / identity["candidate_id"],
        source_path=inputs.selected_source.source_path,
        source_id=config.source.source_id,
        source_sha256=config.source.expected_sha256,
        held_out_manifest_sha256=_sha256_file(manifest_path),
        selected_pages=selected_pages,
        eligible_keys_by_page={page: tuple(keys_by_page[page]) for page in selected_pages},
        review_schema_path=project_root / quality_config.review_schema.path,
    )


def _render_source_pages(context: HeldOutReviewContext, output_root: Path) -> JsonRecord:
    """Write exact 144-DPI RGB source-PDF PNGs and their adjacent manifest."""
    document = pdfium.PdfDocument(context.source_path)
    page_records: list[JsonRecord] = []
    try:
        for physical_page in context.selected_pages:
            page = document[physical_page - 1]
            bitmap = page.render(scale=RENDER_SCALE, rev_byteorder=True)
            try:
                image = bitmap.to_pil().convert("RGB")
                name = f"source-p{physical_page:05d}.png"
                path = output_root / name
                image.save(path, format="PNG", optimize=False, compress_level=9)
                page_records.append(
                    {
                        "physical_page": physical_page,
                        "path": name,
                        "sha256": _sha256_file(path),
                        "pixel_width": image.width,
                        "pixel_height": image.height,
                    }
                )
            finally:
                bitmap.close()
                page.close()
    finally:
        document.close()
    manifest: JsonRecord = {
        "record_type": "held_out_source_render_manifest",
        "schema_version": "1.0.0",
        "candidate_id": context.candidate_id,
        "source_id": context.source_id,
        "source_sha256": context.source_sha256,
        "held_out_manifest_sha256": context.held_out_manifest_sha256,
        "engine": "pypdfium2",
        "engine_version": version("pypdfium2"),
        "settings": _render_settings(),
        "pages": page_records,
    }
    (output_root / "render_manifest.json").write_bytes(stable_json_bytes(manifest))
    return manifest


def _render_settings() -> JsonRecord:
    """Return the complete pinned render and PNG-encoding settings."""
    return {
        "scale": RENDER_SCALE,
        "dpi": RENDER_DPI,
        "pixel_mode": "RGB",
        "alpha": False,
        "format": "PNG",
        "optimize": False,
        "compress_level": 9,
        "encoder": "Pillow",
        "encoder_version": version("Pillow"),
    }


def _annotation_template(context: HeldOutReviewContext, render_manifest: JsonRecord) -> JsonRecord:
    """Create an explicitly incomplete source-only annotation worksheet."""
    render_by_page = {item["physical_page"]: item for item in render_manifest["pages"]}
    return {
        "record_type": "held_out_annotation_template",
        "schema_version": "1.0.0",
        "source_id": context.source_id,
        "source_sha256": context.source_sha256,
        "held_out_manifest_sha256": context.held_out_manifest_sha256,
        "policy_sha256": context.identity["policy_sha256"],
        "code_bundle_sha256": context.identity["code_bundle_sha256"],
        "created_before_corrected_output": True,
        "post_review_tuning_allowed": False,
        "pages": [
            {
                "physical_page": page,
                "source_render_sha256": render_by_page[page]["sha256"],
                "eligible_item_keys": list(context.eligible_keys_by_page[page]),
                "annotations": [
                    {
                        "stable_item_key": key,
                        "expected_boundary": None,
                        "expected_level": None,
                        "expected_parent_key": None,
                        "expected_regime_action": None,
                        "source_ambiguous": None,
                        "note": "",
                    }
                    for key in context.eligible_keys_by_page[page]
                ],
            }
            for page in context.selected_pages
        ],
    }


def _load_json_object(path: Path) -> JsonRecord:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
