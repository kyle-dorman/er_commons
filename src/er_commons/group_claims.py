"""Prepare immutable Task08D native claim cards from current source-only packets."""

from __future__ import annotations

import copy
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.group_claims_inventory import validate_inventory

VERSION = "task08d.claim_review.v2"
OBJECT_NAME = "response_context"
ROOT = Path(__file__).resolve().parents[2]
PROMPT = ROOT / "docs/prompts/task08d_claim_review_v1.md"
SCHEMAS = ROOT / "benchmarks/er_bench/schemas/task08d/v2"
RELATIONSHIPS = ("direct", "supporting", "not-relevant", "unclear")


def digest(content: bytes) -> str:
    """Hash exact bytes without normalizing source or saved text."""
    return hashlib.sha256(content).hexdigest()


def encoded(value: Any) -> bytes:
    """Serialize replay artifacts deterministically, preserving string values."""
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _text(value: Any) -> str:
    """Require substantive text without modifying its exact representation."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Nonblank text required")
    return value


def _ids(rows: list[dict[str, Any]], key: str) -> set[str]:
    """Reject duplicate or empty identifiers before building a lookup."""
    values = [_text(row[key]) for row in rows]
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {key}")
    return set(values)


def _pre(value: Any) -> str:
    """Escape source prose and metadata for passive native display."""
    text = (
        value
        if isinstance(value, str)
        else json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    )
    return (
        '<pre style="white-space:pre-wrap;overflow-wrap:anywhere">' + html.escape(text) + "</pre>"
    )


def _choices(name: str, values: tuple[str, ...]) -> str:
    """Use unique native radio names with stable semantic export aliases."""
    choices = "".join(
        f'<Choice value="{name}_{value}" '
        f'html="{value.replace("-", " ").capitalize()}" alias="{value}"/>'
        for value in values
    )
    return (
        f'<Choices name="{name}" toName="{OBJECT_NAME}" choice="single-radio">{choices}</Choices>'
    )


def _area(name: str, rows: int = 2) -> str:
    """Create a single editable native field with no independent submit button."""
    return (
        f'<TextArea name="{name}" toName="{OBJECT_NAME}" rows="{rows}" '
        'editable="true" transcription="true" showSubmitButton="false" maxSubmissions="1"/>'
    )


def build_form(slot_count: int) -> str:
    """Render fixed claim cards and blank explicit human decision controls."""
    if type(slot_count) is not int or slot_count < 1:
        raise ValueError("Positive slot count required")
    cards = []
    for ordinal in range(1, slot_count + 1):
        slot = f"s{ordinal:03d}"
        cards.append(
            '<View style="border:1px solid #bbb;padding:12px;margin-bottom:16px">'
            f'<Header value="${slot}_title"/>'
            f'<HyperText name="{slot}_source" value="${slot}_html" selectionEnabled="false"/>'
            '<Header value="Exact claim wording" size="5"/>'
            + _area(f"{slot}_text", 12)
            + '<Header value="Relationship" size="5"/>'
            + _choices(f"{slot}_relationship", RELATIONSHIPS)
            + '<Header value="Targets: question-part IDs for direct; '
            'one direct claim ID for supporting; otherwise blank" size="5"/>'
            + _area(f"{slot}_targets")
            + '<Header value="Material contribution or relationship explanation" size="5"/>'
            + _area(f"{slot}_rationale", 10)
            + '<Header value="Decision: approve the exact current wording, '
            'sources, relationship and explanation" size="5"/>'
            + _choices(f"{slot}_decision", ("approve", "reject", "unresolved"))
            + "</View>"
        )
    return (
        '<View className="claim-review-v2"><Style>'
        '.claim-review-v2 textarea[name*="_text"] {'
        "min-height:260px !important;height:260px !important;resize:vertical !important;}"
        '.claim-review-v2 textarea[name*="_rationale"] {'
        "min-height:220px !important;height:220px !important;resize:vertical !important;}"
        '</Style><Header value="Response claims and relationships"/>'
        '<Header size="5" value="Approval records what the response asserts and its relevance. '
        'It does not establish truth or evidence support."/>'
        '<HyperText name="frozen_question" value="$question_html" selectionEnabled="false"/>'
        '<HyperText name="question_parts" value="$parts_html" selectionEnabled="false"/>'
        '<View style="display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px">'
        '<View style="max-height:85vh;overflow:auto">'
        f'<HyperText name="{OBJECT_NAME}" value="$source_html" selectionEnabled="false"/>'
        '</View><View style="max-height:85vh;overflow:auto;min-width:0">'
        + "".join(cards)
        + "</View></View>"
        '<Header value="Whole-case decision"/>'
        + _choices("case_status", ("ready", "unresolved", "stop"))
        + '<Header size="5" value="Case note: explain stops, unresolved issues, '
        'or rejected material"/>'
        + _area("case_note", 3)
        + '<Header size="5" value="After all edits, explicitly confirm '
        'current claim links and target wording"/>'
        + _choices("links_confirmed", ("confirmed",))
        + '<Header size="5" value="Unanswered or unclear question parts: resolve explicitly '
        'without narrowing the frozen question, or keep unresolved"/>'
        + _choices("gaps_status", ("resolved", "unresolved", "not-applicable"))
        + _area("gaps_resolution", 3)
        + "</View>\n"
    )


def _validate_proposal(packet: dict[str, Any], proposal: dict[str, Any], packet_sha: str) -> None:
    """Require complete current-case proposals with resolvable source and relation maps."""
    Draft202012Validator(json.loads((SCHEMAS / "proposal.schema.json").read_bytes())).validate(
        proposal
    )
    if (
        proposal.get("schema_version") != "task08d.proposal.v1"
        or proposal.get("model") != "gpt-6-astra"
    ):
        raise ValueError("Expected versioned Astra proposal")
    if proposal.get("packet_sha256") != packet_sha:
        raise ValueError("Proposal packet binding differs")
    if not re.fullmatch(r"[a-f0-9]{64}", proposal.get("inventory_sha256", "")):
        raise ValueError("Separate assertion inventory binding required")
    if _ids(packet["cases"], "case_id") != _ids(proposal["cases"], "case_id"):
        raise ValueError("Proposal must cover exactly the packet cases")
    sources = {case["case_id"]: case for case in packet["cases"]}
    for case in proposal["cases"]:
        source = sources[case["case_id"]]
        passages = _ids(source["passages"], "passage_id")
        claims = case["claims"]
        claim_ids = _ids(claims, "claim_id")
        parts = _ids(case["question_parts"], "part_id")
        indexed = {claim["claim_id"]: claim for claim in claims}
        if not parts:
            raise ValueError("Frozen question parts must remain visible")
        for part in case["question_parts"]:
            _text(part["text"])
            _text(part["explanation"])
            if (
                part["status"] not in {"addressed", "unanswered", "unclear"}
                or type(part["essential"]) is not bool
            ):
                raise ValueError("Invalid question-part disposition")
            if not set(part["claim_ids"]) <= claim_ids:
                raise ValueError("Unknown question-part claim")
        for claim in claims:
            if not re.fullmatch(r"[A-Z][0-9]{3,}", claim["claim_id"]):
                raise ValueError("Stable claim IDs require a letter and at least three digits")
            _text(claim["text"])
            _text(claim["rationale"])
            for key in ("passage_ids", "targets", "assertion_ids"):
                values = claim[key]
                if (
                    not isinstance(values, list)
                    or any(not isinstance(v, str) or not v for v in values)
                    or len(values) != len(set(values))
                ):
                    raise ValueError("References must be distinct strings")
            if (
                not claim["passage_ids"]
                or not set(claim["passage_ids"]) <= passages
                or not claim["assertion_ids"]
            ):
                raise ValueError(
                    "Claim requires known response passages and inventoried assertions"
                )
            relation, targets = claim["relationship"], claim["targets"]
            if relation not in RELATIONSHIPS:
                raise ValueError("Unknown relationship")
            if relation == "direct" and (not targets or not set(targets) <= parts):
                raise ValueError("Direct claims require known question parts")
            if relation == "supporting" and (
                len(targets) != 1
                or targets[0] not in indexed
                or indexed[targets[0]]["relationship"] != "direct"
            ):
                raise ValueError("Supporting claims require one specific direct target")
            if relation in {"not-relevant", "unclear"} and targets:
                raise ValueError("Nonadvancing relationships require blank targets")


def _parts_html(parts: list[dict[str, Any]]) -> str:
    """Make every addressed and unanswered question part visible in plain language."""
    return "<h3>Question parts and response gaps</h3>" + "".join(
        "<h4>"
        + html.escape(part["part_id"] + " — " + part["status"])
        + (" — essential" if part["essential"] else "")
        + "</h4>"
        + _pre(part["text"])
        + _pre(part["explanation"])
        for part in parts
    )


def _citation_text(value: Any) -> str:
    """Show citation prose and disposition fields without exposing internal IDs."""
    if isinstance(value, str):
        return _pre(value)
    if isinstance(value, list):
        return "".join(_citation_text(item) for item in value)
    if isinstance(value, dict):
        return "".join(
            _citation_text(content)
            for key, content in sorted(value.items())
            if key
            in {
                "text",
                "raw_text",
                "citation_text",
                "mention_text",
                "quote",
                "outcome",
                "terminal_reason",
                "warning",
                "warnings",
                "title",
                "target_annotations",
                "supplied_citations",
                "source_text",
            }
        )
    return ""


def _warnings_html(value: Any) -> str:
    """Render every nested warning value rather than only dictionary field names."""
    if isinstance(value, dict):
        return "".join(
            "<h5>"
            + html.escape(key.replace("_", " ").capitalize())
            + "</h5>"
            + _warnings_html(content)
            for key, content in sorted(value.items())
        )
    if isinstance(value, list):
        return "".join(_warnings_html(item) for item in value) if value else "<p>None recorded.</p>"
    return _pre(value)


def _source_html(source: dict[str, Any]) -> str:
    """Render a readable complete source reader with metadata retained separately."""
    reader = "<h3>Original comment</h3>" + _pre(source["original_comment"]["text"])
    reader += "<h3>Complete linked official responses</h3>"
    for unit in source["responses"]:
        label = str(unit.get("official_label", unit["unit_id"]))
        pages = ", ".join(str(page) for page in unit.get("source_pages", []))
        reader += "<h4>" + html.escape(label) + "</h4>"
        if pages:
            reader += "<p>PDF pages: " + html.escape(pages) + "</p>"
        reader += _pre(unit["text"])
        reader += _citation_text(unit.get("supplied_citations", []))
    reader += "<h3>Exact passages for claim references</h3>"
    for passage in source["passages"]:
        reader += "<h5>" + html.escape(passage["passage_id"]) + "</h5>" + _pre(passage["text"])
    reader += "<h3>Supplied citations and source supplements</h3>"
    reader += _citation_text(source.get("supplements", []))
    reader += _citation_text(source.get("outcomes", []))
    reader += "<h3>Source warnings and uncertainty</h3>"
    reader += _warnings_html(source.get("warnings", []))
    reader += "<details><summary>Full citation and source provenance</summary>"
    reader += _pre({key: source.get(key, []) for key in ("supplements", "outcomes", "closure")})
    return reader + "</details>"


def _claim_html(claim: dict[str, Any], passages: list[dict[str, Any]]) -> str:
    """Attach readable exact source quotations underneath the initial proposal."""
    selected = [p for p in passages if p["passage_id"] in claim["passage_ids"]]
    return (
        "<details><summary>Initial proposal and exact source quotations</summary>"
        + _pre(claim["text"])
        + _pre(claim["rationale"])
        + "".join(
            "<h5>" + html.escape(p["passage_id"]) + "</h5>" + _pre(p["text"]) for p in selected
        )
        + "</details>"
    )


def _result(name: str, value: str, *, choice: bool = False) -> dict[str, Any]:
    """Build native content predictions, never human approval predictions."""
    return {
        "from_name": name,
        "to_name": OBJECT_NAME,
        "type": "choices" if choice else "textarea",
        "value": {"choices" if choice else "text": [value]},
    }


def build_tasks(
    packet: dict[str, Any],
    proposal: dict[str, Any],
    *,
    packet_sha256: str,
    proposal_sha256: str,
    slots: int | None = None,
) -> list[dict[str, Any]]:
    """Prepare one trusted review task per case, showing direct assertions first."""
    from er_commons.group_claims_input import validate_packet

    Draft202012Validator(json.loads((SCHEMAS / "input.schema.json").read_bytes())).validate(packet)
    validate_packet(packet)
    if digest(encoded(packet)) != packet_sha256 or digest(encoded(proposal)) != proposal_sha256:
        raise ValueError("Packet or proposal content hash differs")
    _validate_proposal(packet, proposal, packet_sha256)
    if not all(re.fullmatch(r"[a-f0-9]{64}", value) for value in (packet_sha256, proposal_sha256)):
        raise ValueError("Exact packet and proposal hashes required")
    capacity = max((len(case["claims"]) for case in proposal["cases"]), default=0) + 4
    if slots is not None:
        if type(slots) is not int or slots < capacity:
            raise ValueError("Capacity must retain four addition slots")
        capacity = slots
    proposals = {case["case_id"]: case for case in proposal["cases"]}
    tasks = []
    for source in packet["cases"]:
        proposed = proposals[source["case_id"]]
        claims = sorted(proposed["claims"], key=lambda c: RELATIONSHIPS.index(c["relationship"]))
        data: dict[str, Any] = {
            "form_version": VERSION,
            "case_id": source["case_id"],
            "question": copy.deepcopy(source["question"]),
            "packet_sha256": packet_sha256,
            "proposal_sha256": proposal_sha256,
            "case_input": copy.deepcopy(source),
            "proposal": copy.deepcopy(proposed),
            "slot_count": capacity,
            "slot_bindings": [],
            "question_html": "<h3>"
            + html.escape(source["question"].get("comment_label", source["case_id"]))
            + " — frozen question, unchanged</h3>"
            + _pre(source["question"]["text"]),
            "parts_html": _parts_html(proposed["question_parts"]),
            "source_html": _source_html(source),
        }
        next_id = max((int(c["claim_id"][1:]) for c in claims), default=0) + 1
        results = []
        for index in range(capacity):
            slot = f"s{index + 1:03d}"
            claim = claims[index] if index < len(claims) else None
            claim_id = claim["claim_id"] if claim else f"A{next_id + index - len(claims):03d}"
            data["slot_bindings"].append(
                {
                    "slot": slot,
                    "claim_id": claim_id,
                    "proposal_claim_id": claim_id if claim else None,
                }
            )
            data[f"{slot}_title"] = claim_id if claim else f"{claim_id} — optional added claim"
            data[f"{slot}_html"] = (
                _claim_html(claim, source["passages"])
                if claim
                else "<p>Leave every field blank unless adding a claim. "
                "Added claims require source binding in a new revision; "
                "save them as unresolved.</p>"
            )
            if claim:
                for suffix, value in (
                    ("text", claim["text"]),
                    ("relationship", claim["relationship"]),
                    ("targets", ",".join(claim["targets"])),
                    ("rationale", claim["rationale"]),
                ):
                    if value:
                        results.append(
                            _result(f"{slot}_{suffix}", value, choice=suffix == "relationship")
                        )
        tasks.append({"data": data, "predictions": [{"model_version": VERSION, "result": results}]})
    Draft202012Validator(json.loads((SCHEMAS / "tasks.schema.json").read_bytes())).validate(tasks)
    return tasks


def _snapshots() -> dict[str, bytes]:
    """Snapshot all versioned interfaces needed for exact preparation replay."""
    result = {"prompt.md": PROMPT.read_bytes(), "preparation.py": Path(__file__).read_bytes()}
    for name in (
        "group_claims_input.py",
        "group_claims_export.py",
        "group_claims_inventory.py",
        "group_claims_workflow.py",
    ):
        result[name] = Path(__file__).with_name(name).read_bytes()
    for path in sorted(SCHEMAS.glob("*.json")):
        result[path.name] = path.read_bytes()
    if not list(SCHEMAS.glob("*.json")):
        raise ValueError("Versioned schemas required")
    return result


def prepare(packet_path: Path, proposal_path: Path, output: Path) -> dict[str, Any]:
    """Write immutable tasks and interface snapshots into a fresh directory."""
    packet_raw, proposal_raw = packet_path.read_bytes(), proposal_path.read_bytes()
    inventory_raw = proposal_path.with_name("inventory.json").read_bytes()
    validate_inventory(json.loads(packet_raw), json.loads(inventory_raw), json.loads(proposal_raw))
    tasks = build_tasks(
        json.loads(packet_raw),
        json.loads(proposal_raw),
        packet_sha256=digest(packet_raw),
        proposal_sha256=digest(proposal_raw),
    )
    payloads = {
        **_snapshots(),
        "packet.json": packet_raw,
        "inventory.json": inventory_raw,
        "proposal.json": proposal_raw,
        "tasks.json": encoded(tasks),
        "form.xml": build_form(tasks[0]["data"]["slot_count"]).encode(),
    }
    manifest = {
        "schema_version": VERSION,
        "files": {name: digest(value) for name, value in payloads.items()},
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, value in {**payloads, "manifest.json": encoded(manifest)}.items():
        with (output / name).open("xb") as stream:
            stream.write(value)
    return manifest


def load_prepared(output: Path) -> list[dict[str, Any]]:
    """Rebuild trusted tasks and reject source, form or shared-interface drift."""
    manifest = json.loads((output / "manifest.json").read_bytes())
    snapshots = _snapshots()
    expected = set(snapshots) | {
        "packet.json",
        "inventory.json",
        "proposal.json",
        "tasks.json",
        "form.xml",
    }
    if (
        set(manifest) != {"schema_version", "files"}
        or manifest["schema_version"] != VERSION
        or set(manifest["files"]) != expected
    ):
        raise ValueError("Prepared manifest closure differs")
    contents = {name: (output / name).read_bytes() for name in expected}
    for name, value in contents.items():
        if digest(value) != manifest["files"][name] or (
            name in snapshots and value != snapshots[name]
        ):
            raise ValueError("Prepared source or interface differs")
    validate_inventory(
        json.loads(contents["packet.json"]),
        json.loads(contents["inventory.json"]),
        json.loads(contents["proposal.json"]),
    )
    tasks = build_tasks(
        json.loads(contents["packet.json"]),
        json.loads(contents["proposal.json"]),
        packet_sha256=digest(contents["packet.json"]),
        proposal_sha256=digest(contents["proposal.json"]),
    )
    if (
        encoded(tasks) != contents["tasks.json"]
        or build_form(tasks[0]["data"]["slot_count"]).encode() != contents["form.xml"]
    ):
        raise ValueError("Prepared form or tasks differ from source rebuild")
    return tasks
