"""Completion-last publication of fully researched, still-unreviewed 08E batches."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
from typing import Any

from er_commons.group_claims_batch import read_reference, reference, write_new
from er_commons.group_evidence_batch import load_inputs
from er_commons.group_evidence_chat import export_review, new_journal, render_display
from er_commons.group_evidence_research import validate_packet
from er_commons.pilot_citation_records import bound_bytes, index_records
from er_commons.pilot_evidence import _source_excerpt_html, digest
from er_commons.pilot_evidence_search import verify_index


def _validate_query_intents(directory: Path, packet: dict[str, Any]) -> None:
    """Require every saved intent to end in its exact receipt or a disclosed abort."""
    expected_aborts: dict[str, list[dict[str, Any]]] = {
        track: [] for track in packet["track_results"]
    }
    planned_stems = set()
    for path in sorted((directory / "queries").glob("*/*.plan.json")):
        intent = json.loads(path.read_bytes())
        track = path.parent.name
        query = intent["query"]
        stem = path.name.removesuffix(".plan.json")
        planned_stems.add((track, stem))
        if track not in expected_aborts or intent["track"] != track or query["query_id"] != stem:
            raise ValueError("Saved query intent identity or track differs")
        read_reference(intent["plan"])
        receipt_path = path.with_name(stem + ".receipt.json")
        aborted_path = path.with_name(stem + ".aborted.json")
        if receipt_path.exists() == aborted_path.exists():
            raise ValueError("Saved query intent needs exactly one receipt or aborted diagnostic")
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_bytes())
            for key in ("query_id", "expression", "claim_ids", "purpose", "source_filter", "limit"):
                default = 10 if key == "limit" else None
                if receipt.get(key, default) != query.get(key, default):
                    raise ValueError("Query receipt differs from saved intent: " + key)
        else:
            aborted = json.loads(aborted_path.read_bytes())
            if (
                aborted.get("intent") != reference(path)
                or aborted.get("query_id") != stem
                or aborted.get("status") != "aborted_before_receipt"
                or not aborted.get("error")
            ):
                raise ValueError("Aborted query diagnostic must bind exact intent and error")
            expected_aborts[track].append(reference(aborted_path))
    for path in (directory / "queries").glob("*/*.receipt.json"):
        if (path.parent.name, path.name.removesuffix(".receipt.json")) not in planned_stems:
            raise ValueError("Query receipt has no saved intent")
    for path in (directory / "queries").glob("*/*.aborted.json"):
        if (path.parent.name, path.name.removesuffix(".aborted.json")) not in planned_stems:
            raise ValueError("Aborted query has no saved intent")
    for track, refs in expected_aborts.items():
        saved = packet["track_results"][track].get("aborted_query_diagnostics", [])
        if saved != refs:
            raise ValueError("Packet loses or changes aborted query diagnostics")
        if refs:
            explanation = " ".join(packet["remaining_gaps"] + packet["limitations"])
            for ref in refs:
                if read_reference(ref)["query_id"] not in explanation:
                    raise ValueError("Aborted query must remain explained in packet gaps or limits")


def verify_prepared_result(result_path: Path) -> dict[str, Any]:
    """Verify the immutable preparation inventory before any separate review resume."""
    result = json.loads(result_path.read_bytes())
    if result.get("schema_version") != "task08e.prepared_result.v1":
        raise ValueError("Unknown prepared result")
    handoff: dict[str, Any] = read_reference(result["handoff"])
    completion = read_reference(result["completion"])
    if (
        completion["handoff"] != result["handoff"]
        or handoff["status"] != "prepared, awaiting human review"
        or not handoff["phase_a_complete"]
        or handoff["phase_b_started"]
        or handoff["08f_started"]
        or handoff["human_decisions"] != 0
        or handoff["eligibility"] is not None
        or result["cases"] != len(handoff["cases"])
    ):
        raise ValueError("Preparation completion and result disagree")
    for key in (
        "status",
        "approved_claims",
        "source_occurrences",
        "beyond_claim_findings",
        "query_receipts",
        "held_case_ids",
        "deferred_case_ids",
        "human_decisions",
    ):
        if result.get(key) != handoff.get(key):
            raise ValueError("Prepared result summary differs from handoff: " + key)
    totals = {
        "approved_claims": sum(row["validation"]["claims"] for row in handoff["cases"]),
        "source_occurrences": sum(row["validation"]["sources"] for row in handoff["cases"]),
        "beyond_claim_findings": sum(row["beyond_claim_findings"] for row in handoff["cases"]),
        "query_receipts": sum(row["query_receipts"] for row in handoff["cases"]),
    }
    if any(handoff[key] != count for key, count in totals.items()):
        raise ValueError("Prepared handoff totals differ from case rows")
    for key in ("review_instructions", "qualification"):
        ref = handoff[key]
        if reference(Path(ref["path"])) != ref:
            raise ValueError("Preparation guidance or qualification bytes changed")
    for ref in handoff["raw_source_manifests"]:
        read_reference(ref)
    root = Path(result["completion"]["path"]).parent.resolve()
    files = completion["files"]
    paths = [Path(ref["path"]).resolve() for ref in files]
    if len(paths) != len(set(paths)) or any(not path.is_relative_to(root) for path in paths):
        raise ValueError("Preparation inventory has duplicate or escaping paths")
    actual = {path.resolve() for path in root.rglob("*") if path.is_file()}
    if actual != {*paths, Path(result["completion"]["path"]).resolve()}:
        raise ValueError("Preparation file closure changed")
    for ref in files:
        if reference(Path(ref["path"])) != ref:
            raise ValueError("Prepared file bytes changed: " + ref["path"])
    for case in handoff["cases"]:
        if (
            case["human_decisions"]
            or case["eligibility"] is not None
            or case["disposition"] is not None
        ):
            raise ValueError("Prepared case contains human decisions")
    return handoff


def validate_saved_case(
    directory: Path,
    case: dict[str, Any],
    data_root: Path,
    sources: list[dict[str, Any]],
    *,
    index_identity: str | None = None,
    source_manifest_refs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Verify packet fidelity, raw query closure, allowed corpus and independent review."""
    packet = json.loads((directory / "packet.json").read_bytes())
    if source_manifest_refs is None and packet["sources"]:
        intake_path = directory.parent.parent / "intake_audit.json"
        if not intake_path.exists():
            raise ValueError("Approved intake source manifest references required")
        source_manifest_refs = json.loads(intake_path.read_bytes())["raw_source_manifests"]
    for ref in source_manifest_refs or []:
        read_reference(ref)
    plan_path = directory / packet.get("plan_filename", "plan.json")
    if not plan_path.resolve().is_relative_to(directory.resolve()):
        raise ValueError("Plan escapes case directory")
    plan = json.loads(plan_path.read_bytes())
    validation = validate_packet(packet, case, plan, data_root)
    allowed = {source["source_id"]: source for source in sources}
    tables: dict[str, dict[str, Any]] = {}
    origins: dict[str, dict[str, Any]] = {}
    checked_pdfs: set[str] = set()
    for candidate in packet["sources"]:
        source = allowed.get(candidate["source_id"])
        if source is None or source["extraction_id"] != candidate["extraction_id"]:
            raise ValueError("Citation outside accepted source/extraction corpus")
        paths = {ref["path"] for ref in source["files"].values()}
        if any(anchor["path"] not in paths for anchor in candidate["anchors"]):
            raise ValueError("Canonical anchor outside accepted source bindings")
        manifest_ref = candidate["source_manifest"]
        if source_manifest_refs is not None and not any(
            (data_root / manifest_ref["path"]).resolve() == Path(ref["path"]).resolve()
            and manifest_ref["sha256"] == ref["sha256"]
            for ref in source_manifest_refs
        ):
            raise ValueError("Original PDF manifest is outside approved intake origins")
        manifest_key = json.dumps(manifest_ref, sort_keys=True)
        if manifest_key not in origins:
            origins[manifest_key] = {
                row["source_id"]: row
                for row in json.loads(bound_bytes(manifest_ref, data_root))["sources"]
            }
        origin = origins[manifest_key][candidate["source_id"]]
        if (
            candidate["source_sha256"] != origin["sha256"]
            or candidate["source_pdf_path"] != origin["local_path"]
            or candidate["source_url"] != origin["final_resolved_url"]
            or candidate["pdf_url"].split("#")[0] != origin["final_resolved_url"]
        ):
            raise ValueError("Original PDF citation differs from bound source manifest")
        if origin["local_path"] not in checked_pdfs:
            pdf = (data_root / origin["local_path"]).resolve()
            if not pdf.is_relative_to(data_root.resolve()):
                raise ValueError("Original PDF escapes data root")
            with pdf.open("rb") as stream:
                checksum = hashlib.file_digest(stream, "sha256").hexdigest()
            if checksum != origin["sha256"] or pdf.stat().st_size != origin["byte_size"]:
                raise ValueError("Original PDF bytes changed")
            checked_pdfs.add(origin["local_path"])
        if candidate["citation_unit"]["kind"] == "table":
            sid = candidate["source_id"]
            if sid not in tables:
                tables[sid] = index_records(bound_bytes(source["files"]["tables"], data_root))
            ids = {anchor["record_id"] for anchor in candidate["anchors"]}
            selected = [tables[sid][identity] for identity in ids if identity in tables[sid]]
            families = {row.get("table_family_id") for row in selected} - {None}
            siblings = {
                row["id"] for row in tables[sid].values() if row.get("table_family_id") in families
            }
            if not siblings <= ids:
                raise ValueError("Table occurrence omits canonical continuation family members")
    actual_queries = {}
    for path in (directory / "queries").glob("*/*.receipt.json"):
        receipt = json.loads(path.read_bytes())
        if index_identity is not None and receipt.get("index_identity") != index_identity:
            raise ValueError("Query used a different canonical search index")
        binding = path.with_name(path.name.replace(".receipt.json", ".binding.json"))
        if read_reference(json.loads(binding.read_bytes())) != receipt:
            raise ValueError("Raw query receipt changed")
        if receipt["query_id"] in actual_queries:
            raise ValueError("Duplicate saved query identity")
        actual_queries[receipt["query_id"]] = receipt
    packet_queries = {}
    for result in packet["track_results"].values():
        for receipt in result["query_receipts"]:
            raw = {key: value for key, value in receipt.items() if key != "inspected_hits"}
            packet_queries[receipt["query_id"]] = raw
    if actual_queries != packet_queries:
        raise ValueError("Packet loses or changes actual saved query receipts")
    _validate_query_intents(directory, packet)
    review = json.loads((directory / "independent_review.json").read_bytes())
    if (
        review.get("packet_sha256") != digest(packet)
        or review.get("status") != "pass"
        or not review.get("worker")
        or not review.get("coverage")
        or not review.get("export_fidelity")
        or not review.get("scope_exclusions")
        or not review.get("counterevidence")
        or review.get("blocking_findings") != []
    ):
        raise ValueError("Exact packet needs independent coverage/export/scope review")
    return validation


def publish(
    root: Path,
    result_path: Path,
    data_root: Path,
    sources_path: Path,
    *,
    qualification_path: Path,
    supplement_authorization_path: Path | None = None,
) -> dict[str, Any]:
    """Publish a verified base or explicitly authorized supplement after all gates pass."""
    if supplement_authorization_path is None:
        inputs = load_inputs(result_path)
    else:
        from er_commons.group_evidence_extension import load_supplement_inputs

        inputs = load_supplement_inputs(result_path, supplement_authorization_path)
    intake = json.loads((root / "intake_audit.json").read_bytes())
    audit = intake["search_cache"]
    source_manifests = intake["raw_source_manifests"]
    for ref in source_manifests:
        read_reference(ref)
    review_instructions = reference(root / "REVIEW_INSTRUCTIONS.md")
    qualification = reference(qualification_path)
    read_reference(qualification)
    if reference(sources_path) != audit["canonical_display_bindings"]:
        raise ValueError("Source bindings differ from independently verified intake")
    sources = read_reference(audit["canonical_display_bindings"])
    read_reference(audit["usability_registry"])
    index = verify_index(Path(audit["index"]["path"]))
    if index["index_identity"] != audit["index_identity"]:
        raise ValueError("Source index differs from intake")
    rows = []
    for case in inputs["cases"]:
        directory = root / "cases" / case["case_id"]
        validation = validate_saved_case(
            directory,
            case,
            data_root,
            sources,
            index_identity=index["index_identity"],
            source_manifest_refs=source_manifests,
        )
        packet = json.loads((directory / "packet.json").read_bytes())
        journal = new_journal(packet)
        checkpoint = export_review(packet, journal)
        write_new(directory / "journal_initial.json", journal)
        write_new(directory / "review_checkpoint_initial.json", checkpoint)
        display = render_display(
            packet,
            [
                row["finding_id"]
                for row in packet["claim_findings"] + packet["beyond_claim_findings"]
            ],
        )
        write_new(directory / "review_display.json", display)
        markdown = directory / "REVIEW.md"
        content = display["text"].encode() + b"\n"
        if markdown.exists() and markdown.read_bytes() != content:
            raise ValueError("Saved readable review differs")
        if not markdown.exists():
            with markdown.open("xb") as stream:
                stream.write(content)
        full_sources = directory / "SOURCES.html"
        source_content = (
            "<!doctype html><html><head><meta charset='utf-8'><title>"
            + html.escape(case["case_id"])
            + " complete sources</title></head><body><h1>Complete source occurrences</h1>"
            + "<p>Advisory preparation only. Human decisions remain blank.</p>"
            + "".join(
                "<article id='"
                + html.escape(source["occurrence_id"], quote=True)
                + "'>"
                + _source_excerpt_html(source, source["occurrence_id"])
                + "</article>"
                for source in packet["sources"]
            )
            + "</body></html>"
        ).encode()
        if full_sources.exists() and full_sources.read_bytes() != source_content:
            raise ValueError("Saved complete source display differs")
        if not full_sources.exists():
            with full_sources.open("xb") as stream:
                stream.write(source_content)
        rows.append(
            {
                "case_id": case["case_id"],
                "packet": reference(directory / "packet.json"),
                "review_display": reference(markdown),
                "complete_sources": reference(full_sources),
                "validation": validation,
                "beyond_claim_findings": len(packet["beyond_claim_findings"]),
                "query_receipts": sum(
                    len(track["query_receipts"]) for track in packet["track_results"].values()
                ),
                "remaining_gaps": packet["remaining_gaps"],
                "independent_review": reference(directory / "independent_review.json"),
                "human_decisions": [],
                "eligibility": None,
                "disposition": None,
            }
        )
    handoff = {
        "schema_version": "task08e.prepared_batch.v1",
        "status": "prepared, awaiting human review",
        "cases": rows,
        "held_case_ids": inputs["held_case_ids"],
        "deferred_case_ids": inputs["deferred_case_ids"],
        "upstream_handoff": inputs["upstream_handoff"],
        "phase_a_complete": True,
        "phase_b_started": False,
        "08f_started": False,
        "resume_case_id": rows[0]["case_id"],
        "human_decisions": 0,
        "approved_claims": sum(row["validation"]["claims"] for row in rows),
        "source_occurrences": sum(row["validation"]["sources"] for row in rows),
        "beyond_claim_findings": sum(row["beyond_claim_findings"] for row in rows),
        "query_receipts": sum(row["query_receipts"] for row in rows),
        "eligibility": None,
        "sources": reference(sources_path),
        "review_instructions": review_instructions,
        "qualification": qualification,
        "raw_source_manifests": source_manifests,
    }
    if supplement_authorization_path is not None:
        handoff["research_reopening_authorization"] = reference(supplement_authorization_path)
        handoff["historical_held_case_ids"] = inputs["historical_held_case_ids"]
    write_new(root / "prepared_handoff.json", handoff)
    inventory = [
        reference(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path != root / "completion.json"
    ]
    write_new(
        root / "completion.json",
        {
            "schema_version": "task08e.prepared_completion.v1",
            "handoff": reference(root / "prepared_handoff.json"),
            "files": inventory,
        },
    )
    return {
        "schema_version": "task08e.prepared_result.v1",
        "status": handoff["status"],
        "handoff": reference(root / "prepared_handoff.json"),
        "completion": reference(root / "completion.json"),
        "cases": len(rows),
        "approved_claims": handoff["approved_claims"],
        "source_occurrences": handoff["source_occurrences"],
        "beyond_claim_findings": handoff["beyond_claim_findings"],
        "query_receipts": handoff["query_receipts"],
        "held_case_ids": handoff["held_case_ids"],
        "deferred_case_ids": handoff["deferred_case_ids"],
        "human_decisions": 0,
        "next_action": "Separate question-by-question human review chat",
    }


def main() -> None:
    """Expose an explicit file-backed publication command without implicit execution."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "result", "data-root", "sources", "qualification", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = publish(
        args.root,
        args.result,
        args.data_root,
        args.sources,
        qualification_path=args.qualification,
    )
    write_new(args.output, result)


if __name__ == "__main__":
    main()
