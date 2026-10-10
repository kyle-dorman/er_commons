"""Mechanical checks and readable displays for isolated Task 08F proposals.

A passing record is prepared for human review, never semantically verified or
approved. Source roles and identities come exclusively from the frozen intake.
"""

from __future__ import annotations

import re
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]


def answer_output_schema() -> dict[str, Any]:
    """Return the strict single-answer model contract, without decision fields."""
    text = {"type": "string", "minLength": 1, "pattern": r"\S"}
    point: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "point_id": {"type": "string", "pattern": r"^[A-Za-z][A-Za-z0-9_-]*$"},
            "text": text,
            "citation_ids": {"type": "array", "items": text, "minItems": 1, "uniqueItems": True},
        },
        "required": ["point_id", "text", "citation_ids"],
    }
    qualification = {
        **point,
        "properties": {
            **point["properties"],
            "applies_to": {"type": "array", "items": text, "minItems": 1, "uniqueItems": True},
        },
        "required": [*point["required"], "applies_to"],
    }
    properties = {
        "case_id": text,
        "question": text,
        "conclusion": point,
        "supporting_points": {"type": "array", "items": point},
        "qualifications": {"type": "array", "items": qualification},
        "optional_context": {"type": "array", "items": point},
        "citation_locators": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"occurrence_id": text, "excerpt": text},
                "required": ["occurrence_id", "excerpt"],
            },
        },
        "review_notes": {"type": "array", "items": text},
        "substantive_changes": {"type": "array", "items": text},
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
    }


def blocked_output_schema() -> dict[str, Any]:
    """Describe a specific model obstacle without creating a human disposition."""
    text = {"type": "string", "minLength": 1, "pattern": r"\S"}
    properties = {
        "case_id": text,
        "question": text,
        "blocked_reason": text,
        "review_notes": {"type": "array", "items": text},
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
    }


def preparation_output_schema() -> dict[str, Any]:
    """Use a Structured Outputs root object for either an answer or an obstacle."""
    properties = {
        "status": {"type": "string", "enum": ["proposed", "blocked"]},
        "answer": {"anyOf": [_transport_schema(answer_output_schema()), {"type": "null"}]},
        "blocked_reason": {
            "anyOf": [{"type": "string", "minLength": 1, "pattern": r"\S"}, {"type": "null"}]
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
    }


def _transport_schema(value: Any) -> Any:
    """Remove provider-unsupported uniqueness keywords only from the wire schema."""
    if isinstance(value, dict):
        return {
            key: _transport_schema(member) for key, member in value.items() if key != "uniqueItems"
        }
    if isinstance(value, list):
        return [_transport_schema(member) for member in value]
    return value


def validate_preparation(output: Any, case_input: dict[str, Any]) -> dict[str, Any]:
    """Check the outcome discriminator; a blocked output is never a valid answer."""
    errors = [
        f"{'.'.join(map(str, error.absolute_path)) or '$'}: {error.message}"
        for error in Draft202012Validator(preparation_output_schema()).iter_errors(output)
    ]
    if errors:
        return _report(errors)
    if output["status"] == "proposed":
        if output["blocked_reason"] is not None or output["answer"] is None:
            errors.append("A proposed output requires an answer and null blocked_reason")
        else:
            return validate_answer(output["answer"], case_input)
    elif output["answer"] is not None or output["blocked_reason"] is None:
        errors.append("A blocked output requires null answer and a specific blocked_reason")
    return _report(errors)


def validate_blocked(record: Any, case_input: dict[str, Any]) -> dict[str, Any]:
    """Check a blocked preparation record without treating it as an answer."""
    errors = [
        f"{'.'.join(map(str, error.absolute_path)) or '$'}: {error.message}"
        for error in Draft202012Validator(blocked_output_schema()).iter_errors(record)
    ]
    if not errors:
        for key in ("case_id", "question"):
            if record[key] != case_input[key]:
                errors.append(f"Exact {key} binding differs from frozen intake")
    return _report(errors)


def _report(errors: list[str]) -> dict[str, Any]:
    """Separate mechanical success from semantic judgments and human approval."""
    return {
        "schema_version": "task08f.answer_validation.v1",
        "check_type": "mechanical",
        "valid": not errors,
        "errors": errors,
        "semantic_support_verified": False,
        "human_approval": False,
        "limitations": [
            "Resolved citations and valid structure do not establish semantic support.",
            "Model review notes are advisory; human answer decisions remain blank.",
        ],
    }


def validate_answer(answer: Any, case_input: dict[str, Any]) -> dict[str, Any]:
    """Check exact case/question binding, citation scope and point attachments."""
    errors = [
        f"{'.'.join(map(str, error.absolute_path)) or '$'}: {error.message}"
        for error in Draft202012Validator(answer_output_schema()).iter_errors(answer)
    ]
    if errors:
        return _report(errors)
    for key in ("case_id", "question"):
        if answer[key] != case_input[key]:
            errors.append(f"Exact {key} binding differs from frozen intake")
    citations = {row["occurrence_id"]: row for row in case_input["citations"]}
    if len(citations) != len(case_input["citations"]):
        errors.append("Frozen intake has duplicate citation occurrence IDs")
    essential = [answer["conclusion"], *answer["supporting_points"]]
    essential_ids = {point["point_id"] for point in essential}
    seen: set[str] = set()
    used: set[str] = set()
    for role, points in (
        ("essential", essential),
        ("qualification", answer["qualifications"]),
        ("optional_context", answer["optional_context"]),
    ):
        for point in points:
            pid = point["point_id"]
            if pid in seen:
                errors.append(f"Duplicate point ID: {pid}")
            seen.add(pid)
            if role == "qualification":
                for target in point["applies_to"]:
                    if target not in essential_ids:
                        errors.append(f"{pid}: qualification target is not essential: {target}")
            for cid in point["citation_ids"]:
                used.add(cid)
                citation = citations.get(cid)
                if citation is None:
                    errors.append(f"{pid}: citation outside approved case scope: {cid}")
                    continue
                if role != "optional_context" and citation["role"] == "optional_context":
                    errors.append(f"{pid}: optional context promoted to required support: {cid}")
                _check_citation(citation, errors)
    located: set[str] = set()
    for locator in answer["citation_locators"]:
        cid = locator["occurrence_id"]
        if cid not in used:
            errors.append(f"Unused or unknown citation locator: {cid}")
            continue
        located.add(cid)
        source = citations.get(cid)
        if source is not None:
            text = source.get("full_source_text", source.get("excerpt", ""))
            if locator["excerpt"] not in text:
                errors.append(f"{cid}: locator excerpt is not exact supplied source text")
    for cid in sorted(used - located):
        errors.append(f"{cid}: missing relevant citation locator")
    return _report(errors)


def _check_citation(citation: dict[str, Any], errors: list[str]) -> None:
    """Require intake-owned canonical identity and an inspectable within-unit locator."""
    cid = citation["occurrence_id"]
    target = citation.get("canonical_target", {})
    for key in ("document_id", "edition", "unit_id", "unit_type"):
        if not target.get(key):
            errors.append(f"{cid}: missing canonical target {key}")
    if target.get("unit_type") not in {"section", "subsection", "table"}:
        errors.append(f"{cid}: unsupported canonical unit type")
    if not target.get("pages") and not target.get("anchor"):
        errors.append(f"{cid}: missing canonical pages/anchor")
    if not citation.get("excerpt") and not citation.get("cells"):
        errors.append(f"{cid}: missing relevant excerpt/cell locator")
    if not citation.get("full_source_ref"):
        errors.append(f"{cid}: missing full source reference")
    if citation.get("role") not in {"required", "optional_context"}:
        errors.append(f"{cid}: unrecognized approved citation role")


def _source_label(source: dict[str, Any]) -> str:
    """Render supplied document names or mechanically expand their stable source ID."""
    if label := source.get("source_label") or source.get("document_title"):
        return str(label)
    source_id = str(source.get("source_id", ""))
    if source_id == "deir_main":
        return "DEIR main report"
    match = re.fullmatch(
        r"(deir|feir)_appendix_([a-z]+)([0-9]*)(?:_part_([0-9]+)_of_([0-9]+))?",
        source_id,
    )
    if match:
        report, letter, number, part, total = match.groups()
        prefix = "DEIR" if report == "deir" else "Final EIR"
        appendix = letter.upper() + (f".{number}" if number else "")
        suffix = f" part {part} of {total}" if part else ""
        return f"{prefix} Appendix {appendix}{suffix}"
    return source_id.replace("_", " ") or "Reviewed source"


def render_answer(answer: dict[str, Any], case_input: dict[str, Any]) -> str:
    """Render the sole answer with qualifications attached and linked source excerpts."""
    validation = validate_answer(answer, case_input)
    if not validation["valid"]:
        raise ValueError("Cannot render invalid answer: " + "; ".join(validation["errors"]))
    citations = {row["occurrence_id"]: row for row in case_input["citations"]}
    used: list[str] = []

    def point_line(point: dict[str, Any]) -> str:
        """Give each used source a readable, stable display-local footnote number."""
        links = []
        for cid in point["citation_ids"]:
            if cid not in used:
                used.append(cid)
            links.append(f"[^{used.index(cid) + 1}]")
        return str(point["text"]) + " " + " ".join(links)

    lines = [
        f"# {answer['case_id']} — prepared, awaiting human review",
        "",
        "## Question",
        "",
        answer["question"],
        "",
        "## Answer",
        "",
    ]
    for index, point in enumerate([answer["conclusion"], *answer["supporting_points"]]):
        prefix = "**Conclusion:** " if index == 0 else ""
        lines.append("- " + prefix + point_line(point))
        for qualification in answer["qualifications"]:
            if point["point_id"] in qualification["applies_to"]:
                lines.append("  - **Qualification:** " + point_line(qualification))
    if answer["optional_context"]:
        lines.extend(["", "## Optional context", ""])
        for point in answer["optional_context"]:
            lines.append("- " + point_line(point))
    lines.extend(["", "## Cited sources and relevant locators", ""])
    for index, cid in enumerate(used, 1):
        source = citations[cid]
        target = source["canonical_target"]
        label = _source_label(source)
        location = target.get("label") or source.get("title") or target["unit_type"].title()
        pages = target.get("pages", [])
        page_text = ", ".join(map(str, pages)) if isinstance(pages, list) else str(pages)
        lines.append(
            f"[^{index}]: {label}; {target['edition']}; {location}; pages {page_text}. "
            f"Role: {source['role'].replace('_', ' ')}."
        )
        for locator in answer["citation_locators"]:
            if locator["occurrence_id"] == cid:
                lines.append("    Excerpt: " + locator["excerpt"].replace("\n", "\n    "))
        if source.get("cells"):
            lines.append("    Relevant cells: " + str(source["cells"]))
        if source.get("pdf_url"):
            lines.append(f"    [Source PDF, cited page]({source['pdf_url']})")
        ref = source["full_source_ref"]
        if isinstance(ref, dict):
            path = ref.get("path") or ref.get("binding", {}).get("path")
        else:
            path = ref
        if path:
            lines.append(f"    [Complete source]({path})")
    if answer["review_notes"] or answer["substantive_changes"]:
        lines.extend(["", "## Advisory preparation notes", ""])
        lines.extend("- " + note for note in answer["review_notes"])
        lines.extend("- Substantive change: " + note for note in answer["substantive_changes"])
    lines.extend(["", "08F answer approval: blank. Final disposition: blank.", ""])
    return "\n".join(lines)
