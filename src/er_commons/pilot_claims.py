"""Prepare a sealed response-claim trial and normalize explicit human reviews."""

import argparse
import hashlib
import html
import json
import logging
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

FORM_VERSION = "task07c.claims.trial.v1"
PREDICTION_VERSION = "task07c.claims.v2"


def _sha(raw: bytes) -> str:
    """Hash saved bytes without changing source line endings."""
    return hashlib.sha256(raw).hexdigest()


def _text(value: Any) -> str:
    """Require substantive text without changing its contents."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected nonempty text")
    return value


def _pre(value: str) -> str:
    """Escape source content before wrapping it for readable exact-text display."""
    return '<pre style="white-space:pre-wrap">' + html.escape(value) + "</pre>"


def _passages(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index full exact passages and their parent identities, rejecting collisions."""
    indexed = {}
    for response in source["responses"]:
        if response["full_text"] != "\n".join(p["text"] for p in response["passages"]):
            raise ValueError("Response full text differs from its passages")
        for passage in response["passages"]:
            key = passage["passage_id"]
            if key in indexed:
                raise ValueError("Duplicate passage ID")
            indexed[key] = {
                **passage,
                "source_ref": response["source_ref"],
                "source_id": response["source_id"],
                "unit_id": response["unit_id"],
                "official_label": response["official_label"],
            }
    for passage in source["supplemental_passages"]:
        if passage["passage_id"] in indexed:
            raise ValueError("Duplicate passage ID")
        indexed[passage["passage_id"]] = dict(passage)
    for passage in indexed.values():
        if _sha(_text(passage["text"]).encode()) != passage["text_sha256"]:
            raise ValueError("Passage text hash mismatch")
    return indexed


def format_claims(proposal: dict[str, Any]) -> str:
    """Render short editable references while keeping quote anchors in the proposal."""
    blocks = []
    for claim in proposal["claims"]:
        concerns = ",".join(claim["concern_ids"]) or "unassigned"
        refs = ",".join(dict.fromkeys(r["passage_id"] for r in claim["source_refs"]))
        blocks.append(f"{claim['claim_id']} | {concerns} | {refs}\n{claim['text']}")
    return "\n\n".join(blocks)


def build_trial_task(drafting_dir: Path, proposal_path: Path) -> dict[str, Any]:
    """Verify every sealed packet file and proposal binding before building one task."""
    manifest_raw = (drafting_dir / "packet_manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    if manifest["schema_version"] != "er_commons.task07c.drafting_packet.v1":
        raise ValueError("Unsupported packet schema")
    contents = {}
    for name, binding in manifest["files"].items():
        path = (drafting_dir / name).resolve()
        if not path.is_relative_to(drafting_dir.resolve()):
            raise ValueError("Packet file escapes drafting directory")
        raw = path.read_bytes()
        if _sha(raw) != binding["sha256"] or len(raw) != binding["size_bytes"]:
            raise ValueError(f"Packet checksum mismatch: {name}")
        contents[name] = raw
    source = json.loads(contents["claim_input.json"])
    if source["schema_version"] != "er_commons.task07c.claim_input.v1":
        raise ValueError("Unsupported claim input schema")
    proposal_raw = proposal_path.read_bytes()
    proposal = json.loads(proposal_raw)
    schema = json.loads(contents["proposal.schema.json"])
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(proposal)
    if proposal["input_sha256"] != _sha(contents["claim_input.json"]):
        raise ValueError("Proposal input binding mismatch")
    if proposal["packet_manifest_sha256"] != _sha(manifest_raw):
        raise ValueError("Proposal packet binding mismatch")
    if not (proposal["case_label"] == source["case_label"] == manifest["case_label"]):
        raise ValueError("Case identity mismatch")
    passages = _passages(source)
    concern_ids = [c["concern_id"] for c in source["reviewed_concerns"]]
    if len(set(concern_ids)) != len(concern_ids):
        raise ValueError("Duplicate concern ID")
    response_passages = {p["passage_id"] for r in source["responses"] for p in r["passages"]}
    ids = set()
    for claim in proposal["claims"]:
        _text(claim["text"])
        if claim["claim_id"] in ids:
            raise ValueError("Duplicate claim ID")
        ids.add(claim["claim_id"])
        if not set(claim["concern_ids"]) <= set(concern_ids):
            raise ValueError("Unknown proposal concern")
        if not response_passages.intersection(r["passage_id"] for r in claim["source_refs"]):
            raise ValueError("Each claim requires a response passage, not only a supplement")
        for ref in claim["source_refs"]:
            if ref["passage_id"] not in passages:
                raise ValueError("Unknown proposal passage")
            exact = passages[ref["passage_id"]]["text"]
            quote = _text(ref["quote"])
            start = exact.find(quote)
            if start < 0 or exact.find(quote, start + 1) >= 0:
                raise ValueError("Proposal quote must occur exactly once in its passage")
    coverage = [n["source_ref"] for n in proposal["coverage_notes"]]
    if len(set(coverage)) != len(coverage) or set(coverage) != {
        r["source_ref"] for r in source["responses"]
    }:
        raise ValueError("Coverage notes must uniquely cover all response sources")
    closure = json.loads(contents["response_closure.json"])
    if closure["unresolved_response_mentions"]:
        raise ValueError("Response closure has unresolved referrals")
    if set(closure["response_unit_ids"]) != {r["unit_id"] for r in source["responses"]}:
        raise ValueError("Response closure membership mismatch")
    proposal_text = format_claims(proposal)
    source_html = []
    for ref, passage in passages.items():
        label = passage.get("official_label", "Supplemental source footnote")
        source_html.append(
            f"<h4>{html.escape(ref)} · {html.escape(label)} · "
            f"PDF page {passage['physical_page']}</h4>" + _pre(passage["text"])
        )
    limitations = json.loads(contents["inherited_limitations.json"])
    warning_items = list(source["warnings"])
    if isinstance(limitations, dict):
        coverage_limits = limitations.get("coverage", {})
        if coverage_limits.get("sampled_carries_individually_rereviewed") is False:
            warning_items.append(
                "Some inherited inventory records were reviewed by sampling, not individually."
            )
        figure_count = limitations.get("caption_backed_figures_unavailable_as_text_only_evidence")
        if figure_count:
            warning_items.append(
                f"The inherited inventory contains {figure_count} caption-backed figures "
                "unavailable as text-only evidence."
            )
        edition_warning = limitations.get("final_f1_warning_binding", {}).get("general_warning")
        if edition_warning:
            warning_items.append(edition_warning)
    warning_items.append(
        f"Complete linked-response context: {len(source['responses'])} responses; "
        "no unresolved response referrals."
    )
    data = {
        "case_label": source["case_label"],
        "claim_input": source,
        "original_proposal": proposal,
        "response_closure": closure,
        "inherited_limitations": limitations,
        "form_version": FORM_VERSION,
        "packet_manifest_sha256": _sha(manifest_raw),
        "input_sha256": _sha(contents["claim_input.json"]),
        "proposal_sha256": _sha(proposal_raw),
        "proposal_text": proposal_text,
        "comment_html": _pre(source["original_comment"]["full_text"]),
        "concerns_html": "".join(
            f"<p><strong>{html.escape(c['concern_id'])}</strong> {html.escape(c['text'])}</p>"
            for c in source["reviewed_concerns"]
        ),
        "sources_html": "".join(source_html),
        "proposal_html": "".join(
            f"<h4>{html.escape(c['claim_id'])} · Concerns: "
            + html.escape(", ".join(c["concern_ids"]) or "unassigned")
            + f"</h4><p>{html.escape(c['text'])}</p>"
            + "".join(
                f"<strong>{html.escape(r['passage_id'])}</strong>" + _pre(r["quote"])
                for r in c["source_refs"]
            )
            for c in proposal["claims"]
        ),
        "notes_html": "<h4>Drafting ambiguities</h4><ul>"
        + "".join(f"<li>{html.escape(note)}</li>" for note in proposal["unresolved_issues"])
        + "</ul>",
        "coverage_html": "".join(
            f"<p><strong>{html.escape(note['source_ref'])}</strong> {html.escape(note['note'])}</p>"
            for note in proposal["coverage_notes"]
        ),
        "warnings_html": "<ul>"
        + "".join(f"<li>{html.escape(note)}</li>" for note in warning_items)
        + "</ul>",
    }
    return {
        "data": data,
        "predictions": [
            {
                "model_version": PREDICTION_VERSION,
                "result": [
                    {
                        "from_name": "claims",
                        "to_name": "response_context",
                        "type": "textarea",
                        "value": {"text": [proposal_text]},
                    }
                ],
            }
        ],
    }


def parse_claims(text: str, source: dict[str, Any]) -> list[dict[str, Any]]:
    """Split on claim headers, preserving paragraph breaks and current source bindings."""
    passages = _passages(source)
    concerns = {c["concern_id"] for c in source["reviewed_concerns"]}
    response_passages = {p["passage_id"] for r in source["responses"] for p in r["passages"]}
    claims = []
    ids = set()
    for block in re.split(r"\n(?=[ \t]*C[^|\n]*\|)", _text(text).strip()):
        header, separator, wording = block.partition("\n")
        parts = [p.strip() for p in header.split("|")]
        if len(parts) != 3 or not re.fullmatch(r"C[0-9]{3,}", parts[0]) or not separator:
            raise ValueError("Claims require C001 | Q1,Q2 | R01-P01 followed by claim text")
        local_id, concern_text, passage_text = parts
        if local_id in ids:
            raise ValueError("Duplicate edited claim ID")
        ids.add(local_id)
        concern_refs = (
            [] if concern_text == "unassigned" else [c.strip() for c in concern_text.split(",")]
        )
        refs = [p.strip() for p in passage_text.split(",")]
        if len(set(concern_refs)) != len(concern_refs) or not set(concern_refs) <= concerns:
            raise ValueError("Unknown or duplicate concern reference")
        if len(set(refs)) != len(refs) or not set(refs) <= passages.keys():
            raise ValueError("Unknown or duplicate source reference")
        if not response_passages.intersection(refs):
            raise ValueError("Each claim requires a response passage, not only a supplement")
        claims.append(
            {
                "review_local_id": local_id,
                "text": _text(wording).strip(),
                "concern_ids": concern_refs,
                "source_passages": [passages[ref] for ref in refs],
            }
        )
    return claims


def normalize_review(
    task: dict[str, Any],
    annotation: dict[str, Any],
    *,
    expected_task: dict[str, Any],
    export_lineage: str,
) -> dict[str, Any]:
    """Validate saved human fields against a trusted task and bind edited passages.

    Content-addressed final IDs include case and export lineage. Short C IDs are
    editing references only: retaining one never implies an unchanged claim.
    proposal_local_id is a retained-label association, not split/merge lineage.
    Unresolved reviews preserve malformed partial work without advancing it.
    """
    _text(export_lineage)
    if task.get("data") != expected_task["data"]:
        raise ValueError("Exported task differs from verified packet")
    if annotation.get("was_cancelled") or annotation.get("skipped"):
        raise ValueError("Canceled annotations cannot become reviews")
    if task.get("id") is None or annotation.get("task") != task["id"]:
        raise ValueError("Foreign or unbound task")
    if annotation.get("id") is None or annotation.get("completed_by") is None:
        raise ValueError("Saved annotation and reviewer identities required")
    if task["data"]["form_version"] != FORM_VERSION:
        raise ValueError("Unsupported form")
    fields = {}
    for result in annotation.get("result", []):
        name = result.get("from_name")
        if name not in {"claims", "review_status", "review_note"} or name in fields:
            raise ValueError("Unexpected or duplicate field")
        kind = "choices" if name == "review_status" else "textarea"
        if result.get("to_name") != "response_context" or result.get("type") != kind:
            raise ValueError("Foreign field binding")
        key = "choices" if name == "review_status" else "text"
        value = result.get("value", {})
        values = value.get(key)
        if set(value) != {key} or not isinstance(values, list) or len(values) != 1:
            raise ValueError("Fields require exactly one value")
        if not isinstance(values[0], str):
            raise ValueError("Fields must contain text")
        fields[name] = values[0]
    status = fields.get("review_status")
    if status not in {"approved", "unclear", "needs_context"}:
        raise ValueError("Explicit review status required")
    raw = fields.get("claims", "")
    parse_error = None
    try:
        claims = parse_claims(raw, task["data"]["claim_input"])
    except ValueError as error:
        if status == "approved":
            raise
        claims = []
        parse_error = str(error)
    proposal_ids = {c["claim_id"] for c in task["data"]["original_proposal"]["claims"]}
    for claim in claims:
        identity = {
            "comment_id": task["data"]["claim_input"]["comment_id"],
            "input_sha256": task["data"]["input_sha256"],
            "export_lineage": export_lineage,
            "claim": claim,
        }
        claim["claim_id"] = "claimv1-" + _sha(
            json.dumps(identity, sort_keys=True, ensure_ascii=False).encode()
        )
        local_id = claim["review_local_id"]
        claim["proposal_local_id"] = local_id if local_id in proposal_ids else None
    return {
        "schema_version": "er_commons.task07c.claim_review.v1",
        **{
            k: task["data"][k]
            for k in (
                "case_label",
                "claim_input",
                "original_proposal",
                "response_closure",
                "inherited_limitations",
                "form_version",
                "packet_manifest_sha256",
                "input_sha256",
                "proposal_sha256",
            )
        },
        "claims_text": raw,
        "claims": claims,
        "parse_error": parse_error,
        "review_status": status,
        "review_note": fields.get("review_note", ""),
        "eligible_for_next_stage": status == "approved",
        "export_lineage": export_lineage,
        "task_id": task["id"],
        "annotation_id": annotation["id"],
        "reviewer": annotation["completed_by"],
        "created_at": annotation.get("created_at"),
        "updated_at": annotation.get("updated_at"),
    }


def main() -> None:
    """Prepare a single import file without overwriting any prior artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--drafting-dir", type=Path, required=True)
    prepare.add_argument("--proposal", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    task = build_trial_task(args.drafting_dir, args.proposal)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump([task], handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).info("Wrote one pending claim-review trial: %s", args.output)


if __name__ == "__main__":
    main()
