"""Stable digest and failure primitives for corpus-contract v1.1."""

from __future__ import annotations

import hashlib
from pathlib import PurePosixPath
from typing import Any, Never

import rfc8785

from er_commons.corpus_extraction_contract_v1_1.errors import CorpusExtractionContractError
from er_commons.corpus_extraction_contract_v1_1.model import ArtifactReader, JsonObject


def fail(code: str, detail: str, *, subject: str | None = None) -> Never:
    """Raise one stable contract failure with optional subject context."""
    raise CorpusExtractionContractError(code, detail, subject=subject)


def canonical_sha256(value: Any) -> str:
    """Hash one JSON-compatible value after RFC 8785 serialization."""
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def bytes_sha256(value: bytes) -> str:
    """Hash exact serialized artifact bytes."""
    return hashlib.sha256(value).hexdigest()


def verify_ref(reference: JsonObject, reader: ArtifactReader) -> bytes:
    """Read and verify one closed path, size, and SHA-256 artifact reference."""
    if set(reference) != {"path", "sha256", "byte_size"}:
        fail("artifact_reference", "sealed artifact reference fields differ")
    path = reference["path"]
    digest = reference["sha256"]
    if (
        not isinstance(path, str)
        or not path
        or PurePosixPath(path).is_absolute()
        or ".." in PurePosixPath(path).parts
        or not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
        or not isinstance(reference["byte_size"], int)
        or isinstance(reference["byte_size"], bool)
        or reference["byte_size"] < 0
    ):
        fail("artifact_reference", "sealed artifact reference values are invalid")
    value = reader.read_bytes(reference)
    if len(value) != reference["byte_size"] or bytes_sha256(value) != digest:
        fail("artifact_digest", "artifact bytes differ from their sealed reference")
    return value
