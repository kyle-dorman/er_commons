"""Invented release fixtures exercise all-split source-only intake and source fidelity."""

import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.artifact_io import json_bytes
from er_commons.evidence_only_sources import _binding, load_evidence_sources
from er_commons.group_answer_intake import _compact_anchors


def _release(
    root: Path,
    *,
    corrupt: str | None = None,
    table: bool = False,
    linked: bool = False,
    omitted_context: bool = False,
) -> Path:
    """Seal 49 invented cases and one canonical section, with answer sentinels."""
    root.mkdir()
    canonical = root.parent / "blocks.jsonl"
    canonical.write_bytes(
        json_bytes(
            {
                "id": "block",
                "extraction_id": "ex",
                "document_id": "ex/document/source",
                "canonical_text": "Complete evidence.",
            }
        )
    )
    citation = {
        "occurrence_id": "occurrence",
        "source_id": "source",
        "extraction_id": "ex",
        "canonical_target": {"unit_type": "section", "unit_id": "section"},
        "approved_roles": ["required_support"],
        "full_source_text": "Complete evidence.",
        "tables": [],
        "title": "Invented source",
        "anchors": [
            {
                "path": str(canonical),
                "record_id": "block",
                "locators": [{"text_field": "canonical_text", "start": 0, "end": 18}],
            }
        ],
        "author_notes": "FORBIDDEN AUTHOR NOTES",
    }
    if omitted_context:
        citation["role"] = "optional_context"
        citation["approved_roles"] = []
    files = {"blocks": _binding(canonical)}
    if table:
        tables_path = root.parent / "tables.jsonl"
        table_record = {
            "id": "ex/table/source/t1",
            "extraction_id": "ex",
            "document_id": "ex/document/source",
            "shape": [2, 2],
            "table_family_id": "family",
            "continuation_of": None,
            "cells": [
                {"text": "Volume (m3)", "row_index": 0, "column_index": 0, "is_header": True},
                {"text": "", "row_index": 0, "column_index": 1, "is_header": True},
                {"text": "12*", "row_index": 1, "column_index": 0, "is_header": False},
                {"text": "24", "row_index": 1, "column_index": 1, "is_header": False},
            ],
        }
        footnote = {
            "id": "note",
            "extraction_id": "ex",
            "document_id": "ex/document/source",
            "canonical_text": "* Annual volume.",
        }
        canonical.write_bytes(canonical.read_bytes() + json_bytes(footnote))
        tables_path.write_bytes(json_bytes(table_record))
        files = {"blocks": _binding(canonical), "tables": _binding(tables_path)}
        expanded = [
            {
                "path": str(canonical),
                "record_id": "block",
                "text_field": "canonical_text",
                "start": 0,
                "end": 18,
            }
        ]
        expanded.extend(
            {
                "path": str(tables_path),
                "record_id": table_record["id"],
                "text_field": f"cells.{i}.text",
                "start": 0,
                "end": len(cell["text"]),
            }
            for i, cell in enumerate(table_record["cells"])
            if cell["text"]
        )
        expanded.append(
            {
                "path": str(canonical),
                "record_id": "note",
                "text_field": "canonical_text",
                "start": 0,
                "end": len(footnote["canonical_text"]),
            }
        )
        citation["anchors"] = _compact_anchors(expanded)
        citation["canonical_target"] = {"unit_type": "table", "unit_id": table_record["id"]}
        citation["full_source_text"] = (
            "Complete evidence.\n\nVolume (m3)\n\n12*\n\n24\n\n* Annual volume."
        )
        citation["tables"] = [
            {
                key: value
                for key, value in table_record.items()
                if key not in {"document_id", "extraction_id"}
            }
        ]
        if corrupt == "table_cell":
            citation["tables"][0]["cells"] = citation["tables"][0]["cells"][:-1]
        if corrupt == "empty_cell_span":
            citation["anchors"][1]["locators"].insert(
                1, {"text_field": "cells.1.text", "start": 0, "end": 0}
            )
    if linked:
        source_path = root.parent / "linked.json"
        source_path.write_bytes(
            json_bytes(
                {
                    "source_id": "source",
                    "extraction_id": "ex",
                    "quote": citation["full_source_text"],
                    "anchors": [
                        {
                            "path": str(canonical),
                            "record_id": "block",
                            "text_field": "canonical_text",
                            "start": 0,
                            "end": 18,
                        }
                    ],
                }
            )
        )
        citation["full_source_ref"] = _binding(source_path)
        del citation["anchors"]
    if corrupt == "text":
        citation["full_source_text"] = "Changed evidence."
    if corrupt == "span":
        citation["anchors"][0]["locators"][0]["end"] = 10
    if corrupt == "corpus":
        citation["extraction_id"] = "wrong"

    def save(name: str, value: Any, *, lines: bool = False) -> dict[str, Any]:
        """Write invented JSON objects and bind their exact bytes."""
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"".join(json_bytes(row) for row in value) if lines else json_bytes(value))
        return _binding(path)

    dev, test = [f"D{i:02d}" for i in range(19)], [f"T{i:02d}" for i in range(30)]
    split = save("split.json", {"status": "approved", "dev": dev, "test": test})
    targets, index = {}, []
    for group, ids in (("dev", dev), ("test", test)):
        targets[group] = save(
            f"target/{group}.jsonl", [{"case_id": c, "question": c} for c in ids], lines=True
        )
        for c in ids:
            ref = save(
                f"curator/{c}.json",
                {
                    "case_id": c,
                    "question": c,
                    "final_disposition": "approved",
                    "answer": {"conclusion": "FORBIDDEN REFERENCE ANSWER"},
                    "citation_occurrences": [citation],
                },
            )
            index.append(
                {
                    "case_id": c,
                    "split": group,
                    "reference_record": f"curator/{c}.json",
                    "reference_sha256": ref["sha256"],
                    "citation_units": []
                    if omitted_context
                    else [
                        {
                            "document_id": "ex/document/source",
                            "unit_id": citation["canonical_target"]["unit_id"],
                            "occurrence_ids": ["occurrence"],
                            "role": "required",
                        }
                    ],
                }
            )
    if corrupt == "index":
        index[0]["citation_units"] = []
    index_ref = save("curator/index.jsonl", index, lines=True)
    corpus = save(
        "corpus.json",
        {
            "documents": [
                {
                    "source_id": "source",
                    "extraction_id": "ex",
                    "files": files,
                }
            ]
        },
    )
    handoff = save(
        "handoff.json",
        {"release_id": "fixture", "artifacts": {"corpus": corpus, "reference_index": index_ref}},
    )
    inventory = [
        {**_binding(p), "path": p.relative_to(root).as_posix()}
        for p in sorted(root.rglob("*"))
        if p.is_file()
    ]
    completion = save("completion.json", {"status": "complete", "inventory": inventory})
    pointer = root.parent / "pointer.json"
    pointer.write_bytes(
        json_bytes(
            {
                "status": "complete",
                "release_id": "fixture",
                "completion": completion,
                "handoff": handoff,
                "approved_split": split,
                "target_dev": targets["dev"],
                "target_test": targets["test"],
            }
        )
    )
    return pointer


def test_loads_all_cases_without_answer_or_notes(tmp_path: Path) -> None:
    pointer = _release(tmp_path / "release")
    result = load_evidence_sources(pointer, tmp_path)
    assert len(result["cases"]) == 49
    assert [len(result[key]) for key in ("dev_case_ids", "test_case_ids")] == [19, 30]
    assert "FORBIDDEN" not in json.dumps(result)
    assert result == load_evidence_sources(pointer, tmp_path)


@pytest.mark.parametrize(
    "corrupt,match",
    [("text", "Full source text"), ("span", "spans"), ("corpus", "outside frozen corpus")],
)
def test_source_failures_block_publication(tmp_path: Path, corrupt: str, match: str) -> None:
    pointer = _release(tmp_path / "release", corrupt=corrupt)
    with pytest.raises(ValueError, match=match):
        load_evidence_sources(pointer, tmp_path)


def test_mutated_release_rejected(tmp_path: Path) -> None:
    pointer = _release(tmp_path / "release")
    (tmp_path / "release/target/test.jsonl").write_text("altered")
    with pytest.raises(ValueError, match="Bound size changed"):
        load_evidence_sources(pointer, tmp_path)


def test_canonical_mutation_outside_cited_text_rejected(tmp_path: Path) -> None:
    pointer = _release(tmp_path / "release")
    canonical = tmp_path / "blocks.jsonl"
    record = json.loads(canonical.read_bytes())
    record["unrelated_metadata"] = "altered outside cited span"
    canonical.write_bytes(json_bytes(record))
    with pytest.raises(ValueError, match="Bound size changed"):
        load_evidence_sources(pointer, tmp_path)


def test_table_loader_preserves_headers_empty_cells_units_and_footnotes(tmp_path: Path) -> None:
    pointer = _release(tmp_path / "release", table=True)
    result = load_evidence_sources(pointer, tmp_path)
    source = result["cases"][0]["sources"][0]
    assert source["full_source_text"].endswith("* Annual volume.")
    assert source["tables"][0]["shape"] == [2, 2]
    assert len(source["tables"][0]["cells"]) == 4
    assert source["tables"][0]["cells"][0] == {
        "text": "Volume (m3)",
        "row_index": 0,
        "column_index": 0,
        "is_header": True,
    }
    assert source["tables"][0]["cells"][1]["text"] == ""
    assert len(source["anchors"][1]["locators"]) == 3
    assert (
        result["verification"]["unit_boundary_basis"]
        == "inherited_from_verified_approved_release_not_recomputed"
    )


@pytest.mark.parametrize(
    "corrupt,match", [("table_cell", "table content"), ("empty_cell_span", "spans")]
)
def test_table_loader_rejects_changed_cells_and_incompatible_spans(
    tmp_path: Path, corrupt: str, match: str
) -> None:
    pointer = _release(tmp_path / "release", table=True, corrupt=corrupt)
    with pytest.raises(ValueError, match=match):
        load_evidence_sources(pointer, tmp_path)


def test_linked_expanded_anchors_are_verified_and_bound(tmp_path: Path) -> None:
    pointer = _release(tmp_path / "release", linked=True)
    result = load_evidence_sources(pointer, tmp_path)
    source = result["cases"][0]["sources"][0]
    assert source["anchors"][0]["locators"] == [
        {"text_field": "canonical_text", "start": 0, "end": 18}
    ]
    assert source["reference_role"] == "support"
    assert any(key.startswith("linked_source:") for key in result["source_bindings"])
    (tmp_path / "linked.json").write_text("tampered")
    with pytest.raises(ValueError, match="Bound size changed"):
        load_evidence_sources(pointer, tmp_path)


def test_optional_context_omitted_from_scoring_index_is_preserved(tmp_path: Path) -> None:
    pointer = _release(tmp_path / "release", omitted_context=True)
    source = load_evidence_sources(pointer, tmp_path)["cases"][0]["sources"][0]
    assert source["approved_roles"] == []
    assert source["reference_role"] == "context"
    assert source["reference_role_basis"] == "sealed_optional_context_occurrence"


def test_required_citation_cannot_be_missing_from_index(tmp_path: Path) -> None:
    pointer = _release(tmp_path / "release", corrupt="index")
    with pytest.raises(ValueError, match="Required citation absent"):
        load_evidence_sources(pointer, tmp_path)
