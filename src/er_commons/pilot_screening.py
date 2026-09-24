"""Build one unrated Label Studio UI trial from a sealed 07A sample."""

import argparse
import hashlib
import html
import json
import logging
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

FORM_VERSION = "task07a.screening.trial.v1"
_LOG = logging.getLogger(__name__)

# Rules for the saved Volume 4 extraction, not arbitrary PDFs.
_VOLUME_4_RUNNING_HEADER = re.compile(
    r"Chapter 13\. Responses to Comments\r?\n13\.[^\n]+\n"
    r"(?:[^\n]+\n)?13-\d+ Baylands Specific Plan Final EIR\r?\n"
    r"Volume 4\. Responses to Comments on the Draft EIR\r?\n"
    r"City of Brisbane\r?\nMay 2026\r?\n"
)
_FIGURE_EXTRACT = re.compile(
    r"(^Draft EIR Figure [^\n]+\n.*?)(?=Chapter 13\. Responses to Comments|\Z)",
    re.MULTILINE | re.DOTALL,
)


def _checked_bytes(path: Path, digest: str) -> bytes:
    """Read a pinned input only when its bytes match the sample manifest."""
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != digest:
        raise ValueError(f"Checksum mismatch: {path}")
    return content


def _rows(content: bytes) -> list[dict[str, Any]]:
    """Decode the existing JSONL records without rewriting source artifacts."""
    return [json.loads(line) for line in content.splitlines() if line.strip()]


def _index(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    """Reject duplicate source identities rather than silently replacing them."""
    indexed = {row[key]: row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError(f"Duplicate {key}")
    return indexed


def _paragraphs(text: str) -> str:
    """Join extraction lines: trailing space/tab signals a wrapped continuation.

    A blank line or a line without trailing whitespace ends the paragraph.
    This is a convention of this extraction, not general PDF paragraph detection.
    """
    paragraphs: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        current.append(line.strip())
        if not line or not line.endswith((" ", "\t")):
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    return "".join(f"<p>{html.escape(p)}</p>" for p in paragraphs if p.strip())


def _readable_body_html(original: str, official_label: str) -> str:
    """Separate figure OCR from prose and remove only known presentation furniture."""
    # Captured pieces alternate between prose and figure extraction.
    pieces = _FIGURE_EXTRACT.split(original)
    rendered = []
    for index, piece in enumerate(pieces):
        if index % 2:
            rendered.append(
                '<p class="source-warning">Figure extraction: consult the source PDF '
                "for the visual; extracted labels may be degraded.</p>"
                "<details><summary>Figure caption and extracted labels</summary>"
                f'<pre style="white-space:pre-wrap">{html.escape(piece)}</pre></details>'
            )
        else:
            readable = _VOLUME_4_RUNNING_HEADER.sub("", piece)
            if index == 0:
                readable = re.sub(
                    r"^" + re.escape(official_label) + r"[ \t]*\r?\n",
                    "",
                    readable,
                    count=1,
                )
            rendered.append(_paragraphs(readable))
    return "".join(rendered)


def _unit_html(unit: dict[str, Any], source_base_url: str | None) -> str:
    """Show readable source text, page anchors, and the unchanged extracted original."""
    pages = []
    for page in unit["source_pages"]:
        label = f"PDF {page}"
        if source_base_url:
            url = html.escape(f"{source_base_url}#page={int(page)}", quote=True)
            label = f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'
        pages.append(label)
    original = unit["text"]
    return (
        '<article class="source-unit">'
        f"<h3>{html.escape(unit['official_label'])}</h3>"
        f'<div class="source-pages">Volume 4 · {" · ".join(pages)}</div>'
        f"{_readable_body_html(original, unit['official_label'])}"
        "<details><summary>Original extracted text</summary>"
        f'<pre style="white-space:pre-wrap">{html.escape(original)}</pre></details></article>'
    )


def _references_html(outcomes: list[dict[str, Any]], units: dict[str, Any]) -> str:
    """Display accepted reference labels and warnings without inferring fit."""
    items = []
    for row in outcomes:
        source_label = units[row["source_unit_id"]]["official_label"]
        target = " ".join(row["raw_target_label"].split())
        logical_sources = ", ".join(
            logical_source_id.replace("deir_main", "Main report").replace(
                "deir_appendix_", "Appendix "
            )
            for logical_source_id in row.get("logical_source_ids", [])
        )
        status = row["outcome"].replace("_", " ")
        warning = row.get("terminal_reason") or row.get("final_f1_warning")
        detail = f"{source_label}: {target} — {status}"
        if logical_sources:
            detail += f" ({logical_sources})"
        if warning:
            detail += f". {warning}"
        if any(
            annotation.get("text_only_model_eligibility") is False
            for annotation in row.get("target_annotations", [])
        ):
            detail += ". Visual target: unavailable as text-only evidence."
        items.append(f"<li>{html.escape(detail)}</li>")
    return (
        "<ul>" + "".join(items) + "</ul>"
        "<p>Recorded references are navigation aids, not proof of evidence sufficiency. "
        "Upstream review was sampled; unresolved references and visual evidence need care. "
        "External citations may occur in the original text without a recorded reference.</p>"
    )


def build_trial_task(
    sample_root: Path,
    comment_id: str,
    *,
    data_root: Path | None = None,
    source_base_url: str | None = None,
) -> dict[str, Any]:
    """Prepare exactly one selected comment, preserving complete accepted context and IDs."""
    if not comment_id:
        raise ValueError("An explicit comment_id is required")
    if data_root is None:
        configured = os.environ.get("ER_COMMONS_DATA_ROOT")
        if not configured:
            raise ValueError("Set ER_COMMONS_DATA_ROOT or provide data_root explicitly")
        data_root = Path(configured)
    if source_base_url and urlsplit(source_base_url).scheme not in {"http", "https"}:
        raise ValueError("source_base_url must use http or https")
    manifest_bytes = (sample_root / "selection_manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    sample = _index(
        _rows(_checked_bytes(sample_root / "sample.jsonl", manifest["files"]["sample.jsonl"])),
        "comment_id",
    )
    units = _index(
        _rows(
            _checked_bytes(
                sample_root / "review_context.jsonl", manifest["files"]["review_context.jsonl"]
            )
        ),
        "unit_id",
    )
    if comment_id not in sample:
        raise ValueError(f"Comment is not in the selected sample: {comment_id}")
    case = sample[comment_id]
    context_ids = case["context_unit_ids"]
    direct_ids = case["direct_response_ids"]
    if len(set(context_ids)) != len(context_ids) or len(set(direct_ids)) != len(direct_ids):
        raise ValueError(f"Duplicate context membership for {comment_id}")
    if comment_id not in context_ids or not set(direct_ids) <= set(context_ids):
        raise ValueError(f"Comment or direct responses missing from context for {comment_id}")
    if not set(case["general_response_ids"]) <= set(context_ids):
        raise ValueError(f"General response missing from context for {comment_id}")
    if not set(context_ids) <= units.keys():
        raise ValueError(f"Missing source unit for {comment_id}")
    component = manifest["source_components"]["outcomes"]
    outcomes_path = (data_root / component["path"]).resolve()
    if not outcomes_path.is_relative_to(data_root.resolve()):
        raise ValueError("Outcomes path must remain within data_root")
    all_outcomes = _index(_rows(_checked_bytes(outcomes_path, component["sha256"])), "outcome_id")
    outcomes = [all_outcomes[key] for key in case["reference_outcome_ids"]]
    if any(row["source_unit_id"] not in context_ids for row in outcomes):
        raise ValueError(f"Reference belongs to a different context for {comment_id}")
    context = [key for key in context_ids if key != comment_id and key not in direct_ids]
    data = {
        "case_title": case["comment_label"],
        "source_summary": "Baylands Final EIR · Volume 4 · One-case UI trial",
        "comment_html": _unit_html(units[comment_id], source_base_url),
        "response_html": "".join(_unit_html(units[key], source_base_url) for key in direct_ids),
        "context_html": "".join(_unit_html(units[key], source_base_url) for key in context)
        or "<p>No additional linked response context.</p>",
        "reference_html": _references_html(outcomes, units),
        "form_version": FORM_VERSION,
        "inventory_id": manifest["inventory_id"],
        "sample_sha256": manifest["files"]["sample.jsonl"],
        "sample_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "comment_id": comment_id,
        "accepted_view_id": case["accepted_view_id"],
        "context_unit_ids": context_ids,
        "direct_response_ids": direct_ids,
        "general_response_ids": case["general_response_ids"],
        "relationship_ids": case["relationship_ids"],
        "reference_outcome_ids": case["reference_outcome_ids"],
    }
    return {"data": data}


def main() -> None:
    """Write a one-task JSON import without replacing an existing trial artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-root", type=Path, required=True)
    parser.add_argument("--comment-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-base-url")
    args = parser.parse_args()
    task = build_trial_task(args.sample_root, args.comment_id, source_base_url=args.source_base_url)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump([task], handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    logging.basicConfig(level=logging.INFO)
    _LOG.info("Wrote one unrated UI trial: %s", args.output)


if __name__ == "__main__":
    main()
