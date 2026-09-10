"""Typed production and fixture boundaries for Task 04 input discovery."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InputScopePolicy:
    """Readiness assertions required before Task 04 may bind upstream inputs."""

    expected_source_count: int
    required_readiness_status: str
    require_ordered_source_ids: bool = True

    def __post_init__(self) -> None:
        if self.expected_source_count < 1:
            raise ValueError("Task 04 input scope must contain at least one source")
        if not self.required_readiness_status.strip():
            raise ValueError("Task 04 input scope requires an accepted readiness status")

    @classmethod
    def production(cls) -> InputScopePolicy:
        """Return the accepted Brisbane Task 03H production boundary."""
        return cls(35, "ready_for_user_authorized_clean_run")

    @classmethod
    def synthetic_fixture(cls, *, source_count: int) -> InputScopePolicy:
        """Return an explicit non-production policy for source-free fixture tests."""
        return cls(source_count, "synthetic_fixture_ready")


__all__ = ["InputScopePolicy"]
