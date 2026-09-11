"""Finite resource ceilings for the separately authorized qualification gate."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AcquisitionLimits(BaseModel):
    """Finite ceilings fixed before any request; retries never occur implicitly."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    connect_timeout_seconds: float = Field(gt=0, le=60)
    read_timeout_seconds: float = Field(gt=0, le=120)
    total_timeout_seconds: float = Field(gt=0, le=3600)
    qualification_timeout_seconds: float = Field(gt=0, le=600)
    max_bytes: int = Field(gt=0, le=2 * 1024**3)
    minimum_free_bytes: int = Field(gt=0)
    max_temporary_plus_final_bytes: int = Field(gt=0)
    memory_bytes: int = Field(gt=0, le=32 * 1024**3)
    max_redirects: int = Field(default=3, ge=0, le=5)
    max_pdf_pages: int = Field(default=5000, ge=1, le=5000)
    retries: int = Field(default=0, ge=0, le=0)
    threads: int = Field(default=1, ge=1, le=1)

    @model_validator(mode="after")
    def validate_budget(self) -> AcquisitionLimits:
        """Reserve bounded metadata space in addition to one retained PDF."""
        if self.max_temporary_plus_final_bytes < self.max_bytes + 1024**2:
            raise ValueError("temporary-plus-final budget needs PDF ceiling plus 1 MiB metadata")
        if self.qualification_timeout_seconds > self.total_timeout_seconds:
            raise ValueError("qualification timeout exceeds total timeout")
        return self
