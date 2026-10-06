"""Source-free Task08E qualification around the maintained evidence review adapter.

No function in this module loads a live handoff or publishes advancing claims.
Qualification decisions are always segregated from dataset human decisions.
"""

import copy
import hashlib
import html
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons import pilot_evidence as evidence

VERSION = "task08e.evidence_review.v1"
ELIGIBILITY_VERSION = "task08e.eligibility_review.v1"


def claim_form(max_candidates: int) -> str:
    """Reuse maintained controls and append an editable curator summary."""
    base = evidence.build_claim_form(max_candidates=max_candidates)
    extra = (
        '<Header value="Task08E source-free qualification — never dataset approval" />'
        '<TextArea name="source_summary" toName="evidence" rows="4" '
        'editable="true" transcription="true" maxSubmissions="1" '
        'showSubmitButton="false" placeholder="Curator summary; never changes source text" />'
    )
    return base.rsplit("</View>", 1)[0] + extra + "</View>"


def eligibility_form() -> str:
    """Require explicit human disposition with no preselected eligibility."""
    return """<View><Header value="Task08E synthetic eligibility qualification" />
<HyperText name="eligibility" value="$review_html" />
<Choices name="disposition" toName="eligibility" choice="single-radio">
<Choice value="advance"/><Choice value="stop"/><Choice value="unresolved"/></Choices>
<Choices name="table_usability" toName="eligibility" choice="single-radio">
<Choice value="verified_all_required_family_members"/><Choice value="not_required"/>
<Choice value="unresolved"/></Choices>
<TextArea name="reason" toName="eligibility" rows="4" editable="true"
transcription="true" maxSubmissions="1" showSubmitButton="false"/>
<TextArea name="render_checks" toName="eligibility" rows="4" editable="true"
transcription="true" maxSubmissions="1" showSubmitButton="false"
placeholder="One required table-family member ID per line after human render verification"/>
</View>"""


def _native_fields(
    task: dict[str, Any],
    annotation: dict[str, Any],
    expected: dict[str, Any],
    controls: dict[str, tuple[str, str]],
) -> dict[str, str]:
    """Reject changed bindings, cancelled saves and unknown native fields."""
    if task["data"] != expected["data"]:
        raise ValueError("Trusted task differs")
    if (
        not annotation.get("id")
        or annotation.get("task") != task.get("id")
        or not annotation.get("completed_by")
        or annotation.get("was_cancelled")
        or annotation.get("ground_truth")
        or annotation.get("skipped")
    ):
        raise ValueError("Saved reviewer/task identity required")
    fields = {}
    for row in annotation.get("result", []):
        name = row.get("from_name")
        if name not in controls or name in fields:
            raise ValueError("Unknown or duplicate control")
        kind, target = controls[name]
        if row.get("type") != kind or row.get("to_name") != target:
            raise ValueError("Native control binding mismatch")
        key = "choices" if kind == "choices" else "text"
        value = row.get("value", {}).get(key)
        if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], str):
            raise ValueError("One native field value required")
        fields[name] = value[0]
    return fields


def normalize_claim(
    task: dict[str, Any],
    annotation: dict[str, Any],
    *,
    expected_task: dict[str, Any],
    export_lineage: str,
) -> dict[str, Any]:
    """Keep native annotations while validating unchanged maintained pair semantics."""
    if (
        not export_lineage.strip()
        or expected_task["data"].get("qualification_only") is not True
        or expected_task["data"].get("interface_version") != VERSION
    ):
        raise ValueError("Qualification binding and export lineage required")
    if task["data"] != expected_task["data"] or annotation.get("was_cancelled"):
        raise ValueError("Changed task or cancelled annotation")
    summary_rows = [r for r in annotation["result"] if r.get("from_name") == "source_summary"]
    summary = _native_fields(
        task,
        {**annotation, "result": summary_rows},
        expected_task,
        {"source_summary": ("textarea", "evidence")},
    ).get("source_summary", "")
    native = copy.deepcopy(annotation)
    native["result"] = [r for r in native["result"] if r.get("from_name") != "source_summary"]
    try:
        result = evidence.normalize_claim_review(
            task, native, expected_task=expected_task, export_lineage=export_lineage
        )
    except evidence.ReviewValidationError as error:
        result = error.review
    result.update(
        interface_version=VERSION,
        qualification_only=True,
        source_summary=summary,
        native_annotation=copy.deepcopy(annotation),
        annotation_sha256=evidence.digest(annotation),
        shared_form_sha256=hashlib.sha256(
            claim_form(expected_task["data"]["max_candidates"]).encode()
        ).hexdigest(),
    )
    return result


def prepare_eligibility(
    case_id: str,
    reviews: list[dict[str, Any]],
    *,
    required_table_members: list[str],
    expected_claim_ids: list[str],
    packet: dict[str, Any],
) -> dict[str, Any]:
    """Bind a separate human gate to exact reviewed evidence, without deriving a label."""
    if (
        packet["case_id"] != case_id
        or [c["claim_id"] for c in packet["claims"]] != expected_claim_ids
    ):
        raise ValueError("Packet case and exact claim queue required")
    if not reviews or any(
        r.get("qualification_only") is not True or r.get("case_id") != case_id for r in reviews
    ):
        raise ValueError("Only same-case qualification reviews accepted")
    if (
        len({r["claim_id"] for r in reviews}) != len(reviews)
        or {r["claim_id"] for r in reviews} != set(expected_claim_ids)
        or len(set(expected_claim_ids)) != len(expected_claim_ids)
    ):
        raise ValueError("Exact expected claim closure required")
    if any(r.get("packet_sha256") != evidence.digest(packet) for r in reviews):
        raise ValueError("Reviewed evidence packet differs")
    if len(set(required_table_members)) != len(required_table_members):
        raise ValueError("Duplicate required table-family members")
    claim_text = {c["claim_id"]: c["text"] for c in packet["claims"]}
    gaps = {m["claim_id"]: m["search_gap"] for m in packet["claim_candidates"]}
    labels = {c["candidate_id"]: c["citation_unit"]["citation_label"] for c in packet["candidates"]}
    data = {
        "case_id": case_id,
        "packet": copy.deepcopy(packet),
        "packet_sha256": evidence.digest(packet),
        "qualification_only": True,
        "interface_version": ELIGIBILITY_VERSION,
        "evidence_export_sha256": evidence.digest(reviews),
        "reviews": copy.deepcopy(reviews),
        "required_table_members": required_table_members,
        "review_html": (
            "<h2>Synthetic case eligibility</h2>"
            + "<h3>Original comment</h3>"
            + packet["context"]["comment_html"]
            + "<h3>Frozen question</h3>"
            + packet["context"]["concerns_html"]
            + "<h3>Complete response</h3>"
            + packet["context"]["response_html"]
            + "<h3>Citable sources</h3>"
            + "".join("<pre>" + html.escape(c["quote"]) + "</pre>" for c in packet["candidates"])
            + "".join(
                "<h3>"
                + html.escape(claim_text[r["claim_id"]])
                + "</h3><p>Outcome: "
                + html.escape(str(r["claim_review"]["outcome"]))
                + "</p><p>"
                + html.escape(r.get("source_summary", "No curator summary saved."))
                + "</p><p>Gaps / reasons: "
                + html.escape(r["claim_review"].get("note", ""))
                + "</p><p>Search gap: "
                + html.escape(gaps[r["claim_id"]])
                + "</p>"
                + "".join(
                    "<p>"
                    + html.escape(labels[p["candidate_id"]])
                    + ": "
                    + html.escape(str(p["relationship"]))
                    + " — "
                    + html.escape(p.get("note", ""))
                    + "</p>"
                    for p in r["claim_review"]["pairs"]
                )
                for r in reviews
            )
            + "<p>Required table-family members: "
            + html.escape(", ".join(required_table_members) or "None")
            + "</p>"
            + "<details><summary>Technical bindings and saved relationship history</summary><pre>"
            + html.escape(json.dumps(reviews, indent=2))
            + "</pre></details>"
        ),
    }
    return {"data": data}


def normalize_eligibility(
    task: dict[str, Any],
    annotation: dict[str, Any],
    *,
    expected_task: dict[str, Any],
    export_lineage: str,
) -> dict[str, Any]:
    """Validate explicit saved human gate; unresolved/stop remain nonadvancing."""
    data = expected_task["data"]
    if (
        data.get("qualification_only") is not True
        or data.get("interface_version") != ELIGIBILITY_VERSION
        or not export_lineage.strip()
        or data["evidence_export_sha256"] != evidence.digest(data["reviews"])
        or data["packet_sha256"] != evidence.digest(data["packet"])
    ):
        raise ValueError("Qualification evidence binding required")
    fields = _native_fields(
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
    disposition = fields.get("disposition")
    if disposition not in {"advance", "stop", "unresolved"} or not fields.get("reason", "").strip():
        raise ValueError("Explicit disposition and reason required")
    table_state = fields.get("table_usability")
    if table_state not in {"verified_all_required_family_members", "not_required", "unresolved"}:
        raise ValueError("Explicit table usability decision required")
    if disposition == "advance":
        if any(
            r["claim_review"]["outcome"] != "supported"
            or not r.get("review_complete")
            or r.get("validation_errors")
            for r in data["reviews"]
        ):
            raise ValueError("Unresolved or unsupported claim cannot advance")
        required = set(data["required_table_members"])
        checked = {
            line.strip() for line in fields.get("render_checks", "").splitlines() if line.strip()
        }
        if required:
            if table_state != "verified_all_required_family_members" or checked != required:
                raise ValueError("Every required table-family member needs a human render check")
        elif table_state != "not_required" or checked:
            raise ValueError("Unexpected table checks")
    return {
        "schema_version": "er_commons.task08e.qualification_eligibility.v1",
        "qualification_only": True,
        "case_id": data["case_id"],
        "synthetic_disposition": disposition,
        "advancing_claim_ids": [],
        "human_decision": fields,
        "evidence_export_sha256": data["evidence_export_sha256"],
        "native_annotation": copy.deepcopy(annotation),
        "annotation_sha256": evidence.digest(annotation),
        "task_sha256": evidence.digest(data),
        "export_lineage": export_lineage,
        "form_sha256": hashlib.sha256(eligibility_form().encode()).hexdigest(),
    }


def normalize_export(
    exported_tasks: list[dict[str, Any]],
    *,
    expected_tasks: list[dict[str, Any]],
    project_id: int,
    actual_form: str,
    reviewer_id: int | str,
    export_lineage: str,
    eligibility: bool = False,
    data_root: Path,
) -> dict[str, Any]:
    """Bind a whole native export to its project, exact template, queue and reviewer.

    Untouched tasks are explicit holds. Multiple annotations require an explicit
    caller-selected export revision instead of silently choosing the latest.
    """
    if not expected_tasks:
        raise ValueError("Nonempty expected queue required")
    if not eligibility and len({t["data"]["max_candidates"] for t in expected_tasks}) != 1:
        raise ValueError("Homogeneous template capacity required")
    for expected_task in expected_tasks:
        evidence.validate_candidates(expected_task["data"]["packet"], data_root)
    form = (
        eligibility_form()
        if eligibility
        else claim_form(expected_tasks[0]["data"]["max_candidates"])
    )
    if actual_form != form or not export_lineage.strip():
        raise ValueError("Project form or export lineage mismatch")
    expected = {evidence.digest(t["data"]): t for t in expected_tasks}
    if len(expected) != len(expected_tasks) or not expected:
        raise ValueError("Unique nonempty expected queue required")
    seen = set()
    records = []
    pending = []
    native_ids = set()
    for task in exported_tasks:
        binding = evidence.digest(task["data"])
        if binding not in expected or binding in seen or task.get("id") in native_ids:
            raise ValueError("Unexpected or duplicate native queue task")
        if task.get("project") != project_id or type(task.get("id")) is not int or task["id"] < 1:
            raise ValueError("Project identity differs")
        if expected[binding].get("id") is not None and task["id"] != expected[binding]["id"]:
            raise ValueError("Imported native task identity differs")
        seen.add(binding)
        native_ids.add(task.get("id"))
        annotations = task.get("annotations", [])
        if not annotations:
            pending.append(task["id"])
            continue
        if len(annotations) != 1 or annotations[0].get("completed_by") != reviewer_id:
            raise ValueError("Exact one saved annotation by configured reviewer required")
        normalizer = normalize_eligibility if eligibility else normalize_claim
        records.append(
            normalizer(
                task, annotations[0], expected_task=expected[binding], export_lineage=export_lineage
            )
        )
    if seen != set(expected):
        raise ValueError("Missing tasks from native export")
    result = {
        "schema_version": "er_commons.task08e.qualification_export.v1",
        "qualification_only": True,
        "advancing_claim_ids": [],
        "records": records,
        "pending_task_ids": pending,
        "advancing_case_ids": [],
        "allowed_next_stage": None,
        "project_id": project_id,
        "export_lineage": export_lineage,
        "native_export_sha256": evidence.digest(exported_tasks),
    }

    schema = (
        Path(__file__).resolve().parents[2]
        / "benchmarks/er_bench/schemas/task08e/v1/qualification_export.schema.json"
    )
    Draft202012Validator(json.loads(schema.read_text())).validate(result)
    return result
