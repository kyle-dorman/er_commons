from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from er_commons.artifact_io import write_json_atomic, write_jsonl
from er_commons.chunked_conversion.range_contract import PageInterval, RangeCompletion
from er_commons.chunked_conversion.runtime import aggregate as aggregate_module
from er_commons.chunked_conversion.runtime.aggregate import (
    AggregatePublisher,
    AggregateRangeSummary,
    _split_heading_overlay_in_place,
    collect_warning_evidence,
    core_alignment_records,
    figure_asset_relative_path,
    raster_memory_evidence,
)
from er_commons.chunked_conversion.runtime.contracts import AggregateWorkerSpec
from er_commons.chunked_conversion.runtime.diagnostics import ChunkedConversionError
from er_commons.chunked_conversion.runtime.range_store import VerifiedConvertedRange
from er_commons.document_parsing.content_parsing.ordering_projection import (
    OrderingProjectionArtifact,
    OrderingTableStageObservation,
    TableArtifactSeal,
    TableStageReference,
    capture_table_stage_reference,
)
from er_commons.document_parsing.content_parsing.records import TableStageObservation
from er_commons.document_parsing.heading_evidence_parsing.heading_overlay import (
    split_heading_overlay,
)


def _child(
    range_id: str,
    core: tuple[int, int],
    alignment_pages: tuple[dict[str, Any], ...],
    warnings: tuple[str, ...] = (),
) -> AggregateRangeSummary:
    return AggregateRangeSummary(
        range_id=range_id,
        core_pages=PageInterval(start=core[0], end=core[1]).pages,
        alignment_pages=alignment_pages,
        warnings=warnings,
        observation={"range_id": range_id},
    )


def test_aggregate_creates_a_genuinely_absent_conversion_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fresh namespaces reach child verification instead of failing during staging."""
    plan_path = tmp_path / "plan.json"
    plan_path.write_text("{}\n")
    conversion_root = tmp_path / "new/conversions"
    projection_path = tmp_path / "projection.json"
    projection_path.write_text(
        OrderingProjectionArtifact(
            table_stage_observation=OrderingTableStageObservation(
                status="not_applicable",
                document_scope_complete=True,
                verified_no_table_routes=True,
                routed_pages=(),
                routed_page_count=0,
                logical_table_count=0,
                family_assignment_count=0,
                family_count=0,
                zero_table_pages=(),
            ),
            table_stage=TableStageReference(
                relative_path="table-stage",
                completion_marker="no_table_stage.json",
                completion_marker_sha256="0" * 64,
                no_table_handoff=tuple(
                    TableArtifactSeal(path=name, sha256="0" * 64)
                    for name in (
                        "summary.json",
                        "pages.jsonl",
                        "tables.jsonl",
                        "family_assignments.jsonl",
                        "table_families.json",
                        "manifest.json",
                    )
                ),
            ),
            pages=(),
            decisions=(),
        ).model_dump_json()
        + "\n"
    )
    spec = AggregateWorkerSpec(
        run_id="chunk1-test",
        run_root=(tmp_path / "run").resolve(),
        conversion_root=conversion_root.resolve(),
        data_root=(tmp_path / "data").resolve(),
        config_path=(tmp_path / "config.json").resolve(),
        plan_path=plan_path.resolve(),
        ordering_projection_path=projection_path.resolve(),
    )
    publisher = AggregatePublisher()
    plan = SimpleNamespace(ranges=())
    prepared = SimpleNamespace(conversion_identity=SimpleNamespace(payload={}))
    monkeypatch.setattr(
        cast(Any, aggregate_module).RangePlan,
        "model_validate_json",
        lambda _value: plan,
    )
    monkeypatch.setattr(
        aggregate_module,
        "verify_chunk_inputs",
        lambda *_args: SimpleNamespace(prepared=prepared),
    )
    monkeypatch.setattr(publisher, "_identity", lambda *_args, **_kwargs: {})

    class ReachedChildVerification(RuntimeError):
        pass

    def reached_child_verification(*_args: Any, **_kwargs: Any) -> Any:
        raise ReachedChildVerification

    monkeypatch.setattr(publisher, "_verified_global_inputs", reached_child_verification)

    with pytest.raises(ReachedChildVerification):
        publisher.run(spec)

    attempts = conversion_root / "attempts"
    assert attempts.is_dir()
    assert len(list(attempts.glob("dconv1-*"))) == 1


def test_alignment_emits_core_rows_once_after_exact_overlap_comparison() -> None:
    page1 = {"page_no": 1, "cells": ["one"]}
    page2 = {"page_no": 2, "cells": ["shared"]}
    page3 = {"page_no": 3, "cells": ["three"]}
    children = (
        _child("left", (1, 1), (page1, page2)),
        _child("right", (2, 3), (page2.copy(), page3)),
    )

    assert core_alignment_records(children) == (page1, page2, page3)


def test_aggregate_rebinds_table_reference_to_its_publication_root(tmp_path: Path) -> None:
    owner = (tmp_path / "plan").resolve()
    table_root = owner / "pre_aggregate/tables"
    observation = TableStageObservation(
        status="not_applicable",
        document_scope_complete=True,
        verified_no_table_routes=True,
        routed_pages=[],
        routed_page_count=0,
        logical_table_count=0,
        family_assignment_count=0,
        family_count=0,
        zero_table_pages=[],
    )
    _write_no_table_handoff(table_root, observation)
    projection = OrderingProjectionArtifact(
        table_stage_observation=OrderingTableStageObservation.model_validate(
            observation.model_dump(mode="python")
        ),
        table_stage=capture_table_stage_reference(owner, table_root, observation),
        pages=(),
        decisions=(),
    )
    staging = (tmp_path / "aggregate-staging").resolve()
    docling_root = staging / "documents/source/producer/docling"
    docling_root.mkdir(parents=True)

    AggregatePublisher()._write_ordering_artifacts(
        staging=staging,
        source_id="source",
        docling_root=docling_root,
        plan=cast(Any, SimpleNamespace(plan_id="plan-1")),
        projection=projection,
        projection_owner=owner,
        children=(),
    )

    published = OrderingProjectionArtifact.model_validate_json(
        (staging / "records/ordering_projection.json").read_bytes()
    )
    assert published.table_stage.relative_path == "tables"
    assert not Path(published.table_stage.relative_path).is_absolute()
    assert (staging / "tables/no_table_stage.json").is_file()


def _write_no_table_handoff(root: Path, observation: TableStageObservation) -> None:
    """Write the complete empty table handoff consumed by aggregation."""
    write_json_atomic(
        root / "summary.json",
        {
            "physical_pdf_pages": [],
            "page_count": 0,
            "logical_table_count": 0,
            "family_count": 0,
            "zero_table_pages": [],
            "review_derivatives_retained": False,
        },
    )
    for name in ("pages.jsonl", "tables.jsonl", "family_assignments.jsonl"):
        write_jsonl(root / name, [])
    write_json_atomic(root / "table_families.json", {"families": [], "continuation_decisions": []})
    write_json_atomic(
        root / "manifest.json",
        {
            "schema_version": "1.0.0",
            "source_id": "source",
            "physical_pdf_pages": [],
            "summary": "summary.json",
            "pages": "pages.jsonl",
            "tables": "tables.jsonl",
            "family_assignments": "family_assignments.jsonl",
            "table_families": "table_families.json",
        },
    )
    write_json_atomic(
        root / "no_table_stage.json",
        observation.model_dump(mode="json", exclude_none=True),
    )


def test_figure_asset_path_is_relative_to_the_conversion_root() -> None:
    assert figure_asset_relative_path("deir_main", 3) == Path(
        "documents/deir_main/assets/figures/figure-0003.png"
    )


def test_alignment_rejects_overlap_row_drift_with_range_provenance() -> None:
    children = (
        _child("left", (1, 1), ({"page_no": 1}, {"page_no": 2, "value": "left"})),
        _child("right", (2, 2), ({"page_no": 2, "value": "right"},)),
    )

    with pytest.raises(ChunkedConversionError, match="alignment_overlap") as captured:
        core_alignment_records(children)

    assert captured.value.expected == {
        "range_id": "left",
        "record": {"page_no": 2, "value": "left"},
    }
    assert captured.value.actual == {
        "range_id": "right",
        "record": {"page_no": 2, "value": "right"},
    }


def test_warning_evidence_preserves_child_then_global_order_and_duplicates() -> None:
    children = (
        _child("left", (1, 1), ({"page_no": 1},), ("shared", "left-only")),
        _child("right", (2, 2), ({"page_no": 2},), ("shared",)),
    )

    combined, evidence = collect_warning_evidence(children, ("global",))

    assert combined == ("shared", "left-only", "shared", "global")
    assert evidence == {
        "child_ranges": [
            {"range_id": "left", "warnings": ["shared", "left-only"]},
            {"range_id": "right", "warnings": ["shared"]},
        ],
        "global": ["global"],
        "child_warning_count": 3,
        "global_warning_count": 1,
        "combined_warning_count": 4,
        "combined_order": "range-plan order, then global interpretation",
    }


def test_raster_memory_evidence_reports_single_page_asset_decoding() -> None:
    assert raster_memory_evidence(has_assets=True) == {
        "range_page_rasters": "verified_path_backed_png",
        "all_page_png_bytes_materialized": False,
        "global_interpretation_decoded_page_rasters": 0,
        "asset_crop_peak_decoded_page_rasters": 1,
    }


def test_aggregate_overlay_split_matches_copying_reference_without_second_graph() -> None:
    document = {
        "texts": [
            {"self_ref": "#/texts/0", "level": 3, "text": "Nested"},
            {"self_ref": "#/texts/1", "level": 1, "text": "Base"},
        ],
        "groups": [],
    }
    expected_document, expected_overlay = split_heading_overlay(document)

    overlay = _split_heading_overlay_in_place(document)

    assert document == expected_document
    assert overlay == expected_overlay


def test_aggregate_verifies_each_range_only_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    planned = SimpleNamespace(
        range_id="range-1",
        core=PageInterval(start=1, end=1),
        read=PageInterval(start=1, end=1),
    )
    evidence = SimpleNamespace(page_no=1)
    child = VerifiedConvertedRange(
        planned=cast(Any, planned),
        pages=cast(Any, (evidence,)),
        outline=({"title": "same"},),
        alignment_pages=({"page_no": 1},),
        warnings=(),
        observation={"range_id": "range-1"},
        completion=cast(RangeCompletion, SimpleNamespace()),
        root=tmp_path / "range-1",
        projections=cast(Any, (SimpleNamespace(),)),
    )
    calls: list[str] = []

    class Store:
        def verify(self, range_id: str) -> VerifiedConvertedRange:
            calls.append(range_id)
            return child

    monkeypatch.setattr(aggregate_module, "ConvertedRangeStore", lambda *_args: Store())
    monkeypatch.setattr(aggregate_module, "restore_ordering_page", lambda item: item)
    monkeypatch.setattr(aggregate_module, "page_source", lambda *_args: "page-source")
    projection = cast(
        OrderingProjectionArtifact,
        SimpleNamespace(pages=(SimpleNamespace(page_no=1, ordering_suppressed_table_refs=()),)),
    )

    children, pages, outline, sources = AggregatePublisher()._verified_global_inputs(
        tmp_path,
        cast(Any, SimpleNamespace(ranges=(planned,))),
        projection,
    )

    assert calls == ["range-1"]
    assert [page.page_no for page in pages] == [1]
    assert outline == ({"title": "same"},)
    assert cast(Any, sources) == ("page-source",)
    assert children == (
        AggregateRangeSummary(
            range_id="range-1",
            core_pages=(1,),
            alignment_pages=({"page_no": 1},),
            warnings=(),
            observation={"range_id": "range-1"},
        ),
    )
