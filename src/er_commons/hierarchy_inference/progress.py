"""Structured progress reporting for long hierarchy candidate assembly phases."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import StrEnum


class CandidatePhase(StrEnum):
    """Named candidate-assembly phases retained in logs and failed attempts."""

    SEMANTIC_SCHEMA_VALIDATION = "semantic_schema_validation"
    SEMANTIC_CROSS_RECORD_VALIDATION = "semantic_cross_record_validation"
    STREAMING_PUBLICATION = "streaming_publication"
    TERMINAL_VALIDATION = "terminal_validation"
    INVENTORY_SEAL = "inventory_seal"
    COMPLETION_SEAL = "completion_seal"
    DEEP_AUDIT = "deep_audit"


PHASE_UNITS = {
    CandidatePhase.SEMANTIC_SCHEMA_VALIDATION: "records",
    CandidatePhase.SEMANTIC_CROSS_RECORD_VALIDATION: "checks",
    CandidatePhase.STREAMING_PUBLICATION: "records",
    CandidatePhase.TERMINAL_VALIDATION: "checks",
    CandidatePhase.INVENTORY_SEAL: "files",
    CandidatePhase.COMPLETION_SEAL: "files",
    CandidatePhase.DEEP_AUDIT: "bytes",
}


@dataclass(frozen=True)
class ProgressSnapshot:
    """One phase-qualified progress observation with an explicit unit."""

    phase: CandidatePhase
    processed_units: int
    total_units: int
    unit: str

    def __post_init__(self) -> None:
        if self.total_units < 0 or not 0 <= self.processed_units <= self.total_units:
            raise ValueError("candidate assembly progress counts are invalid")
        if not self.unit:
            raise ValueError("candidate assembly progress unit is required")
        if self.unit != PHASE_UNITS[self.phase]:
            raise ValueError("candidate assembly progress unit differs from its phase")


@dataclass
class CandidateAssemblyProgress:
    """Log bounded phase progress with throughput and an evidence-based ETA."""

    logger: logging.Logger
    candidate_id: str
    report_interval_seconds: float = 30.0
    _phase: CandidatePhase | None = field(default=None, init=False)
    _started_at: float = field(default=0.0, init=False)
    _last_report_at: float = field(default=0.0, init=False)
    _last_snapshot: ProgressSnapshot | None = field(default=None, init=False)
    _total_units: int = field(default=0, init=False)
    _unit: str = field(default="", init=False)

    @property
    def last_snapshot(self) -> ProgressSnapshot | None:
        """Return the latest observation for durable failure evidence."""
        return self._last_snapshot

    def report(self, snapshot: ProgressSnapshot) -> None:
        """Report a phase boundary or throttled progress observation."""
        now = time.perf_counter()
        if snapshot.phase != self._phase:
            self._start_phase(snapshot, now)
        elif snapshot.total_units != self._total_units or snapshot.unit != self._unit:
            raise ValueError("candidate assembly phase changed its total or unit")
        elif (
            self._last_snapshot is not None
            and snapshot.processed_units < self._last_snapshot.processed_units
        ):
            raise ValueError("candidate assembly phase progress regressed")
        self._last_snapshot = snapshot
        elapsed = now - self._started_at
        complete = snapshot.processed_units == snapshot.total_units
        if not complete and now - self._last_report_at < self.report_interval_seconds:
            return
        throughput = snapshot.processed_units / elapsed if elapsed > 0 else 0.0
        remaining = snapshot.total_units - snapshot.processed_units
        eta = remaining / throughput if throughput > 0 else None
        self.logger.info(
            "Hierarchy candidate assembly phase=%s state=%s candidate_id=%s "
            "processed_units=%d total_units=%d elapsed_seconds=%.3f "
            "unit=%s throughput_units_per_second=%.3f eta_seconds=%s",
            snapshot.phase.value,
            "complete" if complete else "progress",
            self.candidate_id,
            snapshot.processed_units,
            snapshot.total_units,
            elapsed,
            snapshot.unit,
            throughput,
            "0.000" if complete else (f"{eta:.3f}" if eta is not None else "unknown"),
        )
        self._last_report_at = now
        self._total_units = snapshot.total_units
        self._unit = snapshot.unit

    def _start_phase(self, snapshot: ProgressSnapshot, now: float) -> None:
        """Start one named phase and reset its rate window."""
        self._phase = snapshot.phase
        self._started_at = now
        self._last_report_at = now
        self._total_units = snapshot.total_units
        self._unit = snapshot.unit
        self.logger.info(
            "Hierarchy candidate assembly phase=%s state=start candidate_id=%s "
            "processed_units=0 total_units=%d unit=%s",
            snapshot.phase.value,
            self.candidate_id,
            snapshot.total_units,
            snapshot.unit,
        )
