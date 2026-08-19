"""Candidate identity and immutable-input policies."""

from __future__ import annotations

from er_commons.hierarchy_inference.bundle import HierarchyBundleView
from er_commons.hierarchy_inference.checks import require
from er_commons.hierarchy_inference.digests import canonical_json_sha256


def candidate_identity_matches_digest(view: HierarchyBundleView) -> None:
    """Bind the candidate ID to every immutable identity input."""
    identity = view.bundle["identity"]
    payload = {key: value for key, value in identity.items() if key != "candidate_id"}
    expected_id = f"hcorv1-{canonical_json_sha256(payload)}"
    require(identity["candidate_id"] == expected_id, "candidate identity digest differs")


def input_inventory_matches_identity(view: HierarchyBundleView) -> None:
    """Require verified source and producer seals to match candidate identity."""
    identity = view.bundle["identity"]
    inventory = view.bundle["input_inventory"]
    for field_name in (
        "source_sha256",
        "producer_completion_sha256",
        "producer_inventory_sha256",
        "conversion_completion_sha256",
        "conversion_inventory_sha256",
    ):
        require(
            inventory[field_name] == identity[field_name],
            f"input inventory {field_name} differs",
        )
