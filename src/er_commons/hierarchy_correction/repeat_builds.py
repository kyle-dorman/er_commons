"""Run, compare, and measure independent hierarchy-correction builds."""

from __future__ import annotations

import hashlib
import json
import statistics
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.hierarchy_correction.candidate_records import stable_json_bytes
from er_commons.hierarchy_correction.failures import RunStage, explicit_failure

JsonRecord = dict[str, Any]
STAGE_NAMES = ("features", "toc_reconciliation", "rules", "hierarchy", "publication")


@dataclass(frozen=True)
class BuildObservation:
    """One subprocess semantic result and its process-local measurements."""

    semantic: JsonRecord
    wall_seconds: float
    stage_wall_time_seconds: Mapping[str, float]
    peak_rss_bytes: int

    @classmethod
    def from_record(cls, value: object, output_path: Path) -> BuildObservation:
        """Validate the small subprocess protocol at its filesystem boundary."""
        if not isinstance(value, dict):
            raise ValueError(f"fresh hierarchy build returned a non-object: {output_path}")
        semantic = value.get("semantic")
        timings = value.get("stage_wall_time_seconds")
        if not isinstance(semantic, dict) or not isinstance(timings, dict):
            raise ValueError(f"fresh hierarchy build payload is malformed: {output_path}")
        if set(timings) != set(STAGE_NAMES):
            raise ValueError(f"fresh hierarchy build stage timings differ: {output_path}")
        return cls(
            semantic=semantic,
            wall_seconds=float(value["wall_seconds"]),
            stage_wall_time_seconds={name: float(timings[name]) for name in STAGE_NAMES},
            peak_rss_bytes=int(value["peak_rss_bytes"]),
        )


@dataclass(frozen=True)
class RepeatBuildResult:
    """Three byte-equal semantic builds plus their retained evidence."""

    builds: tuple[BuildObservation, BuildObservation, BuildObservation]
    evidence_root: Path
    comparison_path: Path

    @property
    def semantic(self) -> JsonRecord:
        """Return the representative semantic after equality has passed."""
        return self.builds[0].semantic

    @property
    def wall_times(self) -> tuple[float, float, float]:
        """Return fresh-build wall times in execution order."""
        return tuple(item.wall_seconds for item in self.builds)  # type: ignore[return-value]

    @property
    def peak_rss_bytes(self) -> int:
        """Return the largest process-local peak RSS observation."""
        return max(item.peak_rss_bytes for item in self.builds)

    def median_stage_times(self) -> dict[str, float]:
        """Reduce each named stage independently across the three runs."""
        return {
            name: statistics.median(item.stage_wall_time_seconds[name] for item in self.builds)
            for name in STAGE_NAMES
        }


def run_fresh_builds(
    data_root: Path,
    config_path: Path,
    evidence_root: Path,
    candidate_id: str,
) -> RepeatBuildResult:
    """Run three isolated processes and require byte-identical semantics."""
    if not candidate_id.startswith("hcorv1-"):
        raise ValueError("repeat-build evidence requires a candidate identity")
    evidence_root.mkdir(parents=True, exist_ok=False)
    builds: list[BuildObservation] = []
    output_paths: list[Path] = []
    for index in range(3):
        output_path = evidence_root / f"build-{index + 1}.json"
        command = _build_command(data_root, config_path, output_path)
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as error:
            details = [
                value.strip()
                for value in (error.stdout, error.stderr)
                if isinstance(value, str) and value.strip()
            ]
            details.append(str(error))
            raise explicit_failure(
                RunStage.FRESH_BUILDS,
                "UNKNOWN_REFERENCE",
                "\n".join(details),
            ) from error
        builds.append(
            BuildObservation.from_record(json.loads(output_path.read_text()), output_path)
        )
        output_paths.append(output_path)

    comparison_path, semantic_match = _write_repeat_comparison(
        evidence_root,
        candidate_id,
        output_paths,
        builds,
    )
    if not semantic_match:
        raise explicit_failure(
            RunStage.FRESH_BUILDS,
            "REPEAT_BUILD_MISMATCH",
            "fresh semantic builds differ",
        )
    return RepeatBuildResult(
        builds=(builds[0], builds[1], builds[2]),
        evidence_root=evidence_root,
        comparison_path=comparison_path,
    )


def _build_command(data_root: Path, config_path: Path, output_path: Path) -> list[str]:
    """Construct the explicit subprocess interface in one inspectable place."""
    return [
        sys.executable,
        "-m",
        "er_commons.hierarchy_correction.single_build",
        "--data-root",
        str(data_root),
        "--config",
        str(config_path),
        "--output",
        str(output_path),
    ]


def _write_repeat_comparison(
    evidence_root: Path,
    candidate_id: str,
    output_paths: list[Path],
    builds: list[BuildObservation],
) -> tuple[Path, bool]:
    """Persist exact build checksums and the normalized semantic disposition."""
    semantic_sha256 = [
        hashlib.sha256(stable_json_bytes(item.semantic)).hexdigest() for item in builds
    ]
    semantic_match = len(set(semantic_sha256)) == 1
    record = {
        "candidate_id": candidate_id,
        "normalization": {
            "comparison_payload": "semantic",
            "excluded_measurement_fields": [
                "peak_rss_bytes",
                "stage_wall_time_seconds",
                "wall_seconds",
            ],
        },
        "builds": [
            {
                "path": path.name,
                "byte_size": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "semantic_sha256": semantic_digest,
            }
            for path, semantic_digest in zip(output_paths, semantic_sha256, strict=True)
        ],
        "semantic_match": semantic_match,
    }
    path = evidence_root / "repeat_comparison.json"
    path.write_bytes(stable_json_bytes(record))
    return path, semantic_match
