"""Render-identity preflight kept separate from the bounded renderer."""

from typing import Any

from er_commons.artifact_io import canonical_json_sha256


def validate_render_identity(
    render_id: str, identity_preimage: dict[str, Any], reused_render: dict[str, Any]
) -> None:
    """Reject identity or sealed-reuse drift before opening any source."""
    if render_id != "renderpackv1-" + canonical_json_sha256(identity_preimage):
        raise ValueError("Task 06H render ID differs from its identity preimage")
    if "reused_render" in identity_preimage and identity_preimage["reused_render"] != reused_render:
        raise ValueError("Task 06H reused render differs from its identity preimage")


__all__ = ["validate_render_identity"]
