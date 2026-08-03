"""Readable primitives for reporting contract failures and stable digests."""

from __future__ import annotations

import hashlib
from typing import Any, Never

import rfc8785

from er_commons.corpus_extraction_contract.errors import CorpusExtractionContractError


def fail(code: str, detail: str, *, subject: str | None = None) -> Never:
    """Raise one stable, contextual contract error."""
    raise CorpusExtractionContractError(code, detail, subject=subject)


def canonical_sha256(value: Any) -> str:
    """Hash one JSON-compatible value after RFC 8785 serialization."""
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def bytes_sha256(value: bytes) -> str:
    """Hash bytes already read from a checked contract artifact."""
    return hashlib.sha256(value).hexdigest()
