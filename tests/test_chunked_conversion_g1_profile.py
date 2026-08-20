"""Contract tests for the readable G1 range-planning profile."""

from __future__ import annotations

from dataclasses import replace

from er_commons.chunked_conversion.qualification.g1_profile import (
    G1CodeIdentity,
    boundary_evidence_record,
    build_g1_plan,
    g1_core_intervals,
)


def _sealed_identity() -> dict[str, object]:
    return {
        "conversion_id": "dconv1-source",
        "identity": {
            "source": {
                "source_id": "deir_appendix_g1",
                "sha256": "a" * 64,
                "byte_size": 100,
            },
            "sealed_release": {"id": "release"},
            "package_versions": {"docling": "1"},
            "model_inventory": {"model": "x"},
        },
    }


def _code() -> G1CodeIdentity:
    return G1CodeIdentity(
        page_evidence="page-v1",
        range_conversion="range-v1",
        planning="plan-v1",
        aggregate="aggregate-v1",
    )


def test_g1_profile_has_exact_gap_free_reviewed_ranges() -> None:
    cores = g1_core_intervals()
    assert [(core.start, core.end) for core in cores] == [
        (1, 232),
        (233, 447),
        (448, 669),
        (670, 887),
        (888, 1107),
        (1108, 1332),
        (1333, 1590),
        (1591, 1811),
        (1812, 1957),
        (1958, 2146),
        (2147, 2232),
        (2233, 2488),
    ]
    assert max(core.end - core.start + 1 for core in cores) <= 275


def test_g1_identity_has_separate_child_and_aggregate_blast_radius() -> None:
    baseline = build_g1_plan(_sealed_identity(), _code())
    merge_change = build_g1_plan(_sealed_identity(), replace(_code(), aggregate="aggregate-v2"))
    child_change = build_g1_plan(_sealed_identity(), replace(_code(), range_conversion="range-v2"))

    assert [item.range_id for item in merge_change.ranges] == [
        item.range_id for item in baseline.ranges
    ]
    assert merge_change.plan_id == baseline.plan_id
    assert child_change.plan_id != baseline.plan_id


def test_boundary_record_explains_every_cut_and_excludes_g2() -> None:
    record = boundary_evidence_record()
    assert len(record["boundaries"]) == 11
    assert record["g2_inspected"] is False
