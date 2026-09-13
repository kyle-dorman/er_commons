"""Authority-aware references for imported documents and collection outputs."""

from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path, PurePosixPath
from typing import Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.collection_processing.contract import JsonObject
from er_commons.collection_processing.inventory_closure import (
    verify_managed_inventory_closure,
)

CollectionAuthority = Literal["document_input_root", "collection_output_root"]

_PROHIBITED_SUFFIXES = frozenset(
    {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
        ".webp",
        ".jp2",
        ".safetensors",
        ".pt",
        ".pth",
        ".bin",
        ".onnx",
        ".gguf",
    }
)


class CollectionArtifactReference(BaseModel):
    """One exact file reference beneath a named collection authority."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authority: CollectionAuthority
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(ge=0)

    @model_validator(mode="after")
    def require_normalized_posix_path(self) -> Self:
        """Reject ambiguous, absolute, and parent-traversing reference paths."""
        pure = PurePosixPath(self.path)
        if (
            pure.is_absolute()
            or pure == PurePosixPath(".")
            or ".." in pure.parts
            or "\\" in self.path
            or pure.as_posix() != self.path
        ):
            raise ValueError("collection artifact reference path must be normalized POSIX")
        return self


class CollectionArtifactResolver:
    """Resolve exact references without conflating retained and new roots."""

    def __init__(self, *, document_input_root: Path, collection_output_root: Path) -> None:
        self._roots: dict[CollectionAuthority, Path] = {
            "document_input_root": self._checked_root(document_input_root, "document_input_root"),
            "collection_output_root": self._checked_root(
                collection_output_root, "collection_output_root"
            ),
        }
        if self._roots["document_input_root"] == self._roots["collection_output_root"]:
            raise ValueError("collection artifact authorities must name distinct roots")

    @staticmethod
    def _checked_root(path: Path, authority: CollectionAuthority) -> Path:
        if path.exists():
            if path.is_symlink() or not path.is_dir():
                raise ValueError(
                    f"collection artifact authority is not a real directory: {authority}"
                )
            return path.resolve()
        if authority == "document_input_root":
            raise ValueError(f"collection artifact authority is not a real directory: {authority}")
        parent = path.parent
        if parent.is_symlink() or not parent.is_dir():
            raise ValueError("absent collection output requires a real existing parent")
        resolved_parent = parent.resolve()
        return resolved_parent / path.name

    def resolve(
        self,
        reference: CollectionArtifactReference | JsonObject,
        *,
        expected_authority: CollectionAuthority | None = None,
    ) -> Path:
        """Verify authority, containment, regular-file status, size, and digest."""
        resolved, item = self._checked_path(reference, expected_authority=expected_authority)
        digest = hashlib.sha256()
        with resolved.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != item.sha256:
            raise ValueError(f"collection artifact checksum differs: {item.path}")
        return resolved

    def _checked_path(
        self,
        reference: CollectionArtifactReference | JsonObject,
        *,
        expected_authority: CollectionAuthority | None,
    ) -> tuple[Path, CollectionArtifactReference]:
        """Validate authority, path form, containment, file type, and size."""
        item = (
            reference
            if isinstance(reference, CollectionArtifactReference)
            else CollectionArtifactReference.model_validate(reference)
        )
        if expected_authority is not None and item.authority != expected_authority:
            raise ValueError(
                "collection artifact reference uses the wrong authority: "
                f"expected={expected_authority} observed={item.authority}"
            )
        relative = PurePosixPath(item.path)
        if relative.suffix.lower() in _PROHIBITED_SUFFIXES:
            raise ValueError(f"prohibited source/model payload access: {item.path}")
        root = self._roots[item.authority]
        candidate = root.joinpath(*relative.parts)
        self._reject_symlink_components(root, relative)
        try:
            metadata = candidate.stat()
        except FileNotFoundError as error:
            raise ValueError(f"collection artifact is absent: {item.path}") from error
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError(f"collection artifact is not a regular file: {item.path}")
        resolved = candidate.resolve()
        if not resolved.is_relative_to(root):
            raise ValueError(f"collection artifact escapes its authority: {item.path}")
        if metadata.st_size != item.byte_size:
            raise ValueError(f"collection artifact byte size differs: {item.path}")
        return resolved, item

    @staticmethod
    def _reject_symlink_components(root: Path, relative: PurePosixPath) -> None:
        current = root
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                raise ValueError(f"collection artifact path contains a symlink: {relative}")

    def read(
        self,
        reference: CollectionArtifactReference | JsonObject,
        *,
        expected_authority: CollectionAuthority | None = None,
    ) -> bytes:
        """Return exact verified compact bytes from the declared authority."""
        resolved, item = self._checked_path(reference, expected_authority=expected_authority)
        value = resolved.read_bytes()
        if len(value) != item.byte_size:
            raise ValueError(f"collection artifact changed while reading: {item.path}")
        if hashlib.sha256(value).hexdigest() != item.sha256:
            raise ValueError(f"collection artifact checksum differs: {item.path}")
        return value

    def read_json(
        self,
        reference: CollectionArtifactReference | JsonObject,
        *,
        expected_authority: CollectionAuthority | None = None,
    ) -> JsonObject:
        """Return one verified JSON object from the declared authority."""
        value = json.loads(self.read(reference, expected_authority=expected_authority))
        if not isinstance(value, dict):
            raise ValueError("collection artifact must contain a JSON object")
        return cast(JsonObject, value)

    def read_jsonl(
        self,
        reference: CollectionArtifactReference | JsonObject,
        *,
        expected_authority: CollectionAuthority | None = None,
    ) -> list[JsonObject]:
        """Return verified JSON-object lines from the declared authority."""
        raw = self.read(reference, expected_authority=expected_authority)
        rows: list[JsonObject] = []
        for line in raw.splitlines():
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError("collection JSONL artifact must contain objects")
            rows.append(cast(JsonObject, value))
        return rows

    def verify_managed_inventory(
        self,
        *,
        root_relative_path: str,
        inventory: JsonObject,
        expected_authority: CollectionAuthority,
    ) -> None:
        """Verify exact managed membership and sizes without reading payload files."""
        verify_managed_inventory_closure(
            authority_root=self._roots[expected_authority],
            root_relative_path=root_relative_path,
            inventory=inventory,
        )


__all__ = [
    "CollectionArtifactReference",
    "CollectionArtifactResolver",
    "CollectionAuthority",
]
