"""Investigation-only Task08E intake and native review; no automatic advancement."""

import copy
import hashlib
import html
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons import group_claims, group_claims_export
from er_commons import group_evidence as shared
from er_commons import group_evidence_cards as cards
from er_commons import pilot_evidence as evidence
from er_commons.group_evidence_transport import hydrate_tasks
from er_commons.group_ranking import digest as byte_digest
from er_commons.group_ranking import encoded

VERSION = "task08e.evidence_review.v2"
ELIGIBILITY_VERSION = "task08e.eligibility_review.v2"


def load_handoff(path: Path, expected_sha256: str) -> dict[str, Any]:
    """Verify sealed bytes, replay saved upstream decisions and retain every gap."""
    if byte_digest(path.read_bytes()) != expected_sha256:
        raise ValueError("Accepted handoff checksum differs")
    handoff: dict[str, Any] = json.loads(path.read_bytes())
    completion = json.loads((path.parent / "completion.json").read_bytes())
    for name, checksum in completion["files"].items():
        if Path(name).name != name or byte_digest((path.parent / name).read_bytes()) != checksum:
            raise ValueError("Upstream export closure differs")
    if completion["files"].get(path.name) != expected_sha256:
        raise ValueError("Handoff absent from completion")
    if (
        handoff["status"] != "complete"
        or handoff.get("policy_revision") != group_claims_export.INVESTIGATION_POLICY
        or handoff.get("advancement_scope") != "08E_investigation_only"
        or handoff.get("eligibility") != "undecided"
    ):
        raise ValueError("Explicit investigation release required")
    prepared = Path(handoff["prepared"])
    if (
        byte_digest((prepared / "manifest.json").read_bytes())
        != handoff["prepared_manifest_sha256"]
    ):
        raise ValueError("Prepared manifest differs")
    tasks = group_claims.load_prepared(prepared)
    native_raw = (path.parent / "native_export.json").read_bytes()
    authorization = json.loads((path.parent / "policy_authorization.json").read_bytes())
    if (
        byte_digest((path.parent / "policy_authorization.json").read_bytes())
        != handoff["authorization_sha256"]
        or authorization["native_export_sha256"] != byte_digest(native_raw)
        or authorization["project_id"] != handoff["project_id"]
        or authorization["policy_revision"] != handoff["policy_revision"]
    ):
        raise ValueError("Investigation authorization differs")
    replay = group_claims_export.normalize_export(
        json.loads(native_raw),
        tasks,
        project_id=handoff["project_id"],
        reviewer_id=handoff["reviewer_id"],
        export_sha256=byte_digest(native_raw),
        policy_revision=handoff["policy_revision"],
    )
    if replay != json.loads((path.parent / "decisions.json").read_bytes()):
        raise ValueError("Saved decision replay differs")
    if (
        replay["records"] != handoff["cases"]
        or replay["advancing_case_ids"] != handoff["advancing_case_ids"]
    ):
        raise ValueError("Handoff cases differ from saved decisions")
    approved = [
        {
            **claim,
            "case_id": case["case_id"],
            "question_id": case["question"]["question_id"],
            "question_version": case["question"]["question_version"],
            "question_text_sha256": case["question"]["text_sha256"],
            "packet_sha256": case["packet_sha256"],
            "proposal_sha256": case["proposal_sha256"],
        }
        for case in replay["records"]
        for claim in case["approved_claims"]
    ]
    if approved != handoff["approved_claims"]:
        raise ValueError("Exact approved claim closure differs")
    return handoff


def case_inputs(
    handoff: dict[str, Any], case_id: str
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Project immutable claims and complete current response context into 07D fields."""
    task = next(
        t
        for t in group_claims.load_prepared(Path(handoff["prepared"]))
        if t["data"]["case_id"] == case_id
    )
    case = task["data"]["case_input"]
    claims = [
        {**copy.deepcopy(c), "local_id": c["claim_id"]}
        for c in handoff["approved_claims"]
        if c["case_id"] == case_id
    ]
    context = {
        "comment_html": "<pre>" + html.escape(case["original_comment"]["text"]) + "</pre>",
        "concerns_html": task["data"]["question_html"] + task["data"]["parts_html"],
        "response_html": task["data"]["source_html"],
    }
    return claims, context


def prepare_claim_tasks(
    packet: dict[str, Any], *, data_root: Path, handoff: dict[str, Any]
) -> list[dict[str, Any]]:
    """Prepare blank evidence tasks bound to exact approved claims and unresolved scope."""
    claims, context = case_inputs(handoff, packet["case_id"])
    if packet["claims"] != claims or packet["context"] != context:
        raise ValueError("Packet differs from current approved claims or complete context")
    case = next(c for c in handoff["cases"] if c["case_id"] == packet["case_id"])
    adapter = {
        "review_status": "approved",
        "case_label": packet["case_id"],
        "claims": claims,
        "evidence_candidate_claim_ids": [c["claim_id"] for c in claims],
        "data": {
            "comment_html": context["comment_html"],
            "concerns_html": context["concerns_html"],
            "sources_html": context["response_html"],
        },
    }
    tasks = evidence.prepare_claim_tasks(packet, data_root=data_root, approved_review=adapter)
    by_candidate = {candidate["candidate_id"]: candidate for candidate in packet["candidates"]}
    for task in tasks:
        task["data"]["reviewer_notes_html"] += (
            "<h3>Proposed source summaries — Astra, advisory</h3>"
            + "".join(
                "<h4>"
                + html.escape(task["data"]["candidate_aliases"][identity])
                + "</h4><p>"
                + html.escape(
                    by_candidate[identity].get("source_summary", "No proposed summary supplied.")
                )
                + "</p>"
                for identity in task["data"]["slots"][0]["candidate_ids"]
            )
            + "<p>These summaries are proposals, not source text or saved human decisions.</p>"
        )
        task["data"].update(
            interface_version=VERSION,
            qualification_only=False,
            upstream_handoff_sha256=byte_digest(encoded(handoff)),
            upstream_case=copy.deepcopy(case),
        )
        claim = task["data"]["claim"]
        chain = [claim["claim_id"]] + [
            link["claim_id"] for link in claim.get("support_chain_versions", [])
        ]
        chain_html = "<p>Approved relationship: " + html.escape(claim["relationship"]) + "</p>"
        chain_html += "<p>Approved chain: " + html.escape(" → ".join(chain)) + "</p>"
        chain_html += (
            "<p>Material contribution: " + html.escape(claim.get("rationale", "")) + "</p>"
        )
        task["data"]["relevance_html"] += chain_html
        task["data"]["relevance_html"] += (
            "<h3>Investigation scope and support chain</h3><p>Ready permits investigation; "
            "all frozen-question gaps remain unresolved. "
            "Evidence and eligibility are undecided.</p>"
            + "<h4>Unresolved question parts</h4><pre>"
            + html.escape(
                json.dumps(case["unresolved_question_parts"], ensure_ascii=False, indent=2)
            )
            + "</pre>"
        )
    return tasks


def bind_project_capacity(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Use one project form without changing any case packet or evidence candidate set."""
    result = copy.deepcopy(tasks)
    capacity = max(t["data"]["max_candidates"] for t in result)
    for task in result:
        task["data"]["project_capacity"] = capacity
        for pair in range(task["data"]["max_candidates"] + 1, capacity + 1):
            task["data"][f"c001_p{pair:02d}_title"] = ""
    return result


def claim_form(max_candidates: int, *, layout_revision: str | None = None) -> str:
    """Reuse qualified controls with explicit investigation-only live instructions."""
    legacy = shared.claim_form(max_candidates).replace(
        "Task08E source-free qualification — never dataset approval",
        "Task08E evidence review — unresolved question scope is preserved; eligibility is separate",
    )

    if layout_revision is None:
        return legacy
    if layout_revision != cards.VERSION:
        raise ValueError("Unsupported evidence layout revision")
    return cards.claim_form(max_candidates, legacy)


def eligibility_form() -> str:
    """Reuse explicit human gate without any preselected eligibility decision."""
    return shared.eligibility_form().replace(
        "Task08E synthetic eligibility qualification", "Task08E evidence-based human eligibility"
    )


def normalize_claim(
    task: dict[str, Any],
    annotation: dict[str, Any],
    *,
    expected_task: dict[str, Any],
    export_lineage: str,
) -> dict[str, Any]:
    """Retain all saved relationships, including insufficient or contradictory evidence."""
    data = expected_task["data"]
    if (
        data.get("qualification_only") is not False
        or data.get("interface_version") != VERSION
        or not export_lineage.strip()
    ):
        raise ValueError("Live version and export binding required")
    summary_rows = [r for r in annotation["result"] if r.get("from_name") == "source_summary"]
    summary = shared._native_fields(
        task,
        {**annotation, "result": summary_rows},
        expected_task,
        {"source_summary": ("textarea", "evidence")},
    ).get("source_summary", "")
    native = {
        **annotation,
        "result": [r for r in annotation["result"] if r.get("from_name") != "source_summary"],
    }
    try:
        result = evidence.normalize_claim_review(
            task, native, expected_task=expected_task, export_lineage=export_lineage
        )
    except evidence.ReviewValidationError as error:
        result = error.review
    result.update(
        interface_version=VERSION,
        qualification_only=False,
        source_summary=summary,
        upstream_case=copy.deepcopy(data["upstream_case"]),
        upstream_handoff_sha256=data["upstream_handoff_sha256"],
        native_annotation=copy.deepcopy(annotation),
        annotation_sha256=evidence.digest(annotation),
        shared_form_sha256=hashlib.sha256(
            claim_form(
                data.get("project_capacity", data["max_candidates"]),
                layout_revision=data.get("layout_revision"),
            ).encode()
        ).hexdigest(),
    )
    if "layout_revision" in data:
        result["layout_revision"] = data["layout_revision"]
    return result


def normalize_export(
    exported_tasks: list[dict[str, Any]],
    *,
    expected_tasks: list[dict[str, Any]],
    project_id: int,
    actual_form: str,
    reviewer_id: int | str,
    export_lineage: str,
    data_root: Path,
    eligibility: bool = False,
) -> dict[str, Any]:
    """Verify exact saved evidence or eligibility queue; never publish a later stage."""
    if not expected_tasks or not export_lineage.strip():
        raise ValueError("Expected queue and export lineage required")
    expected = {evidence.digest(t["data"]): t for t in expected_tasks}
    if len(expected) != len(expected_tasks):
        raise ValueError("Duplicate expected tasks")
    if eligibility:
        form = eligibility_form()
    else:
        capacities = {
            t["data"].get("project_capacity", t["data"]["max_candidates"]) for t in expected_tasks
        }
        if len(capacities) != 1:
            raise ValueError("Homogeneous project form capacity required")
        layouts = {t["data"].get("layout_revision") for t in expected_tasks}
        if len(layouts) != 1:
            raise ValueError("Homogeneous project layout required")
        form = claim_form(next(iter(capacities)), layout_revision=next(iter(layouts)))
    if actual_form != form:
        raise ValueError("Live form differs")
    seen, native_ids = set(), set()
    for task in exported_tasks:
        binding = evidence.digest(task["data"])
        if binding not in expected or binding in seen or task.get("id") in native_ids:
            raise ValueError("Unexpected or duplicate queue task")
        if (
            type(task.get("id")) is not int
            or task["id"] < 1
            or task.get("project") != project_id
            or expected[binding].get("id", task["id"]) != task["id"]
        ):
            raise ValueError("Native project/task identity differs")
        annotations = task.get("annotations", [])
        if annotations and (
            len(annotations) != 1 or annotations[0].get("completed_by") != reviewer_id
        ):
            raise ValueError("One saved annotation by configured reviewer required")
        seen.add(binding)
        native_ids.add(task["id"])
    if seen != set(expected):
        raise ValueError("Missing queue tasks")
    # Native queue identities are verified before opening any external packet.
    hydrated = hydrate_tasks(expected_tasks, data_root=data_root)
    expanded_by_native = {
        evidence.digest(native["data"]): expanded
        for native, expanded in zip(expected_tasks, hydrated, strict=True)
    }
    validated_packets: set[str] = set()
    for task in hydrated:
        packet = task["data"]["packet"]
        packet_digest = evidence.digest(packet)
        if packet_digest not in validated_packets:
            evidence.validate_candidates(packet, data_root)
            validated_packets.add(packet_digest)
    records, pending = [], []
    for task in exported_tasks:
        binding = evidence.digest(task["data"])
        annotations = task.get("annotations", [])
        if not annotations:
            pending.append(task["id"])
            continue
        expanded = expanded_by_native[binding]
        normalizer = normalize_eligibility if eligibility else normalize_claim
        record = normalizer(
            {**task, "data": expanded["data"]},
            annotations[0],
            expected_task=expanded,
            export_lineage=export_lineage,
        )
        if "storage_revision" in task["data"]:
            record.update(
                storage_revision=task["data"]["storage_revision"],
                native_task_sha256=binding,
                packet_ref=copy.deepcopy(task["data"]["packet_ref"]),
            )
        records.append(record)
    result = {
        "schema_version": (
            "er_commons.task08e.eligibility_export.v2"
            if eligibility
            else "er_commons.task08e.evidence_export.v2"
        ),
        "qualification_only": False,
        "records": records,
        "pending_task_ids": pending,
        "project_id": project_id,
        "reviewer_id": reviewer_id,
        "export_lineage": export_lineage,
        "native_export_sha256": evidence.digest(exported_tasks),
        "advancing_case_ids": [],
        "advancing_claim_ids": [],
        "allowed_next_stage": None,
        "eligibility": "human_review" if eligibility else "undecided",
    }

    schema = (
        Path(__file__).resolve().parents[2]
        / "benchmarks/er_bench/schemas/task08e/v2"
        / ("eligibility_export.schema.json" if eligibility else "evidence_export.schema.json")
    )
    Draft202012Validator(json.loads(schema.read_bytes())).validate(result)
    return result


def _required_table_members(packet: dict[str, Any], supplied: list[str]) -> list[str]:
    """Require every anchored canonical table, independently of caller gate metadata."""
    required = sorted(
        {
            anchor["record"]["id"]
            for candidate in packet["candidates"]
            for anchor in candidate["anchors"]
            if "cells" in anchor["record"]
        }
    )
    if len(set(supplied)) != len(supplied) or sorted(supplied) != required:
        raise ValueError("Required table members differ from canonical packet tables")
    if "required_table_members" in packet and (
        len(set(packet["required_table_members"])) != len(packet["required_table_members"])
        or sorted(packet["required_table_members"]) != required
    ):
        raise ValueError("Packet table requirements differ from canonical anchors")
    return required


def prepare_eligibility(
    case_id: str,
    reviews: list[dict[str, Any]],
    *,
    required_table_members: list[str],
    expected_claim_ids: list[str],
    packet: dict[str, Any],
) -> dict[str, Any]:
    """Bind a blank human eligibility gate to actual saved evidence, including gaps."""
    if (
        packet["case_id"] != case_id
        or [c["claim_id"] for c in packet["claims"]] != expected_claim_ids
    ):
        raise ValueError("Exact case claim queue required")
    if (
        not reviews
        or len({r["claim_id"] for r in reviews}) != len(reviews)
        or {r["claim_id"] for r in reviews} != set(expected_claim_ids)
    ):
        raise ValueError("Every claim needs a saved evidence record before eligibility review")
    if any(
        r.get("qualification_only") is not False
        or r.get("interface_version") != VERSION
        or r.get("case_id") != case_id
        or r.get("packet_sha256") != evidence.digest(packet)
        or not r.get("native_annotation")
        for r in reviews
    ):
        raise ValueError("Actual same-packet saved live evidence required")
    _required_table_members(packet, required_table_members)
    upstream_case = reviews[0]["upstream_case"]
    if any(r["upstream_case"] != upstream_case for r in reviews):
        raise ValueError("Different upstream cases")
    data = {
        "interface_version": ELIGIBILITY_VERSION,
        "qualification_only": False,
        "case_id": case_id,
        "packet": copy.deepcopy(packet),
        "packet_sha256": evidence.digest(packet),
        "reviews": copy.deepcopy(reviews),
        "evidence_export_sha256": evidence.digest(reviews),
        "required_table_members": required_table_members,
        "upstream_case": copy.deepcopy(upstream_case),
        "review_html": (
            "<h2>Human eligibility review</h2><p>Investigation does not establish "
            "eligibility or answer adequacy. Preserve all unresolved scope, warnings, "
            "limitations and counterevidence.</p>"
        )
        + packet["context"]["comment_html"]
        + packet["context"]["concerns_html"]
        + packet["context"]["response_html"]
        + "<h3>Saved evidence and exact relationship history</h3><pre>"
        + html.escape(json.dumps(reviews, ensure_ascii=False, indent=2))
        + "</pre>"
        + "<h3>Full source units</h3>"
        + "".join("<pre>" + html.escape(c["quote"]) + "</pre>" for c in packet["candidates"])
        + "<h3>Required table-family members</h3><pre>"
        + html.escape("\n".join(required_table_members) or "None")
        + "</pre>",
    }
    return {"data": data}


def normalize_eligibility(
    task: dict[str, Any],
    annotation: dict[str, Any],
    *,
    expected_task: dict[str, Any],
    export_lineage: str,
) -> dict[str, Any]:
    """Save human stop/unresolved/advance without releasing claims to a later stage."""
    data = expected_task["data"]
    if (
        data.get("qualification_only") is not False
        or data.get("interface_version") != ELIGIBILITY_VERSION
        or not export_lineage.strip()
        or data["evidence_export_sha256"] != evidence.digest(data["reviews"])
        or data["packet_sha256"] != evidence.digest(data["packet"])
    ):
        raise ValueError("Live eligibility bindings differ")
    _required_table_members(data["packet"], data["required_table_members"])
    fields = shared._native_fields(
        task,
        annotation,
        expected_task,
        {
            "disposition": ("choices", "eligibility"),
            "table_usability": ("choices", "eligibility"),
            "reason": ("textarea", "eligibility"),
            "render_checks": ("textarea", "eligibility"),
        },
    )
    if (
        fields.get("disposition") not in {"advance", "stop", "unresolved"}
        or not fields.get("reason", "").strip()
    ):
        raise ValueError("Explicit human disposition and reason required")
    if fields.get("table_usability") not in {
        "verified_all_required_family_members",
        "not_required",
        "unresolved",
    }:
        raise ValueError("Explicit table usability required")
    if fields["disposition"] == "advance":
        if any(not r.get("review_complete") or r.get("validation_errors") for r in data["reviews"]):
            raise ValueError("Incomplete evidence decisions prevent advancement")
        required = set(data["required_table_members"])
        checked = {
            line.strip() for line in fields.get("render_checks", "").splitlines() if line.strip()
        }
        if checked != required or fields["table_usability"] != (
            "verified_all_required_family_members" if required else "not_required"
        ):
            raise ValueError("Every required table-family member needs a human render check")
    return {
        "schema_version": "er_commons.task08e.eligibility_decision.v2",
        "qualification_only": False,
        "case_id": data["case_id"],
        "human_decision": fields,
        "evidence_export_sha256": data["evidence_export_sha256"],
        "native_annotation": copy.deepcopy(annotation),
        "annotation_sha256": evidence.digest(annotation),
        "task_sha256": evidence.digest(data),
        "export_lineage": export_lineage,
        "form_sha256": hashlib.sha256(eligibility_form().encode()).hexdigest(),
        "advancing_claim_ids": [],
        "allowed_next_stage": None,
    }
