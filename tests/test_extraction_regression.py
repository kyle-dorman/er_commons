"""Tests for the fixed Task 03G.1a regression manifest."""

from pathlib import Path

from er_commons.extraction_regression import load_regression_manifest

MANIFEST = Path("configs/brisbane_baylands_2025_deir_task03g1a_regression_v1.json")


def test_checked_in_regression_manifest_binds_explicit_routing_claims() -> None:
    manifest, digest = load_regression_manifest(MANIFEST)

    assert len(digest) == 64
    cases = {case.page: case for case in manifest.routing_geometry.cases}
    assert set(cases) == {1, 2326, 2327, 2328}
    assert cases[2326].expected_strict_table_dominant is True
    assert cases[2326].expected_dense_partial_table is False
    assert cases[2327].expected_dense_partial_table is True
    assert cases[1].expected_route == "layout_regions"
    assert cases[2328].expected_route == "no_table_route"
