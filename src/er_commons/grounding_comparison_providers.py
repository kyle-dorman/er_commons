"""Task 09E.1 provider wire contracts; pure rendering and parsing never dispatch calls."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any

from er_commons.artifact_io import stable_json_sha256

# Preserve the established provider module imports used by saved experiment runners.
from er_commons.grounding_provider_config import (
    CONDITION_IDS as CONDITION_IDS,
)
from er_commons.grounding_provider_config import (
    Condition as Condition,
)
from er_commons.grounding_provider_config import (
    StageKind as StageKind,
)
from er_commons.grounding_provider_config import (
    load_conditions as load_conditions,
)


def _json(value: Any) -> str:
    """Serialize deterministic wire JSON while preserving intentional object order."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _identity(endpoint: str, body: dict[str, Any]) -> str:
    """Bind exact endpoint and body bytes independently of transport credentials."""
    return hashlib.sha256((endpoint + "\n" + _json(body)).encode()).hexdigest()


def _review_ids(payload: dict[str, Any]) -> list[str]:
    """Read only ordered point identity from the common binary observation projection."""
    ids = [item["point_id"] for item in payload["point_assessments"]]
    if len(ids) != len(set(ids)) or any(not isinstance(item, str) or not item for item in ids):
        raise ValueError("Conclusion observations require unique nonempty point IDs")
    return ids


def decision_questions(kind: StageKind, payload: dict[str, Any]) -> list[dict[str, str]]:
    """Freeze binary questions; only conclusion questions share full conclusion visibility."""
    if kind == "abstention":
        return [
            {
                "name": "substantive",
                "instructions": "Does any original answer point make a substantive assertion?",
            },
            {
                "name": "clean_abstention",
                "instructions": (
                    "Does the whole original answer only decline or state inability to answer, "
                    "with no substantive assertion?"
                ),
            },
        ]
    if kind == "point":
        return [
            {
                "name": "supported",
                "instructions": (
                    "Does this point's actual cited evidence establish every substantive assertion "
                    "and material qualification actually made in the target point? "
                    "Judge support, not completeness."
                ),
            }
        ]
    if kind == "conclusion":
        questions = [
            {
                "name": "clean_abstention",
                "instructions": (
                    "Is the whole original answer a genuinely clean abstention "
                    "with no substantive assertions?"
                ),
            },
            {
                "name": "conclusion_supported",
                "instructions": (
                    "Does the actual cited evidence support the original conclusion, "
                    "including any premise on which it necessarily depends?"
                ),
            },
        ]
        questions.extend(
            {
                "name": f"review_{index}",
                "instructions": (
                    f"Independently review original point {point_id!r} against its own actual "
                    "citations. Is every substantive assertion and material qualification "
                    "it actually makes supported? Prior verdicts are fallible observations, "
                    "not evidence."
                ),
            }
            for index, point_id in enumerate(_review_ids(payload))
        )
        return questions
    raise ValueError("Unknown comparison stage")


def _portable_arrays(schema: dict[str, Any]) -> dict[str, Any]:
    """Use supported item unions; exact review ordering remains a local invariant."""
    value = copy.deepcopy(schema)

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            slots = node.pop("prefixItems", None)
            if slots:
                node["items"] = {"anyOf": slots}
                ids = [slot["properties"]["point_id"]["const"] for slot in slots]
                node["description"] = (
                    node.get("description", "")
                    + " Return exactly one review per point in this order: "
                    + _json(ids)
                ).strip()
            elif node.get("type") == "array" and "items" not in node:
                # Only the zero-point conclusion schema has no items in our contract.
                if node.get("maxItems") != 0:
                    raise ValueError("Unbounded array schema lacks an item contract")
                node["items"] = {"$ref": "#/$defs/GenerationReview"}
                node["description"] = "No point reviews are permitted; return an empty array."
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return value


def _schema_for_openai(schema: dict[str, Any]) -> dict[str, Any]:
    """Require every emitted property for strict decoding; empty diagnostics remain legal."""
    value = _portable_arrays(schema)

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            node.pop("default", None)
            for key in ("minLength", "maxLength"):
                node.pop(key, None)
            if "const" in node:
                node["enum"] = [node.pop("const")]
            if node.get("type") == "object":
                node["additionalProperties"] = False
                node["required"] = list(node.get("properties", {}))
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return value


def _schema_for_anthropic(schema: dict[str, Any]) -> dict[str, Any]:
    """Remove unsupported scalar constraints while retaining their meaning in descriptions."""
    value = _portable_arrays(schema)

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            removed = {
                key: node.pop(key)
                for key in ("minLength", "maxLength", "minimum", "maximum", "maxItems")
                if key in node
            }
            if node.get("minItems", 0) > 1:
                removed["minItems"] = node.pop("minItems")
            if removed:
                node["description"] = (
                    node.get("description", "") + " Constraints: " + _json(removed)
                ).strip()
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return value


def _ordered_payload(kind: StageKind, payload: dict[str, Any]) -> dict[str, Any]:
    """Place unchanged visible evidence before varying content without adding any fields."""
    orders = {
        "abstention": ["points"],
        "point": ["evidence", "question", "context_points", "point"],
        "conclusion": ["evidence", "question", "answer", "point_assessments"],
    }
    keys = orders[kind]
    return {key: copy.deepcopy(payload[key]) for key in keys if key in payload} | {
        key: copy.deepcopy(value) for key, value in payload.items() if key not in keys
    }


def cache_prefix_text(rendered: dict[str, Any]) -> str:
    """Expose ordered visible text for byte audits, never claiming exact token prefixes."""
    body = rendered["body"]
    parts: list[str] = []
    if "system" in body:
        parts.extend(block["text"] for block in body["system"])
    if "text" in body:
        parts.append(_json(body["text"]))
    if "output_config" in body:
        parts.append(_json(body["output_config"]))
    for message in body.get("input", body.get("messages", [])):
        content = message["content"]
        parts.append(
            content if isinstance(content, str) else "\n".join(block["text"] for block in content)
        )
    if "state" in body:
        parts.append(_json(body["state"]))
    if "questions" in body:
        parts.append(_json(body["questions"]))
    return "\n".join(parts)


def render_request(
    condition: Condition,
    kind: StageKind,
    payload: dict[str, Any],
    prompt: str,
    schema: dict[str, Any],
) -> dict[str, Any]:
    """Render a deterministic provider request without adding data or generating observations."""
    if kind not in {"abstention", "point", "conclusion"}:
        raise ValueError("Unknown comparison stage")
    body: dict[str, Any] = {"model": condition.model}
    ordered_payload = _ordered_payload(kind, payload)
    text = _json(ordered_payload)
    if condition.api == "openai_responses":
        content: list[dict[str, Any]] = [{"type": "input_text", "text": text}]
        if condition.settings.get("evidence_cache_breakpoint") and kind != "abstention":
            # Serialize complete values, so nested keys and escaped delimiters cannot move the cut.
            prefix = _json({key: ordered_payload[key] for key in ("evidence", "question")})
            prefix = prefix[:-1] + ","
            if not text.startswith(prefix):
                raise ValueError(
                    "Evidence breakpoint requires evidence/question before dynamic input"
                )
            content = [
                {
                    "type": "input_text",
                    "text": prefix,
                    "prompt_cache_breakpoint": {"mode": "explicit"},
                },
                {"type": "input_text", "text": text[len(prefix) :]},
            ]
        body.update(
            input=[
                {"role": "developer", "content": [{"type": "input_text", "text": prompt}]},
                {"role": "user", "content": content},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": f"grounding_{kind}",
                    "strict": True,
                    "schema": _schema_for_openai(schema),
                }
            },
            max_output_tokens=condition.output_cap,
            store=False,
            truncation="disabled",
            reasoning={"effort": condition.settings["reasoning_effort"]},
        )
        for name in (
            "prompt_cache_options",
            "prompt_cache_retention",
            "prompt_cache_key",
            "temperature",
            "top_p",
        ):
            if name in condition.settings:
                body[name] = copy.deepcopy(condition.settings[name])
    elif condition.api == "anthropic_messages":
        anthropic_content: list[dict[str, Any]] = [{"type": "text", "text": text}]
        if condition.settings.get("anthropic_evidence_cache_breakpoint") and kind != "abstention":
            prefix = _json({key: ordered_payload[key] for key in ("evidence", "question")})
            prefix = prefix[:-1] + ","
            if not text.startswith(prefix):
                raise ValueError(
                    "Anthropic breakpoint requires evidence/question before dynamic input"
                )
            anthropic_content = [
                {
                    "type": "text",
                    "text": prefix,
                    "cache_control": {"type": "ephemeral", "ttl": "5m"},
                },
                {"type": "text", "text": text[len(prefix) :]},
            ]
        body.update(
            system=[
                {
                    "type": "text",
                    "text": prompt,
                    "cache_control": {"type": "ephemeral", "ttl": "5m"},
                }
            ],
            messages=[{"role": "user", "content": anthropic_content}],
            max_tokens=condition.output_cap,
            thinking={"type": "adaptive"},
            output_config={
                "effort": condition.settings["reasoning_effort"],
                "format": {"type": "json_schema", "schema": _schema_for_anthropic(schema)},
            },
        )
    elif condition.api == "fireworks_chat":
        body.update(
            messages=[
                {
                    "role": "system",
                    "content": prompt + "\nReturn JSON matching this schema:\n" + _json(schema),
                },
                {"role": "user", "content": text},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": f"grounding_{kind}", "schema": copy.deepcopy(schema)},
            },
            max_tokens=condition.output_cap,
            stream=False,
        )
        if condition.settings.get("fireworks_reasoning_mode") == "prompt_schema":
            # Fireworks native structured mode disables reasoning. Keep the same
            # schema in the system prompt and enforce it on the returned JSON locally.
            body.pop("response_format")
            body["reasoning_effort"] = "medium"
            body["context_length_exceeded_behavior"] = "error"
        if condition.settings.get("fireworks_evidence_cache_prefix"):
            # Keep the whole rubric, payload and schema unchanged; move only the
            # variable schema framing beyond the evidence-bearing JSON payload.
            body["messages"] = [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": text + "\nReturn JSON matching this schema:\n" + _json(schema),
                },
            ]
            stable = {
                "model": condition.model,
                "kind": kind,
                "prompt": prompt,
                "evidence": ordered_payload.get("evidence"),
                "question": ordered_payload.get("question"),
            }
            body["prompt_cache_key"] = stable_json_sha256(stable)
        if "fireworks_cache_isolation_key" in condition.settings:
            body["prompt_cache_isolation_key"] = condition.settings["fireworks_cache_isolation_key"]
    elif condition.api == "openai_decisions":
        body.update(
            input=[
                {"role": "user", "content": [{"type": "input_text", "text": prompt + "\n" + text}]}
            ],
            questions=[
                {"type": "predicate", **question} for question in decision_questions(kind, payload)
            ],
        )
    else:
        body.update(
            state={"instructions": prompt, "payload": copy.deepcopy(ordered_payload)},
            questions={
                q["name"]: {
                    "type": "noul",
                    "instructions": q["instructions"],
                    "criteria": {
                        "false": "No, the stated condition is not satisfied.",
                        "true": "Yes, the stated condition is satisfied.",
                    },
                }
                for q in decision_questions(kind, payload)
            },
        )
    return {
        "endpoint": condition.endpoint,
        "model": condition.model,
        "body": body,
        "request_sha256": _identity(condition.endpoint, body),
    }


def count_request(rendered: dict[str, Any]) -> dict[str, Any]:
    """Count rendered input without sampling-only fields; bind the complete request identity."""
    if rendered["endpoint"] != "https://api.openai.com/v1/responses":
        raise ValueError("No qualified exact counter for this endpoint")
    body = copy.deepcopy(rendered["body"])
    for field in (
        "max_output_tokens",
        "store",
        "prompt_cache_options",
        "prompt_cache_retention",
        "prompt_cache_key",
        "temperature",
        "top_p",
    ):
        body.pop(field, None)
    endpoint = "https://api.openai.com/v1/responses/input_tokens"
    return {
        "endpoint": endpoint,
        "body": body,
        "model": rendered["model"],
        "request_sha256": _identity(endpoint, body),
        "counted_request_sha256": rendered["request_sha256"],
    }


def estimated_count_request(rendered: dict[str, Any]) -> dict[str, Any]:
    """Bind Anthropic's estimated count to the exact input fields, never an exact receipt."""
    if rendered["endpoint"] != "https://api.anthropic.com/v1/messages":
        raise ValueError("No native estimated counter for this endpoint")
    allowed = {"model", "system", "messages", "thinking", "output_config", "max_tokens"}
    if set(rendered["body"]) - allowed:
        raise ValueError("Unreviewed Anthropic fields in estimated counter request")
    body = copy.deepcopy(rendered["body"])
    body.pop("max_tokens", None)
    endpoint = "https://api.anthropic.com/v1/messages/count_tokens"
    return {
        "endpoint": endpoint,
        "body": body,
        "model": rendered["model"],
        "request_sha256": _identity(endpoint, body),
        "counted_request_sha256": rendered["request_sha256"],
        "counting_mode": "provider_estimate",
    }


def _integer(value: Any, field: str) -> int:
    """Reject boolean, fractional, negative and missing native usage counts."""
    if type(value) is not int or value < 0:
        raise ValueError(f"Invalid native usage field: {field}")
    return value


def _parse_usage(condition: Condition, response: dict[str, Any]) -> dict[str, Any]:
    """Normalize disjoint billed token buckets without inventing unreported cache hits."""
    usage = response.get("usage")
    if not isinstance(usage, dict):
        raise ValueError("Native response lacks token usage")
    for field in ("input_tokens_details", "prompt_tokens_details", "cache_creation"):
        if field in usage and not isinstance(usage[field], dict):
            raise ValueError("Malformed native usage details")
    read: int | None = None
    write: int | None = None
    if condition.api == "anthropic_messages":
        ordinary = _integer(usage.get("input_tokens"), "input_tokens")
        if "cache_read_input_tokens" in usage:
            read = _integer(usage["cache_read_input_tokens"], "cache_read_input_tokens")
        if "cache_creation_input_tokens" in usage:
            write = _integer(usage["cache_creation_input_tokens"], "cache_creation_input_tokens")
        total = ordinary + (read or 0) + (write or 0)
        output = _integer(usage.get("output_tokens"), "output_tokens")
    elif condition.api == "fireworks_chat":
        total = _integer(usage.get("prompt_tokens"), "prompt_tokens")
        output = _integer(usage.get("completion_tokens"), "completion_tokens")
        details = usage.get("prompt_tokens_details", {})
        if "cached_tokens" in details:
            read = _integer(details["cached_tokens"], "cached_tokens")
        ordinary = total - (read or 0)
    else:
        total = _integer(usage.get("input_tokens"), "input_tokens")
        output = _integer(
            usage.get("output_tokens", 0)
            if condition.api == "openai_decisions"
            else usage.get("output_tokens"),
            "output_tokens",
        )
        details = usage.get("input_tokens_details", {})
        if "cached_tokens" in details:
            read = _integer(details["cached_tokens"], "cached_tokens")
        if "cache_write_tokens" in details:
            write = _integer(details["cache_write_tokens"], "cache_write_tokens")
        ordinary = total - (read or 0) - (write or 0)
    if ordinary < 0:
        raise ValueError("Native cache counts exceed total input")
    return {
        "input_tokens": total,
        "ordinary_input_tokens": ordinary,
        "output_tokens": output,
        "cache_read_tokens": read,
        "cache_write_tokens": write,
        "native_usage": copy.deepcopy(usage),
    }


def parse_usage(condition: Condition, response: dict[str, Any]) -> dict[str, Any]:
    """Report malformed usage uniformly without exposing native values or secret text."""
    try:
        return _parse_usage(condition, response)
    except (TypeError, AttributeError, KeyError, OverflowError):
        raise ValueError("Malformed native usage") from None


def _probability(value: Any) -> bool:
    """Freeze the threshold and retain exact ties as unscored failures."""
    if type(value) not in {int, float} or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Invalid decision probability")
    if value == 0.5:
        raise ValueError("Exact decision probability tie")
    return bool(value > 0.5)


def _parse_decisions(
    condition: Condition, kind: StageKind, payload: dict[str, Any], response: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, float]]:
    """Validate complete named predictions before applying the common semantic projection."""
    expected = [q["name"] for q in decision_questions(kind, payload)]
    answers = response.get("answers")
    values: dict[str, Any] = {}
    if condition.api == "openai_decisions":
        if not isinstance(answers, list):
            raise ValueError("Decisions requires an answer array")
        for item in answers:
            if not isinstance(item, dict) or item.get("type") != "predicate":
                raise ValueError("Decision refusal or invalid answer type")
            name = item.get("name")
            if not isinstance(name, str) or name in values:
                raise ValueError("Duplicate or invalid decision name")
            values[name] = item.get("probability")
    else:
        if not isinstance(answers, dict):
            raise ValueError("System One requires a named answer mapping")
        for name, item in answers.items():
            if not isinstance(item, dict) or item.get("type") != "noul":
                raise ValueError("Decision refusal or invalid answer type")
            values[name] = item.get("noul")
    if set(values) != set(expected):
        raise ValueError("Missing or unexpected native decision IDs")
    verdicts = {name: _probability(values[name]) for name in expected}
    probabilities = {name: float(values[name]) for name in expected}
    decision: dict[str, Any]
    if kind == "abstention":
        substantive, clean = verdicts["substantive"], verdicts["clean_abstention"]
        if substantive and clean:
            raise ValueError("Inconsistent substantive and clean-abstention decisions")
        decision = {
            "classification": "substantive"
            if substantive
            else "clean_abstention"
            if clean
            else "ambiguous"
        }
    elif kind == "point":
        decision = {"point_id": payload["point"]["point_id"], "supported": verdicts["supported"]}
    else:
        clean = verdicts["clean_abstention"]
        reviews = [
            {"point_id": point_id, "supported": verdicts[f"review_{index}"]}
            for index, point_id in enumerate(_review_ids(payload))
        ]
        if clean and (
            verdicts["conclusion_supported"] or any(item["supported"] for item in reviews)
        ):
            raise ValueError("Clean abstention conflicts with supported content")
        decision = {
            "clean_abstention": clean,
            "conclusion_supported": None if clean else verdicts["conclusion_supported"],
            "point_reviews": reviews,
        }
    return decision, probabilities


def _generation_text(condition: Condition, response: dict[str, Any]) -> str:
    """Reject refusal and truncated output before decoding one generated JSON object."""
    if condition.api == "openai_responses":
        if response.get("status") != "completed":
            raise ValueError("Generation incomplete or failed")
        blocks = [
            block
            for item in response.get("output", [])
            if item.get("type") == "message"
            for block in item.get("content", [])
        ]
        if any(block.get("type") == "refusal" for block in blocks):
            raise ValueError("Generation refusal")
        texts = [block["text"] for block in blocks if block.get("type") == "output_text"]
    elif condition.api == "anthropic_messages":
        if response.get("stop_reason") != "end_turn":
            raise ValueError("Generation refusal, truncation or unexpected stop")
        texts = [
            block["text"] for block in response.get("content", []) if block.get("type") == "text"
        ]
    else:
        choices = response.get("choices", [])
        if len(choices) != 1 or choices[0].get("finish_reason") != "stop":
            raise ValueError("Generation truncation or invalid choice count")
        message = choices[0].get("message", {})
        if message.get("refusal"):
            raise ValueError("Generation refusal")
        texts = [message.get("content")]
    if len(texts) != 1 or not isinstance(texts[0], str):
        raise ValueError("Generation requires exactly one text result")
    return texts[0]


def _parse_response(
    condition: Condition, kind: StageKind, payload: dict[str, Any], response: dict[str, Any]
) -> dict[str, Any]:
    """Return semantic raw data, native usage and separate probabilities for local validation."""
    model = response.get("model")
    if model != condition.model:
        raise ValueError("Native response model does not match frozen condition")
    if response.get("error") is not None:
        raise ValueError("Native provider error")
    probabilities: dict[str, float] = {}
    if condition.kind == "decision":
        decision, probabilities = _parse_decisions(condition, kind, payload, response)
    else:
        decision = json.loads(
            _generation_text(condition, response), object_pairs_hook=_unique_object
        )
        if not isinstance(decision, dict):
            raise ValueError("Generated decision must be a JSON object")
    return {
        "decision": decision,
        "usage": parse_usage(condition, response),
        "probabilities": probabilities,
    }


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate generated JSON fields instead of silently selecting the last one."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate generated JSON field")
        result[key] = value
    return result


def parse_response(
    condition: Condition, kind: StageKind, payload: dict[str, Any], response: dict[str, Any]
) -> dict[str, Any]:
    """Convert malformed native envelopes into safe stage errors without losing usage receipts."""
    try:
        return _parse_response(condition, kind, payload, response)
    except (TypeError, AttributeError, KeyError, OverflowError, json.JSONDecodeError):
        raise ValueError("Malformed native response") from None
