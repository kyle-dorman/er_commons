"""Replay saved development answers with isolated frozen judges and explicit failures."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, TypedDict, cast

from jsonschema import ValidationError, validate  # type: ignore[import-untyped]

from er_commons import (
    adequacy_binary,
    conclusion_structured,
    no_answer,
    point_grounding,
    support_conclusion,
    support_material,
)
from er_commons.artifact_io import sha256_bytes, stable_json_sha256
from er_commons.automatic_metric_inputs import (
    ReferenceResolution,
    SourceCatalog,
    canonical_unit,
    resolve_citations,
)
from er_commons.automatic_metrics import calculate_metrics
from er_commons.target_generation import output_schema, validate_record

IDENTITY_FIELDS = (
    "run_id",
    "case_id",
    "candidate_id",
    "candidate_sha256",
    "repeat",
    "attempt",
    "request_sha256",
)


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON keys before inspecting any candidate prose."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _evaluation_item(
    identity: dict[str, Any],
    component: str,
    point_id: str | None,
    packet: dict[str, Any] | None,
    **extra: Any,
) -> dict[str, Any]:
    """Bind one projection to its complete candidate and point identity."""
    key = {"identity": identity, "component": component, "point_id": point_id}
    if "prompt_version" in extra:
        key.update(prompt_version=extra["prompt_version"], input_version=extra["input_version"])
    return {
        **key,
        "sample_id": stable_json_sha256(key),
        "packet": packet,
        "payload_sha256": stable_json_sha256(packet),
        "status": "not_run",
        **extra,
    }


class AnswerPoint(TypedDict):
    """Validated point fields shared by answer groups and citation checks."""

    point_id: str
    text: str
    citation_ids: list[str]
    applies_to: list[str]


class CandidateAnswer(TypedDict):
    """Native answer shape after schema and point-identity validation."""

    status: str
    conclusion: AnswerPoint
    supporting_points: list[AnswerPoint]
    qualifications: list[AnswerPoint]
    optional_context: list[AnswerPoint]


@dataclass(frozen=True)
class _PreparedSources:
    """Verified delivery and citation mappings used by isolated projections."""

    payload: dict[str, Any]
    passages: dict[str, Any]
    mapping_rows: dict[str, Any]
    catalog: SourceCatalog
    references: ReferenceResolution

    def evidence(self, citation: str) -> dict[str, Any]:
        """Retain complete point-owned source text/tables and exact canonical locator."""
        p = self.passages[citation]
        unit = self.mapping_rows[citation]["canonical_unit"]
        return {
            "occurrence_id": citation,
            "source_id": p["source_id"],
            "canonical_target": {
                "unit_type": unit[2],
                "unit_id": unit[3],
                "extraction_id": unit[1],
                "breadcrumb": [{"heading_text": heading} for heading in p["heading_path"]],
            },
            **{
                k: p[k]
                for k in ("title", "full_source_text", "tables", "physical_pages", "printed_labels")
            },
        }


def _validate_identity(candidate_bytes: bytes, identity: dict[str, Any]) -> dict[str, Any]:
    """Validate the byte-bound identity and discard unrelated caller fields."""
    identity = {key: identity[key] for key in IDENTITY_FIELDS}
    if any(
        not isinstance(identity[k], str) or not identity[k]
        for k in IDENTITY_FIELDS
        if k not in {"repeat", "attempt"}
    ):
        raise ValueError("Missing candidate identity")
    if any(type(identity[k]) is not int or identity[k] < 1 for k in ("repeat", "attempt")):
        raise ValueError("Invalid repeat/attempt identity")
    if sha256_bytes(candidate_bytes) != identity["candidate_sha256"]:
        raise ValueError("Candidate byte hash mismatch")
    expected_id = stable_json_sha256(
        {k: identity[k] for k in IDENTITY_FIELDS if k != "candidate_id"}
    )
    if expected_id != identity["candidate_id"]:
        raise ValueError("Candidate identity mismatch")
    return identity


def _prepare_sources(
    identity: dict[str, Any],
    target_record: dict[str, Any],
    mapping: dict[str, Any],
    delivery_receipt: dict[str, Any],
    expected_split: str,
) -> _PreparedSources:
    """Verify exact split-bound delivery before resolving canonical citation roles."""
    if expected_split not in {"dev", "test"}:
        raise ValueError("Unsupported expected split")
    validate_record(target_record)
    payload = target_record["payload"]
    if (
        target_record["case_id"] != identity["case_id"]
        or mapping["case_id"] != identity["case_id"]
        or mapping["split"] != expected_split
        or mapping["payload_sha256"] != stable_json_sha256(payload)
    ):
        raise ValueError("Cross-case or wrong-split mapping")
    users = [m for m in delivery_receipt.get("input", []) if m.get("role") == "user"]
    if len(users) != 1 or len(users[0].get("content", [])) != 1:
        raise ValueError("Ambiguous delivered user payload")
    content = users[0]["content"][0]
    if content.get("type") != "input_text" or json.loads(content["text"]) != payload:
        raise ValueError("Delivered payload differs from Task10")
    passages = {p["citation_id"]: p for p in payload["passages"]}
    rows = {p["citation_id"]: p for p in mapping["passages"]}
    if len(rows) != len(mapping["passages"]) or set(rows) != set(passages):
        raise ValueError("Duplicate or incomplete passage mapping")
    catalog = SourceCatalog(
        {key: frozenset({canonical_unit(row["canonical_unit"])}) for key, row in rows.items()}
    )
    if any(row["reference_role"] not in {"support", "context"} for row in rows.values()):
        raise ValueError("Invalid reference role")
    support = frozenset(
        canonical_unit(r["canonical_unit"])
        for r in rows.values()
        if r["reference_role"] == "support"
    )
    context = (
        frozenset(
            canonical_unit(r["canonical_unit"])
            for r in rows.values()
            if r["reference_role"] == "context"
        )
        - support
    )
    return _PreparedSources(payload, passages, rows, catalog, ReferenceResolution(support, context))


def _parse_answer(candidate_bytes: bytes) -> tuple[CandidateAnswer, list[AnswerPoint]]:
    """Reject malformed schema, duplicate point IDs and unresolved point references."""
    answer = json.loads(candidate_bytes, object_pairs_hook=_unique_json_object)
    validate(answer, output_schema())
    points = [
        answer["conclusion"],
        *answer["supporting_points"],
        *answer["qualifications"],
        *answer["optional_context"],
    ]
    ids = [p["point_id"] for p in points]
    if len(ids) != len(set(ids)) or any(
        not p["point_id"].strip() or not p["text"].strip() for p in points
    ):
        raise ValueError("Duplicate/empty point identity or blank prose")
    if any(not set(p["applies_to"]) <= set(ids) for p in points):
        raise ValueError("Unresolved applies_to")
    return cast(CandidateAnswer, answer), points


def _automatic_checks(
    identity: dict[str, Any],
    answer: CandidateAnswer,
    points: list[AnswerPoint],
    sources: _PreparedSources,
) -> dict[str, Any]:
    """Calculate citation diagnostics against the verified canonical source mapping."""
    citations = resolve_citations(answer, sources.catalog)
    metrics = calculate_metrics(identity["case_id"], sources.references, citations)
    return {
        "schema": "valid",
        "citation": metrics.citation.model_dump(),
        "citation_attempts": list(citations.attempts),
        "citation_diagnostics": list(citations.diagnostics),
        "delivery": "exact_payload_verified",
        "uncited_point_ids": [p["point_id"] for p in points if not p["citation_ids"]],
        "resolved_citations": not citations.invalid_tokens and citations.available,
        "retrieval": {"status": "not_applicable", "recall": None},
    }


def _project_items(
    identity: dict[str, Any],
    answer: CandidateAnswer,
    sources: _PreparedSources,
    reference_conclusion: str,
    structured_reference: dict[str, Any] | None = None,
    conclusion_prompt_version: str | None = None,
    support_prompt_version: str | None = None,
) -> list[dict[str, Any]]:
    """Build A, point-owned G, S and C inputs in their stable dispatch order."""
    items: list[dict[str, Any]] = []
    conclusion = answer["conclusion"]["text"]
    items.append(
        _evaluation_item(
            identity, "A", None, no_answer.validate_input({"candidate_conclusion": conclusion})
        )
    )

    for group in ("supporting_points", "qualifications"):
        for point in answer[group]:
            prepared = asdict(
                point_grounding.prepare_point(
                    sources.payload["question"],
                    point["text"],
                    point["citation_ids"],
                    allowed_citation_ids=sources.passages,
                    load_evidence=sources.evidence,
                )
            )
            packet = prepared.pop("packet")
            items.append(
                _evaluation_item(identity, "G", point["point_id"], packet, group=group, **prepared)
            )
    conclusion_packet = {
        "question": sources.payload["question"],
        "candidate_conclusion": conclusion,
        **(
            structured_reference
            if structured_reference is not None
            else {"reference_conclusion": reference_conclusion}
        ),
    }
    support_packet: dict[str, Any] = {
        "question": sources.payload["question"],
        "candidate_conclusion": conclusion,
        "candidate_supporting_points": [
            {"point_id": p["point_id"], "text": p["text"]} for p in answer["supporting_points"]
        ],
    }
    if support_prompt_version != support_conclusion.VERSION:
        support_packet["candidate_qualifications"] = [p["text"] for p in answer["qualifications"]]
    support_input_version = (
        support_material.INPUT_VERSION
        if support_prompt_version == support_material.VERSION
        else support_conclusion.INPUT_VERSION
    )
    for component, packet, prompt_version, input_version in (
        (
            "S",
            support_packet,
            support_prompt_version,
            support_input_version,
        ),
        (
            "C",
            conclusion_packet,
            conclusion_prompt_version,
            "conclusion_structured.input.v1",
        ),
    ):
        version_fields = {}
        if prompt_version is not None:
            version_fields = {"prompt_version": prompt_version, "input_version": input_version}
        items.append(
            _evaluation_item(
                identity,
                component,
                None,
                adequacy_binary.validate_input(
                    cast(adequacy_binary.Component, component),
                    packet,
                    prompt_version=prompt_version,
                ),
                **version_fields,
            )
        )
    return items


def prepare_candidate(
    candidate_bytes: bytes,
    identity: dict[str, Any],
    target_record: dict[str, Any],
    mapping: dict[str, Any],
    delivery_receipt: dict[str, Any],
    reference_conclusion: str,
    *,
    expected_split: str = "dev",
    structured_reference: dict[str, Any] | None = None,
    conclusion_prompt_version: str | None = None,
    support_prompt_version: str | None = None,
) -> dict[str, Any]:
    """Project a byte-bound candidate; malformed answers remain reportable, never repaired.

    The caller verifies the sealed files and successful transport receipt. This
    function checks the actual native user request against the complete payload.
    """
    if support_prompt_version not in {None, support_conclusion.VERSION, support_material.VERSION}:
        raise ValueError("Support projection requires an explicit registered S version")
    if conclusion_prompt_version is not None or structured_reference is not None:
        if (
            conclusion_prompt_version != conclusion_structured.VERSION_V6
            or structured_reference is None
        ):
            raise ValueError("Structured reference requires explicit conclusion v6")
        if set(structured_reference) != {"reference_required_points", "reference_optional_points"}:
            raise ValueError(
                "Structured reference must contain exactly required and optional points"
            )
        adequacy_binary.validate_input(
            "C",
            {
                "question": "Reference validation",
                "candidate_conclusion": "Reference validation",
                **structured_reference,
            },
            prompt_version=conclusion_prompt_version,
        )
    identity = _validate_identity(candidate_bytes, identity)
    sources = _prepare_sources(identity, target_record, mapping, delivery_receipt, expected_split)
    plan: dict[str, Any] = {
        "schema_version": "task11c.plan.v1",
        "identity": identity,
        "items": [],
        "bindings": {
            "target_sha256": stable_json_sha256(target_record),
            "mapping_sha256": stable_json_sha256(mapping),
            "delivery_sha256": stable_json_sha256(delivery_receipt),
        },
    }
    try:
        answer, points = _parse_answer(candidate_bytes)
    except (ValueError, TypeError, KeyError, ValidationError) as error:
        # JSON Schema errors are retained without allowing projection from malformed prose.
        plan["automatic"] = {
            "schema": "invalid",
            "error": str(error),
            "retrieval": {"status": "not_applicable", "recall": None},
        }
        return plan
    plan["automatic"] = _automatic_checks(identity, answer, points, sources)
    plan["guard_empty_other_prose"] = not (
        answer["supporting_points"] or answer["qualifications"] or answer["optional_context"]
    )
    plan["supporting_point_count"] = len(answer["supporting_points"])
    plan["optional_context"] = answer["optional_context"]
    plan["items"] = _project_items(
        identity,
        answer,
        sources,
        reference_conclusion,
        structured_reference,
        conclusion_prompt_version,
        support_prompt_version,
    )
    return plan


def _join_judgments(
    plan: dict[str, Any], judgments: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Reject orphan, duplicate, cross-answer and altered-projection judgments."""
    expected = {item["sample_id"]: item for item in plan["items"]}
    result: dict[str, dict[str, Any]] = {}
    for judgment in judgments:
        sid = judgment["sample_id"]
        if sid not in expected or sid in result:
            raise ValueError("Duplicate or orphan judgment")
        item = expected[sid]
        if any(
            judgment.get(k) != item[k]
            for k in ("identity", "component", "point_id", "payload_sha256")
        ):
            raise ValueError("Cross-answer or projection judgment mismatch")
        if "prompt_version" in item and any(
            judgment.get(key) != item[key] for key in ("prompt_version", "input_version")
        ):
            raise ValueError("Judgment prompt or input version mismatch")
        if item["status"] != "not_run":
            raise ValueError("Judgment supplied for mechanically blocked point")
        outcome = {**judgment, "decision": None}
        if judgment["status"] == "completed":
            try:
                raw = judgment["raw_output"]
                component = item["component"]
                if component == "A":
                    decision = no_answer.parse_output(raw)
                elif component == "G":
                    decision = point_grounding.parse_output(raw)
                else:
                    decision = adequacy_binary.parse_output(
                        component,
                        raw,
                        prompt_version=item.get("prompt_version"),
                        payload=item["packet"],
                    )
                    if item.get("prompt_version") == conclusion_structured.VERSION_V6:
                        outcome.update(
                            conclusion_structured.aggregate_diagnostics(
                                decision, item["packet"], version=conclusion_structured.VERSION_V6
                            )
                        )
                outcome["decision"] = decision
                if component == "C":
                    outcome["quotation_fidelity"] = adequacy_binary.quote_fidelity_diagnostics(
                        raw, item["packet"]
                    )
            except (ValueError, TypeError, KeyError) as error:
                outcome.update(status="invalid_output", error=str(error))
        elif judgment["status"] != "execution_error":
            raise ValueError("Unknown judgment status")
        result[sid] = outcome
    return result


def _answer_route(plan: dict[str, Any], joined: dict[str, dict[str, Any]]) -> str:
    """Use A for routing, guarding clean abstentions against other answer prose."""
    route = "invalid_answer" if plan["automatic"]["schema"] != "valid" else "a_unavailable"
    a = next((joined.get(i["sample_id"]) for i in plan["items"] if i["component"] == "A"), None)
    if a and a["decision"]:
        route = a["decision"]["classification"]
        if route == "clean_abstention" and not plan["guard_empty_other_prose"]:
            route = "mixed_abstention"
    return route


def _undispatched_status(component: str, route: str) -> str:
    """Distinguish required missing judgments from deliberate route-based skips."""
    if component == "A":
        return "missing_judgment"
    if route == "a_unavailable":
        return "blocked_a_unavailable"
    if route in {"clean_abstention", "mixed_abstention", "ambiguous"}:
        return "skipped_" + route
    return "missing_judgment"


def _support_structure(plan: dict[str, Any], route: str) -> str:
    """Explain support availability without treating abstentions as missing bases."""
    if route == "clean_abstention":
        return "not_applicable"
    count = plan.get("supporting_point_count")
    if count == 0:
        return "missing_basis"
    if count:
        return "present"
    return "unavailable"


def build_report(plan: dict[str, Any], judgments: list[dict[str, Any]]) -> dict[str, Any]:
    """Report every point, retaining mechanical failures even when A is unavailable."""
    joined = _join_judgments(plan, judgments)
    route = _answer_route(plan, joined)
    results = []
    for item in plan["items"]:
        sid = item["sample_id"]
        if sid in joined:
            if item["component"] != "A" and route != "substantive":
                raise ValueError("Judgment contradicts abstention/unavailable routing")
            result = {**item, **joined[sid]}
        else:
            result = {**item, "decision": None}
            if item["status"] == "not_run":
                result["status"] = _undispatched_status(item["component"], route)
        result.pop("packet", None)
        results.append(result)
    complete = bool(results) and all(
        r["status"] in {"completed", "precheck_failed", "skipped_clean_abstention"} for r in results
    )
    return {
        "schema_version": "task11c.report.v1",
        "identity": plan["identity"],
        "bindings": plan["bindings"],
        "automatic": plan["automatic"],
        "route": route,
        "coverage_complete": complete,
        "results": results,
        "empty_support": plan.get("supporting_point_count") == 0,
        "support_structure": _support_structure(plan, route),
        "strict_joint_result": "deferred_to_task12",
        "optional_context": {
            "status": "not_required_for_grounding",
            "points": plan.get("optional_context", []),
        },
    }


def pending_items(plan: dict[str, Any], judgments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dispatch A first, then all applicable isolated components without rerolls."""
    report = build_report(plan, judgments)
    indexed = {i["sample_id"]: i for i in plan["items"]}
    if report["route"] == "a_unavailable":
        return [
            indexed[r["sample_id"]]
            for r in report["results"]
            if r["component"] == "A" and r["status"] == "missing_judgment"
        ]
    return [indexed[r["sample_id"]] for r in report["results"] if r["status"] == "missing_judgment"]


def readable_report(report: dict[str, Any]) -> str:
    """Render compact diagnostics while the adjacent JSON retains complete receipts."""
    identity = report["identity"]
    automatic = report["automatic"]
    lines = [
        f"# {identity['case_id']} development evaluation",
        "",
        f"Candidate: `{identity['candidate_id']}`",
        f"Run: `{identity['run_id']}`; repeat {identity['repeat']}; attempt {identity['attempt']}.",
        "",
        f"Route: **{report['route']}**. Coverage complete: {report['coverage_complete']}.",
        f"Schema: {automatic['schema']}. Support structure: {report['support_structure']}.",
        "Retrieval: not applicable (supplied evidence).",
    ]
    citation = automatic.get("citation", {})
    lines += [
        f"Citation precision / recall / F1: {citation.get('precision')} / "
        f"{citation.get('recall')} / {citation.get('f1')}.",
        "",
        "| Component | Point | Status | Decision |",
        "| --- | --- | --- | --- |",
    ]
    for item in report["results"]:
        decision = item.get("decision") or {}
        value = next(
            (
                decision[k]
                for k in (
                    "classification",
                    "supported",
                    "support_sufficient",
                    "conclusion_adequate",
                )
                if k in decision
            ),
            "unavailable",
        )
        lines.append(
            f"| {item['component']} | {item['point_id'] or '—'} | {item['status']} | {value} |"
        )
    lines.append("")
    for item in report["results"]:
        decision = item.get("decision") or {}
        reason = (
            decision.get("reason")
            or decision.get("explanation")
            or item.get("error")
            or item.get("error_type")
        )
        if reason:
            lines += [f"**{item['component']} {item['point_id'] or ''}:** {reason}", ""]
    lines += [
        "Strict combined reporting is deferred to Task 12. "
        "Judge decisions are diagnostic, not proof of correctness.",
        "",
    ]
    return "\n".join(lines)
