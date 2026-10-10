"""Judge qualification must preserve content while blocking label leakage."""

import json
from pathlib import Path

import pytest

from er_commons.judge_qualification_packets import project_payload, selected_rows


def packet() -> dict:
    """Create deliberately revealing IDs and metadata at every projection boundary."""
    answer = {
        "status": "answered",
        "conclusion": {
            "point_id": "F01-contradiction",
            "text": "Exact claim.",
            "citation_ids": ["O1"],
            "expected_score": 0,
        },
        "supporting_points": [],
        "qualifications": [
            {
                "point_id": "O02-omission",
                "text": "Exact caveat.",
                "citation_ids": ["O1"],
                "applies_to": ["F01-contradiction"],
            }
        ],
        "optional_context": [],
        "synthetic_expectation": "SECRET",
    }
    return {
        "question": "Which limit?",
        "reference_answer": answer,
        "sources": [
            {
                "occurrence_id": "O1",
                "source_id": "deir",
                "full_source_text": "Exact source.\n5 mg/L",
                "role": "gold",
                "approved_roles": ["support"],
                "tables": [{"cells": [{"text": "5", "column_index": 0, "row_index": 0}]}],
            },
            {
                "occurrence_id": "O2",
                "source_id": "deir",
                "full_source_text": "Reference-only evidence",
                "tables": [],
            },
        ],
    }


def test_separate_boundaries_and_exact_content() -> None:
    """Grounding excludes uncited reference evidence and anonymizes attachments."""
    source = packet()
    grounding = project_payload(source, source["reference_answer"], "grounding")
    adequacy = project_payload(source, source["reference_answer"], "adequacy")
    assert "reference_answer" not in grounding
    assert len(grounding["evidence"]) == 1
    assert len(adequacy["evidence"]) == 2
    for projected in (grounding, adequacy):
        serialized = json.dumps(projected)
        for secret in (
            "F01-contradiction",
            "O02-omission",
            "expected_score",
            "SECRET",
            "approved_roles",
            '"gold"',
        ):
            assert secret not in serialized
        assert projected["answer"]["qualifications"][0]["applies_to"] == ["P1"]
        assert projected["evidence"][0]["full_source_text"] == "Exact source.\n5 mg/L"
        assert projected["evidence"][0]["tables"] == source["sources"][0]["tables"]
    assert source["reference_answer"]["conclusion"]["point_id"] == "F01-contradiction"


def test_unresolved_citation_not_repaired() -> None:
    """A defect remains unresolved without carrying its revealing synthetic ID."""
    source = packet()
    source["reference_answer"]["conclusion"]["citation_ids"] = ["F10-FAKE"]
    result = project_payload(source, source["reference_answer"], "grounding")
    citation = result["answer"]["conclusion"]["citation_ids"][0]
    assert citation not in {s["citation_id"] for s in result["evidence"]}
    assert "F10-FAKE" not in json.dumps(result)


def test_reserved_payload_never_decoded(tmp_path: Path) -> None:
    """Invalid JSON in a nonselected payload proves routing precedes JSON decode."""
    path = tmp_path / "answers.jsonl"
    path.write_text(
        '{"variant_id":"reserved","answer":INVALID JSON}\n'
        '{"variant_id":"allowed","answer":{"text":"safe"}}\n'
    )
    assert selected_rows(path, {"allowed"})["allowed"]["answer"] == {"text": "safe"}


def test_ambiguous_and_missing_routes_fail_closed(tmp_path: Path) -> None:
    """Never guess a routing identity or silently drop a required record."""
    path = tmp_path / "answers.jsonl"
    path.write_text('{"variant_id":"a","variant_id":"b"}\n')
    with pytest.raises(ValueError, match="exactly one"):
        selected_rows(path, {"a"})
    path.write_text('{"variant_id":"b"}\n')
    with pytest.raises(ValueError, match="missing"):
        selected_rows(path, {"a"})


def sealed_fixture(tmp_path: Path) -> Path:
    """Create a minimal sealed intake with forbidden payloads deliberately undecodable."""
    from er_commons.artifact_io import file_reference, json_bytes

    root = tmp_path / "source"
    batch = root / "batch"
    published = batch / "published"
    published.mkdir(parents=True)
    artifacts = {}

    def write(path: Path, value: object) -> dict:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(json_bytes(value))
        return file_reference(path, root=root)

    ids = [f"C041-dev-{i}" for i in range(423)]
    reservation = {
        "development_variant_ids": ids,
        "final_check_variant_ids": [f"reserved-{i}" for i in range(118)],
        "excluded_variant_ids": [f"excluded-{i}" for i in range(5)],
    }
    artifacts["reservation.json"] = write(published / "reservation.json", reservation)
    expectations = [
        {
            "variant_id": identity,
            "case_id": "C041",
            "comparison_eligible": True,
            "grounding": {"score": 0},
            "adequacy": {"score": 0},
        }
        for identity in ids
    ]
    path = published / "expectations.jsonl"
    path.write_bytes(b"".join(json_bytes(r) for r in expectations))
    artifacts["expectations.jsonl"] = file_reference(path, root=root)
    path = published / "answers.jsonl"
    path.write_bytes(
        json_bytes(
            {"variant_id": ids[0], "case_id": "C041", "answer": packet()["reference_answer"]}
        )
        + b'{"variant_id":"reserved-0","answer":INVALID JSON}\n'
    )
    artifacts["answers.jsonl"] = file_reference(path, root=root)
    case_ids = ["C041", "C037", "C014", *[f"dev{i}" for i in range(16)]]
    write(batch / "prepared.json", {"case_ids": case_ids})
    for case in case_ids[:3]:
        write(batch / "cases" / case / "input.json", {"case_id": case, **packet()})
    inventory = [file_reference(p, root=batch) for p in batch.rglob("*") if p.is_file()]
    completion = write(batch / "completion.json", {"inventory": {"files": inventory}})
    completion["path"] = str(root / completion["path"])
    for value in artifacts.values():
        value["path"] = str(root / value["path"])
    pointer = tmp_path / "result.json"
    pointer.write_bytes(
        json_bytes(
            {
                "status": "complete_with_limitations",
                "namespace": str(root),
                "batch_completion": completion,
                "artifacts": artifacts,
            }
        )
    )
    return pointer


def test_sealed_prepare_and_identical_resume(tmp_path: Path) -> None:
    """Full preparation is deterministic and never parses reserved answer content."""
    from er_commons.judge_qualification_packets import prepare_packets

    pointer = sealed_fixture(tmp_path)
    output = tmp_path / "output"
    first = prepare_packets(pointer, output)
    assert first == prepare_packets(pointer, output)
    assert first["packet_count"] == 8
    packets = json.loads((output / "packets.json").read_text())
    assert {p["size"] for p in packets} == {"short", "typical", "large", "contrast"}
    assert all("synthetic_expectation" not in json.dumps(p["payload"]) for p in packets)
    (output / "packets.json").write_text("corrupted")
    with pytest.raises(FileExistsError):
        prepare_packets(pointer, output)


def test_tampered_source_rejected_before_publication(tmp_path: Path) -> None:
    """A changed allowed source cannot inherit the seal or publish a new projection."""
    from er_commons.judge_qualification_packets import prepare_packets

    pointer = sealed_fixture(tmp_path)
    (tmp_path / "source/batch/cases/C041/input.json").write_text("changed")
    with pytest.raises(ValueError, match="size changed"):
        prepare_packets(pointer, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_comparison_gate_precedes_answer_access(tmp_path: Path) -> None:
    """A reservation entry is insufficient when the independent comparison flag excludes it."""
    from er_commons.artifact_io import file_reference, json_bytes
    from er_commons.judge_qualification_packets import prepare_packets

    pointer = sealed_fixture(tmp_path)
    result = json.loads(pointer.read_text())
    path = Path(result["artifacts"]["expectations.jsonl"]["path"])
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["comparison_eligible"] = False
    path.write_bytes(b"".join(json_bytes(row) for row in rows))
    result["artifacts"]["expectations.jsonl"] = {
        **file_reference(path, root=path.parent),
        "path": str(path),
    }
    # An invalid answer binding proves the exclusion check ran before answer access.
    result["artifacts"]["answers.jsonl"]["path"] = str(tmp_path / "absent")
    pointer.write_bytes(json_bytes(result))
    with pytest.raises(ValueError, match="comparison exclusion"):
        prepare_packets(pointer, tmp_path / "output")


def test_nested_canonical_provenance_is_not_model_input() -> None:
    """Canonical source locators retain meaning without nested pipeline metadata."""
    source = packet()
    source["sources"][0]["canonical_target"] = {
        "unit_id": "unit-1",
        "citation_label": "Table 1",
        "pages": [7],
        "receipt_ref": {"path": "SECRET_REVIEW_PATH", "sha256": "SECRET_HASH"},
        "breadcrumb": [{"heading_text": "Water", "heading_block_id": "SECRET_BLOCK"}],
        "figure_refs": [
            {
                "record_id": "figure-1",
                "interpretation": "not_evaluated_as_text_evidence",
                "path": "SECRET_FIGURE_PATH",
                "record": {"raw_links": "SECRET_RAW"},
            }
        ],
    }
    projected = project_payload(source, source["reference_answer"], "grounding")
    assert "SECRET" not in json.dumps(projected)
    target = projected["evidence"][0]["canonical_target"]
    assert target["citation_label"] == "Table 1"
    assert target["pages"] == [7]
    assert target["breadcrumb"] == [{"heading_text": "Water"}]
    assert target["figure_refs"] == [
        {"record_id": "figure-1", "interpretation": "not_evaluated_as_text_evidence"}
    ]
    assert projected["evidence"][0]["tables"] == source["sources"][0]["tables"]
    assert projected["evidence"][0]["full_source_text"] == source["sources"][0]["full_source_text"]
