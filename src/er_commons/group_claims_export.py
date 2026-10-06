"""Normalize saved claim reviews without granting proposal or evidence authority."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime
from typing import Any

VERSION = "task08d.claim_review.v2"
LEGACY_VERSION = "task08d.claim_review.v1"
INVESTIGATION_POLICY = "task08d.investigation.v1"
CHOICES = {"relationship", "decision", "case_status", "links_confirmed", "gaps_status"}
SLOT_FIELDS = {"text", "passages", "relationship", "targets", "rationale", "decision"}
CASE_FIELDS = {"case_status", "case_note", "links_confirmed", "gaps_resolution", "gaps_status"}


def _hash(value: Any) -> str:
    """Hash canonical JSON for exact reviewed content and relationship bindings."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def _digest(value: Any, label: str) -> str:
    """Require an explicit lowercase SHA-256 provenance value."""
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
        raise ValueError(f"{label}: invalid SHA-256")
    return value


def _positive(value: Any, label: str) -> int:
    """Require native positive IDs without accepting booleans."""
    if type(value) is not int or value < 1:
        raise ValueError(f"{label}: positive integer required")
    return value


def _timestamp(value: Any) -> None:
    """Require timezone-qualified native save timestamps."""
    if (
        not isinstance(value, str)
        or datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is None
    ):
        raise ValueError("Saved annotation requires timezone-qualified timestamps")


def _trusted(data: dict[str, Any]) -> None:
    """Check version, frozen question and unique source/slot identities."""
    if data.get("form_version") not in {VERSION, LEGACY_VERSION}:
        raise ValueError("Unrecognized claim form version")
    for key in ("packet_sha256", "proposal_sha256"):
        _digest(data.get(key), key)
    question = data["question"]
    if not question.get("question_id") or not question.get("question_version"):
        raise ValueError("Frozen question identity required")
    if hashlib.sha256(question["text"].encode()).hexdigest() != question["text_sha256"]:
        raise ValueError("Frozen question text hash mismatch")
    for collection, key in (
        (data["slot_bindings"], "slot"),
        (data["slot_bindings"], "claim_id"),
        (data["case_input"]["passages"], "passage_id"),
        (data["proposal"]["question_parts"], "part_id"),
    ):
        values = [item[key] for item in collection]
        if len(set(values)) != len(values) or not all(values):
            raise ValueError(f"Duplicate or empty {key}")
    proposal_ids = {claim["claim_id"] for claim in data["proposal"]["claims"]}
    if len(proposal_ids) != len(data["proposal"]["claims"]):
        raise ValueError("Duplicate proposal claim ID")
    bound_ids = [
        slot["proposal_claim_id"] for slot in data["slot_bindings"] if slot.get("proposal_claim_id")
    ]
    if len(bound_ids) != len(set(bound_ids)) or set(bound_ids) != proposal_ids:
        raise ValueError("Every proposal claim requires exactly one slot")
    if data["form_version"] == VERSION:
        passage_ids = {passage["passage_id"] for passage in data["case_input"]["passages"]}
        for claim in data["proposal"]["claims"]:
            anchors = claim.get("passage_ids")
            if (
                not isinstance(anchors, list)
                or not anchors
                or any(not isinstance(anchor, str) for anchor in anchors)
                or len(set(anchors)) != len(anchors)
                or any(anchor not in passage_ids for anchor in anchors)
            ):
                raise ValueError("Invalid trusted proposal source passage anchors")
    for passage in data["case_input"]["passages"]:
        if not isinstance(passage.get("text"), str) or not passage["text"].strip():
            raise ValueError("Nonempty exact source text required")
        if (
            "text_sha256" in passage
            and hashlib.sha256(passage["text"].encode()).hexdigest() != passage["text_sha256"]
        ):
            raise ValueError("Source passage text hash mismatch")


def _fields(annotation: dict[str, Any], data: dict[str, Any]) -> dict[str, str]:
    """Read saved native controls exclusively, rejecting duplicate or foreign controls."""
    names = {
        f"{slot['slot']}_{field}": field
        for slot in data["slot_bindings"]
        for field in _slot_fields(data)
    }
    names.update({key: key for key in CASE_FIELDS})
    results = annotation.get("result")
    if not isinstance(results, list):
        raise ValueError("Native result list required")
    fields: dict[str, str] = {}
    for result in results:
        name = result.get("from_name")
        if name not in names or name in fields:
            raise ValueError("Unknown or duplicate native control")
        kind, key = ("choices", "choices") if names[name] in CHOICES else ("textarea", "text")
        if result.get("to_name") != "response_context" or result.get("type") != kind:
            raise ValueError("Foreign native control binding")
        value = result.get("value")
        if not isinstance(value, dict) or set(value) != {key}:
            raise ValueError("Malformed native value")
        values = value[key]
        if not isinstance(values, list) or len(values) != 1 or not isinstance(values[0], str):
            raise ValueError("Exactly one native value required")
        fields[name] = values[0]
    return fields


def _ids(value: str) -> list[str]:
    """Parse explicit comma-separated IDs without inventing targets or anchors."""
    return [item.strip() for item in value.split(",") if item.strip()]


def _slot_fields(data: dict[str, Any]) -> set[str]:
    """Keep legacy native anchors readable; v2 anchors are exclusively trusted data."""
    return SLOT_FIELDS if data["form_version"] == LEGACY_VERSION else SLOT_FIELDS - {"passages"}


def _claims(
    data: dict[str, Any], fields: dict[str, str], *, policy_revision: str | None = None
) -> tuple[list[dict[str, Any]], list[str]]:
    """Retain every proposed or populated claim and collect review-blocking errors."""
    passages = {p["passage_id"]: p for p in data["case_input"]["passages"]}
    parts = {p["part_id"] for p in data["proposal"]["question_parts"]}
    proposals = {claim["claim_id"]: claim for claim in data["proposal"]["claims"]}
    claims: list[dict[str, Any]] = []
    errors: list[str] = []
    for binding in data["slot_bindings"]:
        values = {key: fields.get(f"{binding['slot']}_{key}", "") for key in _slot_fields(data)}
        if not binding.get("proposal_claim_id") and not any(
            value.strip() for value in values.values()
        ):
            continue
        claim = {**copy.deepcopy(binding), **values}
        if data["form_version"] == LEGACY_VERSION:
            claim["passage_ids"] = _ids(values["passages"])
        else:
            proposal = proposals.get(binding.get("proposal_claim_id"))
            claim["passage_ids"] = copy.deepcopy(proposal["passage_ids"]) if proposal else []
            claim["source_binding_origin"] = "trusted_proposal" if proposal else "unbound_addition"
        claim["targets"] = _ids(values["targets"])
        claim["source_spans"] = [
            copy.deepcopy(passages[p]) for p in claim["passage_ids"] if p in passages
        ]
        claim["source_spans_sha256"] = _hash(claim["source_spans"])
        claim["text_sha256"] = hashlib.sha256(values["text"].encode()).hexdigest()
        claim["errors"] = []
        if values["decision"] not in {"approve", "reject", "unresolved"}:
            claim["errors"].append("explicit claim disposition missing")
        if values["decision"] == "unresolved":
            claim["errors"].append("unresolved claim blocks case")
        if values["decision"] == "approve":
            if claim.get("source_binding_origin") == "unbound_addition":
                claim["errors"].append("new claim requires source-bound re-review before approval")
            if not values["text"].strip():
                claim["errors"].append("approved text is blank")
            if (
                not claim["passage_ids"]
                or len(set(claim["passage_ids"])) != len(claim["passage_ids"])
                or any(p not in passages for p in claim["passage_ids"])
            ):
                claim["errors"].append("invalid source passage anchors")
            relation = values["relationship"]
            targets = claim["targets"]
            if relation not in {"direct", "supporting", "not-relevant", "unclear"}:
                claim["errors"].append("invalid relationship")
            elif relation == "direct" and (
                not targets
                or len(set(targets)) != len(targets)
                or any(t not in parts for t in targets)
            ):
                claim["errors"].append("direct claim requires known question-part targets")
            elif relation == "supporting" and (
                len(targets) != 1 or not values["rationale"].strip()
            ):
                claim["errors"].append(
                    "support requires one claim target and material contribution rationale"
                    if policy_revision == INVESTIGATION_POLICY
                    else "support requires one direct target and material contribution rationale"
                )
            elif relation in {"not-relevant", "unclear"} and targets:
                claim["errors"].append("nonadvancing relationship cannot carry targets")
            if relation == "unclear":
                claim["errors"].append("unclear relationship blocks case")
        claims.append(claim)
    if policy_revision == INVESTIGATION_POLICY:
        _support_chains(claims)
        return claims, [f"{c['claim_id']}: {error}" for c in claims for error in c["errors"]]
    by_id = {claim["claim_id"]: claim for claim in claims}
    for claim in claims:
        if (
            claim["decision"] == "approve"
            and claim["relationship"] == "supporting"
            and len(claim["targets"]) == 1
        ):
            target = by_id.get(claim["targets"][0])
            if (
                target is None
                or target["decision"] != "approve"
                or target["relationship"] != "direct"
                or target["errors"]
            ):
                claim["errors"].append("support target is not an approved usable direct claim")
            else:
                claim["target_content_sha256"] = _hash(
                    {
                        key: target[key]
                        for key in (
                            "text",
                            "passage_ids",
                            "source_spans_sha256",
                            "relationship",
                            "targets",
                        )
                    }
                )
        errors.extend(f"{claim['claim_id']}: {error}" for error in claim["errors"])
    return claims, errors


def _support_chains(claims: list[dict[str, Any]]) -> None:
    """Bind each support path to approved usable claims ending at a direct claim.

    Inspect the original per-claim errors so validation is independent of slot order.
    Every supporting edge retains its own material-contribution rationale.
    """
    by_id = {claim["claim_id"]: claim for claim in claims}
    invalid = {claim["claim_id"] for claim in claims if claim["errors"]}
    content_keys = (
        "text",
        "passage_ids",
        "source_spans_sha256",
        "relationship",
        "targets",
        "rationale",
    )
    for claim in claims:
        if claim["decision"] != "approve" or claim["relationship"] != "supporting":
            continue
        current = claim
        seen = {claim["claim_id"]}
        chain = []
        while current["relationship"] == "supporting":
            targets = current["targets"]
            target = by_id.get(targets[0]) if len(targets) == 1 else None
            if (
                target is None
                or target["claim_id"] in seen
                or target["claim_id"] in invalid
                or target["decision"] != "approve"
                or target["relationship"] not in {"direct", "supporting"}
            ):
                claim["errors"].append(
                    "support chain must be acyclic and end at an approved usable direct claim"
                )
                break
            seen.add(target["claim_id"])
            chain.append(
                {
                    "claim_id": target["claim_id"],
                    "content_sha256": _hash({key: target.get(key, "") for key in content_keys}),
                }
            )
            current = target
        else:
            claim["target_content_sha256"] = chain[0]["content_sha256"]
            claim["support_chain"] = chain
            claim["support_chain_sha256"] = _hash(chain)


def _record(
    task: dict[str, Any], reviewer_id: int, *, policy_revision: str | None = None
) -> dict[str, Any]:
    """Preserve drafts, holds and stops; release only a fully bound ready case."""
    data = task["data"]
    record = {
        key: copy.deepcopy(data[key])
        for key in ("case_id", "question", "packet_sha256", "proposal_sha256", "form_version")
    }
    record.update(
        task_id=task["id"],
        state="unreviewed",
        claims=[],
        approved_claims=[],
        errors=[],
        provenance=None,
    )
    annotations, drafts = task.get("annotations"), task.get("drafts")
    if not isinstance(annotations, list) or not isinstance(drafts, list):
        raise ValueError("Native annotations and drafts must be lists")
    if len(annotations) > 1:
        raise ValueError("Multiple annotations require explicit reconciliation")
    if drafts:
        record["state"] = "pending_draft"
        return record
    if not annotations:
        return record
    annotation = annotations[0]
    if annotation.get("was_cancelled") or annotation.get("skipped"):
        record["state"] = "pending_cancelled"
        return record
    _positive(annotation.get("id"), "Annotation ID")
    if type(annotation.get("task")) is not int or annotation["task"] != task["id"]:
        raise ValueError("Foreign annotation task binding")
    reviewer = annotation.get("completed_by")
    actual = reviewer.get("id") if isinstance(reviewer, dict) else reviewer
    if _positive(actual, "Reviewer ID") != reviewer_id:
        raise ValueError("Foreign reviewer binding")
    for key in ("created_at", "updated_at"):
        _timestamp(annotation.get(key))
    fields = _fields(annotation, data)
    claims, errors = _claims(data, fields, policy_revision=policy_revision)
    status = fields.get("case_status")
    if status not in {"ready", "unresolved", "stop"}:
        errors.append("explicit case status missing")
    if status in {"unresolved", "stop"} and not fields.get("case_note", "").strip():
        errors.append("case hold or stop requires explanation")
    addressed = {
        target
        for claim in claims
        if claim["decision"] == "approve"
        and claim["relationship"] == "direct"
        and not claim["errors"]
        for target in claim["targets"]
    }
    gaps = [
        part
        for part in data["proposal"]["question_parts"]
        if part["status"] != "addressed" or part["part_id"] not in addressed
    ]
    gaps_status = fields.get("gaps_status")
    if gaps_status not in {"resolved", "unresolved", "not-applicable"}:
        errors.append("explicit question-gap disposition missing")
    investigation_scope = policy_revision == INVESTIGATION_POLICY and gaps_status == "unresolved"
    if gaps_status == "unresolved" and not investigation_scope:
        errors.append("unresolved question scope blocks case")
    if (
        gaps
        and not investigation_scope
        and (gaps_status != "resolved" or not fields.get("gaps_resolution", "").strip())
    ):
        errors.append("unanswered or unclear question parts require explicit human resolution")
    if fields.get("links_confirmed") != "confirmed":
        errors.append("current exact claim relationships not confirmed")
    direct = [
        c
        for c in claims
        if c["decision"] == "approve" and c["relationship"] == "direct" and not c["errors"]
    ]
    if not direct:
        errors.append("no usable approved direct claim")
    provenance = {
        key: copy.deepcopy(annotation[key])
        for key in ("id", "completed_by", "created_at", "updated_at")
    }
    provenance["annotation_sha256"] = _hash(annotation)
    provenance["task_data_sha256"] = _hash(data)
    record.update(
        state=status or "incomplete",
        claims=claims,
        errors=errors,
        fields=fields,
        provenance=provenance,
        question_parts=copy.deepcopy(data["proposal"]["question_parts"]),
    )
    if policy_revision == INVESTIGATION_POLICY:
        record.update(
            policy_revision=policy_revision,
            investigation_only=True,
            scope_unresolved=gaps_status == "unresolved",
            unresolved_question_parts=copy.deepcopy(gaps),
            eligibility="undecided",
            advancement_scope="08E_investigation_only" if status == "ready" else None,
        )
    if status == "ready":
        if errors:
            raise ValueError(f"Ready case {data['case_id']} is invalid: {'; '.join(errors)}")
        for claim in claims:
            claim["claim_version"] = _hash(
                {
                    "claim": claim,
                    "question": data["question"],
                    "provenance": provenance,
                    "project_id": task["project"],
                    **({"policy_revision": policy_revision} if policy_revision else {}),
                }
            )
        record["approved_claims"] = copy.deepcopy(
            [
                c
                for c in claims
                if c["decision"] == "approve" and c["relationship"] in {"direct", "supporting"}
            ]
        )
        record["approved_claims"].sort(key=lambda c: c["relationship"] != "direct")
        versions = {c["claim_id"]: c["claim_version"] for c in record["approved_claims"]}
        for claim in record["approved_claims"]:
            if claim["relationship"] == "supporting":
                claim["target_claim_version"] = versions[claim["targets"][0]]
                if policy_revision == INVESTIGATION_POLICY:
                    claim["support_chain_versions"] = [
                        {**binding, "claim_version": versions[binding["claim_id"]]}
                        for binding in claim["support_chain"]
                    ]
    return record


def normalize_export(
    native_tasks: list[dict[str, Any]],
    trusted_tasks: list[dict[str, Any]],
    *,
    project_id: int,
    reviewer_id: int,
    export_sha256: str,
    policy_revision: str | None = None,
) -> dict[str, Any]:
    """Validate complete native saved reviews against independently trusted inputs.

    Every disposition and raw native history survives; only ready, confirmed cases
    advance. Unresolved claims conservatively block the whole case.
    """
    if policy_revision not in {None, INVESTIGATION_POLICY}:
        raise ValueError("Unrecognized claim review policy revision")
    _positive(project_id, "Project ID")
    _positive(reviewer_id, "Reviewer ID")
    _digest(export_sha256, "Native export")
    expected = {}
    for task in trusted_tasks:
        data = task["data"]
        _trusted(data)
        if data["case_id"] in expected:
            raise ValueError("Duplicate trusted case")
        expected[data["case_id"]] = data
    if not expected:
        raise ValueError("Trusted case set must be nonempty")
    versions = {data["form_version"] for data in expected.values()}
    if len(versions) != 1:
        raise ValueError("Mixed claim form versions require separate exports")
    records, seen, task_ids, annotation_ids = [], set(), set(), set()
    for task in native_tasks:
        data = task.get("data", {})
        case_id = data.get("case_id")
        if case_id not in expected or case_id in seen or data != expected[case_id]:
            raise ValueError("Native case differs from exact trusted input")
        task_id = _positive(task.get("id"), "Task ID")
        if (
            task_id in task_ids
            or type(task.get("project")) is not int
            or task["project"] != project_id
        ):
            raise ValueError("Duplicate task or foreign project binding")
        record = _record(task, reviewer_id, policy_revision=policy_revision)
        for annotation in task["annotations"]:
            annotation_id = _positive(annotation.get("id"), "Annotation ID")
            if annotation_id in annotation_ids:
                raise ValueError("Duplicate annotation ID")
            annotation_ids.add(annotation_id)
        records.append(record)
        seen.add(case_id)
        task_ids.add(task_id)
    if seen != expected.keys():
        raise ValueError("Export must include every trusted case")
    positions = {key: i for i, key in enumerate(expected)}
    records.sort(key=lambda r: positions[r["case_id"]])
    return {
        **(
            {
                "policy_revision": policy_revision,
                "advancement_scope": "08E_investigation_only",
                "eligibility": "undecided",
            }
            if policy_revision
            else {}
        ),
        "schema_version": next(iter(versions)),
        "project_id": project_id,
        "reviewer_id": reviewer_id,
        "export_sha256": export_sha256,
        "records": records,
        "native_tasks": copy.deepcopy(native_tasks),
        "advancing_case_ids": [r["case_id"] for r in records if r["state"] == "ready"],
        "status": "complete"
        if all(
            r["state"] in {"ready", "stop"}
            and not (r["state"] == "stop" and not r.get("fields", {}).get("case_note", "").strip())
            for r in records
        )
        else "incomplete",
    }
