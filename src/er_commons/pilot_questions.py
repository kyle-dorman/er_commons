"""Prepare a comment-only question-review trial and validate human review exports."""

import argparse
import hashlib
import html
import json
import logging
import re
from pathlib import Path
from typing import Any

FORM_VERSION = "task07b.questions.trial.v1"
# Label Studio selects one prediction version project-wide, across case packets.
PREDICTION_VERSION = "task07b.questions.v1"
_SOURCE_FIELDS = (
    "comment_id",
    "comment_label",
    "original_comment",
    "original_comment_sha256",
    "source_pages",
    "source_span_ids",
    "source_note",
)
_PROPOSAL_FIELDS = (
    "schema_version",
    "comment_id",
    "comment_label",
    "input_comment_sha256",
    "proposal_version",
    "concerns",
    "draft_note",
    "model",
)
_PROVENANCE_FIELDS = (
    *_SOURCE_FIELDS,
    "form_version",
    "original_proposal",
    "packet_manifest_sha256",
    "proposal_sha256",
)


def _sha(content: bytes) -> str:
    """Hash exact saved bytes without normalizing source line endings."""
    return hashlib.sha256(content).hexdigest()


def _nonempty(value: Any, name: str) -> str:
    """Require a nonblank string while preserving its original characters."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def build_trial_task(drafting_dir: Path) -> dict[str, Any]:
    """Verify the explicit packet and project only comment and proposal fields."""
    manifest_bytes = (drafting_dir / "packet_manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest["schema_version"] != "er_commons.task07b.drafting_packet_manifest.v1":
        raise ValueError("Unsupported packet schema")
    contents = {}
    for name in ("comment_input.json", "drafting_prompt.md"):
        contents[name] = (drafting_dir / name).read_bytes()
        if _sha(contents[name]) != manifest["files"][name]:
            raise ValueError(f"Checksum mismatch: {name}")
    source = json.loads(contents["comment_input.json"])
    proposal_bytes = (drafting_dir / "proposal.json").read_bytes()
    proposal = json.loads(proposal_bytes)
    if source["schema_version"] != "er_commons.task07b.comment_drafting_input.v1":
        raise ValueError("Unsupported comment schema")
    if proposal["schema_version"] != "er_commons.task07b.concern_proposal.v1":
        raise ValueError("Unsupported proposal schema")
    original = _nonempty(source["original_comment"], "original_comment")
    text_hash = _sha(original.encode("utf-8"))
    if not (
        text_hash
        == source["original_comment_sha256"]
        == manifest["original_comment_sha256"]
        == proposal["input_comment_sha256"]
    ):
        raise ValueError("Original comment text identity mismatch")
    for key, manifest_key in (
        ("comment_id", "selected_case_id"),
        ("comment_label", "comment_label"),
    ):
        if not (_nonempty(source[key], key) == manifest[manifest_key] == proposal[key]):
            raise ValueError(f"Comment identity mismatch: {key}")
    pages = source["source_pages"]
    spans = source["source_span_ids"]
    if not isinstance(pages, list) or not pages or any(type(p) is not int or p < 1 for p in pages):
        raise ValueError("source_pages must contain positive PDF page numbers")
    if not isinstance(spans, list) or not spans:
        raise ValueError("source_span_ids must contain source bindings")
    for span in spans:
        _nonempty(span, "source_span_id")
    if not isinstance(source["source_note"], str):
        raise ValueError("source_note must be text")
    concerns = proposal["concerns"]
    if not isinstance(concerns, list) or not concerns:
        raise ValueError("Proposal must contain concerns")
    for concern in concerns:
        _nonempty(concern, "concern")
    draft_note = proposal["draft_note"]
    if not isinstance(draft_note, str):
        raise ValueError("draft_note must be text")
    note_html = (
        f"<p><strong>Draft note:</strong> {html.escape(draft_note)}</p>"
        if draft_note.strip()
        else ""
    )
    _nonempty(proposal["proposal_version"], "proposal_version")
    proposal_text = "\n".join(f"{i}. {text}" for i, text in enumerate(concerns, 1))
    data = {key: source[key] for key in _SOURCE_FIELDS}
    data.update(
        {
            "original_proposal": {key: proposal[key] for key in _PROPOSAL_FIELDS},
            "proposal_text": proposal_text,
            "proposal_html": "<ol>"
            + "".join(f"<li>{html.escape(c)}</li>" for c in concerns)
            + "</ol>"
            + note_html,
            "comment_html": f'<pre style="white-space:pre-wrap">{html.escape(original)}</pre>',
            "source_summary": "Volume 4 · PDF page " + ", ".join(str(p) for p in pages),
            "form_version": FORM_VERSION,
            "packet_manifest_sha256": _sha(manifest_bytes),
            "proposal_sha256": _sha(proposal_bytes),
        }
    )
    return {
        "data": data,
        "predictions": [
            {
                "model_version": PREDICTION_VERSION,
                "result": [
                    {
                        "from_name": "concerns",
                        "to_name": "comment",
                        "type": "textarea",
                        "value": {"text": [proposal_text]},
                    }
                ],
            }
        ],
    }


def _approved_list(text: str) -> None:
    """Require sequential numbered, nonblank items; permit wrapped continuation lines."""
    items = re.split(r"(?m)^\s*(\d+)\.\s*", text)
    if items[0].strip() or len(items) < 3:
        raise ValueError("Approved concerns require a numbered list")
    for expected, index in enumerate(range(1, len(items), 2), 1):
        if int(items[index]) != expected or not items[index + 1].strip():
            raise ValueError("Approved concerns require sequential nonempty numbered items")


def normalize_review(
    task: dict[str, Any], annotation: dict[str, Any], *, expected_task: dict[str, Any]
) -> dict[str, Any]:
    """Validate a saved annotation against a freshly built, trusted packet projection.

    The caller must obtain expected_task from build_trial_task, not the review export.
    Predictions never establish approval.
    """
    if task.get("data") != expected_task["data"]:
        raise ValueError("Exported task data differs from the verified drafting packet")
    if annotation.get("was_cancelled") or annotation.get("skipped"):
        raise ValueError("Canceled annotations cannot become reviews")
    if task.get("id") is None or annotation.get("task") != task["id"]:
        raise ValueError("Annotation belongs to a different or unbound task")
    if annotation.get("id") is None or annotation.get("completed_by") is None:
        raise ValueError("Saved annotation and reviewer identities are required")
    if task["data"]["form_version"] != FORM_VERSION:
        raise ValueError("Unsupported review form")
    fields: dict[str, Any] = {}
    for result in annotation.get("result", []):
        name = result.get("from_name")
        if name not in {"concerns", "review_status", "review_note"} or name in fields:
            raise ValueError("Unexpected or duplicate review field")
        expected_type = "choices" if name == "review_status" else "textarea"
        if result.get("to_name") != "comment" or result.get("type") != expected_type:
            raise ValueError("Foreign review field binding")
        value = result.get("value", {})
        key = "choices" if name == "review_status" else "text"
        values = value.get(key)
        if set(value) != {key} or not isinstance(values, list) or len(values) != 1:
            raise ValueError("Review fields require exactly one value")
        if not isinstance(values[0], str):
            raise ValueError("Review values must be text")
        fields[name] = values[0]
    status = fields.get("review_status")
    if status not in {"approved", "unclear", "needs_context"}:
        raise ValueError("An explicit review status is required")
    text = fields.get("concerns", "")
    if status == "approved":
        _approved_list(text)
    return {
        **{key: task["data"][key] for key in _PROVENANCE_FIELDS},
        "schema_version": "er_commons.task07b.concern_review.v1",
        "concerns": text,
        "review_status": status,
        "review_note": fields.get("review_note", ""),
        "eligible_for_next_stage": status == "approved",
        "task_id": task["id"],
        "annotation_id": annotation["id"],
        "reviewer": annotation["completed_by"],
        "created_at": annotation.get("created_at"),
        "updated_at": annotation.get("updated_at"),
    }


def main() -> None:
    """Write one task to a new file; never overwrite trial or reviewed artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--drafting-dir", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    task = build_trial_task(args.drafting_dir)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump([task], handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).info("Wrote one pending question-review trial: %s", args.output)


if __name__ == "__main__":
    main()
