"""Canonical JSON digests used by correction and review records."""

from __future__ import annotations

import hashlib
from typing import Any

import rfc8785


def canonical_json_sha256(value: Any) -> str:
    """Return the SHA-256 over RFC 8785 canonical JSON bytes."""
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()
