"""Small authority-aware references for repository and artifact-root records."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.artifact_io import sha256_file
from er_commons.artifact_verification import VerificationBudget


class AuthorityReference(BaseModel):
    """A closed file reference resolved beneath one explicitly named root."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authority: Literal["repository", "artifact_root"]
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(ge=0)

    @model_validator(mode="after")
    def require_contained_path(self) -> Self:
        """Reject absolute and parent-traversing paths before root resolution."""
        relative = Path(self.path)
        if relative.is_absolute() or ".." in relative.parts or relative == Path("."):
            raise ValueError("authority reference must contain a relative path")
        return self

    def resolve(
        self,
        *,
        repository_root: Path,
        artifact_root: Path,
        budget: VerificationBudget | None = None,
        role: str = "input_binding",
        source_id: str = "shared",
    ) -> Path:
        """Resolve and verify the named file under its declared authority."""
        root = (repository_root if self.authority == "repository" else artifact_root).resolve()
        path = (root / self.path).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"authority reference is absent or escapes its root: {self.path}")
        if path.stat().st_size != self.byte_size:
            raise ValueError(f"authority reference byte size differs: {self.path}")
        digest = (
            budget.hash_file(path, root=root, role=role, source_id=source_id)
            if budget is not None
            else sha256_file(path)
        )
        if digest != self.sha256:
            raise ValueError(f"authority reference SHA-256 differs: {self.path}")
        return path


def reference_for_path(
    path: Path, *, repository_root: Path, artifact_root: Path, sha256: str
) -> AuthorityReference:
    """Describe a verified path without guessing an authority outside known roots."""
    resolved = path.resolve()
    repository = repository_root.resolve()
    artifacts = artifact_root.resolve()
    if resolved.is_relative_to(artifacts):
        authority: Literal["repository", "artifact_root"] = "artifact_root"
        root = artifacts
    elif resolved.is_relative_to(repository):
        authority = "repository"
        root = repository
    else:
        raise ValueError(f"resolved specification is outside declared authorities: {path}")
    return AuthorityReference(
        authority=authority,
        path=resolved.relative_to(root).as_posix(),
        sha256=sha256,
        byte_size=resolved.stat().st_size,
    )


def authority_root_for_path(path: Path, *, repository_root: Path, artifact_root: Path) -> Path:
    """Return the declared containing root for a repository or artifact file."""
    resolved = path.resolve()
    artifacts = artifact_root.resolve()
    repository = repository_root.resolve()
    if resolved.is_relative_to(artifacts):
        return artifacts
    if resolved.is_relative_to(repository):
        return repository
    raise ValueError(f"path is outside repository and artifact roots: {path}")


__all__ = ["AuthorityReference", "authority_root_for_path", "reference_for_path"]
