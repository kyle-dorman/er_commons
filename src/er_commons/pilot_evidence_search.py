"""Repeatable lexical retrieval and heading-bounded citation assembly for Task 07D.

Callers own eligibility, query planning, semantic selection and human review. This
module verifies explicit file bindings and never assigns evidence support labels.
"""

import hashlib
import json
import sqlite3
import sys
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path
from typing import Any

from er_commons.pilot_evidence import SECTION_SCHEMA, candidate_id, digest, validate_candidates

DDL = (
    "CREATE VIRTUAL TABLE content USING fts5(text, source UNINDEXED, "
    "extraction_id UNINDEXED, record_id UNINDEXED, path UNINDEXED, "
    'snapshot UNINDEXED, tokenize="unicode61")'
)
SELECT = (
    "SELECT source, extraction_id, record_id, path, text, snapshot, bm25(content) AS score "
    "FROM content WHERE content MATCH ?"
)
ORDER = " ORDER BY score, source, record_id LIMIT ?"


def file_sha256(path: Path) -> str:
    """Hash full file bytes without loading large canonical files into memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _path(root: Path, relative: str) -> Path:
    """Resolve an explicitly relative canonical path inside its configured root."""
    path = (root / relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root.resolve()):
        raise ValueError("Canonical path escapes data root")
    return path


def _iter_records(path: Path) -> Iterator[dict[str, Any]]:
    """Stream canonical JSON objects, identifying the file and line on bad input."""
    with path.open() as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid canonical JSON at {path}:{line_number}") from error
            if not isinstance(record, dict):
                raise ValueError(f"Expected canonical object at {path}:{line_number}")
            yield record


def _read_records(path: Path) -> dict[str, Any]:
    """Read exact records and reject ambiguous duplicate canonical IDs."""
    result: dict[str, Any] = {}
    for record in _iter_records(path):
        if record["id"] in result:
            raise ValueError(f"Duplicate canonical record ID {record['id']!r} in {path}")
        result[record["id"]] = record
    return result


def _index_source(connection: sqlite3.Connection, source: dict[str, Any], data_root: Path) -> int:
    """Insert searchable blocks/cells in canonical order, retaining exact snapshots."""
    count = 0
    for kind in ("blocks", "tables"):
        binding = source["files"][kind]
        for record in _iter_records(_path(data_root, binding["path"])):
            if record.get("is_toc_row") or record.get("content_layer") in {"header", "footer"}:
                continue
            text = (
                record.get("canonical_text", "")
                if kind == "blocks"
                else "\n".join(cell["text"] for cell in record["cells"])
            )
            if not text:
                continue
            connection.execute(
                "INSERT INTO identities VALUES (?,?)", (source["source_id"], record["id"])
            )
            connection.execute(
                "INSERT INTO content VALUES (?,?,?,?,?,?)",
                (
                    text,
                    source["source_id"],
                    source["extraction_id"],
                    record["id"],
                    binding["path"],
                    json.dumps(record, ensure_ascii=False),
                ),
            )
            count += 1
    return count


def build_index(index_path: Path, sources: list[dict[str, Any]], data_root: Path) -> dict[str, Any]:
    """Build a new persistent cache from source/extraction IDs and hashed blocks/tables.

    Each source requires source_id, extraction_id and files mapping blocks/tables
    to {path, sha256}. Additional source metadata is retained in the manifest.
    The adjacent .manifest.json is written last; failed builds cannot be reused.
    """
    manifest_path = index_path.with_suffix(index_path.suffix + ".manifest.json")
    if index_path.exists() or manifest_path.exists():
        raise FileExistsError(index_path)
    if not sources or len({s["source_id"] for s in sources}) != len(sources):
        raise ValueError("Require nonempty distinct eligible sources")
    ordered = sorted(sources, key=lambda source: source["source_id"])
    for source in ordered:
        if not source["extraction_id"]:
            raise ValueError("Missing extraction identity")
        for kind in ("blocks", "tables"):
            binding = source["files"][kind]
            if file_sha256(_path(data_root, binding["path"])) != binding["sha256"]:
                raise ValueError("Canonical file hash differs from source binding")
    index_path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents a concurrent builder from replacing this cache.
    with index_path.open("xb"):
        pass
    counts: dict[str, int] = {}
    # SQLite's connection context commits/rolls back but does not close the handle.
    # Close it before hashing the finished database or returning a failed build.
    with closing(sqlite3.connect(index_path)) as connection, connection:
        connection.execute(DDL)
        connection.execute("CREATE TABLE identities (source TEXT, id TEXT, PRIMARY KEY(source,id))")
        for source in ordered:
            counts[source["source_id"]] = _index_source(connection, source, data_root)
        connection.execute("INSERT INTO content(content) VALUES ('integrity-check')")
    manifest = {
        "schema_version": "er_commons.task07d.search_index.v1",
        "sources": ordered,
        "indexed_counts": counts,
        "sqlite_version": sqlite3.sqlite_version,
        "python_version": sys.version,
        "ddl": DDL,
        "select_sql": SELECT,
        "order_sql": ORDER,
        "tokenizer": "unicode61",
        "ranking": "default bm25 ascending, source, record_id",
        "code_sha256": file_sha256(Path(__file__)),
        "index_sha256": file_sha256(index_path),
    }
    manifest["index_identity"] = "search07d-" + digest(manifest)
    with manifest_path.open("x") as stream:
        json.dump(manifest, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    return manifest


def verify_index(index_path: Path) -> dict[str, Any]:
    """Verify the completed cache manifest and full database before reuse."""
    manifest: dict[str, Any] = json.loads(
        index_path.with_suffix(index_path.suffix + ".manifest.json").read_text()
    )
    identity = manifest.pop("index_identity")
    if identity != "search07d-" + digest(manifest):
        raise ValueError("Search manifest identity mismatch")
    manifest["index_identity"] = identity
    if file_sha256(index_path) != manifest["index_sha256"]:
        raise ValueError("Search cache hash mismatch")
    return manifest


def search(
    index_path: Path,
    *,
    query_id: str,
    expression: str,
    claim_ids: list[str],
    purpose: str,
    source_filter: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Return ordered hits and exact record snapshots; retain failed SQL as receipts.

    The caller saves the planned expression before calling and the receipt after.
    A source filter uses the same full-corpus statistics as unrestricted queries.
    Each call verifies all cache bytes; no process-local trust cache bypasses the
    sealed manifest. Query receipts remain usable across code-only refactors.
    """
    if not 1 <= limit <= 10 or not query_id or not claim_ids or not purpose:
        raise ValueError("Require query identity, claims, purpose and a 1..10 limit")
    manifest = verify_index(index_path)
    if source_filter and source_filter not in {s["source_id"] for s in manifest["sources"]}:
        raise ValueError("Source filter is outside frozen index")
    sql = SELECT + (" AND source=?" if source_filter else "")
    parameters: list[Any] = [expression] + ([source_filter] if source_filter else [])
    receipt: dict[str, Any] = {
        "query_id": query_id,
        "expression": expression,
        "claim_ids": claim_ids,
        "purpose": purpose,
        "source_filter": source_filter,
        "limit": limit,
        "index_identity": manifest["index_identity"],
        "sql": sql + ORDER,
        "hits": [],
        "status": "completed",
    }
    with closing(
        sqlite3.connect(index_path.resolve().as_uri() + "?mode=ro", uri=True)
    ) as connection:
        try:
            count = connection.execute("SELECT count(*) FROM (" + sql + ")", parameters).fetchone()[
                0
            ]
            for row in connection.execute(sql + ORDER, parameters + [limit]):
                source, extraction, identity, path, text, snapshot, score = row
                receipt["hits"].append(
                    {
                        "rank": len(receipt["hits"]) + 1,
                        "source_id": source,
                        "extraction_id": extraction,
                        "record_id": identity,
                        "path": path,
                        "text": text,
                        "record": json.loads(snapshot),
                        "score": score,
                    }
                )
            receipt.update(
                total_matches=count, returned_count=len(receipt["hits"]), truncated=count > limit
            )
        except sqlite3.OperationalError as error:
            receipt.update(status="error", error=str(error), total_matches=None, truncated=None)
    return receipt


def _anchor(path: str, record: dict[str, Any], field: str = "canonical_text") -> dict[str, Any]:
    """Bind an entire block or nonempty cell without changing canonical text."""
    text: Any = record
    for component in field.split("."):
        text = text[int(component)] if isinstance(text, list) else text[component]
    if not text:
        raise ValueError("Empty canonical anchor")
    return dict(
        path=path,
        record_id=record["id"],
        record_id_field="id",
        record=record,
        text_field=field,
        start=0,
        end=len(text),
        quote=text,
    )


def assemble_section(
    *,
    source: dict[str, Any],
    section_id: str,
    data_root: Path,
    printed_labels_by_page: dict[int, str],
    metadata: dict[str, Any],
    table_association_receipt: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Assemble complete narrative and any supported section-tail table separately.

    Source files must bind blocks, sections and tables by path/hash. Metadata
    supplies edition, source_url, limitations, and optionally PDF URL and notes.
    Printed labels are explicit caller-verified physical-page mappings; missing
    labels and unsupported table-note layouts fail closed, never guessed.
    """
    records: dict[str, dict[str, Any]] = {}
    for kind in ("blocks", "sections", "tables"):
        binding = source["files"][kind]
        path = _path(data_root, binding["path"])
        if file_sha256(path) != binding["sha256"]:
            raise ValueError("Canonical file hash mismatch during citation assembly")
        records[kind] = _read_records(path)
    blocks, sections, tables = (records[k] for k in ("blocks", "sections", "tables"))
    section = sections[section_id]
    heading = blocks[section["heading_block_id"]]
    following = [
        b
        for b in blocks.values()
        if b["block_type"] == "heading"
        and b.get("content_layer") == "body"
        and b["sequence"] > heading["sequence"]
    ]
    if not following:
        raise ValueError("Section has no explicit next heading boundary")
    next_heading = min(following, key=lambda b: b["sequence"])
    members = [i for i in section["ordered_child_ids"] if i not in sections]
    table_ids = [i for i in members if i in tables]
    if len(table_ids) > 1 and table_association_receipt is None:
        raise ValueError("Multiple tables require a verified table-note association policy")
    exclusions = []
    selections: list[tuple[str, list[str], str | None]] = []
    if table_association_receipt is not None:
        from er_commons.pilot_citation_units import reviewed_table_associations

        groups = reviewed_table_associations(
            table_association_receipt,
            data_root=data_root,
            source_id=source["source_id"],
            section_id=section_id,
            section_path=source["files"]["sections"]["path"],
            members=members,
            blocks=blocks,
            tables=tables,
        )
        exclusions = [
            dict(kind="table", table_id=g["table_id"], member_record_ids=g["member_record_ids"])
            for g in groups
        ]
        removed = {i for g in groups for i in g["member_record_ids"]}
        selections.append(("section", [i for i in members if i not in removed], None))
        selections.extend(("table", g["member_record_ids"], g["table_id"]) for g in groups)
    elif table_ids:
        table_id = table_ids[0]
        position = members.index(table_id)
        if (
            position == 0
            or members[position - 1] not in blocks
            or blocks[members[position - 1]]["block_type"] != "caption"
        ):
            raise ValueError("Table requires its preceding canonical caption")
        tail = members[position - 1 :]
        if any(i not in blocks for i in members[position + 1 :]):
            raise ValueError("Unsupported table section tail")
        exclusions = [dict(kind="table", table_id=table_id, member_record_ids=tail)]
        selections.append(("section", members[: position - 1], None))
        selections.append(("table", tail, table_id))
    else:
        selections.append(("section", members, None))
    candidates = []
    block_path = source["files"]["blocks"]["path"]
    for kind, selected, table_id in selections:
        anchors = []
        for identity in selected:
            if identity in blocks:
                anchors.append(_anchor(block_path, blocks[identity]))
            else:
                table = tables[identity]
                anchors.extend(
                    _anchor(source["files"]["tables"]["path"], table, f"cells.{i}.text")
                    for i, cell in enumerate(table["cells"])
                    if cell["text"]
                )
        pages = sorted(
            {
                int(region["page_id"].rsplit("/p", 1)[-1])
                for anchor in anchors
                for region in anchor["record"]["regions"]
            }
        )
        labels = [printed_labels_by_page[page] for page in pages]
        title = (
            heading["canonical_text"]
            if kind == "section"
            else blocks[selected[0]]["canonical_text"]
        )
        candidate = {
            **metadata,
            "source_id": source["source_id"],
            "extraction_id": source["extraction_id"],
            "anchors": anchors,
            "quote": "\n\n".join(a["quote"] for a in anchors),
            "title": title,
            "physical_pages": pages,
            "printed_labels": labels,
        }
        if candidate.get("pdf_url"):
            candidate["pdf_url"] = candidate["pdf_url"].split("#")[0] + "#page=" + str(pages[0])
        candidate["citation_unit"] = dict(
            schema_version="er_commons.task07d.citation_unit.v1",
            kind=kind,
            section_id=section_id,
            section_record=dict(
                path=source["files"]["sections"]["path"],
                record_id=section_id,
                record_id_field="id",
                record=section,
            ),
            heading_anchor=_anchor(block_path, heading),
            breadcrumb=[
                dict(
                    section_id=sid,
                    heading_block_id=sections[sid]["heading_block_id"],
                    heading_text=blocks[sections[sid]["heading_block_id"]]["canonical_text"],
                )
                for sid in section["section_path_ids"]
                if sections[sid].get("heading_block_id") in blocks
            ],
            start_block_id=heading["id"],
            next_heading_anchor=_anchor(block_path, next_heading),
            boundary_policy="heading_to_next_heading_exclusive",
            section_member_record_ids=members,
            member_record_ids=selected,
            separately_cited_units=exclusions if kind == "section" else [],
            table_id=table_id,
            citation_label=title + " (pp. " + ", ".join(labels) + ")",
        )
        if table_association_receipt is not None:
            candidate["citation_unit"]["schema_version"] = "er_commons.task07d.citation_unit.v2"
            candidate["citation_unit"]["table_association_receipt"] = table_association_receipt
        candidate["candidate_id"] = candidate_id(candidate)
        candidates.append(candidate)
    validate_candidates({"schema_version": SECTION_SCHEMA, "candidates": candidates}, data_root)
    return candidates
