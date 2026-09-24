"""Exercise immutable packet boundaries and edited source attribution."""

import copy
import hashlib
import json

import pytest

from er_commons.pilot_claims import build_trial_task, normalize_review


def write_json(path, value):
    """Write predictable fixture bytes for manifest bindings."""
    path.write_text(json.dumps(value), encoding="utf-8")
    raw = path.read_bytes()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}


@pytest.fixture
def packet(tmp_path):
    """Build a small independent sealed packet with two distinct exact sources."""
    drafting = tmp_path / "drafting"
    drafting.mkdir()
    responses = []
    for index, text in enumerate(
        ["May apply <script> & only here.", "Another qualified claim."], 1
    ):
        responses.append(
            {
                "source_ref": f"R0{index}",
                "source_id": "volume",
                "unit_id": f"unit{index}",
                "official_label": f"Response {index}",
                "full_text": text,
                "passages": [
                    {
                        "passage_id": f"R0{index}-P01",
                        "text": text,
                        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                        "physical_page": index,
                        "page_text_start": 0,
                        "page_text_end": len(text),
                        "page_id": f"page{index}",
                    }
                ],
            }
        )
    source = {
        "schema_version": "er_commons.task07c.claim_input.v1",
        "case_label": "case",
        "comment_id": "comment",
        "responses": responses,
        "supplemental_passages": [],
        "reviewed_concerns": [{"concern_id": "Q1", "text": "Explain <why>."}],
        "original_comment": {"full_text": "Original <comment>."},
        "warnings": ["Not facts."],
    }
    files = {
        "claim_input.json": source,
        "response_closure.json": {
            "unresolved_response_mentions": [],
            "response_unit_ids": ["unit1", "unit2"],
        },
        "inherited_limitations.json": ["Extraction limits"],
        "proposal.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
        },
    }
    bindings = {name: write_json(drafting / name, value) for name, value in files.items()}
    manifest = {
        "schema_version": "er_commons.task07c.drafting_packet.v1",
        "case_label": "case",
        "files": bindings,
    }
    manifest_binding = write_json(drafting / "packet_manifest.json", manifest)
    proposal = {
        "case_label": "case",
        "input_sha256": bindings["claim_input.json"]["sha256"],
        "packet_manifest_sha256": manifest_binding["sha256"],
        "claims": [
            {
                "claim_id": "C001",
                "text": "Response says may apply.",
                "concern_ids": ["Q1"],
                "source_refs": [{"passage_id": "R01-P01", "quote": "May apply"}],
            }
        ],
        "coverage_notes": [{"source_ref": r, "note": "Read."} for r in ["R01", "R02"]],
        "unresolved_issues": ["Meaning unclear."],
    }
    proposal_path = tmp_path / "proposal.json"
    write_json(proposal_path, proposal)
    return drafting, proposal_path


def annotation(text, status="approved"):
    """Create explicit saved human fields using the configured object binding."""
    return {
        "task": 1,
        "id": 2,
        "completed_by": 3,
        "result": [
            {
                "from_name": "claims",
                "to_name": "response_context",
                "type": "textarea",
                "value": {"text": [text]},
            },
            {
                "from_name": "review_status",
                "to_name": "response_context",
                "type": "choices",
                "value": {"choices": [status]},
            },
        ],
    }


def normalize(task, review):
    """Use a separately verified expected task rather than trusting an export."""
    return normalize_review({"id": 1, **task}, review, expected_task=task, export_lineage="trial")


def test_full_sources_prefill_escape_and_immutable_proposal(packet):
    task = build_trial_task(*packet)
    data = task["data"]
    assert "&lt;script&gt; &amp;" in data["sources_html"]
    assert "Another qualified claim." in data["sources_html"]
    assert "Meaning unclear." in data["notes_html"]
    assert data["original_proposal"]["claims"][0]["source_refs"][0]["quote"] == "May apply"
    assert task["predictions"][0]["result"][0]["value"]["text"] == [data["proposal_text"]]
    assert "review_status" not in str(task["predictions"])


def test_packet_and_proposal_tampering(packet):
    drafting, proposal = packet
    changed = json.loads(proposal.read_text())
    changed["input_sha256"] = "0" * 64
    write_json(proposal, changed)
    with pytest.raises(ValueError, match="input binding"):
        build_trial_task(*packet)
    (drafting / "claim_input.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        build_trial_task(*packet)


@pytest.mark.parametrize("change", ["quote", "duplicate", "coverage", "unknown"])
def test_invalid_proposal(packet, change):
    proposal = json.loads(packet[1].read_text())
    if change == "quote":
        proposal["claims"][0]["source_refs"][0]["quote"] = "not present"
    elif change == "duplicate":
        proposal["claims"].append(copy.deepcopy(proposal["claims"][0]))
    elif change == "coverage":
        proposal["coverage_notes"][1]["source_ref"] = "R01"
    else:
        proposal["claims"][0]["concern_ids"] = ["Q99"]
    write_json(packet[1], proposal)
    with pytest.raises(ValueError):
        build_trial_task(*packet)


def test_edit_split_merge_delete_binds_current_passages(packet):
    task = build_trial_task(*packet)
    text = "C001 | unassigned | R02-P01\nChanged wording.\n\nC020 | Q1 | R01-P01,R02-P01\nMerged."
    review = normalize(task, annotation(text))
    first, second = review["claims"]
    assert first["source_passages"][0]["text"] == "Another qualified claim."
    assert "quote" not in first["source_passages"][0]
    assert first["proposal_local_id"] == "C001"
    assert second["proposal_local_id"] is None
    assert len(second["source_passages"]) == 2
    original = normalize(task, annotation(task["data"]["proposal_text"]))
    assert first["claim_id"] != original["claims"][0]["claim_id"]
    assert normalize(task, annotation(text))["claims"] == review["claims"]
    assert len(normalize(task, annotation("C020 | Q1 | R01-P01\nOnly remaining."))["claims"]) == 1


@pytest.mark.parametrize(
    "text",
    [
        "",
        "Just text",
        "C001 | Q99 | R01-P01\nClaim",
        "C001 | Q1 | missing\nClaim",
        "C001 | Q1 | R01-P01\n",
        "C001 | Q1 | R01-P01\nA\n\nC001 | Q1 | R01-P01\nB",
    ],
)
def test_malformed_approval_rejected_unresolved_preserved(packet, text):
    task = build_trial_task(*packet)
    with pytest.raises(ValueError):
        normalize(task, annotation(text))
    for status in ["unclear", "needs_context"]:
        unresolved = normalize(task, annotation(text, status))
        assert unresolved["claims_text"] == text
        assert unresolved["parse_error"]
        assert not unresolved["eligible_for_next_stage"]


@pytest.mark.parametrize(
    "change", ["foreign", "unsaved", "reviewer", "status", "binding", "cancel"]
)
def test_review_identity_and_fields(packet, change):
    task = build_trial_task(*packet)
    review = annotation(task["data"]["proposal_text"])
    if change == "foreign":
        review["task"] = 99
    elif change == "unsaved":
        del review["id"]
    elif change == "reviewer":
        del review["completed_by"]
    elif change == "status":
        review["result"].pop()
    elif change == "binding":
        review["result"][0]["to_name"] = "wrong"
    else:
        review["was_cancelled"] = True
    with pytest.raises(ValueError):
        normalize(task, review)


def test_export_data_must_equal_trusted_packet(packet):
    task = build_trial_task(*packet)
    exported = copy.deepcopy(task)
    exported["id"] = 1
    exported["data"]["claim_input"]["responses"][0]["full_text"] = "Tampered"
    with pytest.raises(ValueError, match="differs"):
        normalize_review(
            exported,
            annotation(task["data"]["proposal_text"]),
            expected_task=task,
            export_lineage="trial",
        )


def test_ambiguous_quote_rejected(packet):
    """A source quote must identify exactly one occurrence, including overlaps."""
    proposal = json.loads(packet[1].read_text())
    proposal["claims"][0]["source_refs"][0]["quote"] = "a"
    write_json(packet[1], proposal)
    with pytest.raises(ValueError, match="exactly once"):
        build_trial_task(*packet)


def test_schema_validation_is_not_bypassed(packet):
    """The sealed schema is enforced before claim-specific validation."""
    drafting, proposal_path = packet
    manifest = json.loads((drafting / "packet_manifest.json").read_text())
    manifest["files"]["proposal.schema.json"] = write_json(
        drafting / "proposal.schema.json", {"type": "object", "required": ["schema_version"]}
    )
    binding = write_json(drafting / "packet_manifest.json", manifest)
    proposal = json.loads(proposal_path.read_text())
    proposal["packet_manifest_sha256"] = binding["sha256"]
    write_json(proposal_path, proposal)
    from jsonschema import ValidationError

    with pytest.raises(ValidationError, match="schema_version"):
        build_trial_task(*packet)


def test_export_lineage_separates_final_ids(packet):
    """The same review in a new export has an explicit distinct identity lineage."""
    task = build_trial_task(*packet)
    saved = annotation(task["data"]["proposal_text"])
    first = normalize(task, saved)
    second = normalize_review(
        {"id": 1, **task}, saved, expected_task=task, export_lineage="another-export"
    )
    assert first["claims"][0]["claim_id"] != second["claims"][0]["claim_id"]


def test_footnote_requires_response_context(packet):
    """Supplementary attribution can accompany but cannot replace response passages."""
    drafting, proposal_path = packet
    source = json.loads((drafting / "claim_input.json").read_text())
    footnote = dict(source["responses"][0]["passages"][0])
    footnote["passage_id"] = "R01-FN75"
    footnote["source_ref"] = "R01"
    source["supplemental_passages"] = [footnote]
    manifest = json.loads((drafting / "packet_manifest.json").read_text())
    manifest["files"]["claim_input.json"] = write_json(drafting / "claim_input.json", source)
    binding = write_json(drafting / "packet_manifest.json", manifest)
    proposal = json.loads(proposal_path.read_text())
    proposal["input_sha256"] = manifest["files"]["claim_input.json"]["sha256"]
    proposal["packet_manifest_sha256"] = binding["sha256"]
    write_json(proposal_path, proposal)
    task = build_trial_task(*packet)
    assert "R01-FN75" in task["data"]["sources_html"]
    with pytest.raises(ValueError, match="not only a supplement"):
        normalize(task, annotation("C001 | Q1 | R01-FN75\nClaim."))
    assert normalize(task, annotation("C001 | Q1 | R01-P01,R01-FN75\nClaim."))["claims"]
    proposal["claims"][0]["source_refs"][0]["passage_id"] = "R01-FN75"
    write_json(proposal_path, proposal)
    with pytest.raises(ValueError, match="not only a supplement"):
        build_trial_task(*packet)


def test_approved_argument_paragraph_breaks_remain_inside_blocks(packet):
    """A multi-paragraph argument is one claim until the next explicit header."""
    task = build_trial_task(*packet)
    first = "The response states a qualified conclusion.\n\nIt supplies supporting context."
    second = "The response makes a different argument.\n\nIt retains its limitation."
    raw = f"C001 | Q1 | R01-P01\n{first}\n\nC002 | Q1 | R02-P01\n{second}"
    reviewed = normalize(task, annotation(raw))
    assert reviewed["claims_text"] == raw
    assert [c["text"] for c in reviewed["claims"]] == [first, second]
    assert reviewed["eligible_for_next_stage"]


def test_bad_header_after_paragraph_is_not_swallowed(packet):
    """An invalid new claim header cannot become a continuation of the prior claim."""
    task = build_trial_task(*packet)
    raw = (
        "C001 | Q1 | R01-P01\nFirst paragraph.\n\nSecond paragraph.\n\n"
        "C2 | Q1 | R02-P01\nOther claim."
    )
    with pytest.raises(ValueError, match="Claims require"):
        normalize(task, annotation(raw))
