"""Build immutable combined claim/relevance tasks and validate native reviews."""

import argparse
import copy
import hashlib
import html
import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any

from er_commons import pilot_claims

FORM_VERSION = "task07c1.fixed_slots.v1"
PREDICTION_VERSION = "task07c1.claim_relevance.v1"
RELATIONSHIPS = {"direct", "supporting", "not_relevant", "unclear"}
OBJECT_NAME = "response_context"


def _hash(value: Any) -> str:
    """Hash a JSON value deterministically without altering the saved value."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def _text(value: Any) -> str:
    """Require substantive text while preserving original whitespace."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected nonempty text")
    return value


def _unique(values: Any) -> list[str]:
    """Require a list of distinct nonempty reference strings."""
    if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values):
        raise ValueError("References must be nonempty strings")
    if len(values) != len(set(values)):
        raise ValueError("Duplicate reference")
    return values


def _graph_errors(claims: list[dict[str, Any]], concerns: set[str]) -> list[str]:
    """Validate target types and every supporting path, including cycles."""
    indexed = {c["claim_id"]: c for c in claims}
    errors = []
    for claim in claims:
        relation = claim["relationship"]
        questions = claim["concern_ids"]
        targets = claim["supporting_claim_ids"]
        if relation not in RELATIONSHIPS:
            errors.append(f"{claim['local_id']}: unknown relationship")
        elif relation == "direct":
            if not questions or targets or not set(questions) <= concerns:
                errors.append(f"{claim['local_id']}: direct requires known concern targets only")
        elif relation == "supporting":
            if questions or not targets:
                errors.append(f"{claim['local_id']}: supporting requires claim targets only")
        elif questions or targets:
            errors.append(f"{claim['local_id']}: {relation} requires no targets")

    def reaches_direct(identity: str, visiting: set[str]) -> bool:
        """Require all paths to reach a direct claim without revisiting a node."""
        if identity in visiting or identity not in indexed:
            return False
        claim = indexed[identity]
        if claim["relationship"] == "direct":
            return bool(claim["concern_ids"]) and set(claim["concern_ids"]) <= concerns
        return (
            claim["relationship"] == "supporting"
            and bool(claim["supporting_claim_ids"])
            and all(
                reaches_direct(target, visiting | {identity})
                for target in claim["supporting_claim_ids"]
            )
        )

    for claim in claims:
        if claim["relationship"] == "supporting" and not reaches_direct(claim["claim_id"], set()):
            errors.append(f"{claim['local_id']}: dangling, circular, or non-direct supporting path")
    return errors


def _slot_binding(proposal_id: str, ordinal: int) -> dict[str, Any]:
    """Allocate a persistent spare identity distinct from its UI position."""
    return {
        "slot": f"s{ordinal:03d}",
        "claim_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{proposal_id}/addition/{ordinal}")),
        "local_id": f"C{ordinal:03d}",
        "proposal_claim_id": None,
    }


def _slot_display(binding: dict[str, Any], claim: dict[str, Any] | None) -> str:
    """Present immutable model reasoning and quotations alongside editable fields."""
    if claim is None:
        return "<p>Unused addition slot. Leave all fields blank unless adding a claim.</p>"
    esc = html.escape
    return (
        f"<p><strong>Model proposal:</strong> {esc(claim['text'])}</p>"
        f"<p><strong>Proposed relationship:</strong> {esc(claim['relationship'])}</p>"
        f"<p><strong>Model rationale:</strong> {esc(claim['rationale'])}</p>"
        f"<p><strong>Prior edit provenance:</strong> {esc(claim['prior_edit_note'])}</p>"
        + "".join(
            f"<p><strong>{esc(r['passage_id'])}</strong></p>{pilot_claims._pre(r['quote'])}"
            for r in claim["source_refs"]
        )
    )


def _coverage_display(proposal: dict[str, Any]) -> str:
    """Render coverage using reviewer aliases while preserving raw inventory separately."""
    aliases = {claim["claim_id"]: claim["local_id"] for claim in proposal["claims"]}
    headings = {
        "claim": "Claim",
        "repetition": "Repeated argument",
        "non_substantive": "Source context",
    }
    blocks = []
    for item in proposal["coverage"]:
        entries = []
        for entry in item["entries"]:
            references = ", ".join(aliases[identity] for identity in entry["claim_ids"])
            label = headings[entry["kind"]] + (f" · {references}" if references else "")
            entries.append(
                f"<li><strong>{html.escape(label)}</strong>: {html.escape(entry['note'])}</li>"
            )
        blocks.append(f"<h4>{html.escape(item['passage_id'])}</h4><ul>{''.join(entries)}</ul>")
    return "".join(blocks)


def _result(name: str, value: str, *, choices: bool = False) -> dict[str, Any]:
    """Create one explicitly bound native field result."""
    return {
        "from_name": name,
        "to_name": OBJECT_NAME,
        "type": "choices" if choices else "textarea",
        "value": {"choices" if choices else "text": [value]},
    }


def build_trial_task(
    drafting_dir: Path,
    predecessor_proposal_path: Path,
    proposal_path: Path,
    *,
    slot_count: int | None = None,
) -> dict[str, Any]:
    """Verify predecessor/source bindings and build an unapproved fixed-slot task."""
    predecessor = pilot_claims.build_trial_task(drafting_dir, predecessor_proposal_path)
    data = copy.deepcopy(predecessor["data"])
    raw = proposal_path.read_bytes()
    proposal = json.loads(raw)
    if proposal["schema_version"] != "er_commons.task07c1.proposal.v1":
        raise ValueError("Unsupported proposal schema")
    _text(proposal["proposal_id"])
    if proposal.get("case_label") != data["case_label"]:
        raise ValueError("Proposal case identity mismatch")
    for name in ("input_sha256", "packet_manifest_sha256"):
        if proposal[name] != data[name]:
            raise ValueError(f"Proposal {name} binding mismatch")
    prior = proposal["predecessor_review"]
    prior_raw = Path(prior["path"]).read_bytes()
    if hashlib.sha256(prior_raw).hexdigest() != prior["sha256"]:
        raise ValueError("Predecessor review hash mismatch")
    prior_reviews = json.loads(prior_raw)
    candidates = prior_reviews if isinstance(prior_reviews, list) else [prior_reviews]
    matches = [r for r in candidates if r.get("case_label") == data["case_label"]]
    if len(matches) != 1:
        raise ValueError("Predecessor review requires exactly one matching case")
    prior_review = matches[0]
    if prior_review.get("review_status") != "approved":
        raise ValueError("Predecessor review must be approved")
    if prior_review.get("case_label") != data["case_label"]:
        raise ValueError("Predecessor review case mismatch")
    if prior_review.get("input_sha256") != data["input_sha256"]:
        raise ValueError("Predecessor review input mismatch")
    for name in ("task_id", "annotation_id", "reviewer"):
        if name in prior and prior[name] != prior_review.get(name):
            raise ValueError(f"Predecessor review {name} identity mismatch")
    claims = proposal["claims"]
    if not claims:
        raise ValueError("Proposal requires claims")
    ids = _unique([c["claim_id"] for c in claims])
    aliases = _unique([c["local_id"] for c in claims])
    if any(not re.fullmatch(r"C[0-9]{3,}", alias) for alias in aliases):
        raise ValueError("Claim aliases require Cnnn")
    passages = pilot_claims._passages(data["claim_input"])
    response_ids = {
        p["passage_id"] for r in data["claim_input"]["responses"] for p in r["passages"]
    }
    for claim in claims:
        for name in ("text", "rationale"):
            _text(claim[name])
        if not isinstance(claim["prior_edit_note"], str):
            raise ValueError("Prior edit note must be text")
        _unique(claim["concern_ids"])
        _unique(claim["supporting_claim_ids"])
        refs = list(dict.fromkeys(r["passage_id"] for r in claim["source_refs"]))
        pairs = [(r["passage_id"], r["quote"]) for r in claim["source_refs"]]
        if len(pairs) != len(set(pairs)):
            raise ValueError("Duplicate exact source reference")
        if not set(refs) <= passages.keys() or not response_ids.intersection(refs):
            raise ValueError("Claims require known response passages")
        for ref in claim["source_refs"]:
            exact, quote = passages[ref["passage_id"]]["text"], _text(ref["quote"])
            start = exact.find(quote)
            if start < 0 or exact.find(quote, start + 1) >= 0:
                raise ValueError("Proposal quote must occur exactly once")
    concerns = {c["concern_id"] for c in data["claim_input"]["reviewed_concerns"]}
    errors = _graph_errors(claims, concerns)
    if errors:
        raise ValueError("; ".join(errors))
    coverage_ids = _unique([c["passage_id"] for c in proposal["coverage"]])
    if set(coverage_ids) != passages.keys():
        raise ValueError("Coverage must inventory every passage")
    covered_claims: set[str] = set()
    claim_passages = {
        claim["claim_id"]: {ref["passage_id"] for ref in claim["source_refs"]} for claim in claims
    }
    for item in proposal["coverage"]:
        if not item["entries"]:
            raise ValueError("Coverage requires explicit entries")
        for entry in item["entries"]:
            refs = _unique(entry["claim_ids"])
            _text(entry["note"])
            if entry["kind"] not in {"claim", "repetition", "non_substantive"}:
                raise ValueError("Unknown coverage disposition")
            if not set(refs) <= set(ids):
                raise ValueError("Unknown coverage claim")
            if (entry["kind"] == "non_substantive") != (not refs):
                raise ValueError("Coverage disposition and claim targets disagree")
            if any(item["passage_id"] not in claim_passages[identity] for identity in refs):
                raise ValueError("Coverage claim is not bound to this passage")
            covered_claims.update(refs)
    if covered_claims != set(ids):
        raise ValueError("Coverage must account for every proposal claim")
    capacity = len(claims) + 4 if slot_count is None else slot_count
    if capacity < len(claims) + 4:
        raise ValueError("Capacity requires at least four spare slots")
    bindings, results = [], []
    id_to_alias = dict(zip(ids, aliases, strict=True))
    next_alias = max(int(alias[1:]) for alias in aliases) + 1
    for index in range(1, capacity + 1):
        claim = claims[index - 1] if index <= len(claims) else None
        binding = _slot_binding(proposal["proposal_id"], index)
        if claim:
            binding.update(
                claim_id=claim["claim_id"],
                local_id=claim["local_id"],
                proposal_claim_id=claim["claim_id"],
            )
        else:
            binding["local_id"] = f"C{next_alias:03d}"
            next_alias += 1
        bindings.append(binding)
        slot = binding["slot"]
        data[f"{slot}_title"] = binding["local_id"]
        data[f"{slot}_proposal_html"] = _slot_display(binding, claim)
        if claim:
            targets = claim["concern_ids"] or [
                id_to_alias[target] for target in claim["supporting_claim_ids"]
            ]
            for suffix, value in (
                ("text", claim["text"]),
                (
                    "passages",
                    ",".join(dict.fromkeys(r["passage_id"] for r in claim["source_refs"])),
                ),
                ("relationship", claim["relationship"]),
                ("targets", ",".join(targets)),
            ):
                if value:
                    results.append(
                        _result(f"{slot}_{suffix}", value, choices=suffix == "relationship")
                    )
    data.update(
        form_version=FORM_VERSION,
        original_proposal=proposal,
        predecessor_proposal=predecessor["data"]["original_proposal"],
        predecessor_review=prior_review,
        proposal_sha256=hashlib.sha256(raw).hexdigest(),
        slot_bindings=bindings,
        slot_count=capacity,
        proposal_html="".join(data[f"{b['slot']}_proposal_html"] for b in bindings),
        proposal_text="",
        notes_html="",
        coverage_html=_coverage_display(proposal),
    )
    # Historical policy is preserved in claim_input, but must not contradict this form.
    for warning in data["claim_input"]["warnings"]:
        if "extract only relevant claims" in warning:
            data["warnings_html"] = data["warnings_html"].replace(
                f"<li>{html.escape(warning)}</li>", ""
            )
    data["warnings_html"] += (
        "<p><strong>Replacement policy:</strong> Retain all substantive response claims, "
        "including not-relevant claims. Historical relevance-only extraction instructions "
        "are superseded. These are unreviewed model suggestions, not evidence findings.</p>"
    )
    for warning in proposal.get("warnings", []):
        data["warnings_html"] += f"<p>{html.escape(_text(warning))}</p>"
    return {"data": data, "predictions": [{"model_version": PREDICTION_VERSION, "result": results}]}


def _fields(annotation: dict[str, Any], bindings: list[dict[str, Any]]) -> dict[str, str]:
    """Decode native controls while rejecting foreign, duplicate, or malformed fields."""
    allowed = {"review_status": True, "review_note": False}
    for binding in bindings:
        for suffix in ("text", "passages", "relationship", "targets", "remove"):
            allowed[f"{binding['slot']}_{suffix}"] = suffix in {"relationship", "remove"}
    fields = {}
    for result in annotation.get("result", []):
        name = result.get("from_name")
        if name not in allowed or name in fields:
            raise ValueError("Unknown or duplicate field")
        choice = allowed[name]
        if result.get("to_name") != OBJECT_NAME or result.get("type") != (
            "choices" if choice else "textarea"
        ):
            raise ValueError("Foreign field binding")
        key = "choices" if choice else "text"
        value = result.get("value", {})
        values = value.get(key)
        if set(value) != {key} or not isinstance(values, list) or len(values) > 1:
            raise ValueError("Fields require at most one value")
        if values and not isinstance(values[0], str):
            raise ValueError("Fields require text values")
        fields[name] = values[0] if values else ""
    return fields


def _refs(value: str) -> list[str]:
    """Parse optional comma-separated references without hiding duplicates."""
    return _unique([v.strip() for v in value.split(",")]) if value.strip() else []


def normalize_review(
    task: dict[str, Any],
    annotation: dict[str, Any],
    *,
    expected_task: dict[str, Any],
    export_lineage: str,
) -> dict[str, Any]:
    """Preserve human edits and partial work; validate approved source and relevance maps."""
    _text(export_lineage)
    if task.get("data") != expected_task["data"]:
        raise ValueError("Exported task differs from verified packet")
    if task.get("id") is None or annotation.get("task") != task["id"]:
        raise ValueError("Foreign or unbound task")
    if annotation.get("id") is None or annotation.get("completed_by") is None:
        raise ValueError("Saved annotation and reviewer identities required")
    if annotation.get("was_cancelled") or annotation.get("skipped"):
        raise ValueError("Canceled annotations cannot become reviews")
    data = task["data"]
    if data["form_version"] != FORM_VERSION:
        raise ValueError("Unsupported form")
    fields = _fields(annotation, data["slot_bindings"])
    status = fields.get("review_status")
    if status not in {"approved", "unclear", "needs_context"}:
        raise ValueError("Explicit review status required")
    passages = pilot_claims._passages(data["claim_input"])
    response_ids = {
        p["passage_id"] for r in data["claim_input"]["responses"] for p in r["passages"]
    }
    aliases = {b["local_id"]: b["claim_id"] for b in data["slot_bindings"]}
    concerns = {c["concern_id"] for c in data["claim_input"]["reviewed_concerns"]}
    claims: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    unused_slot_removals: list[dict[str, Any]] = []
    errors: list[str] = []
    for binding in data["slot_bindings"]:
        slot = binding["slot"]
        raw = {
            key: fields.get(f"{slot}_{key}", "")
            for key in ("text", "passages", "relationship", "targets", "remove")
        }
        try:
            if raw["remove"] not in {"", "remove"}:
                raise ValueError("Unknown removal value")
            if raw["remove"]:
                # A removal click on an unused addition slot is not a deleted claim.
                destination = (
                    removed
                    if binding["proposal_claim_id"] or raw["text"].strip()
                    else unused_slot_removals
                )
                destination.append({**binding, "saved_fields": raw})
                continue
            if not any(raw.values()):
                if binding["proposal_claim_id"]:
                    raise ValueError("Proposed claim requires explicit removal")
                continue
            text = _text(raw["text"])
            refs = _refs(raw["passages"])
            if not set(refs) <= passages.keys() or not response_ids.intersection(refs):
                raise ValueError("Claims require known response passages")
            relation = raw["relationship"]
            if relation not in RELATIONSHIPS:
                raise ValueError("Unknown or missing relationship")
            targets = _refs(raw["targets"])
            if relation == "supporting" and not set(targets) <= aliases.keys():
                raise ValueError("Unknown supporting target")
            claim = {
                **binding,
                "text": text,
                "relationship": relation,
                "concern_ids": targets if relation == "direct" else [],
                "supporting_claim_ids": [aliases[t] for t in targets]
                if relation == "supporting"
                else [],
                "source_passages": [passages[r] for r in refs],
                "saved_fields": raw,
            }
            if relation in {"unclear", "not_relevant"} and targets:
                raise ValueError("Unclear/not-relevant claims require no targets")
            claim["revision_sha256"] = _hash(claim)
            claims.append(claim)
        except ValueError as error:
            errors.append(f"{binding['local_id']}: {error}")
    errors.extend(_graph_errors(claims, concerns))
    if not claims:
        errors.append("Review requires at least one retained claim")
    if status == "approved" and errors:
        raise ValueError("; ".join(errors))
    approved = status == "approved" and not errors
    held = [c["claim_id"] for c in claims if c["relationship"] == "unclear"]
    evidence = [c["claim_id"] for c in claims if c["relationship"] in {"direct", "supporting"}]
    return {
        "schema_version": "er_commons.task07c1.review.v1",
        "data": copy.deepcopy(data),
        "case_label": data["case_label"],
        "input_sha256": data["input_sha256"],
        "claims": claims,
        "removed_claims": removed,
        "unused_slot_removals": unused_slot_removals,
        "added_claim_ids": [c["claim_id"] for c in claims if c["proposal_claim_id"] is None],
        "validation_errors": errors,
        "review_status": status,
        "review_note": fields.get("review_note", ""),
        "held_claim_ids": held,
        "evidence_candidate_claim_ids": evidence if approved else [],
        "whole_case_ready": approved and not held,
        "eligible_for_next_stage": approved and not held,
        "export_lineage": export_lineage,
        "task_id": task["id"],
        "annotation_id": annotation["id"],
        "reviewer": annotation["completed_by"],
        "created_at": annotation.get("created_at"),
        "updated_at": annotation.get("updated_at"),
        "native_annotation": copy.deepcopy(annotation),
        "annotation_sha256": _hash(annotation),
    }


def expand_task(
    task: dict[str, Any],
    new_count: int,
    annotation: dict[str, Any],
) -> dict[str, Any]:
    """Prepare a larger task without modifying prior controls, identities, or human fields."""
    expanded = copy.deepcopy(task)
    data = expanded["data"]
    if new_count <= data["slot_count"]:
        raise ValueError("Overflow capacity must increase")
    if data["form_version"] != FORM_VERSION:
        raise ValueError("Unsupported form")
    if task.get("id") is not None and annotation.get("task") != task["id"]:
        raise ValueError("Foreign migration annotation")
    _fields(annotation, data["slot_bindings"])
    next_alias = max(int(b["local_id"][1:]) for b in data["slot_bindings"]) + 1
    for ordinal in range(data["slot_count"] + 1, new_count + 1):
        binding = _slot_binding(data["original_proposal"]["proposal_id"], ordinal)
        binding["local_id"] = f"C{next_alias:03d}"
        next_alias += 1
        data["slot_bindings"].append(binding)
        data[f"{binding['slot']}_title"] = binding["local_id"]
        data[f"{binding['slot']}_proposal_html"] = _slot_display(binding, None)
    data["slot_count"] = new_count
    expanded.pop("id", None)
    expanded.pop("annotations", None)
    expanded.pop("drafts", None)
    expanded["migration"] = {
        "source_task_id": task.get("id"),
        "source_task_sha256": _hash(task),
        "native_annotation": copy.deepcopy(annotation),
        "annotation_sha256": _hash(annotation),
        "instruction": "Rebind task/reviewer identity only after reconciled native migration.",
    }
    return expanded


def main() -> None:
    """Prepare one fresh task import with explicit paths and no overwrite."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    for flag in ("drafting-dir", "predecessor-proposal", "proposal", "output"):
        prepare.add_argument(f"--{flag}", type=Path, required=True)
    prepare.add_argument("--slots", type=int)
    args = parser.parse_args()
    task = build_trial_task(
        args.drafting_dir,
        args.predecessor_proposal,
        args.proposal,
        slot_count=args.slots,
    )
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump([task], handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).info("Wrote one pending combined review task: %s", args.output)


if __name__ == "__main__":
    main()
