"""Small canonical-record operations shared by citation assemblers and validators.

These helpers do not infer boundaries or repair source records. Policy-specific
callers decide which records belong to a citation and which receipts to require.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

Record = dict[str, Any]
RecordIndex = dict[str, Record]


def source_path(data_root: Path, relative: str) -> Path:
    """Resolve a source reference within its artifact root, including symlink checks."""
    path = (data_root / relative).resolve()
    if not path.is_relative_to(data_root.resolve()):
        raise ValueError(f"Citation path escapes data root: {relative}")
    return path


def bound_bytes(binding: Record, data_root: Path) -> bytes:
    """Read exact receipt/source bytes only after checking their recorded digest."""
    raw = source_path(data_root, binding["path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != binding["sha256"]:
        raise ValueError(f"Citation binding hash mismatch: {binding['path']}")
    return raw


def index_records(raw: bytes) -> RecordIndex:
    """Index canonical JSONL without silently replacing duplicate record IDs."""
    result: RecordIndex = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        identity = record["id"]
        if identity in result:
            raise ValueError(f"Duplicate citation source ID: {identity}")
        result[identity] = record
    return result


def block_anchor(path: str, block: Record) -> Record:
    """Bind a full unchanged canonical block, keeping its original record snapshot."""
    text = block["canonical_text"]
    return dict(
        path=path,
        record_id=block["id"],
        record_id_field="id",
        record=block,
        text_field="canonical_text",
        start=0,
        end=len(text),
        quote=text,
    )


def next_body_heading(blocks: RecordIndex, heading: Record) -> Record | None:
    """Find the first later body heading, ignoring running headers and page chrome."""
    return min(
        (
            block
            for block in blocks.values()
            if block["block_type"] == "heading"
            and block.get("content_layer") == "body"
            and block["sequence"] > heading["sequence"]
        ),
        key=lambda block: block["sequence"],
        default=None,
    )


def section_breadcrumb(section: Record, sections: RecordIndex, blocks: RecordIndex) -> list[Record]:
    """Preserve the parsed ancestry for headings present in the canonical records."""
    return [
        dict(
            section_id=identity,
            heading_block_id=sections[identity]["heading_block_id"],
            heading_text=blocks[sections[identity]["heading_block_id"]]["canonical_text"],
        )
        for identity in section["section_path_ids"]
        if sections[identity].get("heading_block_id") in blocks
    ]


def canonical_table_binding(candidate: dict[str, Any]) -> dict[str, Any]:
    """Compare canonical table bindings while allowing separate display occurrences."""
    anchor_fields = (
        "path",
        "record_id_field",
        "record_id",
        "record",
        "text_field",
        "start",
        "end",
        "quote",
    )
    return {
        **{
            key: candidate.get(key)
            for key in ("source_id", "source_pdf_path", "source_sha256", "edition")
        },
        "unit": {
            key: value
            for key, value in candidate["citation_unit"].items()
            if key != "citation_label"
        },
        "anchors": [
            {key: anchor.get(key) for key in anchor_fields} for anchor in candidate["anchors"]
        ],
    }
