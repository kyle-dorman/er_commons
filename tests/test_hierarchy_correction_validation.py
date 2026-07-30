"""Cross-record policy tests for hierarchy correction v1."""

from __future__ import annotations

from typing import Any

import pytest
from hierarchy_correction_support import (
    VALID_BUNDLE,
    semantic_mutation_cases,
    valid_deep_hierarchy_bundle,
    valid_multiple_roots_bundle,
)

from er_commons.hierarchy_correction import (
    HierarchyCorrectionContractError,
    validate_hierarchy_correction_bundle,
)

SEMANTIC_MUTATION_CASES = semantic_mutation_cases()


def test_valid_bundle_passes_every_cross_record_policy() -> None:
    """Exercise the complete ordered policy registry on the positive fixture."""
    validate_hierarchy_correction_bundle(VALID_BUNDLE)


@pytest.mark.parametrize(
    "invalid_bundle",
    [bundle for _, bundle in SEMANTIC_MUTATION_CASES],
    ids=[name for name, _ in SEMANTIC_MUTATION_CASES],
)
def test_named_semantic_mutation_fails(
    invalid_bundle: dict[str, Any],
) -> None:
    """Make the failing responsibility visible in the pytest case name."""
    with pytest.raises(HierarchyCorrectionContractError):
        validate_hierarchy_correction_bundle(invalid_bundle)


def test_hierarchy_edges_must_remain_in_reading_order() -> None:
    """Reject a relationship set serialized in the wrong edge order."""
    bundle = valid_deep_hierarchy_bundle()
    validate_hierarchy_correction_bundle(bundle)
    bundle["hierarchy"]["edges"].reverse()

    with pytest.raises(HierarchyCorrectionContractError, match="edges differ"):
        validate_hierarchy_correction_bundle(bundle)


def test_hierarchy_roots_must_remain_in_reading_order() -> None:
    """Reject root keys serialized in an order different from decisions."""
    bundle = valid_multiple_roots_bundle()
    validate_hierarchy_correction_bundle(bundle)
    bundle["hierarchy"]["roots"].reverse()

    with pytest.raises(HierarchyCorrectionContractError, match="roots differ"):
        validate_hierarchy_correction_bundle(bundle)
