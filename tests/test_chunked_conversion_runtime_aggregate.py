from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from er_commons.chunked_conversion.range_contract import PageInterval
from er_commons.chunked_conversion.runtime import aggregate as aggregate_module
from er_commons.chunked_conversion.runtime.aggregate import (
    AggregatePublisher,
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
)


def _child(
    range_id: str,
    core: tuple[int, int],
    alignment_pages: tuple[dict[str, Any], ...],
    warnings: tuple[str, ...] = (),
) -> VerifiedConvertedRange:
    planned = SimpleNamespace(
        range_id=range_id,
        core=PageInterval(start=core[0], end=core[1]),
    )
    return cast(
        VerifiedConvertedRange,
        SimpleNamespace(
            planned=planned,
            alignment_pages=alignment_pages,
            warnings=warnings,
        ),
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
            table_stage_observation={},
            table_stage_root=(tmp_path / "table-stage").as_posix(),
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
        aggregate_module.RangePlan,
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

    def reached_child_verification(*_args: Any) -> Any:
        raise ReachedChildVerification

    monkeypatch.setattr(publisher, "_verified_children", reached_child_verification)

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
