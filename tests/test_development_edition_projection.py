"""Offline edition mapping, source fidelity, leakage and identity boundaries."""

import copy
from typing import Any

import pytest

from er_commons.artifact_io import stable_json_sha256
from er_commons.development_edition_projection import build_mapping, project_item
from er_commons.point_grounding import validate_input


def fixture() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Invent an already delivered source and legacy pending G item."""
    passage = {
        "citation_id": "P1",
        "source_id": "invented",
        "title": "Invented appendix",
        "heading_path": ["Scenario"],
        "edition": (
            "2026 Final EIR Appendix F.1 "
            "(accepted qualified substitute; no Draft-equivalence assumed)"
        ),
        "full_source_text": "  Invented source wording.\n",
        "tables": [],
        "physical_pages": [3],
        "printed_labels": ["B-3"],
    }
    record = {
        "schema_version": "task10.evidence_only.v1",
        "case_id": "C014",
        "payload": {"question": "Invented question?", "passages": [passage]},
    }
    annotations = {
        "P1": {
            "bibliography": {"year": 2026, "document_kind": "Final EIR", "appendix": "F.1"},
            "curation_qualification": "accepted qualified substitute; no Draft-equivalence assumed",
        }
    }
    source = {
        k: copy.deepcopy(passage[k])
        for k in [
            "source_id",
            "title",
            "full_source_text",
            "tables",
            "physical_pages",
            "printed_labels",
        ]
    }
    source.update(
        occurrence_id="P1",
        canonical_target={
            "unit_type": "section",
            "unit_id": "invented-section",
            "extraction_id": "invented-extraction",
            "breadcrumb": [{"heading_text": "Scenario"}],
        },
    )
    identity = {
        "case_id": "C014",
        "candidate_sha256": "a" * 64,
        "request_sha256": "b" * 64,
        "run_id": "c" * 64,
        "repeat": 1,
        "attempt": 1,
    }
    identity["candidate_id"] = stable_json_sha256(identity)
    key = {"identity": identity, "component": "G", "point_id": "S1"}
    packet = {
        "question": record["payload"]["question"],
        "point_text": "The appendix is a Final EIR source.",
        "evidence": [source],
    }
    item = {
        **key,
        "sample_id": stable_json_sha256(key),
        "packet": packet,
        "payload_sha256": stable_json_sha256(packet),
        "status": "not_run",
        "group": "supporting_points",
        "supported": None,
        "error_type": None,
        "citation_ids": ["P1"],
        "unresolved_citation_ids": [],
    }
    return record, annotations, item


def rehash(item: dict[str, Any]) -> None:
    """Keep a changed fixture's legacy hashes valid to test deeper guards."""
    item["payload_sha256"] = stable_json_sha256(item["packet"])
    item["sample_id"] = stable_json_sha256(
        {k: item[k] for k in ("identity", "component", "point_id")}
    )


def test_only_bibliographic_locator_changes_and_originals_unchanged() -> None:
    """Source bytes, point scope and originals survive; curation never enters G."""
    record, annotations, item = fixture()
    mapping = build_mapping(record, annotations)
    originals = copy.deepcopy((record, annotations, mapping, item))
    projected = project_item(item, record, mapping)
    assert (record, annotations, mapping, item) == originals
    packet = projected["packet"]
    assert packet["evidence"][0]["canonical_target"].pop("edition") == "2026 Final EIR Appendix F.1"
    assert packet == item["packet"]
    assert projected["sample_id"] != item["sample_id"]
    assert projected["payload_sha256"] != item["payload_sha256"]
    assert projected["identity"] == item["identity"]
    assert projected["projection"]["mapping_sha256"] == stable_json_sha256(mapping)
    assert projected["projection"]["original_item_sha256"] == stable_json_sha256(item)
    assert validate_input(project_item(item, record, mapping)["packet"])


def test_plain_edition_mapping_and_repeat_identity_separation() -> None:
    """Unqualified labels work without curation; candidate repeat identity stays distinct."""
    record, annotations, item = fixture()
    record["payload"]["passages"][0]["edition"] = "2025 Draft EIR"
    annotations["P1"] = {
        "bibliography": {"year": 2025, "document_kind": "Draft EIR", "appendix": None},
        "curation_qualification": None,
    }
    mapping = build_mapping(record, annotations)
    first = project_item(item, record, mapping)
    item["identity"]["repeat"] = 2
    item["identity"]["candidate_id"] = stable_json_sha256(
        {k: v for k, v in item["identity"].items() if k != "candidate_id"}
    )
    rehash(item)
    second = project_item(item, record, mapping)
    assert first["packet"] == second["packet"]
    assert first["sample_id"] != second["sample_id"]


@pytest.mark.parametrize(
    "change", ["passage_hash", "target_hash", "case", "version", "duplicate", "unknown", "curation"]
)
def test_mapping_tampering_fails(change: str) -> None:
    """Every audited binding and its explicit classification is checked anew."""
    record, annotations, item = fixture()
    mapping = build_mapping(record, annotations)
    if change == "passage_hash":
        mapping["entries"][0]["passage_sha256"] = "bad"
    elif change == "target_hash":
        mapping["target_record_sha256"] = "bad"
    elif change == "case":
        mapping["case_id"] = "C041"
    elif change == "version":
        mapping["schema_version"] = "unregistered"
    elif change == "duplicate":
        mapping["entries"].append(copy.deepcopy(mapping["entries"][0]))
    elif change == "unknown":
        mapping["entries"][0]["expected_label"] = True
    else:
        mapping["entries"][0]["curation_qualification"] = None
    with pytest.raises(ValueError):
        project_item(item, record, mapping)


@pytest.mark.parametrize(
    "kind",
    ["missing", "extra", "mixed", "year_bool", "appendix_prose", "foreign_case", "no_edition"],
)
def test_invalid_or_unmapped_metadata_fails(kind: str) -> None:
    """No implicit splitting, coercion, fallback or unselected case is allowed."""
    record, annotations, _ = fixture()
    if kind == "missing":
        annotations.clear()
    elif kind == "extra":
        annotations["P2"] = copy.deepcopy(annotations["P1"])
    elif kind == "mixed":
        annotations["P1"]["bibliography"]["document_kind"] = "Final EIR accepted"
    elif kind == "year_bool":
        annotations["P1"]["bibliography"]["year"] = True
    elif kind == "appendix_prose":
        annotations["P1"]["bibliography"]["appendix"] = "F.1 (accepted)"
    elif kind == "foreign_case":
        record["case_id"] = "C999"
    else:
        record["payload"]["passages"][0].pop("edition")
    with pytest.raises(ValueError):
        build_mapping(record, annotations)


@pytest.mark.parametrize(
    "kind",
    [
        "text",
        "table",
        "heading",
        "question",
        "source_id",
        "unmapped",
        "locator_leak",
        "packet_leak",
        "item_leak",
        "verdict",
        "stale_error",
        "citation_mismatch",
        "old_payload",
        "candidate_id",
    ],
)
def test_input_fidelity_and_leakage_fail_closed(kind: str) -> None:
    """Do not launder changed evidence, extra judge context or stale verdicts."""
    record, annotations, item = fixture()
    mapping = build_mapping(record, annotations)
    source = item["packet"]["evidence"][0]
    if kind == "text":
        source["full_source_text"] += "altered"
    elif kind == "table":
        source["tables"] = [{"expected_label": True}]
    elif kind == "heading":
        source["canonical_target"]["breadcrumb"][0]["heading_text"] = "changed"
    elif kind == "question":
        item["packet"]["question"] = "changed"
    elif kind == "source_id":
        source["source_id"] = "another"
    elif kind == "unmapped":
        source["occurrence_id"] = "P2"
    elif kind == "locator_leak":
        source["canonical_target"]["approved"] = True
    elif kind == "packet_leak":
        item["packet"]["reference_answer"] = "forbidden"
    elif kind == "item_leak":
        item["raw_output"] = "saved judgment"
    elif kind == "verdict":
        item["supported"] = True
    elif kind == "stale_error":
        item["error_type"] = "old failure"
    elif kind == "citation_mismatch":
        item["citation_ids"] = ["P1", "P2"]
    elif kind == "candidate_id":
        item["identity"]["candidate_id"] = "d" * 64
    rehash(item)
    if kind == "old_payload":
        item["payload_sha256"] = "bad"
    with pytest.raises(ValueError):
        project_item(item, record, mapping)


def test_frozen_input_validator_still_rejects_top_level_edition() -> None:
    """Adapter uses an existing locator slot, not an expanded frozen input allowlist."""
    _, _, item = fixture()
    item["packet"]["evidence"][0]["edition"] = "2025 Draft EIR"
    with pytest.raises(ValueError):
        validate_input(item["packet"])


def test_mapping_identity_changes_even_when_model_payload_does_not() -> None:
    """A different audited qualification cannot reuse the old evaluation identity."""
    record, annotations, item = fixture()
    first = project_item(item, record, build_mapping(record, annotations))
    annotations["P1"]["curation_qualification"] = "distinct audited qualification"
    record["payload"]["passages"][0]["edition"] = (
        "2026 Final EIR Appendix F.1 (distinct audited qualification)"
    )
    second = project_item(item, record, build_mapping(record, annotations))
    assert first["packet"] == second["packet"]
    assert first["payload_sha256"] == second["payload_sha256"]
    assert first["sample_id"] != second["sample_id"]
    assert first["projection"]["mapping_sha256"] != second["projection"]["mapping_sha256"]
