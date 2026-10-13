"""Versioned semantic decisions with quotation diagnostics outside the stage graph."""

from __future__ import annotations

import copy
import json
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons import grounding_abstention as gate
from er_commons import grounding_comparison_prompts as prompts
from er_commons import grounding_stages as legacy
from er_commons.grounding_evidence import source_texts
from er_commons.judge_packets import serialize_payload

VERSION = "task09e1.semantic_grounding.v1"


class StrictModel(BaseModel):
    """Reject coercions and unrecognized fields before interpreting any decision."""

    model_config = ConfigDict(strict=True, extra="forbid")


class PointDecision(StrictModel):
    """The sole point observation allowed to cross the stage boundary."""

    point_id: str = Field(min_length=1)
    supported: bool


class GateDecision(StrictModel):
    """Preserve the answer-only gate's three outcomes across providers."""

    classification: gate.Classification


class ConclusionStatus(StrictModel):
    """Keep nullable clean abstention consistent across native and generated results."""

    conclusion_supported: bool | None
    clean_abstention: bool

    @model_validator(mode="after")
    def consistent_abstention(self) -> Self:
        """Null support is legal exactly when the judge reports clean abstention."""
        if self.clean_abstention != (self.conclusion_supported is None):
            raise ValueError("Conclusion support is null exactly for clean abstention")
        return self


class ConclusionDecision(ConclusionStatus):
    """The common conclusion decision contains only ordered binary reviews."""

    point_reviews: list[PointDecision]


class Quote(StrictModel):
    """Source identity is structural; copied text is an optional diagnostic."""

    citation_id: str = Field(min_length=1)
    excerpt: str = ""


class Issue(StrictModel):
    """An optional candidate span never determines validity of a binary decision."""

    assertion: str = ""
    explanation: str = ""


class GenerationPoint(PointDecision):
    """Generation-only commentary remains outside the point observation."""

    locators: list[Quote] = Field(default_factory=list)
    unsupported_assertions: list[Issue] = Field(default_factory=list)
    explanation: str = ""


class GenerationReview(PointDecision):
    """A review explanation may be saved but never becomes a new observation."""

    explanation: str = ""


class GenerationConclusion(ConclusionStatus):
    """Optional generation diagnostics do not gate downstream scoring."""

    point_reviews: list[GenerationReview]
    locators: list[Quote] = Field(default_factory=list)
    explanation: str = ""


class GenerationGate(GateDecision):
    """Optional gate rationale does not change its classification contract."""

    explanation: str = ""


def point_inputs(packet: dict[str, Any]) -> list[dict[str, Any]]:
    """Reuse historical exact point/evidence projection without adding visible sources."""
    return legacy.point_inputs(packet)


def stage_prompt(kind: str) -> str:
    """Return frozen generation instructions without depending on legacy prompt edits."""
    values = {
        "abstention": prompts.GENERATION_ABSTENTION,
        "point": prompts.GENERATION_POINT,
        "conclusion": prompts.GENERATION_CONCLUSION,
    }
    if kind not in values:
        raise ValueError("Unknown grounding stage")
    return values[kind]


def native_stage_prompt(kind: str) -> str:
    """Return frozen classification instructions without generation-only diagnostics."""
    values = {
        "abstention": prompts.DECISION_ABSTENTION,
        "point": prompts.DECISION_POINT,
        "conclusion": prompts.DECISION_CONCLUSION,
    }
    if kind not in values:
        raise ValueError("Unknown grounding stage")
    return values[kind]


def _checked_conclusion(value: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Revalidate the original payload and only the common ordered binary observations."""
    if set(value) != {"question", "answer", "evidence", "point_assessments"}:
        raise ValueError("Conclusion input permits only original payload and point assessments")
    payload = json.loads(
        serialize_payload(
            {key: value[key] for key in ("question", "answer", "evidence")}, "grounding"
        )
    )
    inputs = legacy.projected_point_inputs(payload)
    rows = value["point_assessments"]
    if not isinstance(rows, list) or len(rows) != len(inputs):
        raise ValueError("Conclusion requires all point assessments in packet order")
    predictions = [PointDecision.model_validate(row).model_dump() for row in rows]
    if [row["point_id"] for row in predictions] != [row["point"]["point_id"] for row in inputs]:
        raise ValueError("Conclusion requires exact ordered point IDs")
    return payload, predictions


def conclusion_input(packet: dict[str, Any], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    """Retain unsupported original text while forwarding only strict binary observations."""
    value = {**legacy.grounding_payload(packet), "point_assessments": copy.deepcopy(decisions)}
    payload, predictions = _checked_conclusion(value)
    return {**payload, "point_assessments": predictions}


def stage_schema(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Bind generation responses to exact visible IDs while keeping quote fields optional."""
    if kind == "abstention":
        gate._validate_input(payload)
        return GenerationGate.model_json_schema()
    if kind == "point":
        checked = legacy.checked_point_input(payload)
        schema = GenerationPoint.model_json_schema()
        schema["properties"]["point_id"]["const"] = checked.point.point_id
        return schema
    if kind == "conclusion":
        _, predictions = _checked_conclusion(payload)
        schema = GenerationConclusion.model_json_schema()
        reviews = schema["properties"]["point_reviews"]
        reviews.pop("items")
        items = []
        for prediction in predictions:
            item = copy.deepcopy(schema["$defs"]["GenerationReview"])
            item["properties"]["point_id"]["const"] = prediction["point_id"]
            items.append(item)
        if items:
            reviews["prefixItems"] = items
        reviews.update(minItems=len(items), maxItems=len(items))
        return schema
    raise ValueError("Unknown grounding stage")


def _quotation_diagnostics(result: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Fail invalid source identities; report absent or nonliteral text independently."""
    sources = {row["citation_id"]: row for row in payload.get("evidence", [])}
    locators = []
    for quote in result.get("locators", []):
        source = sources.get(quote["citation_id"])
        if source is None or source["resolution"] != "resolved":
            raise ValueError("Locator must identify an actual resolved citation in this input")
        texts = source_texts(source)
        excerpt = quote["excerpt"]
        locators.append(
            {
                **quote,
                "source_linked": True,
                "literal_match": bool(excerpt.strip()) and any(excerpt in text for text in texts),
            }
        )
    target = payload.get("point", {}).get("text", "")
    issues = [
        {
            **issue,
            "literal_match": bool(issue["assertion"].strip()) and issue["assertion"] in target,
        }
        for issue in result.get("unsupported_assertions", [])
    ]
    return {
        "status": "applicable",
        "locators": locators,
        "unsupported_assertions": issues,
        "missing_quotation": not locators or any(not row["excerpt"].strip() for row in locators),
    }


def _strict_view(kind: str, raw: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Check historical output requirements without fabricating legacy point rationales."""
    try:
        if kind == "abstention":
            gate.validate_result(raw, payload)
        elif kind == "point":
            legacy.validate_point(raw, payload)
        else:
            # The new projection intentionally cannot enter legacy conclusion_input.
            # Validate identical response-only legacy requirements over original evidence.
            result = legacy.ConclusionAssessment.model_validate_json(raw)
            legacy.validate_locators(result.locators, payload["evidence"])
    except ValueError as error:
        return {"status": "schema_error", "error": str(error)}
    return {"status": "validated"}


def validate_stage(
    kind: str, raw: str, payload: dict[str, Any], native: bool = False
) -> dict[str, Any]:
    """Return minimal semantic decisions with separate diagnostics, never repaired output."""
    stage_schema(kind, payload)
    models: dict[str, tuple[type[BaseModel], type[BaseModel]]] = {
        "abstention": (GateDecision, GenerationGate),
        "point": (PointDecision, GenerationPoint),
        "conclusion": (ConclusionDecision, GenerationConclusion),
    }
    parsed = models[kind][0 if native else 1].model_validate_json(raw)
    result = parsed.model_dump(mode="json")
    if kind == "abstention":
        decision = {"classification": result["classification"]}
    elif kind == "point":
        decision = {key: result[key] for key in ("point_id", "supported")}
        if decision["point_id"] != payload["point"]["point_id"]:
            raise ValueError("Point assessment must retain the exact target point ID")
    else:
        _, predictions = _checked_conclusion(payload)
        decision = {
            "conclusion_supported": result["conclusion_supported"],
            "clean_abstention": result["clean_abstention"],
            "point_reviews": [
                {key: row[key] for key in ("point_id", "supported")}
                for row in result["point_reviews"]
            ],
        }
        if [row["point_id"] for row in decision["point_reviews"]] != [
            row["point_id"] for row in predictions
        ]:
            raise ValueError("Conclusion reviews must cover every point exactly once in order")
        if decision["clean_abstention"] and (
            payload["answer"]["status"] != "abstained" or predictions
        ):
            raise ValueError("Clean abstention requires abstained status and no other points")
    not_applicable = {"status": "not_applicable"}
    return {
        "decision": decision,
        "quotation_diagnostics": not_applicable
        if native or kind == "abstention"
        else _quotation_diagnostics(result, payload),
        "strict_legacy": not_applicable if native else _strict_view(kind, raw, payload),
        "generation_diagnostics": None if native else result,
    }


def aggregate(points: list[dict[str, Any]], conclusion: dict[str, Any]) -> dict[str, Any]:
    """Score agreeing semantic decisions only, preserving historical zero-point behavior."""
    predictions = [PointDecision.model_validate(row) for row in points]
    result = ConclusionDecision.model_validate(conclusion)
    ids = [point.point_id for point in predictions]
    if len(ids) != len(set(ids)) or [row.point_id for row in result.point_reviews] != ids:
        raise ValueError("Aggregation requires distinct IDs and identical ordered review coverage")
    disagreements = [
        point.point_id
        for point, review in zip(predictions, result.point_reviews, strict=True)
        if point.supported != review.supported
    ]
    if disagreements:
        return {
            "status": "unresolved_disagreement",
            "score": None,
            "disagreement_point_ids": disagreements,
        }
    if result.clean_abstention:
        if predictions:
            raise ValueError("Clean abstention cannot contain substantive point assessments")
        return {"status": "not_applicable", "score": None, "disagreement_point_ids": []}
    score = (
        0
        if not result.conclusion_supported
        else 1
        if any(not p.supported for p in predictions)
        else 2
    )
    return {"status": "scored", "score": score, "disagreement_point_ids": []}


class GenerationConclusionOnly(ConclusionStatus):
    """Experimental conclusion-only output never fabricates independent point reviews."""

    locators: list[Quote] = Field(default_factory=list)
    explanation: str = ""


def conclusion_only_prompt() -> str:
    """Return the preserved experimental prompt without rewriting review instructions."""
    return prompts.CONCLUSION_ONLY


def conclusion_only_schema(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate genuine original observations but expose no prediction-derived output values."""
    _checked_conclusion(payload)
    return GenerationConclusionOnly.model_json_schema()


def validate_conclusion_only(raw: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Keep conclusion-only decisions distinct from outputs containing independent reviews."""
    _, predictions = _checked_conclusion(payload)
    result = GenerationConclusionOnly.model_validate_json(raw)
    if result.clean_abstention and (payload["answer"]["status"] != "abstained" or predictions):
        raise ValueError("Clean abstention requires abstained status and no other points")
    return {
        "decision": result.model_dump(exclude={"explanation", "locators"}),
        "generation_diagnostics": result.model_dump(),
        "quotation_diagnostics": _quotation_diagnostics(result.model_dump(), payload),
        "strict_legacy": {"status": "not_applicable"},
    }


def aggregate_conclusion_only(
    points: list[dict[str, Any]], conclusion: dict[str, Any]
) -> dict[str, Any]:
    """Use frozen point decisions directly; no independent-review disagreement gate exists."""
    predictions = [PointDecision.model_validate(row) for row in points]
    if len({row.point_id for row in predictions}) != len(predictions):
        raise ValueError("Aggregation requires distinct original point IDs")
    result = ConclusionStatus.model_validate(conclusion)
    if result.clean_abstention:
        if predictions:
            raise ValueError("Clean abstention cannot contain substantive point assessments")
        return {"status": "not_applicable", "score": None, "disagreement_point_ids": []}
    score = (
        0
        if not result.conclusion_supported
        else 1
        if any(not p.supported for p in predictions)
        else 2
    )
    return {"status": "scored", "score": score, "disagreement_point_ids": []}
