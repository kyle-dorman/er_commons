"""Disposable source and semantic-overlay review artifacts for Task 03E.4."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from importlib.metadata import version
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium  # type: ignore[import-untyped]
from PIL import Image, ImageDraw, ImageFont

from er_commons.canonical_extraction.publication import stable_json_bytes
from er_commons.semantic_materialization.errors import SemanticMaterializationInvariantError

JsonObject = dict[str, Any]
RENDER_SCALE = 2.0
SIDEBAR_WIDTH = 920


def _load_jsonl(path: Path) -> list[JsonObject]:
    """Load one candidate collection in persisted order."""
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _sha256(path: Path) -> str:
    """Return the complete digest of one review artifact."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _short(record_id: str | None) -> str:
    """Return a readable local record identifier for an overlay."""
    return "none" if record_id is None else record_id.rsplit("/", 1)[-1]


def _region_box(record: JsonObject, page_id: str) -> tuple[float, float, float, float] | None:
    """Return the first producer-PDF region anchored to the reviewed page."""
    for region in record.get("regions", []):
        if region.get("page_id") == page_id and region.get("origin") == "bottom_left":
            left, bottom, right, top = region["bbox"]
            return float(left), float(bottom), float(right), float(top)
    return None


def _diagnostic(
    *,
    page: JsonObject,
    label: JsonObject,
    content_by_id: dict[str, JsonObject],
    sections_by_id: dict[str, JsonObject],
    aliases: list[JsonObject],
) -> JsonObject:
    """Build the compact record view paired with one visual overlay."""
    content = []
    for record_id in page["ordered_content_ids"]:
        record = content_by_id[record_id]
        section = sections_by_id[record["section_id"]]
        content.append(
            {
                "record_id": record_id,
                "record_type": record_id.split("/")[-3],
                "sequence": record["sequence"],
                "semantic_placement": record["semantic_placement"],
                "section_id": record["section_id"],
                "section_path_ids": section["section_path_ids"],
                "heading_owner": record["semantic_placement"] == "heading_owner",
                "replacement_position": (record["semantic_placement"] == "inherited_nontext"),
                "is_toc_row": record.get("is_toc_row", False),
            }
        )
    page_alias_targets = [
        alias
        for alias in aliases
        if any(target["target_id"] == page["id"] for target in alias["targets"])
    ]
    return {
        "schema_version": "er_commons.semantic_review_diagnostic.v1",
        "physical_page_number": page["physical_page_number"],
        "page_id": page["id"],
        "source_printed_page_label": page.get("printed_page_label"),
        "resolved_page_label": label,
        "ordered_content": content,
        "page_alias_targets": page_alias_targets,
    }


def _draw_overlay(
    source: Image.Image,
    diagnostic: JsonObject,
    content_by_id: dict[str, JsonObject],
) -> Image.Image:
    """Draw semantic membership boxes and a complete ordered-content sidebar."""
    overlay = Image.new("RGB", (source.width + SIDEBAR_WIDTH, source.height), "white")
    overlay.paste(source, (0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    font = ImageFont.load_default()
    colors = {
        "heading_owner": (220, 20, 60, 235),
        "inherited_nontext": (20, 100, 220, 235),
        "toc_content": (160, 60, 200, 235),
        "furniture": (90, 90, 90, 220),
        "pre_root": (230, 130, 10, 235),
        "direct_body": (20, 150, 80, 210),
    }
    page_id = diagnostic["page_id"]
    page_height = source.height / RENDER_SCALE
    for index, item in enumerate(diagnostic["ordered_content"], start=1):
        record = content_by_id[item["record_id"]]
        bbox = _region_box(record, page_id)
        if bbox is None:
            continue
        left, bottom, right, top = bbox
        rectangle = (
            left * RENDER_SCALE,
            (page_height - top) * RENDER_SCALE,
            right * RENDER_SCALE,
            (page_height - bottom) * RENDER_SCALE,
        )
        color = colors[item["semantic_placement"]]
        draw.rectangle(rectangle, outline=color, width=4)
        draw.text((rectangle[0] + 2, rectangle[1] + 2), str(index), fill=color, font=font)

    x = source.width + 14
    label = diagnostic["resolved_page_label"]
    lines = [
        f"physical page: {diagnostic['physical_page_number']}",
        f"source label: {diagnostic['source_printed_page_label']!r}",
        f"resolved: {label['resolved_state']} {label['resolved_label']!r}",
        f"basis: {label['resolution_basis']!r}",
        f"page aliases: {len(diagnostic['page_alias_targets'])}",
        "",
        "mixed order | placement | section path",
    ]
    for index, item in enumerate(diagnostic["ordered_content"], start=1):
        path = ">".join(_short(value) for value in item["section_path_ids"])
        lines.append(
            f"{index:02d} {_short(item['record_id'])} | {item['semantic_placement']} | {path}"
        )
    y = 14
    for line in lines:
        draw.text((x, y), line, fill=(0, 0, 0, 255), font=font)
        y += 15
    return overlay


def _candidate_id(candidate_root: Path) -> str:
    """Read the canonical ID instead of inferring it from a staging dirname."""
    identity = json.loads((candidate_root / "records" / "extraction_identity.json").read_bytes())
    candidate_id = identity.get("extraction_id")
    if not isinstance(candidate_id, str) or not candidate_id.startswith("exv1-"):
        raise SemanticMaterializationInvariantError(
            stage="semantic review",
            invariant="candidate identity contains a valid extraction ID",
            expected="exv1- prefixed string",
            observed=candidate_id,
            subject=(candidate_root / "records" / "extraction_identity.json").as_posix(),
        )
    return candidate_id


def _verify_existing(root: Path, candidate_id: str, review_pages: tuple[int, ...]) -> Path:
    """Checksum-verify an existing closed review cache before reuse."""
    manifest_path = root / "review_manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    if manifest.get("candidate_id") != candidate_id:
        raise SemanticMaterializationInvariantError(
            stage="semantic review reuse",
            invariant="review cache belongs to the candidate",
            expected=candidate_id,
            observed=manifest.get("candidate_id"),
            subject=manifest_path.as_posix(),
        )
    observed_pages = tuple(item["physical_page_number"] for item in manifest["pages"])
    if observed_pages != review_pages:
        raise SemanticMaterializationInvariantError(
            stage="semantic review reuse",
            invariant="review cache uses the configured page sample",
            expected=review_pages,
            observed=observed_pages,
            subject=manifest_path.as_posix(),
        )
    for item in manifest["pages"]:
        for key in ("source", "overlay", "diagnostic"):
            artifact = root / item[key]["path"]
            if not artifact.is_file() or _sha256(artifact) != item[key]["sha256"]:
                observed = _sha256(artifact) if artifact.is_file() else "missing"
                raise SemanticMaterializationInvariantError(
                    stage="semantic review reuse",
                    invariant="review artifact matches its manifest checksum",
                    expected=item[key]["sha256"],
                    observed=observed,
                    subject=artifact.as_posix(),
                )
    return manifest_path


def build_semantic_review_cache(
    *,
    review_root: Path,
    source_pdf: Path,
    candidate_root: Path,
    review_pages: tuple[int, ...],
) -> Path:
    """Render exactly the predeclared ten-page source/semantic review sample."""
    candidate_id = _candidate_id(candidate_root)
    if review_root.name != candidate_id:
        raise SemanticMaterializationInvariantError(
            stage="semantic review",
            invariant="review-cache root is keyed by candidate ID",
            expected=candidate_id,
            observed=review_root.name,
            subject=review_root.as_posix(),
        )
    if review_root.exists():
        return _verify_existing(review_root, candidate_id, review_pages)

    pages = _load_jsonl(candidate_root / "canonical" / "pages.jsonl")
    labels = _load_jsonl(candidate_root / "observations" / "page_labels.jsonl")
    sections = _load_jsonl(candidate_root / "canonical" / "sections.jsonl")
    aliases = _load_jsonl(candidate_root / "canonical" / "target_aliases.jsonl")
    content = [
        *_load_jsonl(candidate_root / "canonical" / "blocks.jsonl"),
        *_load_jsonl(candidate_root / "canonical" / "tables.jsonl"),
        *_load_jsonl(candidate_root / "canonical" / "figures.jsonl"),
    ]
    page_by_number = {item["physical_page_number"]: item for item in pages}
    label_by_number = {item["physical_page_number"]: item for item in labels}
    sections_by_id = {item["id"]: item for item in sections}
    content_by_id = {item["id"]: item for item in content}

    review_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{review_root.name}.", dir=review_root.parent))
    document = pdfium.PdfDocument(source_pdf)
    page_artifacts: list[JsonObject] = []
    try:
        for physical_page in review_pages:
            pdf_page = document[physical_page - 1]
            bitmap = pdf_page.render(scale=RENDER_SCALE, rev_byteorder=True)
            try:
                source = bitmap.to_pil().convert("RGB")
            finally:
                bitmap.close()
                pdf_page.close()
            stem = f"p{physical_page:05d}"
            source_path = staging / f"source-{stem}.png"
            source.save(source_path, format="PNG", optimize=False, compress_level=9)
            diagnostic = _diagnostic(
                page=page_by_number[physical_page],
                label=label_by_number[physical_page],
                content_by_id=content_by_id,
                sections_by_id=sections_by_id,
                aliases=aliases,
            )
            diagnostic_path = staging / f"diagnostic-{stem}.json"
            diagnostic_path.write_bytes(stable_json_bytes(diagnostic))
            overlay = _draw_overlay(source, diagnostic, content_by_id)
            overlay_path = staging / f"semantic-overlay-{stem}.png"
            overlay.save(overlay_path, format="PNG", optimize=False, compress_level=9)
            page_artifacts.append(
                {
                    "physical_page_number": physical_page,
                    "source": {"path": source_path.name, "sha256": _sha256(source_path)},
                    "overlay": {"path": overlay_path.name, "sha256": _sha256(overlay_path)},
                    "diagnostic": {
                        "path": diagnostic_path.name,
                        "sha256": _sha256(diagnostic_path),
                    },
                }
            )
        manifest = {
            "schema_version": "er_commons.semantic_review_manifest.v1",
            "candidate_id": candidate_id,
            "source_pdf_sha256": _sha256(source_pdf),
            "engine": "pypdfium2",
            "engine_version": version("pypdfium2"),
            "render_scale": RENDER_SCALE,
            "pages": page_artifacts,
        }
        manifest_path = staging / "review_manifest.json"
        manifest_path.write_bytes(stable_json_bytes(manifest))
        staging.rename(review_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    finally:
        document.close()
    return review_root / "review_manifest.json"
