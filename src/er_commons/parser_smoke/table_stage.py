"""Adapt successful smoke routes to the maintained clean table stage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.document_parsing.content_parsing.sources import CompleteResolvedSource
from er_commons.document_parsing.content_parsing.table_request import (
    TableSource,
    build_table_request,
)
from er_commons.document_parsing.table_reconstruction.pipeline import run_table_extraction
from er_commons.parser_smoke.config import SmokeSpec


def run_smoke_tables(
    data_root: Path,
    smoke_id: str,
    source: CompleteResolvedSource,
    routes: list[dict[str, Any]],
    source_root: Path,
    spec: SmokeSpec,
) -> dict[int, dict[str, Any]]:
    """Run one source's routed pages with no review renders and return page outcomes."""
    request = build_table_request(
        pipeline_id=smoke_id,
        source_release_version=spec.source_release_version,
        source=TableSource.from_complete_source(source),
        routes=routes,
        artifact_relative_root=(source_root / "tables").relative_to(data_root),
        detection=spec.table_detection,
        cleanup=spec.table_cleanup,
        retain_review_derivatives=False,
    )
    request_path = source_root / "table_request.json"
    write_json_atomic(request_path, request.model_dump(mode="json"))
    table_root = source_root / "tables"
    manifest_path = run_table_extraction(data_root, request_path, table_root)
    pages = [
        json.loads(line)
        for line in (table_root / "pages.jsonl").read_text().splitlines()
        if line.strip()
    ]
    for page in pages:
        page_root = table_root / "pages" / f"page_{int(page['physical_pdf_page']):05d}"
        result = json.loads((page_root / "result.json").read_text())
        if result.get("artifacts"):
            raise ValueError("smoke table stage retained forbidden review derivatives")
        for table in result["tables"]:
            for role in ("raw_csv", "clean_csv", "cells"):
                artifact = table[role]
                path = page_root / artifact["path"]
                if not path.is_file() or sha256_file(path) != artifact["sha256"]:
                    raise ValueError(
                        f"smoke table artifact failed validation: "
                        f"{source.source_id} page {page['physical_pdf_page']} {role}"
                    )
    return {
        int(page["physical_pdf_page"]): {
            "status": "complete",
            "table_count": int(page["table_count"]),
            "route": page["route"],
            "result": (Path("tables") / page["result"]).as_posix(),
            "manifest": manifest_path.relative_to(source_root).as_posix(),
        }
        for page in pages
    }
