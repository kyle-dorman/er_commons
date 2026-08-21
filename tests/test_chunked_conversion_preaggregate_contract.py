"""Ownership and restart characterization for the pre-aggregate boundary."""

from pathlib import Path

import pytest

from er_commons.chunked_conversion.runtime.contracts import PreAggregateContext


def test_preaggregate_context_requires_absolute_contract_paths(tmp_path: Path) -> None:
    context = PreAggregateContext(
        child_root=(tmp_path / "child").resolve(),
        data_root=(tmp_path / "data").resolve(),
        config_path=(tmp_path / "config.json").resolve(),
        plan_path=(tmp_path / "plan.json").resolve(),
        run_id="run-1",
        plan_id="plan-1",
    )

    assert context.child_root.is_absolute()
    assert context.plan_id == "plan-1"
    with pytest.raises(ValueError, match="absolute"):
        PreAggregateContext(
            child_root=Path("relative"),
            data_root=context.data_root,
            config_path=context.config_path,
            plan_path=context.plan_path,
            run_id=context.run_id,
            plan_id=context.plan_id,
        )


def test_publication_roles_are_distinct() -> None:
    publication = {
        "ordered_non_table_content": "documents/x/producer/docling/document.json",
        "canonical_tables": "pre_aggregate/documents/x/producer/tables",
        "raw_evidence": "ranges/<range_id>/pages",
    }

    assert len(set(publication.values())) == 3
    assert publication["raw_evidence"] != publication["canonical_tables"]
