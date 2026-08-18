"""Source-indexed document targets derived from sealed successful candidates."""

from __future__ import annotations

from pathlib import Path

from er_commons.collection_processing.contract import JsonObject
from er_commons.collection_processing.storage import read_jsonl
from er_commons.document_publication.published_document import DocumentTerminalEvidence


def build_document_targets(
    evidence: tuple[DocumentTerminalEvidence, ...], extraction_root: Path
) -> list[JsonObject]:
    """Index document records by source identity without using display aliases."""
    rows: list[JsonObject] = []
    for item in evidence:
        if item.candidate_id is None:
            continue
        document_refs = [
            reference
            for reference in item.target_records_refs
            if Path(str(reference["path"])).name == "documents.jsonl"
        ]
        if len(document_refs) != 1:
            raise ValueError("successful candidate lacks one sealed document stream")
        for document in read_jsonl(_absolute(document_refs[0], extraction_root)):
            rows.append(
                {
                    "source_id": item.source["source_id"],
                    "source_ordinal": item.source_ordinal,
                    "candidate_id": item.candidate_id,
                    "target_id": document["id"],
                }
            )
    return sorted(
        rows,
        key=lambda row: (row["source_ordinal"], row["target_id"], row["candidate_id"]),
    )


def _absolute(reference: JsonObject, extraction_root: Path) -> Path:
    path = (extraction_root / str(reference["path"])).resolve()
    if not path.is_relative_to(extraction_root.resolve()):
        raise ValueError("artifact reference escapes extraction root")
    return path
