"""Small immutable values shared by the amended corpus-contract validators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

type JsonObject = dict[str, Any]


class ArtifactReader(Protocol):
    """Read the exact bytes named by one contract artifact reference."""

    def read_bytes(self, reference: JsonObject) -> bytes:
        """Return bytes for the already scoped and contained reference."""
        ...


@dataclass(frozen=True)
class DerivedIdentity:
    """One verified typed identity and the exact closed preimage that derives it."""

    value: str
    preimage: JsonObject


@dataclass(frozen=True)
class IdentityPrefixes:
    """Typed prefixes retained by the corrective v1.1 executable amendment."""

    index: str = "idxv1"
    resolution: str = "resv1"
    handoff: str = "handoffv1"


PREFIXES = IdentityPrefixes()
