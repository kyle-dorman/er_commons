"""Deterministic identity for one canonical interpretation of frozen PDFs."""

from __future__ import annotations

import hashlib
from typing import Any

import rfc8785


def extraction_identity_sha256(identity: dict[str, Any]) -> str:
    """Hash the normative identity fields with RFC 8785 and SHA-256.

    The derived ``extraction_id`` and ``identity_sha256`` fields are excluded
    so the identity does not recursively hash itself.
    """
    normative_fields = {
        key: value
        for key, value in identity.items()
        if key not in {"extraction_id", "identity_sha256"}
    }
    return hashlib.sha256(rfc8785.dumps(normative_fields)).hexdigest()
