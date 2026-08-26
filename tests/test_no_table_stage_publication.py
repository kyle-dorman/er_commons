"""Regression tests for complete no-table producer handoffs."""

import json
from pathlib import Path
from types import SimpleNamespace

from er_commons.document_parsing.content_parsing.table_processing import (
    run_complete_table_stage,
)


def test_no_table_stage_publishes_empty_table_contract(tmp_path: Path) -> None:
    """A no-table route still publishes every consumer-facing table artifact."""
    config = SimpleNamespace()
    config.source_id = "document"
    config.pipeline_id = "pipeline"
    source = SimpleNamespace(source_id="document")
    routes = []

    result = run_complete_table_stage(
        data_root=tmp_path,
        staging_root=tmp_path / "staging",
        config=config,
        source=source,
        routes=routes,
        table_runner=None,
        producer_run_id="prv1-test",
    )

    root = tmp_path / "staging/documents/document/producer/tables"
    assert result.status == "not_applicable"
    assert json.loads((root / "table_families.json").read_text()) == {
        "families": [],
        "continuation_decisions": [],
    }
    assert (root / "tables.jsonl").read_text() == ""
    assert (root / "family_assignments.jsonl").read_text() == ""
    assert (root / "manifest.json").is_file()
