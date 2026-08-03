"""Typed subordinate identities for restartable document extraction."""

from __future__ import annotations

from typing import Any

import rfc8785

from er_commons.corpus_extraction_contract.checks import bytes_sha256


def canonical_digest(value: Any) -> str:
    """Return SHA-256 over RFC 8785 canonical JSON bytes."""
    return bytes_sha256(rfc8785.dumps(value))


def typed_id(prefix: str, preimage: dict[str, Any]) -> str:
    """Derive a namespaced identity from a closed preimage."""
    return f"{prefix}-{canonical_digest(preimage)}"


def build_scope_id(*, run_spec_sha256: str, production_extraction_id: str) -> str:
    """Bind the declared document scope and operational policy."""
    return typed_id(
        "scopev1",
        {
            "schema_version": "er_commons.document_scope_identity.v1",
            "run_spec_sha256": run_spec_sha256,
            "production_extraction_id": production_extraction_id,
        },
    )


def build_transaction_id(*, scope_id: str, source_id: str, source_sha256: str, attempt: int) -> str:
    """Bind one source and monotonically numbered whole-document attempt."""
    return typed_id(
        "txv1",
        {
            "schema_version": "er_commons.document_transaction_identity.v1",
            "scope_id": scope_id,
            "source_id": source_id,
            "source_sha256": source_sha256,
            "attempt": attempt,
        },
    )


def build_candidate_id(
    *,
    production_extraction_id: str,
    source_id: str,
    content_digest: str,
    control_digest: str,
) -> str:
    """Bind completed stage-one managed content without attempt/self-reference."""
    return typed_id(
        "docv1",
        {
            "schema_version": "er_commons.document_candidate_identity.v1",
            "production_extraction_id": production_extraction_id,
            "source_id": source_id,
            "content_digest": content_digest,
            "control_digest": control_digest,
        },
    )
