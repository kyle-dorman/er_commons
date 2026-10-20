"""Source-free checks for sealed reporting inputs and canonical complexity counts."""

import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.artifact_io import sha256_bytes
from er_commons.reporting_counts import citation_complexity, response_unit_counts
from er_commons.reporting_inputs import SealedInputs


def test_sealed_inputs_detect_tampering_and_duplicate_inventory(tmp_path: Path) -> None:
    """Changed bytes or ambiguous manifests cannot silently become reporting evidence."""
    content = b'{"case_id":"invented"}'
    (tmp_path / "record.json").write_bytes(content)
    row = {"path": "record.json", "sha256": sha256_bytes(content), "byte_size": len(content)}
    inputs = SealedInputs(tmp_path, {"files": [row]})
    assert inputs.json("record.json") == {"case_id": "invented"}
    (tmp_path / "record.json").write_bytes(b'{"case_id":"modified"}')
    with pytest.raises(ValueError, match="mismatch"):
        inputs.json("record.json")
    with pytest.raises(ValueError, match="Duplicate"):
        SealedInputs(tmp_path, {"files": [row, row]})
    with pytest.raises(ValueError, match="Unsealed"):
        inputs.read("other.json")


def test_sealed_inputs_reject_escaping_paths_and_duplicate_json(tmp_path: Path) -> None:
    """Path traversal and duplicate JSON values are integrity errors."""
    with pytest.raises(ValueError, match="escaping"):
        SealedInputs(tmp_path, {"files": [{"path": "../outside.json"}]})
    content = b'{"repeat":1,"repeat":2}'
    (tmp_path / "record.json").write_bytes(content)
    inputs = SealedInputs(
        tmp_path,
        {
            "files": [
                {"path": "record.json", "sha256": sha256_bytes(content), "byte_size": len(content)}
            ]
        },
    )
    with pytest.raises(ValueError, match="Duplicate JSON"):
        inputs.json("record.json")


def _automatic(ids: list[str]) -> dict[str, Any]:
    """Model complete-answer citation attempts including repeated and unresolved tokens."""
    return {
        "delivery": "exact_payload_verified",
        "citation_attempts": [
            {
                "raw": cid,
                "token": f"str:{cid}",
                "status": "invalid" if cid == "BAD" else "resolved",
            }
            for cid in ids
        ],
    }


def test_complexity_separates_citation_occurrences_and_distinct_response_units() -> None:
    """Distinct canonical units include conclusion/context citations but not repeated aliases."""
    section = ["doc", "extract", "section", "stable-section"]
    table = ["doc", "extract", "table", "stable-table"]
    mapping = {
        "passages": [
            {"citation_id": "P1", "canonical_unit": section},
            {"citation_id": "P2", "canonical_unit": section},
            {"citation_id": "P3", "canonical_unit": table},
        ]
    }
    result = citation_complexity(_automatic(["P1", "P1", "P2", "P3", "BAD", "BAD"]), mapping)
    assert result["citation_occurrences"] == 6
    assert result["resolved_citation_occurrences"] == 4
    assert result["invalid_citation_occurrences"] == 2
    assert result["response_units"] == 2
    assert result["sections"] == result["tables"] == result["documents"] == 1
    assert result["input_citations"] == 2
    assert result["input_sections"] == result["input_tables"] == 1
    assert result["input_response_units"] == 2
    assert result["invalid_ids"] == ["str:BAD"]
    assert result["delivery_coverage"] == 1.0
    result = citation_complexity(_automatic(["P3"]), mapping)
    assert result["sections"] == 0
    assert result["tables"] == result["response_units"] == 1
    assert result["citation_occurrences"] == 1
    assert json.loads(json.dumps(result))["canonical_units"] == [table]


def test_empty_citations_and_missing_delivery_are_distinct() -> None:
    """An empty complete citation list has zero units; absent delivery is not zero coverage."""
    result = citation_complexity({"citation_attempts": []}, {"passages": []})
    assert result["citation_occurrences"] == result["response_units"] == result["documents"] == 0
    assert result["delivery_coverage"] is None


def test_saved_unit_recount_preserves_occurrences_and_canonical_identity() -> None:
    """Persisted unit lists replay the same counts without reopening source content."""
    section = ["doc", "extract", "section", "same-heading"]
    table = ["doc", "extract", "table", "same-heading"]
    other_document = ["other-doc", "extract", "section", "same-heading"]
    attempts = _automatic(["P1", "P1", "P2", "P3"])["citation_attempts"]
    result = response_unit_counts(
        [section, table, other_document, section], [section, table, other_document], attempts
    )
    assert result["response_units"] == 3
    assert result["citation_occurrences"] == result["resolved_citation_occurrences"] == 4
    assert result["documents"] == result["sections"] == 2
    assert result["tables"] == 1
    assert result["invalid_citation_occurrences"] == 0


def test_unavailable_and_ambiguous_attempts_are_not_invalid() -> None:
    """Resolution failures retain their distinct statuses instead of inventing invalid links."""
    attempts = [
        {"status": status, "token": f"str:{status}"}
        for status in ("resolved", "invalid", "ambiguous", "unavailable")
    ]
    result = response_unit_counts([], [], attempts)
    assert result["citation_occurrences"] == 4
    assert result["resolved_citation_occurrences"] == 1
    assert result["unresolved_citation_occurrences"] == 3
    assert result["invalid_citation_occurrences"] == 1
    assert result["ambiguous_citation_occurrences"] == 1
    assert result["unavailable_citation_occurrences"] == 1
    assert result["invalid_ids"] == ["str:invalid"]
    assert result["invalid_id_count"] == 1


def test_unresolved_citations_do_not_become_invalid_id_failures() -> None:
    """Ambiguous mappings and absent inputs preserve uncertainty in the invalid-ID audit."""
    result = response_unit_counts(
        [],
        [],
        [
            {"status": "ambiguous", "token": "str:P1"},
            {"status": "unavailable", "token": "sentinel", "unextractable": True},
        ],
    )
    assert result["invalid_ids"] == []
    assert result["invalid_id_count"] == 0
    assert result["citation_occurrence_status"] == "unavailable_unextractable"


@pytest.mark.parametrize("raw", [None, {"point_id": "missing-citation-field"}])
def test_unextractable_sentinels_do_not_become_citation_occurrences(raw: Any) -> None:
    """Missing fields and non-point records make totals unavailable, not fabricated citations."""
    attempts = _automatic(["P1"])["citation_attempts"] + [
        {"raw": raw, "status": "unavailable", "token": "sentinel", "unextractable": True}
    ]
    result = response_unit_counts([], [], attempts)
    assert result["citation_occurrences"] is None
    assert result["unavailable_citation_occurrences"] is None
    assert result["citation_occurrence_status"] == "unavailable_unextractable"
    assert result["unextractable_citation_fields"] == 1
    assert result["observed_citation_occurrences"] == 1
    assert result["observed_resolved_citation_occurrences"] == 1
