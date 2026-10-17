"""Invented evidence packets exercise isolation, complete content and sealed splits."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from test_evidence_only_sources import _release

from er_commons import evidence_only
from er_commons.artifact_io import json_bytes, sha256_bytes
from er_commons.evidence_only_sources import load_evidence_sources


def _source(unit: str = "a", *, role: str = "required_support") -> dict[str, Any]:
    """Provide a complete invented canonical unit with review-only sentinels."""
    return {
        "occurrence_id": f"occ-{unit}",
        "source_id": "source",
        "extraction_id": "ex",
        "canonical_target": {
            "unit_type": "section",
            "unit_id": unit,
            "pages": [4, 5],
            "breadcrumb": [{"heading_text": "Water", "notes": "FORBIDDEN HEADING"}],
            "notes": "FORBIDDEN TARGET",
        },
        "approved_roles": [role],
        "reference_role": "context" if role == "optional_context" else "support",
        "reference_role_basis": "sealed_citation_index",
        "title": "Invented source",
        "edition": "Qualified substitute edition",
        "printed_labels": ["IV-4", "IV-5"],
        "full_source_text": "Complete source text, including units (mg/L) and footnote *.",
        "tables": [],
        "anchors": [{"record_id": f"block-{unit}", "path": "invented.jsonl"}],
        "author_notes": "FORBIDDEN SOURCE",
    }


def _case(sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Keep the reference answer alongside, but outside, target-facing inputs."""
    return {
        "case_id": "D00",
        "split": "dev",
        "question": "What does the evidence support?",
        "sources": [_source()] if sources is None else sources,
        "answer": {"conclusion": "FORBIDDEN CONCLUSION"},
        "supporting_points": ["FORBIDDEN POINT"],
        "official_response": "FORBIDDEN RESPONSE",
    }


def _intake() -> dict[str, Any]:
    """Use exactly the frozen split cardinalities without any real benchmark text."""
    dev, test = [f"D{i:02d}" for i in range(19)], [f"T{i:02d}" for i in range(30)]
    cases = [
        {**_case(), "case_id": case_id, "split": split}
        for split, ids in (("dev", dev), ("test", test))
        for case_id in ids
    ]
    return {
        "dev_case_ids": dev,
        "test_case_ids": test,
        "cases": cases,
        "verification": {"invented": True},
        "release_id": "invented",
        "source_bindings": {},
        "data_root": "/invented",
    }


def test_recursive_allowlist_preserves_table_content_and_continuations() -> None:
    source = _source()
    source["canonical_target"]["unit_type"] = "table"
    source["tables"] = [
        {
            "id": "table-1",
            "caption": "Concentration (mg/L)",
            "table_family_id": "family",
            "cells": [
                {
                    "text": "Concentration (mg/L)",
                    "row_index": 0,
                    "column_index": 0,
                    "is_header": True,
                    "column_span": 2,
                    "notes": "FORBIDDEN CELL",
                }
            ],
            "notes": "FORBIDDEN TABLE",
        },
        {
            "id": "table-2",
            "continuation_of": "table-1",
            "table_family_id": "family",
            "cells": [{"text": "3.2*", "row_index": 0, "column_index": 0}],
        },
    ]
    original = copy.deepcopy(source)
    record, mapping = evidence_only.build_case(_case([source]))
    payload = record["payload"]
    assert "FORBIDDEN" not in json.dumps(payload)
    assert set(payload) == {"question", "passages"}
    passage = payload["passages"][0]
    assert passage["full_source_text"] == source["full_source_text"]
    assert passage["source_id"] == "source"
    assert passage["heading_path"] == ["Water"]
    assert passage["edition"] == "Qualified substitute edition"
    assert passage["physical_pages"] == [4, 5]
    assert passage["printed_labels"] == ["IV-4", "IV-5"]
    assert passage["tables"][0]["cells"][0]["column_span"] == 2
    assert passage["tables"][1]["continuation_of"] == "table-1"
    assert passage["tables"][1]["cells"][0]["text"] == "3.2*"
    assert mapping["passages"][0]["reference_role"] == "support"
    assert source == original


def test_deduplication_canonical_order_and_support_precedence() -> None:
    context, duplicate, later = _source(role="optional_context"), _source(), _source("z")
    duplicate["occurrence_id"] = "second-occurrence"
    first = evidence_only.build_case(_case([later, context, duplicate]))
    assert first == evidence_only.build_case(_case([duplicate, later, context]))
    record, mapping = first
    assert [p["citation_id"] for p in record["payload"]["passages"]] == ["P1", "P2"]
    assert [p["canonical_unit"][-1] for p in mapping["passages"]] == ["a", "z"]
    assert mapping["passages"][0]["reference_role"] == "support"
    assert mapping["passages"][0]["occurrence_ids"] == ["occ-a", "second-occurrence"]
    assert mapping["passages"][0]["approved_roles"] == ["optional_context", "required_support"]


def test_conflicting_duplicates_fail() -> None:
    source, duplicate = _source(), _source()
    duplicate["occurrence_id"] = "other"
    duplicate["full_source_text"] = "Changed text"
    with pytest.raises(ValueError, match="Conflicting duplicate"):
        evidence_only.build_case(_case([source, duplicate]))


@pytest.mark.parametrize(
    "missing",
    [
        "full_source_text",
        "tables",
        "anchors",
        "approved_roles",
        "reference_role",
        "reference_role_basis",
    ],
)
def test_incomplete_sources_fail(missing: str) -> None:
    source = _source()
    source.pop(missing)
    with pytest.raises(ValueError):
        evidence_only.build_case(_case([source]))


def test_publication_is_deterministic_and_split_exact() -> None:
    intake = _intake()
    files = evidence_only.publication_files(intake)
    intake["cases"].reverse()
    assert files == evidence_only.publication_files(intake)
    assert len(files["target/dev.jsonl"].splitlines()) == 19
    assert len(files["target/test.jsonl"].splitlines()) == 30
    assert b"FORBIDDEN" not in files["target/dev.jsonl"]
    intake["cases"].pop()
    with pytest.raises(ValueError, match="membership"):
        evidence_only.publication_files(intake)


def test_publish_resumes_exact_partial_writes_and_seals_last(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    files = evidence_only.publication_files(_intake())
    output = tmp_path / "published"
    (output / "target").mkdir(parents=True)
    (output / "target/dev.jsonl").write_bytes(files["target/dev.jsonl"])
    written = []
    original = evidence_only.publish_bytes_no_clobber

    def capture(path: Path, content: bytes) -> Any:
        """Record write ordering while preserving the real no-clobber publisher."""
        written.append(path.name)
        return original(path, content)

    monkeypatch.setattr(evidence_only, "publish_bytes_no_clobber", capture)
    evidence_only.publish_files(output, files)
    assert written[-1] == "completion.json"
    assert all((output / name).read_bytes() == content for name, content in files.items())
    evidence_only.publish_files(output, files)


def test_changed_input_is_rejected_before_any_publication_write(tmp_path: Path) -> None:
    files = evidence_only.publication_files(_intake())
    output = tmp_path / "published"
    evidence_only.publish_files(output, files)
    changed = dict(files)
    changed["target/test.jsonl"] = b"changed\n"
    (output / "target/dev.jsonl").unlink()
    with pytest.raises(FileExistsError, match="changed output"):
        evidence_only.publish_files(output, changed)
    assert not (output / "target/dev.jsonl").exists()
    assert (output / "target/test.jsonl").read_bytes() == files["target/test.jsonl"]


def test_default_loader_never_reads_test_packets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence_only.publish_files(tmp_path, evidence_only.publication_files(_intake()))
    original = Path.open

    def guarded(path: Path, *args: Any, **kwargs: Any) -> Any:
        """Reject any attempted opening of the held-out target dataset."""
        assert path != tmp_path / "target/test.jsonl"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    records = evidence_only.load_records(tmp_path)
    assert [row["case_id"] for row in records] == _intake()["dev_case_ids"]


@pytest.mark.parametrize("name", ["target/dev.jsonl", "evaluator/dev_mappings.jsonl"])
def test_published_byte_tampering_fails_validation(tmp_path: Path, name: str) -> None:
    evidence_only.publish_files(tmp_path, evidence_only.publication_files(_intake()))
    path = tmp_path / name
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="Bound size changed"):
        evidence_only.validate_publication(tmp_path)
    if name == "target/dev.jsonl":
        with pytest.raises(ValueError, match="Bound size changed"):
            evidence_only.load_records(tmp_path)


def test_rebuild_rejects_coherently_resealed_mapping_tampering(tmp_path: Path) -> None:
    pointer = _release(tmp_path / "release")
    intake = load_evidence_sources(pointer, tmp_path)
    output = tmp_path / "publication"
    evidence_only.publish_files(output, evidence_only.publication_files(intake))
    assert evidence_only.validate_publication(output)["case_count"] == 49
    path = output / "evaluator/dev_mappings.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["passages"][0]["canonical_unit"][-1] = "wrong-section"
    path.write_bytes(b"".join(json_bytes(row) for row in rows))
    seal_path = output / "completion.json"
    seal = json.loads(seal_path.read_text())
    for binding in seal["inventory"]:
        if binding["path"] == "evaluator/dev_mappings.jsonl":
            binding["sha256"] = sha256_bytes(path.read_bytes())
            binding["byte_size"] = path.stat().st_size
    seal_path.write_bytes(json_bytes(seal))
    with pytest.raises(ValueError, match="differs from rebuilt inputs"):
        evidence_only.validate_publication(output)


def test_sealed_index_role_preserves_legacy_role_lists() -> None:
    """The verified release index owns final roles even when old lists are empty."""
    source = _source()
    source["approved_roles"] = []
    source["reference_role"] = "support"
    record, mapping = evidence_only.build_case(_case([source]))
    assert mapping["passages"][0]["reference_role"] == "support"
    assert mapping["passages"][0]["approved_roles"] == []
    assert "reference_role" not in json.dumps(record["payload"])


def test_distinct_approved_scopes_share_canonical_unit_without_losing_text() -> None:
    """Keep both approved views when one table ID covers section and footnote scopes."""
    first, second = _source(), _source()
    second["occurrence_id"] = "other-scope"
    second["anchors"] = [{"record_id": "different-block", "path": "invented.jsonl"}]
    second["full_source_text"] = "Additional approved context and footnotes."
    record, mapping = evidence_only.build_case(_case([first, second]))
    assert len(record["payload"]["passages"]) == 2
    assert {p["full_source_text"] for p in record["payload"]["passages"]} == {
        first["full_source_text"],
        second["full_source_text"],
    }
    assert mapping["passages"][0]["canonical_unit"] == mapping["passages"][1]["canonical_unit"]
    assert evidence_only.build_case(_case([second, first])) == (record, mapping)


def test_loader_rejects_duplicate_inventory_paths(tmp_path: Path) -> None:
    """A malformed seal must not silently replace an earlier inventory binding."""
    evidence_only.publish_files(tmp_path, evidence_only.publication_files(_intake()))
    path = tmp_path / "completion.json"
    seal = json.loads(path.read_text())
    seal["inventory"].append(dict(seal["inventory"][0]))
    path.write_bytes(json_bytes(seal))
    with pytest.raises(ValueError, match="Duplicate output inventory path"):
        evidence_only.load_records(tmp_path)
    with pytest.raises(ValueError, match="Duplicate output inventory path"):
        evidence_only.validate_publication(tmp_path)
