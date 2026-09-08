"""Source-free tests for Task 05C operational range receipts."""

from __future__ import annotations

from copy import deepcopy

import pytest

from er_commons.response_inventory.pilot_policy import TASK05C_PILOT_RANGES
from er_commons.response_inventory.range_receipts import (
    build_range_receipt,
    contiguous_range_key,
    pilot_aggregation_is_ready,
    range_receipt_is_reusable,
)

DIGESTS = {
    "code_sha256": "1" * 64,
    "config_sha256": "2" * 64,
    "run_spec_sha256": "3" * 64,
    "schema_sha256": "4" * 64,
}
BINDINGS = [
    {
        "role": "task05a_completion",
        "identity": "649ec0664a6f7aebdfc6b7da011161d696385ed246bc726becaf89c416f652dd",
        "authority": "artifact_root",
        "path": "working/05a/source_free_v1/records/task05a_completion.json",
    },
    {
        "role": "source_record",
        "identity": "feir_volume_4@1a5437cc",
        "authority": "artifact_root",
        "path": "datasets/ceqa/raw/source_manifest.json",
    },
]


def _receipt(page_range: tuple[int, int]) -> dict[str, object]:
    key = contiguous_range_key(page_range)
    return build_range_receipt(
        page_range,
        status="complete",
        bindings=reversed(BINDINGS),
        digests=DIGESTS,
        files=[{"path": f"ranges/{key}/records.jsonl", "byte_size": 101}],
        semantic_digest="a" * 64,
    )


def test_receipt_is_deterministic_and_reuse_requires_exact_evidence() -> None:
    page_range = (31, 44)
    receipt = _receipt(page_range)
    assert receipt["range_key"] == "000031-000044"
    assert receipt["bindings"] == sorted(BINDINGS, key=lambda item: item["role"])
    assert range_receipt_is_reusable(
        receipt,
        page_range,
        bindings=BINDINGS,
        digests=DIGESTS,
        files=[{"path": "ranges/000031-000044/records.jsonl", "byte_size": 101}],
        semantic_digest="a" * 64,
    )

    changed_size = deepcopy(receipt)
    changed_size["files"][0]["byte_size"] = 102  # type: ignore[index]
    changed_receipts = [changed_size]
    changed_binding = deepcopy(receipt)
    changed_binding["bindings"][0]["identity"] = "changed"  # type: ignore[index]
    changed_receipts.append(changed_binding)
    changed_digest = deepcopy(receipt)
    changed_digest["digests"]["code_sha256"] = "9" * 64  # type: ignore[index]
    changed_receipts.append(changed_digest)
    changed_semantic_digest = deepcopy(receipt)
    changed_semantic_digest["semantic_digest"] = "b" * 64
    changed_receipts.append(changed_semantic_digest)

    for changed in changed_receipts:
        assert not range_receipt_is_reusable(
            changed,
            page_range,
            bindings=BINDINGS,
            digests=DIGESTS,
            files=[{"path": "ranges/000031-000044/records.jsonl", "byte_size": 101}],
            semantic_digest="a" * 64,
        )


def test_partial_or_failed_receipt_cannot_count_complete() -> None:
    receipts = [_receipt(page_range) for page_range in TASK05C_PILOT_RANGES]
    assert pilot_aggregation_is_ready(receipts)
    assert not pilot_aggregation_is_ready(receipts[:-1])

    failed = build_range_receipt(
        TASK05C_PILOT_RANGES[-1],
        status="failed",
        bindings=BINDINGS,
        digests=DIGESTS,
        files=[],
        semantic_digest=None,
        failure="simulated interruption",
    )
    assert not pilot_aggregation_is_ready([*receipts[:-1], failed])

    partial = deepcopy(receipts[-1])
    partial.pop("semantic_digest")
    assert not pilot_aggregation_is_ready([*receipts[:-1], partial])


def test_aggregation_requires_the_exact_14_ranges_and_shared_bindings() -> None:
    receipts = [_receipt(page_range) for page_range in TASK05C_PILOT_RANGES]

    wrong_range = _receipt((739, 744))
    assert not pilot_aggregation_is_ready([*receipts[:-1], wrong_range])

    changed_binding = deepcopy(receipts[-1])
    changed_binding["bindings"][0]["identity"] = "changed"  # type: ignore[index]
    assert not pilot_aggregation_is_ready([*receipts[:-1], changed_binding])


def test_invalid_range_and_incomplete_complete_receipt_are_rejected() -> None:
    with pytest.raises(ValueError, match="invalid contiguous page range"):
        contiguous_range_key((5, 4))
    with pytest.raises(ValueError, match="semantic_digest"):
        build_range_receipt(
            (1, 5),
            status="complete",
            bindings=BINDINGS,
            digests=DIGESTS,
            files=[{"path": "range.jsonl", "byte_size": 1}],
            semantic_digest=None,
        )
