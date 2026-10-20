"""Invented-only offline context isolation and immutable evidence fixtures."""

import copy
import json
from typing import Any

import pytest
from test_target_generation import packet

from er_commons import context_projection as cp
from er_commons.artifact_io import stable_json_sha256 as digest


def fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    record = packet()
    record["payload"]["question"] = "How does the DEIR address 2100 flooding?"
    p = record["payload"]["passages"][0]
    p["edition"] = "2026 Final EIR (accepted qualified substitute; no Draft-equivalence assumed)"
    p["full_source_text"] += " The 2025 Draft EIR predicts 2100 flooding of 1.2 feet."
    p["heading_path"] = ["Section 7: Year 2100 conditions"]
    labels = {
        "P1": {
            "document": "EIR Appendix F.1",
            "title": p["title"],
            "heading_path": p["heading_path"],
        }
    }
    return record, cp.build_locator_map(record, labels)


def item(component: str, record: dict[str, Any]) -> dict[str, Any]:
    identity = {
        "run_id": "a" * 64,
        "case_id": "C041",
        "attempt": 1,
        "repeat": 1,
        "request_sha256": "b" * 64,
        "candidate_sha256": "c" * 64,
    }
    identity["candidate_id"] = digest(identity)
    p = record["payload"]["passages"][0]
    question = record["payload"]["question"]
    payloads = {
        "A": {"candidate_conclusion": "An invented answer."},
        "G": {
            "question": question,
            "point_text": "The old Draft EIR claim remains unchanged.",
            "evidence": [
                {
                    "occurrence_id": "P1",
                    "source_id": p["source_id"],
                    "canonical_target": {
                        "unit_type": "section",
                        "unit_id": "unit1",
                        "extraction_id": "extract1",
                        "breadcrumb": [{"heading_text": h} for h in p["heading_path"]],
                        "edition": p["edition"],
                    },
                    **{
                        k: copy.deepcopy(p[k])
                        for k in (
                            "title",
                            "full_source_text",
                            "tables",
                            "physical_pages",
                            "printed_labels",
                        )
                    },
                }
            ],
        },
        "S": {
            "question": question,
            "candidate_conclusion": "An invented answer.",
            "candidate_supporting_points": [{"point_id": "S1", "text": "A premise."}],
            "candidate_qualifications": [],
        },
        "C": {
            "question": question,
            "candidate_conclusion": "An invented answer.",
            "reference_conclusion": "The DEIR supplies a secret gold detail.",
        },
    }
    point = "S1" if component == "G" else None
    key = {"identity": identity, "component": component, "point_id": point}
    return {
        **key,
        "sample_id": digest(key),
        "payload_sha256": digest(payloads[component]),
        "packet": payloads[component],
        "status": "not_run",
        **({"citation_ids": ["P1"], "supported": None} if component == "G" else {}),
    }


def test_all_contexts_same_summary_no_target_gold() -> None:
    record, mapping = fixture()
    original = copy.deepcopy(record)
    summary = "A proposed mixed-use development in Brisbane."
    target = cp.project_target(record, mapping, summary=summary, prompt="Target instructions.")
    envelopes = [target]
    for component in ("A", "G", "S", "C"):
        prior = item(component, record)
        envelopes.append(
            cp.project_judge(prior, record, mapping, summary=summary, prompt="Frozen " + component)
        )
        assert envelopes[-1]["context_id"] != prior["sample_id"]
        assert envelopes[-1]["status"] == "not_run"
    prefix = "<project_context>\n" + summary + "\n</project_context>\n\n"
    assert all(e["messages"][0]["content"].startswith(prefix) for e in envelopes)
    assert len({e["identity"]["summary_sha256"] for e in envelopes}) == 1
    assert "secret gold detail" not in json.dumps(target["messages"])
    assert record == original
    p = target["payload"]["passages"][0]
    assert "edition" not in p
    assert p["title"].startswith("EIR Appendix F.1:")
    assert p["full_source_text"] == record["payload"]["passages"][0]["full_source_text"]
    assert p["tables"] == record["payload"]["passages"][0]["tables"]
    assert "2025 Draft EIR predicts 2100" in p["full_source_text"]
    assert target["payload"]["question"] == "How does the EIR address 2100 flooding?"
    ground = envelopes[2]["payload"]["evidence"][0]
    assert "edition" not in ground["canonical_target"]
    assert ground["canonical_target"]["unit_id"] == "unit1"
    assert ground["full_source_text"] == p["full_source_text"]
    assert ground["tables"] == p["tables"]
    assert envelopes[2]["payload"]["point_text"] == "The old Draft EIR claim remains unchanged."


def test_c_reference_derivative_is_explicit_and_bound() -> None:
    record, mapping = fixture()
    prior = item("C", record)
    reference = {
        "original_reference_sha256": digest(prior["packet"]["reference_conclusion"]),
        "reference_conclusion": "The EIR supplies a secret gold detail.",
        "publication_sha256": "d" * 64,
    }
    projected = cp.project_judge(
        prior, record, mapping, summary="Context.", prompt="Frozen.", reference=reference
    )
    assert projected["payload"]["reference_conclusion"] == reference["reference_conclusion"]
    assert prior["packet"]["reference_conclusion"].startswith("The DEIR")
    reference["original_reference_sha256"] = "e" * 64
    with pytest.raises(ValueError, match="original"):
        cp.project_judge(
            prior, record, mapping, summary="Context.", prompt="Frozen.", reference=reference
        )


@pytest.mark.parametrize("component", ["A", "G", "S"])
def test_reference_cannot_enter_other_components(component: str) -> None:
    record, mapping = fixture()
    with pytest.raises(ValueError, match="Reference leakage"):
        cp.project_judge(
            item(component, record),
            record,
            mapping,
            summary="Context.",
            prompt="Frozen.",
            reference={},
        )


@pytest.mark.parametrize("mutation", ["source", "mapping", "label"])
def test_stale_or_unsafe_mapping_rejected(mutation: str) -> None:
    record, mapping = fixture()
    if mutation == "source":
        record["payload"]["passages"][0]["tables"][0]["cells"][0]["text"] = "CHANGED"
    elif mutation == "mapping":
        mapping["entries"][0]["original_locator"]["edition"] = "changed"
    else:
        mapping["entries"][0]["neutral"]["title"] = "2026 Final EIR"
    with pytest.raises(ValueError):
        cp.project_target(record, mapping, summary="Context.", prompt="Prompt.")


@pytest.mark.parametrize("mutation", ["verdict", "payload", "ownership", "extra"])
def test_unsafe_judge_input_rejected(mutation: str) -> None:
    record, mapping = fixture()
    prior = item("G", record)
    if mutation == "verdict":
        prior["supported"] = True
    elif mutation == "payload":
        prior["packet"]["point_text"] = "changed"
    elif mutation == "ownership":
        prior["citation_ids"] = ["P2"]
    else:
        prior["feedback"] = "SECRET"
    with pytest.raises(ValueError):
        cp.project_judge(prior, record, mapping, summary="Context.", prompt="Prompt.")


def test_identity_binds_context_and_prompt() -> None:
    record, mapping = fixture()
    a = cp.project_target(record, mapping, summary="First.", prompt="Prompt.")
    b = cp.project_target(record, mapping, summary="Second.", prompt="Prompt.")
    c = cp.project_target(record, mapping, summary="First.", prompt="Changed.")
    assert len({a["context_id"], b["context_id"], c["context_id"]}) == 3


def test_question_transform_preserves_scenario_facts() -> None:
    assert (
        cp.neutral_question("2025 Draft EIR and FEIR project 6.9 feet by 2100.")
        == "EIR and EIR project 6.9 feet by 2100."
    )


def test_reference_publication_changes_identity_not_messages() -> None:
    record, mapping = fixture()
    prior = item("C", record)
    reference = {
        "original_reference_sha256": digest(prior["packet"]["reference_conclusion"]),
        "reference_conclusion": "The EIR supplies a secret gold detail.",
        "publication_sha256": "d" * 64,
    }
    first = cp.project_judge(
        prior, record, mapping, summary="Context.", prompt="Frozen.", reference=reference
    )
    reference["publication_sha256"] = "e" * 64
    second = cp.project_judge(
        prior, record, mapping, summary="Context.", prompt="Frozen.", reference=reference
    )
    assert first["messages"] == second["messages"]
    assert first["context_id"] != second["context_id"]
    assert first["identity"]["private_provenance_sha256"] == digest(first["private_provenance"])


def test_question_normalization_absorbs_nested_edition_acronyms() -> None:
    for text in ("Draft DEIR", "Final FEIR", "2025 Draft DEIR", "2026 Final DEIR"):
        neutral = cp.neutral_question(text + " scenario 2100, final grading within 2 years.")
        assert neutral == "EIR scenario 2100, final grading within 2 years."
        assert cp.neutral_question(neutral) == neutral
