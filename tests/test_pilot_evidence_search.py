"""Exercise reproducible search and fail-closed canonical citation boundaries."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from er_commons.pilot_evidence_search import (
    assemble_section,
    build_index,
    file_sha256,
    search,
    verify_index,
)


def corpus(tmp_path: Path) -> dict:
    """Create canonical section text with a complete table and next heading."""
    blocks = []
    for i, (kind, text) in enumerate(
        [
            ("heading", "Air quality"),
            ("paragraph", "Operational emissions baseline"),
            ("caption", "Table 1: emissions"),
            ("paragraph", "Note: baseline assumption"),
            ("heading", "Next section"),
            ("paragraph", "Operational emissions header"),
        ]
    ):
        blocks.append(
            dict(
                id=f"b{i}",
                document_id="x/document/deir_main",
                block_type=kind,
                canonical_text=text,
                content_layer="header" if i == 5 else "body",
                section_id="s1" if i < 4 else "s2",
                sequence=i,
                regions=[{"page_id": "x/p0001"}],
            )
        )
    table = dict(
        id="t1",
        document_id="x/document/deir_main",
        section_id="s1",
        cells=[{"text": "Pollutant"}, {"text": "NOx"}, {"text": ""}],
        regions=[{"page_id": "x/p0001"}],
    )
    sections = [
        dict(
            id="s1",
            document_id="x/document/deir_main",
            heading_block_id="b0",
            section_path_ids=["s1"],
            ordered_child_ids=["b0", "b1", "b2", "t1", "b3"],
        ),
        dict(
            id="s2",
            document_id="x/document/deir_main",
            heading_block_id="b4",
            section_path_ids=["s2"],
            ordered_child_ids=["b4"],
        ),
    ]
    files = {}
    for kind, rows in [("blocks", blocks), ("tables", [table]), ("sections", sections)]:
        path = tmp_path / (kind + ".jsonl")
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        files[kind] = dict(path=path.name, sha256=file_sha256(path))
    return dict(source_id="deir_main", extraction_id="accepted-v1", files=files)


def test_search_replays_and_preserves_source_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with closing(sqlite3.connect(":memory:")) as connection:
        try:
            connection.execute("CREATE VIRTUAL TABLE capability USING fts5(text)")
        except sqlite3.OperationalError:
            pytest.skip("This Python SQLite build lacks FTS5; run with an FTS5-enabled interpreter")
    connections: list[sqlite3.Connection] = []
    original_connect = sqlite3.connect

    def tracked_connect(*args, **kwargs):
        """Keep handles to verify both successful and failed queries close them."""
        connection = original_connect(*args, **kwargs)
        connections.append(connection)
        return connection

    monkeypatch.setattr(sqlite3, "connect", tracked_connect)
    source = corpus(tmp_path)
    db = tmp_path / "index.sqlite"
    manifest = build_index(db, [source], tmp_path)
    assert manifest["indexed_counts"] == {"deir_main": 6}
    args = dict(
        query_id="q1",
        expression="operational AND emissions",
        claim_ids=["c1"],
        purpose="central proposition",
    )
    first = search(db, **args)
    assert first == search(db, **args)
    assert first["total_matches"] == 1
    assert first["hits"][0]["record"]["id"] == "b1"
    filtered = search(db, **args, source_filter="deir_main")
    assert filtered["hits"] == first["hits"]
    assert search(db, **{**args, "expression": '"'})["status"] == "error"
    assert verify_index(db) == manifest
    for connection in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            connection.execute("SELECT 1")
    with pytest.raises(FileExistsError):
        build_index(db, [source], tmp_path)
    db.write_bytes(db.read_bytes() + b"altered")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_index(db)


def test_hash_and_scope_fail_closed(tmp_path: Path) -> None:
    source = corpus(tmp_path)
    source["files"]["blocks"]["sha256"] = "wrong"
    with pytest.raises(ValueError, match="hash differs"):
        build_index(tmp_path / "bad.sqlite", [source], tmp_path)
    assert not (tmp_path / "bad.sqlite").exists()


def test_complete_section_separates_full_table_tail(tmp_path: Path) -> None:
    source = corpus(tmp_path)
    candidates = assemble_section(
        source=source,
        section_id="s1",
        data_root=tmp_path,
        printed_labels_by_page={1: "4-1"},
        metadata=dict(
            edition="Draft EIR", source_url="https://example.org/source.pdf", limitations=[]
        ),
    )
    assert len(candidates) == 2
    section, table = candidates
    assert section["citation_unit"]["member_record_ids"] == ["b0", "b1"]
    assert table["citation_unit"]["member_record_ids"] == ["b2", "t1", "b3"]
    assert table["quote"] == "Table 1: emissions\n\nPollutant\n\nNOx\n\nNote: baseline assumption"
    assert section["citation_unit"]["next_heading_anchor"]["record_id"] == "b4"
    with pytest.raises(ValueError, match="next heading"):
        assemble_section(
            source=source,
            section_id="s2",
            data_root=tmp_path,
            printed_labels_by_page={1: "4-1"},
            metadata={},
        )
    with pytest.raises(KeyError):
        assemble_section(
            source=source,
            section_id="s1",
            data_root=tmp_path,
            printed_labels_by_page={},
            metadata={},
        )


def test_malformed_canonical_json_identifies_source_line(tmp_path: Path) -> None:
    source = corpus(tmp_path)
    path = tmp_path / source["files"]["blocks"]["path"]
    path.write_text(path.read_text() + "not-json\n")
    source["files"]["blocks"]["sha256"] = file_sha256(path)
    with pytest.raises(ValueError, match=r"Invalid canonical JSON at .*blocks.jsonl:7"):
        assemble_section(
            source=source,
            section_id="s1",
            data_root=tmp_path,
            printed_labels_by_page={1: "4-1"},
            metadata={},
        )
