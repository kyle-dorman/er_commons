"""Injectable source and document-publication verification adapters for Task 04."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from er_commons.artifact_io import sha256_file
from er_commons.document_publication.records import SourceIdentity
from er_commons.document_publication.storage import verify_candidate


@dataclass(frozen=True)
class CandidateSeal:
    """Checksums proving one candidate passed its owning publication verifier."""

    completion_sha256: str
    inventory_sha256: str


class CandidateVerifier(Protocol):
    """Verify document-publication identity, coverage, inventory, and closure."""

    def verify(self, candidate: Path, source: SourceIdentity) -> CandidateSeal:
        """Return exact terminal seals only after complete candidate verification."""
        ...


class SourceFileVerifier(Protocol):
    """Verify one existing source file against its sealed catalog identity."""

    def verify(self, source_pdf: Path, expected_sha256: str) -> str:
        """Return the verified checksum or raise with source-path context."""
        ...


class DocumentPublicationVerifier:
    """Narrow adapter over the owning document-publication candidate verifier."""

    def verify(self, candidate: Path, source: SourceIdentity) -> CandidateSeal:
        """Require identity, full coverage, inventory seal, bytes, and managed closure."""
        try:
            completion = verify_candidate(candidate, candidate.name, source)
        except Exception as error:
            raise ValueError(
                f"invalid document publication candidate {candidate}: {error}"
            ) from error
        inventory = candidate / "records" / "artifact_inventory.json"
        return CandidateSeal(sha256_file(completion), sha256_file(inventory))


class Sha256SourceFileVerifier:
    """Verify source PDF bytes before rendering or review identity binding."""

    def verify(self, source_pdf: Path, expected_sha256: str) -> str:
        """Reject any existing source PDF whose bytes differ from the catalog."""
        if not source_pdf.is_file():
            raise FileNotFoundError(source_pdf)
        actual = sha256_file(source_pdf)
        if actual != expected_sha256:
            raise ValueError(
                f"source PDF checksum differs for {source_pdf}: expected "
                f"{expected_sha256}, found {actual}"
            )
        return actual


__all__ = [
    "CandidateSeal",
    "CandidateVerifier",
    "DocumentPublicationVerifier",
    "Sha256SourceFileVerifier",
    "SourceFileVerifier",
]
