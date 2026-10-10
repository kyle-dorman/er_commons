"""Bounded Task 09B projections; not the later general-purpose judge packet system."""

from __future__ import annotations

import argparse
import copy
import json
import logging
import re
from pathlib import Path
from typing import Any

from er_commons.artifact_io import (
    file_reference,
    json_bytes,
    publish_bytes_no_clobber,
    stable_json_sha256,
)
from er_commons.synthetic_intake import verify_binding

CASES = {"C041": "short", "C037": "typical", "C014": "large"}
DIMENSIONS = ("grounding", "adequacy")
_VARIANT = re.compile(r'"variant_id"\s*:\s*"([^"\\]+)"')


def _binding(path: Path) -> dict[str, Any]:
    """Retain an absolute checksum binding for external qualification provenance."""
    return {**file_reference(path, root=path.parent), "path": str(path.resolve())}


def _read(path: Path) -> dict[str, Any]:
    """Decode a verified object."""
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("Expected an object")
    return value


def selected_rows(path: Path, allowed: set[str]) -> dict[str, dict[str, Any]]:
    """Route by literal metadata before decoding any selected answer/expectation payload.

    The sealed publisher emits unescaped variant IDs. Ambiguous routing fails closed;
    non-selected lines are never JSON-decoded, including all reserved answer rows.
    """
    rows = {}
    with path.open() as stream:
        for line in stream:
            if not line.strip():
                continue
            ids = _VARIANT.findall(line)
            if len(ids) != 1:
                raise ValueError("Expected exactly one routing variant_id")
            if ids[0] not in allowed:
                continue
            row = json.loads(line)
            if row["variant_id"] != ids[0] or ids[0] in rows:
                raise ValueError("Ambiguous or duplicate selected identity")
            rows[ids[0]] = row
    if set(rows) != allowed:
        raise ValueError("Selected records missing")
    return rows


def _answer(answer: dict[str, Any], citations: dict[str, str]) -> dict[str, Any]:
    """Allowlist substantive answer fields and consistently anonymize all point links."""
    points = [
        answer["conclusion"],
        *answer["supporting_points"],
        *answer["qualifications"],
        *answer["optional_context"],
    ]
    point_ids = {point["point_id"]: f"P{i + 1}" for i, point in enumerate(points)}
    if len(point_ids) != len(points):
        raise ValueError("Duplicate answer point IDs")

    def point(row: dict[str, Any]) -> dict[str, Any]:
        """Keep exact text, citation membership and qualification attachment semantics."""
        result = {
            "point_id": point_ids[row["point_id"]],
            "text": row["text"],
            "citation_ids": [citations[c] for c in row["citation_ids"]],
        }
        if "applies_to" in row:
            result["applies_to"] = [point_ids[p] for p in row["applies_to"]]
        return result

    result = {
        "status": answer["status"],
        "conclusion": point(answer["conclusion"]),
        **{
            key: [point(p) for p in answer[key]]
            for key in ("supporting_points", "qualifications", "optional_context")
        },
    }
    if "citation_locators" in answer:
        result["citation_locators"] = [
            {"occurrence_id": citations[p["occurrence_id"]], "excerpt": p["excerpt"]}
            for p in answer["citation_locators"]
        ]
    return result


def _canonical_target(target: dict[str, Any]) -> dict[str, Any]:
    """Keep readable source locators, excluding review receipts and extraction internals."""
    result = {
        key: copy.deepcopy(target[key])
        for key in ("unit_id", "kind", "unit_type", "citation_label", "edition", "pages")
        if key in target
    }
    if "breadcrumb" in target:
        result["breadcrumb"] = [
            {"heading_text": row["heading_text"]}
            for row in target["breadcrumb"]
            if "heading_text" in row
        ]
    if "figure_refs" in target:
        result["figure_refs"] = [
            {key: copy.deepcopy(row[key]) for key in ("record_id", "interpretation") if key in row}
            for row in target["figure_refs"]
        ]
    return result


def project_payload(
    packet: dict[str, Any], answer: dict[str, Any], dimension: str
) -> dict[str, Any]:
    """Keep grounding reference-blind; adequacy receives separate reference/evidence."""
    if dimension not in DIMENSIONS:
        raise ValueError("Unknown judge dimension")
    selected_answers = [answer]
    if dimension == "adequacy":
        selected_answers.append(packet["reference_answer"])
    cited = set()
    for value in selected_answers:
        for p in [
            value["conclusion"],
            *value["supporting_points"],
            *value["qualifications"],
            *value["optional_context"],
        ]:
            cited.update(p["citation_ids"])
        cited.update(p["occurrence_id"] for p in value.get("citation_locators", []))
    sources: list[dict[str, Any]] = []
    citations: dict[str, str] = {}
    seen: dict[str, str] = {}
    for source in packet["sources"]:
        if dimension == "grounding" and source["occurrence_id"] not in cited:
            continue
        # These are canonical source fields only, never approval/gold-role metadata.
        row = {
            key: copy.deepcopy(source[key])
            for key in (
                "source_id",
                "title",
                "edition",
                "canonical_target",
                "full_source_text",
                "tables",
                "physical_pages",
                "printed_labels",
            )
            if key in source
        }
        if "canonical_target" in row:
            row["canonical_target"] = _canonical_target(row["canonical_target"])
        identity = stable_json_sha256(row)
        if identity not in seen:
            seen[identity] = f"S{len(sources) + 1}"
            sources.append({"citation_id": seen[identity], **row})
        citations[source["occurrence_id"]] = seen[identity]
    # Preserve unresolved citations as unresolved; do not repair synthetic defects.
    for citation in sorted(cited - citations.keys()):
        citations[citation] = f"U{len(citations) + 1}"
    result = {
        "question": packet["question"],
        "answer": _answer(answer, citations),
        "evidence": sources,
    }
    if dimension == "adequacy":
        result["reference_answer"] = _answer(packet["reference_answer"], citations)
    return result


def prepare_packets(result_path: Path, output: Path) -> dict[str, Any]:
    """Publish six control shapes plus two development contrasts, with separate provenance."""
    result = _read(result_path)
    if result.get("status") != "complete_with_limitations":
        raise ValueError("09A is not sealed")
    root = Path(result["namespace"]).resolve()
    completion_path = verify_binding(result["batch_completion"], root)
    batch = completion_path.parent
    inventory = {b["path"]: b for b in _read(completion_path)["inventory"]["files"]}

    def artifact(name: str) -> Path:
        """Verify every consumed published artifact against the sealed pointer."""
        return verify_binding(result["artifacts"][name], root)

    reservation = _read(artifact("reservation.json"))
    groups = [
        reservation[k]
        for k in ("development_variant_ids", "final_check_variant_ids", "excluded_variant_ids")
    ]
    if [len(g) for g in groups] != [423, 118, 5] or len(set(sum(groups, []))) != 546:
        raise ValueError("Frozen reservation populations differ")
    allowed = set(groups[0])
    expectations = selected_rows(artifact("expectations.jsonl"), allowed)
    if any(row.get("comparison_eligible") is not True for row in expectations.values()):
        raise ValueError("Development reservation includes comparison exclusion")
    prepared = _read(verify_binding(inventory["prepared.json"], batch))
    if len(prepared["case_ids"]) != 19 or not set(CASES) <= set(prepared["case_ids"]):
        raise ValueError("Qualification cases not in sealed development intake")
    contrasts = {}
    for dimension in DIMENSIONS:
        candidates = [
            r
            for r in expectations.values()
            if r["case_id"] == "C041" and isinstance(r[dimension]["score"], int)
        ]
        if not candidates:
            raise ValueError("No eligible short-case contrast")
        contrasts[dimension] = min(
            candidates, key=lambda r: (r[dimension]["score"], r["variant_id"])
        )
    variants = selected_rows(
        artifact("answers.jsonl"), {r["variant_id"] for r in contrasts.values()}
    )
    packets: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    for case_id, size in CASES.items():
        packet_path = verify_binding(inventory[f"cases/{case_id}/input.json"], batch)
        packet = _read(packet_path)
        if packet["case_id"] != case_id:
            raise ValueError("Development packet identity differs")
        for dimension in DIMENSIONS:
            selections: list[tuple[dict[str, Any], str, dict[str, Any] | None]] = [
                (packet["reference_answer"], size, None)
            ]
            if case_id == "C041":
                expectation = contrasts[dimension]
                row = variants[expectation["variant_id"]]
                if row["case_id"] != case_id:
                    raise ValueError("Variant case differs")
                selections.append((row["answer"], "contrast", expectation))
            for answer, label, proposal in selections:
                payload = project_payload(packet, answer, dimension)
                identifier = f"q{len(packets) + 1:02d}"
                packets.append(
                    {
                        "id": identifier,
                        "case_id": case_id,
                        "dimension": dimension,
                        "size": label,
                        "payload": payload,
                    }
                )
                provenance.append(
                    {
                        "id": identifier,
                        "payload_sha256": stable_json_sha256(payload),
                        "input": _binding(packet_path),
                        "variant_id": proposal["variant_id"] if proposal else f"{case_id}-CONTROL",
                        "synthetic_expectation": proposal,
                        "interpretation": "Qualification only, not accuracy evidence",
                    }
                )
    # Both writes are deterministic, no-clobber, and safely repeatable.
    output.mkdir(parents=True, exist_ok=True)
    publish_bytes_no_clobber(output / "packets.json", json_bytes(packets))
    publish_bytes_no_clobber(output / "provenance.json", json_bytes(provenance))
    manifest = {
        "schema_version": "task09b.qualification_packets.v1",
        "packet_count": len(packets),
        "packets_path": str((output / "packets.json").resolve()),
        "packets": _binding(output / "packets.json"),
        "provenance": _binding(output / "provenance.json"),
        "source_result": _binding(result_path),
        "reservation": result["artifacts"]["reservation.json"],
        "base_calls": 6,
        "contrast_calls": 2,
        "reserved_answer_payloads_parsed": False,
        "test_content_parsed": False,
    }
    publish_bytes_no_clobber(output / "completion.json", json_bytes(manifest))
    return manifest


def main() -> None:
    """Prepare the bounded qualification projection from an explicit sealed result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare"])
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    result = prepare_packets(args.result, args.output)
    logging.info("Prepared qualification packets: %s", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
