"""Source anchoring and explicit support-review boundaries."""

import copy
import json
from pathlib import Path
from xml.etree import ElementTree

import pytest

from er_commons import pilot_evidence as evidence


@pytest.fixture
def prepared(tmp_path: Path):
    """Build one immutable claim and two candidates from canonical source records."""
    record = {"id": "b1", "source_id": "deir_main", "text": "Existing uses remain unchanged."}
    (tmp_path / "blocks.jsonl").write_text(json.dumps(record) + "\n")
    candidate = {
        "source_id": "deir_main",
        "edition": "Draft",
        "source_url": "https://example.org/source.pdf",
        "physical_pages": [1],
        "printed_labels": ["4.9-61"],
        "limitations": ["sampled review"],
        "anchors": [
            {
                "path": "blocks.jsonl",
                "record_id_field": "id",
                "record_id": "b1",
                "record": record,
                "text_field": "text",
                "start": 0,
                "end": len(record["text"]),
                "quote": record["text"],
            }
        ],
        "quote": record["text"],
    }
    candidate["candidate_id"] = evidence.candidate_id(candidate)
    claim = {
        "claim_id": "claim-1",
        "local_id": "C001",
        "text": "Existing emissions stay unchanged.",
        "relationship": "direct",
        "concern_ids": ["Q1"],
        "supporting_claim_ids": [],
    }
    review = {
        "review_status": "approved",
        "case_label": "case",
        "claims": [claim],
        "evidence_candidate_claim_ids": ["claim-1"],
    }
    packet = {
        "schema_version": evidence.SCHEMA,
        "case_id": "case",
        "claims": [claim],
        "context": dict.fromkeys(
            ("comment_html", "concerns_html", "response_html"), "<p>Context</p>"
        ),
        "source_bindings": {},
        "candidates": [candidate],
        "discovery_attempts": [],
        "claim_candidates": [
            {
                "claim_id": "claim-1",
                "candidate_ids": [candidate["candidate_id"]],
                "overflow_candidate_ids": [],
                "search_gap": "Bounded search.",
            }
        ],
    }
    review["data"] = {
        "comment_html": "<p>Context</p>",
        "concerns_html": "<p>Context</p>",
        "sources_html": "<p>Context</p>",
    }
    return packet, review, tmp_path


def annotation(**values):
    """Construct native fields without assigning them to real human reviewers."""
    result = []
    for name, value in values.items():
        kind = "textarea" if name.endswith("note") else "choices"
        result.append(
            {
                "from_name": name,
                "to_name": "evidence",
                "type": kind,
                "value": {
                    "text" if kind == "textarea" else "choices": value
                    if isinstance(value, list)
                    else [value]
                },
            }
        )
    return {"id": 1, "task": 2, "completed_by": "synthetic-test", "result": result}


def test_explicit_review_and_no_defaults(prepared):
    packet, review, root = prepared
    task = evidence.prepare_task(packet, data_root=root, approved_review=review)
    form = evidence.build_form(task)
    xml = ElementTree.fromstring(form)
    notes = xml.findall(".//TextArea")
    assert notes and all(note.attrib["transcription"] == "true" for note in notes)
    assert all(note.attrib["editable"] == "true" for note in notes)
    assert "selected=" not in form
    native = {**task, "id": 2}
    result = evidence.normalize_review(
        native,
        annotation(
            c001_p01_label="supports",
            c001_outcome="supported",
            c001_set=["E01"],
            case_status="reviewed",
        ),
        expected_task=task,
        export_lineage="synthetic",
    )
    assert result["claims"][0]["outcome"] == "supported"
    assert (
        result["claims"][0]["pairs"][0]["candidate_id"] == packet["candidates"][0]["candidate_id"]
    )


@pytest.mark.parametrize("mutation", ["quote", "snapshot", "claims", "path"])
def test_tampered_inputs_rejected(prepared, mutation):
    packet, review, root = prepared
    packet = copy.deepcopy(packet)
    candidate = packet["candidates"][0]
    if mutation == "quote":
        candidate["anchors"][0]["quote"] = "invented"
    elif mutation == "snapshot":
        candidate["anchors"][0]["record"]["source_id"] = "other"
    elif mutation == "path":
        candidate["anchors"][0]["path"] = "../elsewhere.jsonl"
    else:
        packet["claims"][0]["text"] = "edited"
    candidate["candidate_id"] = evidence.candidate_id(candidate)
    with pytest.raises(ValueError):
        evidence.prepare_task(packet, data_root=root, approved_review=review)


def test_partial_requires_explanation_and_overall_set(prepared):
    packet, review, root = prepared
    task = evidence.prepare_task(packet, data_root=root, approved_review=review)
    with pytest.raises(ValueError, match="explanation"):
        evidence.normalize_review(
            {**task, "id": 2},
            annotation(c001_p01_label="partial", c001_outcome="partial", case_status="reviewed"),
            expected_task=task,
            export_lineage="synthetic",
        )


def test_needs_context_preserves_unfinished_work(prepared):
    packet, review, root = prepared
    task = evidence.prepare_task(packet, data_root=root, approved_review=review)
    result = evidence.normalize_review(
        {**task, "id": 2},
        annotation(case_status="needs_context", case_note="Read the table footnote."),
        expected_task=task,
        export_lineage="synthetic",
    )
    assert result["validation_errors"]
    assert result["claims"][0]["outcome"] == ""


@pytest.mark.parametrize("mutation", ["duplicate", "unknown", "object", "task", "evidence"])
def test_native_binding_rejected(prepared, mutation):
    packet, review, root = prepared
    task = evidence.prepare_task(packet, data_root=root, approved_review=review)
    saved = annotation(
        c001_p01_label="supports",
        c001_outcome="supported",
        c001_set=["E01"],
        case_status="reviewed",
    )
    if mutation == "duplicate":
        saved["result"].append(saved["result"][0])
    elif mutation == "unknown":
        saved["result"][0]["from_name"] = "unknown"
    elif mutation == "object":
        saved["result"][0]["to_name"] = "other"
    elif mutation == "task":
        saved["task"] = 99
    else:
        saved["result"][2]["value"]["choices"] = ["E99"]
    with pytest.raises(ValueError):
        evidence.normalize_review(
            {**task, "id": 2}, saved, expected_task=task, export_lineage="synthetic"
        )


@pytest.mark.parametrize("pair_label", ["context", "no_support", "unusable"])
def test_background_cannot_become_supported_outcome(prepared, pair_label):
    packet, review, root = prepared
    task = evidence.prepare_task(packet, data_root=root, approved_review=review)
    with pytest.raises(ValueError, match="supporting evidence"):
        evidence.normalize_review(
            {**task, "id": 2},
            annotation(
                c001_p01_label=pair_label,
                c001_p01_note="Reason",
                c001_outcome="supported",
                c001_set=["E01"],
                case_status="reviewed",
            ),
            expected_task=task,
            export_lineage="synthetic",
        )


def test_context_cannot_be_substituted(prepared):
    packet, review, root = prepared
    packet["context"]["comment_html"] = "<p>Untrusted replacement</p>"
    with pytest.raises(ValueError, match="Context"):
        evidence.prepare_task(packet, data_root=root, approved_review=review)


def test_table_cells_preserve_exact_canonical_snapshot(prepared):
    packet, review, root = prepared
    record = {
        "id": "t1",
        "source_id": "deir_main",
        "shape": [2, 2],
        "cells": [
            {"row_index": 0, "column_index": 0, "text": "Pollutant"},
            {"row_index": 0, "column_index": 1, "text": "Pounds/day"},
            {"row_index": 1, "column_index": 0, "text": "NOx"},
            {"row_index": 1, "column_index": 1, "text": "10"},
        ],
    }
    (root / "tables.jsonl").write_text(json.dumps(record) + "\n")
    candidate = packet["candidates"][0]
    candidate["anchors"] = [
        {
            "path": "tables.jsonl",
            "record_id_field": "id",
            "record_id": "t1",
            "record": record,
            "text_field": f"cells.{i}.text",
            "start": 0,
            "end": len(cell["text"]),
            "quote": cell["text"],
        }
        for i, cell in enumerate(record["cells"])
    ]
    candidate["quote"] = "\n\n".join(cell["text"] for cell in record["cells"])
    candidate["candidate_id"] = evidence.candidate_id(candidate)
    packet["claim_candidates"][0]["candidate_ids"] = [candidate["candidate_id"]]
    task = evidence.prepare_task(packet, data_root=root, approved_review=review)
    assert "<td>Pounds/day</td>" in task["data"]["evidence_html"]
    record = copy.deepcopy(record)
    record["cells"][3]["text"] = "999"
    (root / "tables.jsonl").write_text(json.dumps(record) + "\n")
    with pytest.raises(ValueError, match="snapshot"):
        evidence.prepare_task(packet, data_root=root, approved_review=review)


def test_overflow_retained_but_not_presented_as_judgment(prepared):
    packet, review, root = prepared
    overflow = copy.deepcopy(packet["candidates"][0])
    overflow["title"] = "Overflow title"
    overflow["candidate_id"] = evidence.candidate_id(overflow)
    packet["candidates"].append(overflow)
    packet["claim_candidates"][0]["overflow_candidate_ids"] = [overflow["candidate_id"]]
    task = evidence.prepare_task(packet, data_root=root, approved_review=review)
    assert "Overflow title" not in task["data"]["evidence_html"]
    assert "Overflow: E02" in task["data"]["c001_html"]
    assert len(task["data"]["slots"][0]["candidate_ids"]) == 1


def test_header_display_merges_only_blank_header_placeholders():
    record = {
        "cells": [
            {"row_index": 0, "column_index": 0, "text": "Operational emissions"},
            {"row_index": 0, "column_index": 1, "text": ""},
            {"row_index": 1, "column_index": 0, "text": "10"},
            {"row_index": 1, "column_index": 1, "text": ""},
        ]
    }
    original = copy.deepcopy(record)
    output = evidence._table_html(record, 1)
    assert '<th colspan="2">Operational emissions</th>' in output
    assert "<td>10</td><td></td>" in output
    assert record == original


def test_claim_tasks_preserve_full_packet_and_shared_form(prepared):
    packet, review, root = prepared
    for index in (2, 3):
        candidate = copy.deepcopy(packet["candidates"][0])
        candidate["title"] = f"Source {index}"
        candidate["candidate_id"] = evidence.candidate_id(candidate)
        packet["candidates"].append(candidate)
        claim = copy.deepcopy(packet["claims"][0])
        claim.update(claim_id=f"claim-{index}", local_id=f"C00{index}", text=f"Claim {index}")
        packet["claims"].append(claim)
        review["claims"].append(copy.deepcopy(claim))
        review["evidence_candidate_claim_ids"].append(claim["claim_id"])
        packet["claim_candidates"].append(
            {
                "claim_id": claim["claim_id"],
                "candidate_ids": [candidate["candidate_id"]],
                "overflow_candidate_ids": [],
                "search_gap": "Limited search.",
            }
        )
    packet["claim_candidates"][0]["candidate_ids"] = [
        c["candidate_id"] for c in packet["candidates"]
    ]
    original = copy.deepcopy(packet)
    tasks = evidence.prepare_claim_tasks(packet, data_root=root, approved_review=review)
    assert len(tasks) == 3
    assert packet == original
    assert all(t["data"]["packet"] == original for t in tasks)
    assert all(t["data"]["packet_sha256"] == evidence.digest(original) for t in tasks)
    assert len({t["data"]["claim_task_id"] for t in tasks}) == 3
    assert tasks == evidence.prepare_claim_tasks(packet, data_root=root, approved_review=review)
    data = tasks[2]["data"]
    assert data["claim_heading"] == "case · C003 · 3 of 3"
    assert data["evidence_options"] == [{"value": "E03"}]
    assert "Source 3" in data["evidence_html"] and "Source 2" not in data["evidence_html"]
    assert len(data["slots"]) == 1
    xml = ElementTree.fromstring(evidence.build_claim_form())
    assert all("selected" not in choice.attrib for choice in xml.findall(".//Choice"))
    assert all(control.attrib.get("required") != "true" for control in xml.findall(".//Choices"))
    assert xml.find(".//Choices[@name='c001_set']") is None
    assert xml.find(".//Choices[@name='claim_status']") is None
    assert xml.find(".//Choices[@name='case_status']") is None
    result = evidence.normalize_claim_review(
        {**tasks[2], "id": 2},
        annotation(
            c001_p01_label="supports",
            c001_outcome="supported",
        ),
        expected_task=tasks[2],
        export_lineage="synthetic",
    )
    assert "evidence_set" not in result["claim_review"]
    assert result["claim_id"] == "claim-3"
    assert result["review_complete"] is True
    assert "claim_status" not in result and "claim_note" not in result
    assert "case_status" not in result and "claims" not in result
    assert result["schema_version"] == "er_commons.task07d.claim_evidence_review.v2"


@pytest.mark.parametrize(
    "extra",
    [
        {"c001_p02_label": "supports"},
        {"c001_p02_label": []},
        {"case_status": "reviewed"},
        {"c001_set": ["E99"]},
        {"c001_set": ["E01"]},
        {"claim_status": "reviewed"},
        {"claim_note": "Old note"},
    ],
)
def test_claim_review_rejects_inactive_or_foreign_controls(prepared, extra):
    packet, review, root = prepared
    task = evidence.prepare_claim_tasks(packet, data_root=root, approved_review=review)[0]
    values = dict(
        c001_p01_label="supports",
        c001_outcome="supported",
    )
    values.update(extra)
    with pytest.raises(ValueError):
        evidence.normalize_claim_review(
            {**task, "id": 2}, annotation(**values), expected_task=task, export_lineage="synthetic"
        )


def test_claim_gap_and_partial_work_remain_explicit(prepared):
    packet, review, root = prepared
    packet["claim_candidates"][0]["candidate_ids"] = []
    task = evidence.prepare_claim_tasks(packet, data_root=root, approved_review=review)[0]
    assert "evidence-count-0" in task["data"]["claim_html"]
    assert task["data"]["evidence_options"] == []
    result = evidence.normalize_claim_review(
        {**task, "id": 2},
        annotation(c001_outcome="unresolved", c001_note="Need the underlying model."),
        expected_task=task,
        export_lineage="synthetic",
    )
    assert result["review_complete"] and not result["validation_errors"]
    with pytest.raises(ValueError):
        evidence.normalize_claim_review(
            {**task, "id": 2},
            annotation(),
            expected_task=task,
            export_lineage="synthetic",
        )
    with pytest.raises(ValueError, match="Case-level"):
        evidence.normalize_review(
            {**task, "id": 2}, annotation(), expected_task=task, export_lineage="synthetic"
        )


def test_historical_claim_form_keeps_its_provenance(prepared):
    """Old task versions retain their original form binding after layout revisions."""
    import hashlib

    packet, review, root = prepared
    task = evidence.prepare_claim_tasks(packet, data_root=root, approved_review=review)[0]
    task["data"]["form_version"] = evidence.LEGACY_CLAIM_FORM_VERSION
    result = evidence.normalize_claim_review(
        {**task, "id": 2},
        annotation(claim_status="needs_context", claim_note="Source context needed."),
        expected_task=task,
        export_lineage="historical-synthetic",
    )
    historical = evidence.build_claim_form(evidence.LEGACY_CLAIM_FORM_VERSION)
    assert result["form_sha256"] == hashlib.sha256(historical.encode()).hexdigest()
    assert result["form_sha256"] != hashlib.sha256(evidence.build_claim_form().encode()).hexdigest()
    with pytest.raises(ValueError, match="Unknown claim form"):
        evidence.build_claim_form("unknown")


@pytest.mark.parametrize(
    "version, expected_hash",
    [
        (
            "task07d.claim_evidence_review.v1",
            "d84f9ce3b96aafc95fe282c9600da70f866bf67d29457827c53d665109cfd3f6",
        ),
        (
            "task07d.claim_evidence_review.v2",
            "030f09faf4a7610f27f47a1c8f35079f083aa6231e6b9008bc44e39b4ec6298c",
        ),
    ],
)
def test_historical_form_bytes_are_unchanged(version, expected_hash):
    """Sealed project exports retain exactly the form used to collect them."""
    import hashlib

    assert hashlib.sha256(evidence.build_claim_form(version).encode()).hexdigest() == expected_hash


@pytest.mark.parametrize(
    "capacity, expected_hash",
    [
        (1, "335cd5471a88accbad70313bd5700c1fc00ff2ab148ebc9393b1bd69d289c9ab"),
        (3, "6254cf2a84d7d5488139f69e8c024d7625e9d0df029e5744a05f8806acdbedca"),
        (10, "3778172af007271767f42fd503c63a7f2f827cd92fe0a036170311efdd9263e9"),
    ],
)
def test_current_form_preserves_sealed_bytes(capacity, expected_hash):
    """Moving renderers must preserve hashes used by the completed MVP reviews."""
    import hashlib

    form = evidence.build_claim_form(max_candidates=capacity)
    assert hashlib.sha256(form.encode()).hexdigest() == expected_hash


def test_rejected_claim_review_retains_normalized_provenance(prepared):
    """Explicitly dispositioned inconsistencies do not require a second native parser."""
    packet, review, root = prepared
    task = evidence.prepare_claim_tasks(packet, data_root=root, approved_review=review)[0]
    native = annotation(c001_p01_label="context", c001_outcome="supported")
    with pytest.raises(evidence.ReviewValidationError) as caught:
        evidence.normalize_claim_review(
            {**task, "id": 2}, native, expected_task=task, export_lineage="synthetic"
        )
    rejected = caught.value.review
    assert rejected["review_complete"] is False
    assert rejected["claim_id"] == task["data"]["claim_id"]
    assert rejected["claim_task_id"] == task["data"]["claim_task_id"]
    assert "claims" not in rejected
    assert rejected["claim_review"]["pairs"][0]["relationship"] == "context"
    assert rejected["claim_review"]["outcome"] == "supported"
    assert rejected["native_annotation"] == native
    assert rejected["annotation_sha256"] == evidence.digest(native)
    assert str(caught.value) == "; ".join(rejected["validation_errors"])
    native["result"].clear()
    assert rejected["native_annotation"]["result"]


def test_foreign_native_controls_have_no_dispositionable_review(prepared):
    """Structural failures cannot be accepted as mere outcome-consistency warnings."""
    packet, review, root = prepared
    task = evidence.prepare_claim_tasks(packet, data_root=root, approved_review=review)[0]
    native = annotation(c001_p01_label="context", c001_outcome="supported", foreign="supports")
    with pytest.raises(ValueError, match="Unknown, duplicate, or foreign") as caught:
        evidence.normalize_claim_review(
            {**task, "id": 2}, native, expected_task=task, export_lineage="synthetic"
        )
    assert not isinstance(caught.value, evidence.ReviewValidationError)


def test_claim_source_text_and_reviewer_commentary_are_separate(prepared):
    """A reviewer can distinguish quotations from retrieval limits and corrections."""
    packet, review, root = prepared
    candidate = packet["candidates"][0]
    candidate["citation_relation"] = {
        "kind": "corrected",
        "note": "The response named the wrong footnote.",
    }
    candidate["candidate_id"] = evidence.candidate_id(candidate)
    packet["claim_candidates"][0]["candidate_ids"] = [candidate["candidate_id"]]
    original = copy.deepcopy(packet)
    data = evidence.prepare_claim_tasks(packet, data_root=root, approved_review=review)[0]["data"]
    assert packet == original
    assert data["claim"]["text"] == packet["claims"][0]["text"]
    assert "Existing uses remain unchanged." in data["evidence_html"]
    assert "Source excerpt" in data["evidence_html"]
    for note in ("sampled review", "Bounded search.", "The response named the wrong footnote."):
        assert note not in data["evidence_html"]
        assert note not in data["claim_html"]
        assert note in data["reviewer_notes_html"]
    assert "not source text" in data["reviewer_notes_html"]
    assert "<details><summary>Source provenance" in data["reviewer_notes_html"]
    assert data["concerns_html"] == review["data"]["concerns_html"]
    xml = ElementTree.fromstring(evidence.build_claim_form())
    children = list(xml)
    claim_index = next(i for i, child in enumerate(children) if child.attrib.get("name") == "claim")
    context_index = next(
        i for i, child in enumerate(children) if child.attrib.get("className") == "question-context"
    )
    layout_index = next(
        i for i, child in enumerate(children) if child.attrib.get("className") == "layout"
    )
    assert claim_index < context_index < layout_index
    context = children[context_index]
    assert context.find("HyperText[@name='concerns']") is not None
    assert context.find("Collapse/Panel/HyperText[@name='comment']") is not None
    columns = list(children[layout_index])
    assert [c.attrib["className"] for c in columns] == ["decisions", "sources"]
    assert columns[0].find("HyperText[@name='reviewer_notes']") is not None
    assert columns[1].find("HyperText[@name='evidence']") is not None


@pytest.mark.parametrize(
    "kind, label",
    [
        ("corrected", "corrected citation"),
        ("omitted", "additional citation"),
        ("supplied", None),
    ],
)
def test_citation_notes_distinguish_corrections_from_supplied_references(prepared, kind, label):
    """Ordinary response citations remain provenance without adding review clutter."""
    packet, review, root = prepared
    candidate = packet["candidates"][0]
    candidate["citation_relation"] = {"kind": kind, "note": "Citation relationship detail."}
    candidate["candidate_id"] = evidence.candidate_id(candidate)
    packet["claim_candidates"][0]["candidate_ids"] = [candidate["candidate_id"]]
    data = evidence.prepare_claim_tasks(packet, data_root=root, approved_review=review)[0]["data"]
    assert data["packet"]["candidates"][0]["citation_relation"]["kind"] == kind
    assert "Citation relationship detail." not in data["evidence_html"]
    if label:
        assert label in data["reviewer_notes_html"]
        assert "Citation relationship detail." in data["reviewer_notes_html"]
    else:
        assert "Citation relationship detail." not in data["reviewer_notes_html"]


@pytest.mark.parametrize("count", [4, 8])
def test_fuller_claim_review_preserves_every_candidate(prepared, count):
    """All retrieved candidates remain judgeable, including previous overflow entries."""
    import hashlib

    packet, review, root = prepared
    for index in range(2, count + 1):
        candidate = copy.deepcopy(packet["candidates"][0])
        candidate["title"] = f"Background {index}"
        candidate["retrieval_reason"] = f"Check methodological detail {index} <without endorsing>."
        candidate["candidate_id"] = evidence.candidate_id(candidate)
        packet["candidates"].append(candidate)
    ids = [c["candidate_id"] for c in packet["candidates"]]
    split = 0 if count == 4 else count
    packet["claim_candidates"][0]["candidate_ids"] = ids[:split]
    packet["claim_candidates"][0]["overflow_candidate_ids"] = ids[split:]
    packet["claim_candidates"][0]["search_gap"] = ""
    original = copy.deepcopy(packet)
    task = evidence.prepare_claim_tasks(packet, data_root=root, approved_review=review)[0]
    assert packet == original and task["data"]["packet"] == original
    assert task["data"]["max_candidates"] == count
    assert task["data"]["slots"][0]["candidate_ids"] == ids
    assert len(task["data"]["evidence_options"]) == count
    assert task["data"]["evidence_html"].count('class="source-excerpt"') == count
    assert "Check methodological detail" not in task["data"]["evidence_html"]
    assert "&lt;without endorsing&gt;" in task["data"]["reviewer_notes_html"]
    form = evidence.build_claim_form(max_candidates=count)
    xml = ElementTree.fromstring(form)
    assert len(xml.findall(".//View[@className]")) >= count
    assert xml.find(f'.//Choices[@name="c001_p{count:02d}_label"]') is not None
    assert xml.find(f'.//Choices[@name="c001_p{count + 1:02d}_label"]') is None
    assert f".evidence-count-{count - 1}) .pair-{count}" in form
    assert f".evidence-count-{count}) .pair-{count}" not in form
    values = {f"c001_p{i:02d}_label": "context" for i in range(1, count + 1)}
    values.update(c001_outcome="no_support_found")
    result = evidence.normalize_claim_review(
        {**task, "id": 2}, annotation(**values), expected_task=task, export_lineage="synthetic"
    )
    assert len(result["claim_review"]["pairs"]) == count
    assert result["form_sha256"] == hashlib.sha256(form.encode()).hexdigest()
    assert "case_status" not in result
    values[f"c001_p{count + 1:02d}_label"] = "context"
    with pytest.raises(ValueError, match="Unknown"):
        evidence.normalize_claim_review(
            {**task, "id": 2}, annotation(**values), expected_task=task, export_lineage="synthetic"
        )
    task["data"]["max_candidates"] = count - 1
    with pytest.raises(ValueError, match="capacity"):
        evidence.normalize_claim_review(
            {**task, "id": 2}, annotation(), expected_task=task, export_lineage="synthetic"
        )


def test_fuller_form_keeps_v3_form_bytes():
    """The prior split-pane review continues to reproduce its sealed form hash."""
    import hashlib

    form = evidence.build_claim_form(evidence.CONTEXT_CLAIM_FORM_VERSION)
    assert (
        hashlib.sha256(form.encode()).hexdigest()
        == "761e4ed3c659386d4b9f648f9a812e1f7012bd751f0ae2de4403f19cce45adf0"
    )


@pytest.mark.parametrize("capacity", [0, -1, True, 2.5])
def test_invalid_candidate_capacity_rejected(capacity):
    """Capacity cannot silently omit controls or accept noninteger configuration."""
    with pytest.raises(ValueError, match="capacity"):
        evidence.build_claim_form(max_candidates=capacity)


@pytest.mark.parametrize(
    "capacity, expected_hash",
    [
        (1, "0e742fb4102cfd002eda9f34a5d98e4f1fb2b57c046dd17ad339f724de3b0fe3"),
        (3, "764152d681cafed4f521c588483a078ef3f32dc0c5488476457b7e8856a6ccb1"),
        (5, "9467839036de1bc15ee0a84d0aeb6c74dfe86c29a756fdcb270c25d2a37ad597"),
    ],
)
def test_v4_capacity_forms_keep_exact_bytes(capacity, expected_hash):
    """Historical variable-capacity forms preserve their original hashes."""
    import hashlib

    form = evidence.build_claim_form(evidence.FULLER_CLAIM_FORM_VERSION, max_candidates=capacity)
    assert hashlib.sha256(form.encode()).hexdigest() == expected_hash


@pytest.mark.parametrize(
    "labels,outcome,note,valid",
    [
        (["supports", "supports"], "supported", "", True),
        (["partial", "partial"], "supported", "Together these cover both parts.", True),
        (["partial", "partial"], "supported", "", False),
        (["context", "context"], "supported", "", False),
        (["supports", "context"], "partial", "The remaining part is unverified.", True),
        (["context", "context"], "partial", "A gap.", False),
        (["contradicts", "context"], "conflicting", "This conflicts with the claim.", True),
        (["supports", "context"], "conflicting", "A conflict.", False),
        (["supports", "context"], "no_support_found", "", False),
        (["supports", "context"], "no_support_found", "Positive passage is superseded.", True),
        (["context", "context"], "unresolved", "Need more context.", True),
        (["context", "context"], "unresolved", "", False),
        (["context", "context"], "", "", False),
        (["context", ""], "no_support_found", "", False),
    ],
)
def test_simplified_outcome_consistency(prepared, labels, outcome, note, valid):
    """Completion follows explicit judgments, never a fabricated human evidence set."""
    packet, review, root = prepared
    candidate = copy.deepcopy(packet["candidates"][0])
    candidate["title"] = "Second source"
    candidate["candidate_id"] = evidence.candidate_id(candidate)
    packet["candidates"].append(candidate)
    packet["claim_candidates"][0]["candidate_ids"] = [
        c["candidate_id"] for c in packet["candidates"][:2]
    ]
    task = evidence.prepare_claim_tasks(packet, data_root=root, approved_review=review)[0]
    values = dict(c001_outcome=outcome, c001_note=note)
    for i, label in enumerate(labels, 1):
        values[f"c001_p{i:02d}_label"] = label
        values[f"c001_p{i:02d}_note"] = "Covered part and remaining gap; reason."
    native = annotation(**values)
    if not valid:
        with pytest.raises(ValueError):
            evidence.normalize_claim_review(
                {**task, "id": 2}, native, expected_task=task, export_lineage="synthetic"
            )
        return
    result = evidence.normalize_claim_review(
        {**task, "id": 2}, native, expected_task=task, export_lineage="synthetic"
    )
    assert result["review_complete"] is True
    assert "evidence_set" not in result["claim_review"]
    assert "claim_status" not in result and "claim_note" not in result
    assert result["native_annotation"] == native


def test_v4_normalizer_keeps_historical_set_and_status(prepared):
    """Earlier human exports keep their explicit status and selected source set."""
    packet, review, root = prepared
    task = evidence.prepare_claim_tasks(packet, data_root=root, approved_review=review)[0]
    task["data"]["form_version"] = evidence.FULLER_CLAIM_FORM_VERSION
    result = evidence.normalize_claim_review(
        {**task, "id": 2},
        annotation(
            c001_p01_label="supports",
            c001_outcome="supported",
            c001_set=["E01"],
            claim_status="reviewed",
        ),
        expected_task=task,
        export_lineage="historical-synthetic",
    )
    assert result["schema_version"] == "er_commons.task07d.claim_evidence_review.v1"
    assert result["claim_status"] == "reviewed"
    assert result["claim_review"]["evidence_set"] == [packet["candidates"][0]["candidate_id"]]
    assert "review_complete" not in result
