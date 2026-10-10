"""Publication cannot hide receipt drift or bypass independent full-packet review."""

import json
from pathlib import Path

import pytest
from test_group_evidence_research import fixture

from er_commons.group_claims_batch import reference, write_new
from er_commons.group_evidence_publication import validate_saved_case
from er_commons.pilot_evidence import digest


def prepared(tmp_path: Path) -> tuple[dict, Path]:
    """Save an entirely synthetic no-citation packet with exact raw search receipts."""
    case, plan, packet = fixture(tmp_path)
    directory = tmp_path / "case"
    write_new(directory / "plan.json", plan)
    write_new(directory / "packet.json", packet)
    for track, result in packet["track_results"].items():
        for receipt in result["query_receipts"]:
            raw = {key: value for key, value in receipt.items() if key != "inspected_hits"}
            path = directory / "queries" / track / (receipt["query_id"] + ".receipt.json")
            write_new(path, raw)
            write_new(path.with_name(receipt["query_id"] + ".binding.json"), reference(path))
            write_new(
                path.with_name(receipt["query_id"] + ".plan.json"),
                {
                    "track": track,
                    "plan": reference(directory / "plan.json"),
                    "query": {k: raw[k] for k in ("query_id", "expression", "purpose")},
                },
            )
    write_new(
        directory / "independent_review.json",
        {
            "packet_sha256": digest(packet),
            "status": "pass",
            "worker": "synthetic-reviewer",
            "coverage": "All five synthetic tracks",
            "export_fidelity": "exact",
            "scope_exclusions": "No external sources",
            "counterevidence": "synthetic gaps retained",
            "blocking_findings": [],
        },
    )
    return case, directory


def test_raw_receipt_fidelity(tmp_path: Path) -> None:
    """A changed raw receipt remains an error even after a new file hash is written."""
    case, directory = prepared(tmp_path)
    assert validate_saved_case(directory, case, tmp_path, [])["status"] == "valid"
    path = next((directory / "queries").glob("*/*.receipt.json"))
    raw = json.loads(path.read_bytes())
    raw["expression"] = "different"
    path.write_text(json.dumps(raw))
    path.with_name(path.name.replace(".receipt.json", ".binding.json")).write_text(
        json.dumps(reference(path))
    )
    with pytest.raises(ValueError, match="actual saved query"):
        validate_saved_case(directory, case, tmp_path, [])


def test_independent_review_cannot_be_missing(tmp_path: Path) -> None:
    """Machine binding validation alone cannot publish the question packet."""
    case, directory = prepared(tmp_path)
    path = directory / "independent_review.json"
    review = json.loads(path.read_bytes())
    review["packet_sha256"] = "stale"
    path.write_text(json.dumps(review))
    with pytest.raises(ValueError, match="independent coverage"):
        validate_saved_case(directory, case, tmp_path, [])


def test_pending_intent_requires_exact_disclosed_abort(tmp_path: Path) -> None:
    """A crashed invocation stays visible and cannot silently vanish from the packet."""
    from er_commons.group_evidence_publication import _validate_query_intents

    _, directory = prepared(tmp_path)
    packet = json.loads((directory / "packet.json").read_bytes())
    intent_path = directory / "queries/question_gaps/crashed.plan.json"
    write_new(
        intent_path,
        {
            "track": "question_gaps",
            "plan": reference(directory / "plan.json"),
            "query": {"query_id": "crashed", "expression": "test", "source_filter": ["bad"]},
        },
    )
    with pytest.raises(ValueError, match="exactly one receipt"):
        _validate_query_intents(directory, packet)
    aborted_path = intent_path.with_name("crashed.aborted.json")
    aborted = {
        "intent": reference(intent_path),
        "query_id": "crashed",
        "status": "aborted_before_receipt",
        "error": "Invalid filter type before receipt",
    }
    write_new(aborted_path, aborted)
    with pytest.raises(ValueError, match="loses or changes aborted"):
        _validate_query_intents(directory, packet)
    packet["track_results"]["question_gaps"]["aborted_query_diagnostics"] = [
        reference(aborted_path)
    ]
    with pytest.raises(ValueError, match="explained"):
        _validate_query_intents(directory, packet)
    packet["limitations"].append(
        "crashed failed before receipt; correct-filter retry saved separately."
    )
    _validate_query_intents(directory, packet)
    aborted_path.write_text(json.dumps({**aborted, "error": "changed failure"}))
    with pytest.raises(ValueError, match="loses or changes aborted"):
        _validate_query_intents(directory, packet)


def test_receipt_must_preserve_planned_expression(tmp_path: Path) -> None:
    """Rebinding the raw receipt does not permit it to diverge from its saved intent."""
    from er_commons.group_evidence_publication import _validate_query_intents

    _, directory = prepared(tmp_path)
    packet = json.loads((directory / "packet.json").read_bytes())
    path = next((directory / "queries").glob("*/*.plan.json"))
    intent = json.loads(path.read_bytes())
    intent["query"]["expression"] = "another expression"
    path.write_text(json.dumps(intent))
    with pytest.raises(ValueError, match="differs from saved intent"):
        _validate_query_intents(directory, packet)


def test_publication_seals_blank_review_and_is_restartable(tmp_path: Path, monkeypatch) -> None:
    """Actual export files replay unchanged and every sealed byte remains discoverable."""
    from er_commons import group_evidence_publication as publication
    from er_commons.group_claims_batch import read_reference

    case, original = prepared(tmp_path)
    directory = tmp_path / "cases" / case["case_id"]
    directory.parent.mkdir()
    original.rename(directory)
    for receipt_path in (directory / "queries").glob("*/*.receipt.json"):
        receipt_path.with_name(
            receipt_path.name.replace(".receipt.json", ".binding.json")
        ).write_text(json.dumps(reference(receipt_path)))
        plan_path = receipt_path.with_name(receipt_path.name.replace(".receipt.json", ".plan.json"))
        intent = json.loads(plan_path.read_bytes())
        intent["plan"] = reference(directory / "plan.json")
        plan_path.write_text(json.dumps(intent))
    sources = tmp_path / "sources.json"
    registry = tmp_path / "registry.json"
    write_new(sources, [])
    write_new(registry, {"synthetic": True})
    write_new(
        tmp_path / "intake_audit.json",
        {
            "raw_source_manifests": [],
            "search_cache": {
                "canonical_display_bindings": reference(sources),
                "usability_registry": reference(registry),
                "index": {"path": str(tmp_path / "synthetic.sqlite")},
                "index_identity": "synthetic-index",
            },
        },
    )
    (tmp_path / "REVIEW_INSTRUCTIONS.md").write_text("Synthetic review instructions")
    qualification = tmp_path / "qualification.json"
    write_new(qualification, {"status": "passed", "live_human_decisions": 0})
    monkeypatch.setattr(
        publication,
        "load_inputs",
        lambda _: {
            "cases": [case],
            "held_case_ids": ["HELD"],
            "deferred_case_ids": ["DEFERRED"],
            "upstream_handoff": {"synthetic": True},
        },
    )
    monkeypatch.setattr(
        publication, "verify_index", lambda _: {"index_identity": "synthetic-index"}
    )
    first = publication.publish(
        tmp_path,
        tmp_path / "upstream.json",
        tmp_path,
        sources,
        qualification_path=qualification,
    )
    second = publication.publish(
        tmp_path,
        tmp_path / "upstream.json",
        tmp_path,
        sources,
        qualification_path=qualification,
    )
    assert first == second
    handoff = read_reference(first["handoff"])
    assert handoff["phase_b_started"] is False
    assert handoff["human_decisions"] == 0
    assert handoff["resume_case_id"] == "SYNTHETIC"
    assert handoff["cases"][0]["eligibility"] is None
    assert handoff["qualification"] == reference(qualification)
    assert handoff["review_instructions"] == reference(tmp_path / "REVIEW_INSTRUCTIONS.md")
    completion = read_reference(first["completion"])
    for ref in completion["files"]:
        assert reference(Path(ref["path"])) == ref
    journal = json.loads((directory / "journal_initial.json").read_bytes())
    assert journal["events"] == []
    assert "Synthetic claim" in (directory / "REVIEW.md").read_text()
    assert "Human decisions remain blank" in (directory / "SOURCES.html").read_text()
    result_path = tmp_path.parent / (tmp_path.name + "-result.json")
    write_new(result_path, first)
    assert publication.verify_prepared_result(result_path) == handoff
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
        changed = {**first, key: "wrong summary"}
        result_path.write_text(json.dumps(changed))
        with pytest.raises(ValueError, match="summary differs"):
            publication.verify_prepared_result(result_path)
    result_path.write_text(json.dumps(first))
    (directory / "REVIEW.md").write_text("changed display")
    with pytest.raises(ValueError, match="bytes changed"):
        publication.verify_prepared_result(result_path)


@pytest.mark.parametrize("mutation", ["url", "pdf_bytes", "manifest"])
def test_original_pdf_binding_rejected(tmp_path: Path, monkeypatch, mutation: str) -> None:
    """The production origin gate rejects wrong links and changed original PDF bytes."""
    import hashlib

    from er_commons import group_evidence_publication as publication

    case, directory = prepared(tmp_path)
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"synthetic PDF bytes")
    manifest = tmp_path / "manifest.json"
    row = {
        "source_id": "synthetic",
        "local_path": pdf.name,
        "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "byte_size": pdf.stat().st_size,
        "final_resolved_url": "https://example.org/source.pdf",
    }
    write_new(manifest, {"sources": [row]})
    approved_manifest = reference(manifest)
    packet = json.loads((directory / "packet.json").read_bytes())
    packet["sources"] = [
        {
            "source_id": "synthetic",
            "extraction_id": "ex",
            "anchors": [],
            "citation_unit": {"kind": "section"},
            "source_manifest": {"path": manifest.name, "sha256": reference(manifest)["sha256"]},
            "source_sha256": row["sha256"],
            "source_pdf_path": pdf.name,
            "source_url": row["final_resolved_url"],
            "pdf_url": row["final_resolved_url"],
        }
    ]
    # Isolate original-document validation; canonical packet gates have separate tests.
    monkeypatch.setattr(publication, "validate_packet", lambda *args: {"status": "valid"})
    if mutation == "url":
        packet["sources"][0]["pdf_url"] = "https://example.org/other.pdf"
    elif mutation == "pdf_bytes":
        pdf.write_bytes(b"changed original")
    else:
        # Internally consistent same-ID alternate edition must not choose its own trust root.
        alternate = tmp_path / "alternate.pdf"
        alternate.write_bytes(b"self-consistent wrong edition")
        alternate_manifest = tmp_path / "alternate_manifest.json"
        alternate_row = {
            **row,
            "local_path": alternate.name,
            "sha256": hashlib.sha256(alternate.read_bytes()).hexdigest(),
            "byte_size": alternate.stat().st_size,
            "final_resolved_url": "https://example.org/alternate.pdf",
        }
        write_new(alternate_manifest, {"sources": [alternate_row]})
        packet["sources"][0].update(
            source_manifest={
                "path": alternate_manifest.name,
                "sha256": reference(alternate_manifest)["sha256"],
            },
            source_sha256=alternate_row["sha256"],
            source_pdf_path=alternate.name,
            source_url=alternate_row["final_resolved_url"],
            pdf_url=alternate_row["final_resolved_url"],
        )
    (directory / "packet.json").write_text(json.dumps(packet))
    with pytest.raises(ValueError, match="Original PDF"):
        validate_saved_case(
            directory,
            case,
            tmp_path,
            [{"source_id": "synthetic", "extraction_id": "ex", "files": {}}],
            source_manifest_refs=[approved_manifest],
        )
